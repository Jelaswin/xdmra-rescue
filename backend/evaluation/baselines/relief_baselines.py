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
    """Select the first warehouse that has stock for all items."""
    
    name = "first_stocked_warehouse"
    
    def select(self, scenario: ReliefScenario) -> ReliefBaselineResult:
        import time
        start_time = time.perf_counter()
        
        for wh in scenario.warehouses:
            if wh.get("operating_status") not in ["active", "limited"]:
                continue
            
            all_items_available = True
            for item_type, qty_needed in scenario.items.items():
                inventory = wh.get("inventory", {})
                available = inventory.get(item_type, 0)
                if available < qty_needed:
                    all_items_available = False
                    break
            
            if all_items_available:
                distance = haversine_distance(scenario.latitude, scenario.longitude, wh["latitude"], wh["longitude"])
                return ReliefBaselineResult(
                    algorithm=self.name,
                    scenario_id=scenario.scenario_id,
                    success=True,
                    warehouses_used=[wh["id"]],
                    fulfilment_pct=100.0,
                    shortage=0,
                    distance_km=distance,
                    stock_violations=0,
                    split_allocation=False,
                    computation_time_ms=(time.perf_counter() - start_time) * 1000
                )
        
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
            failure_reason="No single warehouse has complete stock"
        )


class NearestStockedWarehouseBaseline:
    """Select the nearest warehouse that has stock."""
    
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
                failure_reason="No eligible warehouses"
            )
        
        eligible.sort(key=lambda x: x[1])
        
        selected_wh, distance = eligible[0]
        
        total_needed = sum(scenario.items.values())
        total_available = sum(selected_wh.get("inventory", {}).get(item, 0) for item in scenario.items)
        
        if total_available >= total_needed:
            return ReliefBaselineResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=True,
                warehouses_used=[selected_wh["id"]],
                fulfilment_pct=100.0,
                shortage=0,
                distance_km=distance,
                stock_violations=0,
                split_allocation=False,
                computation_time_ms=(time.perf_counter() - start_time) * 1000
            )
        else:
            fulfilment = (total_available / total_needed * 100) if total_needed > 0 else 0
            return ReliefBaselineResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=True,
                warehouses_used=[selected_wh["id"]],
                fulfilment_pct=fulfilment,
                shortage=total_needed - total_available,
                distance_km=distance,
                stock_violations=0,
                split_allocation=False,
                computation_time_ms=(time.perf_counter() - start_time) * 1000
            )


class HighestStockCoverageBaseline:
    """Select warehouse with highest stock coverage percentage."""
    
    name = "highest_stock_coverage"
    
    def select(self, scenario: ReliefScenario) -> ReliefBaselineResult:
        import time
        start_time = time.perf_counter()
        
        candidates = []
        for wh in scenario.warehouses:
            if wh.get("operating_status") not in ["active", "limited"]:
                continue
            
            total_needed = sum(scenario.items.values())
            total_available = sum(wh.get("inventory", {}).get(item, 0) for item in scenario.items)
            coverage = (total_available / total_needed * 100) if total_needed > 0 else 0
            
            distance = haversine_distance(scenario.latitude, scenario.longitude, wh["latitude"], wh["longitude"])
            candidates.append((wh, coverage, distance))
        
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
                failure_reason="No eligible warehouses"
            )
        
        candidates.sort(key=lambda x: (-x[1], x[2]))
        selected_wh, coverage, distance = candidates[0]
        
        total_needed = sum(scenario.items.values())
        total_available = sum(selected_wh.get("inventory", {}).get(item, 0) for item in scenario.items)
        fulfilment = coverage
        shortage = max(0, total_needed - total_available)
        
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
            computation_time_ms=(time.perf_counter() - start_time) * 1000
        )


class SingleWarehouseOnlyBaseline:
    """Force single warehouse allocation even if it means shortages."""
    
    name = "single_warehouse_only"
    
    def select(self, scenario: ReliefScenario) -> ReliefBaselineResult:
        import time
        start_time = time.perf_counter()
        
        candidates = []
        for wh in scenario.warehouses:
            if wh.get("operating_status") not in ["active", "limited"]:
                continue
            total_available = sum(wh.get("inventory", {}).get(item, 0) for item in scenario.items)
            if total_available > 0:
                distance = haversine_distance(scenario.latitude, scenario.longitude, wh["latitude"], wh["longitude"])
                candidates.append((wh, total_available, distance))
        
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
                failure_reason="No warehouses with inventory"
            )
        
        candidates.sort(key=lambda x: (-x[1], x[2]))
        selected_wh, total_available, distance = candidates[0]
        
        total_needed = sum(scenario.items.values())
        fulfilment = min(100, (total_available / total_needed * 100)) if total_needed > 0 else 0
        shortage = max(0, total_needed - total_available)
        
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
            computation_time_ms=(time.perf_counter() - start_time) * 1000
        )


def get_all_relief_baselines() -> Dict[str, Any]:
    """Return all available relief baseline algorithms."""
    return {
        "first_stocked_warehouse": FirstStockedWarehouseBaseline(),
        "nearest_stocked_warehouse": NearestStockedWarehouseBaseline(),
        "highest_stock_coverage": HighestStockCoverageBaseline(),
        "single_warehouse_only": SingleWarehouseOnlyBaseline()
    }