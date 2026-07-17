"""
Relief Baseline Evaluation Strategies.

These are evaluation-only baseline algorithms that do NOT modify
the production X-DMRA allocation system.
"""

import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2


@dataclass
class ReliefScenario:
    """A test scenario for relief evaluation."""
    scenario_id: str
    incident_id: int
    items: Dict[str, int]  # item_type -> quantity needed
    total_people: int
    latitude: float
    longitude: float
    warehouses: List[Dict[str, Any]]  # Each with inventory


@dataclass
class ReliefBaselineResult:
    """Result from a relief baseline strategy."""
    algorithm: str
    scenario_id: str
    success: bool
    warehouses_used: List[int]
    fulfilment_pct: float
    shortage: int
    distance_km: float
    stock_violations: int
    split_allocation: bool
    computation_time_ms: float
    total_requested: int
    failure_reason: Optional[str] = None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate straight-line Haversine distance in km."""
    R = 6371.0
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c


class FirstStockedWarehouseBaseline:
    """Select the first warehouse that has complete stock for ALL requested items.
    
    A warehouse is selected only when it can supply ALL items from its own inventory.
    Partial fulfilment from multiple warehouses is NOT considered single-source success.
    """
    
    name = "first_stocked_warehouse"
    
    def select(self, scenario: ReliefScenario) -> ReliefBaselineResult:
        import time
        start_time = time.perf_counter()
        
        for wh in scenario.warehouses:
            if wh.get("operating_status") not in ["active", "limited"]:
                continue
            
            wh_inventory = wh.get("inventory", {})
            
            all_items_available = True
            per_item_supplies = {}
            total_supplied = 0
            total_requested = 0
            has_any_stock = False
            
            for item_type, qty_needed in scenario.items.items():
                total_requested += qty_needed
                available = wh_inventory.get(item_type, 0)
                if available > 0:
                    has_any_stock = True
                supplied = min(qty_needed, available)
                per_item_supplies[item_type] = supplied
                total_supplied += supplied
                if available < qty_needed:
                    all_items_available = False
            
            if not has_any_stock:
                continue
            
            if all_items_available and total_supplied > 0:
                distance = haversine_distance(scenario.latitude, scenario.longitude, wh["latitude"], wh["longitude"])
                shortage = max(0, total_requested - total_supplied)
                fulfilment = (total_supplied / total_requested * 100) if total_requested > 0 else 0
                return ReliefBaselineResult(
                    algorithm=self.name,
                    scenario_id=scenario.scenario_id,
                    success=True,
                    warehouses_used=[wh["id"]],
                    fulfilment_pct=fulfilment,
                    shortage=shortage,
                    distance_km=distance,
                    stock_violations=0,
                    split_allocation=False,
                    computation_time_ms=(time.perf_counter() - start_time) * 1000,
                    total_requested=total_requested
                )

        total_demand = sum(scenario.items.values())
        return ReliefBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=False,
            warehouses_used=[],
            fulfilment_pct=0.0,
            shortage=total_demand,
            distance_km=0.0,
            stock_violations=0,
            split_allocation=False,
            computation_time_ms=(time.perf_counter() - start_time) * 1000,
            failure_reason="No single warehouse has complete stock for all items",
            total_requested=total_demand
        )


class NearestStockedWarehouseBaseline:
    """Select the nearest warehouse that has stock.
    
    Uses per-item min(requested, available) to compute total supplied.
    Excess of one item CANNOT compensate for shortage of another.
    """
    
    name = "nearest_stocked_warehouse"
    
    def select(self, scenario: ReliefScenario) -> ReliefBaselineResult:
        import time
        start_time = time.perf_counter()
        
        eligible = []
        for wh in scenario.warehouses:
            if wh.get("operating_status") not in ["active", "limited"]:
                continue
            distance = haversine_distance(scenario.latitude, scenario.longitude, wh["latitude"], wh["longitude"])
            eligible.append((wh, distance))
        
        if not eligible:
            return ReliefBaselineResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                warehouses_used=[],
                fulfilment_pct=0.0,
                shortage=sum(scenario.items.values()),
                distance_km=0.0,
                stock_violations=0,
                split_allocation=False,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="No eligible warehouses",
                total_requested=sum(scenario.items.values())
            )

        eligible.sort(key=lambda x: x[1])
        selected_wh, distance = eligible[0]
        wh_inventory = selected_wh.get("inventory", {})

        total_requested = sum(scenario.items.values())
        total_supplied = 0
        for item_type, qty_needed in scenario.items.items():
            available = wh_inventory.get(item_type, 0)
            total_supplied += min(qty_needed, available)

        if total_supplied > 0:
            fulfilment = (total_supplied / total_requested * 100) if total_requested > 0 else 0
            shortage = max(0, total_requested - total_supplied)
            return ReliefBaselineResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=True,
                warehouses_used=[selected_wh["id"]],
                fulfilment_pct=fulfilment,
                shortage=shortage,
                distance_km=distance,
                stock_violations=0,
                split_allocation=False,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                total_requested=total_requested
            )
        else:
            return ReliefBaselineResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                warehouses_used=[],
                fulfilment_pct=0.0,
                shortage=total_requested,
                distance_km=distance,
                stock_violations=0,
                split_allocation=False,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="No items available at nearest warehouse",
                total_requested=total_requested
            )


class HighestStockCoverageBaseline:
    """Select warehouse with highest per-item coverage percentage.

    Per-item coverage = min(requested[item], available[item])
    Total supplied = sum of per-item coverage
    Fulfilment = total_supplied / total_requested (capped at 100% per warehouse)

    Excess of one item CANNOT compensate for shortage of another.
    """

    name = "highest_stock_coverage"

    def select(self, scenario: ReliefScenario) -> ReliefBaselineResult:
        import time
        start_time = time.perf_counter()

        total_requested = sum(scenario.items.values())

        candidates = []
        for wh in scenario.warehouses:
            if wh.get("operating_status") not in ["active", "limited"]:
                continue

            wh_inventory = wh.get("inventory", {})
            total_supplied = 0

            for item_type, qty_needed in scenario.items.items():
                available = wh_inventory.get(item_type, 0)
                supplied = min(qty_needed, available)
                total_supplied += supplied

            coverage_pct = (total_supplied / total_requested * 100) if total_requested > 0 else 0
            distance = haversine_distance(scenario.latitude, scenario.longitude, wh["latitude"], wh["longitude"])
            candidates.append((wh, total_supplied, coverage_pct, distance))

        if not candidates:
            return ReliefBaselineResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                warehouses_used=[],
                fulfilment_pct=0.0,
                shortage=total_requested,
                distance_km=0.0,
                stock_violations=0,
                split_allocation=False,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="No eligible warehouses",
                total_requested=total_requested
            )

        candidates.sort(key=lambda x: (-x[2], x[3]))
        selected_wh, total_supplied, coverage_pct, distance = candidates[0]

        fulfilment = coverage_pct
        shortage = max(0, total_requested - total_supplied)

        return ReliefBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            warehouses_used=[selected_wh["id"]],
            fulfilment_pct=fulfilment,
            shortage=shortage,
            distance_km=distance,
            stock_violations=0,
            split_allocation=False,
            computation_time_ms=(time.perf_counter() - start_time) * 1000,
            total_requested=total_requested
        )


class SingleWarehouseOnlyBaseline:
    """Force single warehouse allocation even if it means shortages.
    
    Uses per-item min(requested, available) - CANNOT exceed per-item demand.
    Excess of one item CANNOT compensate for shortage of another.
    """
    
    name = "single_warehouse_only"
    
    def select(self, scenario: ReliefScenario) -> ReliefBaselineResult:
        import time
        start_time = time.perf_counter()
        
        candidates = []
        for wh in scenario.warehouses:
            if wh.get("operating_status") not in ["active", "limited"]:
                continue
            wh_inventory = wh.get("inventory", {})
            total_supplied = 0
            for item_type, qty_needed in scenario.items.items():
                available = wh_inventory.get(item_type, 0)
                total_supplied += min(qty_needed, available)
            if total_supplied > 0:
                distance = haversine_distance(scenario.latitude, scenario.longitude, wh["latitude"], wh["longitude"])
                candidates.append((wh, total_supplied, distance))
        
        if not candidates:
            return ReliefBaselineResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                warehouses_used=[],
                fulfilment_pct=0.0,
                shortage=sum(scenario.items.values()),
                distance_km=0.0,
                stock_violations=0,
                split_allocation=False,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="No warehouses with inventory",
                total_requested=sum(scenario.items.values())
            )

        candidates.sort(key=lambda x: (-x[1], x[2]))
        selected_wh, total_supplied, distance = candidates[0]

        total_requested = sum(scenario.items.values())
        fulfilment = min(100, (total_supplied / total_requested * 100)) if total_requested > 0 else 0
        shortage = max(0, total_requested - total_supplied)

        return ReliefBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            warehouses_used=[selected_wh["id"]],
            fulfilment_pct=fulfilment,
            shortage=shortage,
            distance_km=distance,
            stock_violations=0,
            split_allocation=False,
            computation_time_ms=(time.perf_counter() - start_time) * 1000,
            total_requested=total_requested
        )


def get_all_relief_baselines() -> Dict[str, Any]:
    """Return all available relief baseline algorithms."""
    return {
        "first_stocked_warehouse": FirstStockedWarehouseBaseline(),
        "nearest_stocked_warehouse": NearestStockedWarehouseBaseline(),
        "highest_stock_coverage": HighestStockCoverageBaseline(),
        "single_warehouse_only": SingleWarehouseOnlyBaseline()
    }