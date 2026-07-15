from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database import Base

class IncidentSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class IncidentStatus(str, enum.Enum):
    reported = "reported"
    verified = "verified"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"

class TeamAvailability(str, enum.Enum):
    available = "available"
    assigned = "assigned"
    unavailable = "unavailable"

class AllocationStatus(str, enum.Enum):
    recommended = "recommended"
    approved = "approved"
    dispatched = "dispatched"
    completed = "completed"
    cancelled = "cancelled"
    superseded = "superseded"
    reallocated = "reallocated"

class ReallocationStatus(str, enum.Enum):
    detected = "detected"
    recommended = "recommended"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"

class RouteRisk(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    blocked = "blocked"

class LocationAccuracy(str, enum.Enum):
    exact_gps = "exact_gps"
    confirmed_landmark = "confirmed_landmark"
    approximate_area = "approximate_area"
    unknown = "unknown"

class LocationSource(str, enum.Enum):
    map_click = "map_click"
    place_search = "place_search"
    shared_gps = "shared_gps"
    manual_coordinates = "manual_coordinates"
    imported_report = "imported_report"

def utcnow():
    return datetime.now(timezone.utc)

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    incident_type = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    severity = Column(Enum(IncidentSeverity), nullable=False)
    affected_people = Column(Integer, default=0)
    injured_people = Column(Integer, default=0)
    vulnerable_people = Column(Integer, default=0)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.reported)
    
    # Phase 2 Added fields
    trapped_people = Column(Integer, default=0)
    children_count = Column(Integer, default=0)
    elderly_count = Column(Integer, default=0)
    required_skills = Column(JSON, default=list)
    required_equipment = Column(JSON, default=list)
    priority_score = Column(Float, nullable=True)
    priority_level = Column(String, nullable=True) # low, medium, high, critical
    priority_reasons = Column(JSON, default=list)

    # Phase 3 ML fields
    ml_priority_level = Column(String, nullable=True)
    ml_priority_confidence = Column(Float, nullable=True)
    ml_model_name = Column(String, nullable=True)
    ml_model_version = Column(String, nullable=True)
    ml_predicted_at = Column(DateTime, nullable=True)
    priority_agreement_status = Column(String, nullable=True)
    requires_priority_review = Column(Integer, default=0) # bool

    # Phase 4 Location fields
    location_name = Column(String, nullable=True)
    location_accuracy = Column(Enum(LocationAccuracy), nullable=True)
    location_source = Column(Enum(LocationSource), nullable=True)
    location_notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    allocations = relationship("Allocation", back_populates="incident")

class RescueTeam(Base):
    __tablename__ = "rescue_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    skills = Column(JSON, nullable=False)
    equipment = Column(JSON, nullable=False)
    capacity = Column(Integer, nullable=False)
    current_workload = Column(Integer, default=0)
    availability_status = Column(Enum(TeamAvailability), default=TeamAvailability.available)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    allocations = relationship("Allocation", back_populates="rescue_team")

class Allocation(Base):
    __tablename__ = "allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    rescue_team_id = Column(Integer, ForeignKey("rescue_teams.id"), nullable=False)
    status = Column(Enum(AllocationStatus), default=AllocationStatus.recommended)
    
    # Phase 2 Added fields
    recommendation_score = Column(Float, nullable=True)
    explanation = Column(String, nullable=True)
    
    # Phase 5 Added fields
    superseded_by_allocation_id = Column(Integer, ForeignKey("allocations.id"), nullable=True)
    supersedes_allocation_id = Column(Integer, ForeignKey("allocations.id"), nullable=True)
    ended_at = Column(DateTime, nullable=True)
    termination_reason = Column(String, nullable=True)
    reallocation_reason = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    incident = relationship("Incident", back_populates="allocations")
    rescue_team = relationship("RescueTeam", back_populates="allocations")

class RouteCondition(Base):
    __tablename__ = "route_conditions"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    rescue_team_id = Column(Integer, ForeignKey("rescue_teams.id"), nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    risk_level = Column(Enum(RouteRisk), nullable=False, default=RouteRisk.low)
    is_blocked = Column(Integer, default=0) # boolean stored as integer for sqlite compat 
    estimated_delay_minutes = Column(Integer, default=0)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class ReallocationEvent(Base):
    __tablename__ = "reallocation_events"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    previous_allocation_id = Column(Integer, ForeignKey("allocations.id"), nullable=False)
    previous_team_id = Column(Integer, ForeignKey("rescue_teams.id"), nullable=False)
    replacement_team_id = Column(Integer, ForeignKey("rescue_teams.id"), nullable=True)
    trigger_type = Column(String, nullable=False)
    trigger_description = Column(String, nullable=True)
    old_recommendation_score = Column(Float, nullable=True)
    new_recommendation_score = Column(Float, nullable=True)
    explanation = Column(String, nullable=True)
    status = Column(Enum(ReallocationStatus), default=ReallocationStatus.detected)
    created_at = Column(DateTime, default=utcnow)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)


# --- Phase 6 Relief Models ---

class WarehouseOperatingStatus(str, enum.Enum):
    active = "active"
    limited = "limited"
    closed = "closed"
    unavailable = "unavailable"

class ReliefRequestStatus(str, enum.Enum):
    draft = "draft"
    confirmed = "confirmed"
    recommended = "recommended"
    partially_allocated = "partially_allocated"
    allocated = "allocated"
    dispatched = "dispatched"
    completed = "completed"
    cancelled = "cancelled"

class ReliefSourceType(str, enum.Enum):
    system_suggested = "system_suggested"
    officer_entered = "officer_entered"
    officer_modified = "officer_modified"

class VehicleAvailability(str, enum.Enum):
    available = "available"
    assigned = "assigned"
    unavailable = "unavailable"
    maintenance = "maintenance"

class DispatchStatus(str, enum.Enum):
    approved = "approved"
    preparing = "preparing"
    dispatched = "dispatched"
    delivered = "delivered"
    cancelled = "cancelled"
    failed = "failed"

class InventoryMovementType(str, enum.Enum):
    stock_added = "stock_added"
    reserved = "reserved"
    reservation_released = "reservation_released"
    dispatched = "dispatched"
    delivered = "delivered"
    correction = "correction"
    expired = "expired"

class Warehouse(Base):
    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    location_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    warehouse_type = Column(String, nullable=True)
    operating_status = Column(Enum(WarehouseOperatingStatus), default=WarehouseOperatingStatus.active)
    maximum_dispatch_capacity = Column(Integer, default=0)
    current_dispatch_workload = Column(Integer, default=0)
    contact_reference = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class ReliefInventory(Base):
    __tablename__ = "relief_inventory"
    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    item_type = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    quantity_available = Column(Integer, default=0)
    quantity_reserved = Column(Integer, default=0)
    reorder_level = Column(Integer, default=0)
    expiry_date = Column(DateTime, nullable=True)
    batch_reference = Column(String, nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class ReliefRequest(Base):
    __tablename__ = "relief_requests"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    support_duration_days = Column(Integer, default=1)
    status = Column(Enum(ReliefRequestStatus), default=ReliefRequestStatus.draft)
    generated_by = Column(String, nullable=True)
    total_people = Column(Integer, default=0)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class ReliefRequestItem(Base):
    __tablename__ = "relief_request_items"
    id = Column(Integer, primary_key=True, index=True)
    relief_request_id = Column(Integer, ForeignKey("relief_requests.id"), nullable=False)
    item_type = Column(String, nullable=False)
    requested_quantity = Column(Integer, default=0)
    approved_quantity = Column(Integer, default=0)
    source_type = Column(Enum(ReliefSourceType), default=ReliefSourceType.system_suggested)
    calculation_reason = Column(String, nullable=True)

class DeliveryVehicle(Base):
    __tablename__ = "delivery_vehicles"
    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    name = Column(String, nullable=False)
    vehicle_type = Column(String, nullable=True)
    capacity_units = Column(Integer, default=0)
    availability_status = Column(Enum(VehicleAvailability), default=VehicleAvailability.available)
    current_workload = Column(Integer, default=0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class ReliefRecommendation(Base):
    __tablename__ = "relief_recommendations"
    id = Column(Integer, primary_key=True, index=True)
    relief_request_id = Column(Integer, ForeignKey("relief_requests.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    recommendation_score = Column(Float, default=0.0)
    stock_coverage_percentage = Column(Float, default=0.0)
    distance_km = Column(Float, default=0.0)
    route_risk = Column(String, nullable=True)
    delivery_capacity_score = Column(Float, default=0.0)
    workload_score = Column(Float, default=0.0)
    explanation = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)

class ReliefDispatch(Base):
    __tablename__ = "relief_dispatches"
    id = Column(Integer, primary_key=True, index=True)
    relief_request_id = Column(Integer, ForeignKey("relief_requests.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("delivery_vehicles.id"), nullable=True)
    status = Column(Enum(DispatchStatus), default=DispatchStatus.approved)
    dispatch_reference = Column(String, nullable=True)
    total_allocated_units = Column(Integer, default=0)
    recommendation_score = Column(Float, nullable=True)
    explanation = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class ReliefDispatchItem(Base):
    __tablename__ = "relief_dispatch_items"
    id = Column(Integer, primary_key=True, index=True)
    relief_dispatch_id = Column(Integer, ForeignKey("relief_dispatches.id"), nullable=False)
    inventory_id = Column(Integer, ForeignKey("relief_inventory.id"), nullable=False)
    item_type = Column(String, nullable=False)
    allocated_quantity = Column(Integer, default=0)
    unit = Column(String, nullable=True)

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("relief_inventory.id"), nullable=False)
    relief_dispatch_id = Column(Integer, ForeignKey("relief_dispatches.id"), nullable=True)
    movement_type = Column(Enum(InventoryMovementType), nullable=False)
    quantity = Column(Integer, default=0)
    quantity_before = Column(Integer, default=0)
    quantity_after = Column(Integer, default=0)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)

# --- Phase 7 Shelter Allocation Models ---

class ShelterOperatingStatus(str, enum.Enum):
    open = "open"
    limited = "limited"
    full = "full"
    closed = "closed"
    unavailable = "unavailable"

class ShelterRequestStatus(str, enum.Enum):
    draft = "draft"
    confirmed = "confirmed"
    recommended = "recommended"
    partially_allocated = "partially_allocated"
    allocated = "allocated"
    in_transit = "in_transit"
    admitted = "admitted"
    completed = "completed"
    cancelled = "cancelled"

class ShelterReservationStatus(str, enum.Enum):
    approved = "approved"
    preparing = "preparing"
    in_transit = "in_transit"
    admitted = "admitted"
    cancelled = "cancelled"
    completed = "completed"
    failed = "failed"

class ShelterCapacityMovementType(str, enum.Enum):
    reserved = "reserved"
    reservation_released = "reservation_released"
    admitted = "admitted"
    discharged = "discharged"
    correction = "correction"
    transferred = "transferred"

class EmergencyShelter(Base):
    __tablename__ = "emergency_shelters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    shelter_type = Column(String, nullable=True)
    location_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    operating_status = Column(Enum(ShelterOperatingStatus), default=ShelterOperatingStatus.open)
    
    total_capacity = Column(Integer, default=0)
    occupied_capacity = Column(Integer, default=0)
    reserved_capacity = Column(Integer, default=0)
    maximum_daily_intake = Column(Integer, default=0)
    current_intake_workload = Column(Integer, default=0)
    
    has_medical_support = Column(Integer, default=0) # boolean
    has_accessibility_support = Column(Integer, default=0)
    has_women_child_safe_area = Column(Integer, default=0)
    has_food = Column(Integer, default=0)
    has_drinking_water = Column(Integer, default=0)
    has_power_backup = Column(Integer, default=0)
    has_sanitation = Column(Integer, default=0)
    supports_long_term_stay = Column(Integer, default=0)
    
    contact_reference = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class ShelterRequest(Base):
    __tablename__ = "shelter_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    total_displaced_people = Column(Integer, default=0)
    adults = Column(Integer, default=0)
    children = Column(Integer, default=0)
    elderly_people = Column(Integer, default=0)
    injured_people = Column(Integer, default=0)
    accessibility_required = Column(Integer, default=0)
    pregnant_women = Column(Integer, default=0)
    medical_observation_required = Column(Integer, default=0)
    household_count = Column(Integer, default=0)
    expected_stay_days = Column(Integer, default=1)
    status = Column(Enum(ShelterRequestStatus), default=ShelterRequestStatus.draft)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class ShelterRecommendation(Base):
    __tablename__ = "shelter_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    shelter_request_id = Column(Integer, ForeignKey("shelter_requests.id"), nullable=False)
    shelter_id = Column(Integer, ForeignKey("emergency_shelters.id"), nullable=False)
    recommendation_score = Column(Float, default=0.0)
    available_capacity = Column(Integer, default=0)
    proposed_people_count = Column(Integer, default=0)
    distance_km = Column(Float, default=0.0)
    capacity_score = Column(Float, default=0.0)
    distance_score = Column(Float, default=0.0)
    medical_support_score = Column(Float, default=0.0)
    vulnerability_support_score = Column(Float, default=0.0)
    utility_score = Column(Float, default=0.0)
    overcrowding_risk_score = Column(Float, default=0.0)
    route_risk = Column(String, nullable=True)
    explanation = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)

class ShelterReservation(Base):
    __tablename__ = "shelter_reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    shelter_request_id = Column(Integer, ForeignKey("shelter_requests.id"), nullable=False)
    shelter_id = Column(Integer, ForeignKey("emergency_shelters.id"), nullable=False)
    reserved_people = Column(Integer, default=0)
    status = Column(Enum(ShelterReservationStatus), default=ShelterReservationStatus.approved)
    recommendation_score = Column(Float, nullable=True)
    explanation = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    admitted_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class ShelterCapacityMovement(Base):
    __tablename__ = "shelter_capacity_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    shelter_id = Column(Integer, ForeignKey("emergency_shelters.id"), nullable=False)
    shelter_reservation_id = Column(Integer, ForeignKey("shelter_reservations.id"), nullable=True)
    movement_type = Column(Enum(ShelterCapacityMovementType), nullable=False)
    people_count = Column(Integer, default=0)
    occupied_before = Column(Integer, default=0)
    occupied_after = Column(Integer, default=0)
    reserved_before = Column(Integer, default=0)
    reserved_after = Column(Integer, default=0)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)

class ShelterRouteCondition(Base):
    __tablename__ = "shelter_route_conditions"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    shelter_id = Column(Integer, ForeignKey("emergency_shelters.id"), nullable=False)
    risk_level = Column(Enum(RouteRisk), nullable=False, default=RouteRisk.low)
    is_blocked = Column(Integer, default=0) # bool
    estimated_delay_minutes = Column(Integer, default=0)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
