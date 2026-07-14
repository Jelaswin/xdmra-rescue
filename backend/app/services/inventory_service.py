from typing import List
from sqlalchemy.orm import Session
from app.models import (
    ReliefInventory, ReliefDispatch, ReliefDispatchItem, InventoryMovement,
    InventoryMovementType, DispatchStatus, Warehouse
)
from datetime import datetime, timezone
from fastapi import HTTPException

def utcnow():
    return datetime.now(timezone.utc)

def approve_dispatch(db: Session, request_id: int, warehouse_id: int, vehicle_id: int, items_payload: List[dict], recommendation_score: float, explanation: str) -> ReliefDispatch:
    """
    Transactional inventory reservation for a new dispatch.
    """
    total_units = sum(i["allocated_quantity"] for i in items_payload)
    
    dispatch = ReliefDispatch(
        relief_request_id=request_id,
        warehouse_id=warehouse_id,
        vehicle_id=vehicle_id,
        status=DispatchStatus.approved,
        total_allocated_units=total_units,
        recommendation_score=recommendation_score,
        explanation=explanation,
        approved_at=utcnow()
    )
    db.add(dispatch)
    db.flush() # get ID
    
    for item in items_payload:
        item_type = item["item_type"]
        qty = item["allocated_quantity"]
        
        # Get inventory (locked for update in a real DB, here just queried)
        inv = db.query(ReliefInventory).filter(
            ReliefInventory.warehouse_id == warehouse_id,
            ReliefInventory.item_type == item_type
        ).first()
        
        if not inv:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Item {item_type} not found in warehouse {warehouse_id}")
            
        avail = inv.quantity_available - inv.quantity_reserved
        if avail < qty:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {item_type}. Requested {qty}, available {avail}")
            
        qty_before = inv.quantity_reserved
        inv.quantity_reserved += qty
        
        # Record item
        dispatch_item = ReliefDispatchItem(
            relief_dispatch_id=dispatch.id,
            inventory_id=inv.id,
            item_type=item_type,
            allocated_quantity=qty,
            unit=inv.unit
        )
        db.add(dispatch_item)
        
        # Record movement
        movement = InventoryMovement(
            inventory_id=inv.id,
            relief_dispatch_id=dispatch.id,
            movement_type=InventoryMovementType.reserved,
            quantity=qty,
            quantity_before=qty_before,
            quantity_after=inv.quantity_reserved,
            reason="Dispatch approved and stock reserved"
        )
        db.add(movement)
        
    db.commit()
    db.refresh(dispatch)
    return dispatch

def transition_dispatch_status(db: Session, dispatch_id: int, new_status: DispatchStatus):
    dispatch = db.query(ReliefDispatch).filter(ReliefDispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
        
    old_status = dispatch.status
    if old_status == new_status:
        return dispatch
        
    dispatch.status = new_status
    dispatch.updated_at = utcnow()
    
    if new_status == DispatchStatus.dispatched:
        dispatch.dispatched_at = utcnow()
        # Stock is still physically in transit, but we mark it as dispatched in movement history
        _record_bulk_movement(db, dispatch, InventoryMovementType.dispatched, "Stock dispatched from warehouse")
        
    elif new_status == DispatchStatus.delivered:
        dispatch.completed_at = utcnow()
        # Finalize deduction
        items = db.query(ReliefDispatchItem).filter(ReliefDispatchItem.relief_dispatch_id == dispatch.id).all()
        for item in items:
            inv = db.query(ReliefInventory).filter(ReliefInventory.id == item.inventory_id).first()
            inv.quantity_available -= item.allocated_quantity
            inv.quantity_reserved -= item.allocated_quantity
            db.add(InventoryMovement(
                inventory_id=inv.id,
                relief_dispatch_id=dispatch.id,
                movement_type=InventoryMovementType.delivered,
                quantity=item.allocated_quantity,
                quantity_before=inv.quantity_available + item.allocated_quantity,
                quantity_after=inv.quantity_available,
                reason="Stock delivered and finalized"
            ))
            
    elif new_status in [DispatchStatus.cancelled, DispatchStatus.failed]:
        # Release reservations
        if old_status not in [DispatchStatus.delivered]:
            items = db.query(ReliefDispatchItem).filter(ReliefDispatchItem.relief_dispatch_id == dispatch.id).all()
            for item in items:
                inv = db.query(ReliefInventory).filter(ReliefInventory.id == item.inventory_id).first()
                qty_before = inv.quantity_reserved
                inv.quantity_reserved -= item.allocated_quantity
                db.add(InventoryMovement(
                    inventory_id=inv.id,
                    relief_dispatch_id=dispatch.id,
                    movement_type=InventoryMovementType.reservation_released,
                    quantity=item.allocated_quantity,
                    quantity_before=qty_before,
                    quantity_after=inv.quantity_reserved,
                    reason=f"Dispatch {new_status}, reservation released"
                ))

    db.commit()
    db.refresh(dispatch)
    return dispatch

def _record_bulk_movement(db: Session, dispatch: ReliefDispatch, movement_type: InventoryMovementType, reason: str):
    items = db.query(ReliefDispatchItem).filter(ReliefDispatchItem.relief_dispatch_id == dispatch.id).all()
    for item in items:
        # We don't change inventory numbers here, just record the lifecycle state
        db.add(InventoryMovement(
            inventory_id=item.inventory_id,
            relief_dispatch_id=dispatch.id,
            movement_type=movement_type,
            quantity=item.allocated_quantity,
            quantity_before=item.allocated_quantity, # NA
            quantity_after=item.allocated_quantity, # NA
            reason=reason
        ))
