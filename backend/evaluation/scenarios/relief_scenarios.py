"""
Deterministic Relief Evaluation Scenarios.

20+ scenarios covering various relief allocation conditions.
All scenarios are deterministic and reproducible.
"""

from typing import List, Dict, Any
from ..baselines.relief_baselines import ReliefScenario


def _std_vehicles():
    return [
        {"id": 1, "capacity_units": 500, "availability_status": "available"},
        {"id": 2, "capacity_units": 500, "availability_status": "available"},
    ]


def get_relief_scenarios() -> List[ReliefScenario]:
    """Return all deterministic relief evaluation scenarios."""
    return [
        # 1. Single warehouse has complete stock
        ReliefScenario(
            scenario_id="relief_001",
            incident_id=1,
            items={"food_packet": 100, "drinking_water_litre": 200, "medical_kit": 10},
            total_people=100,
            latitude=10.9925,
            longitude=76.9600,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"food_packet": 500, "drinking_water_litre": 1000, "medical_kit": 50, "blanket": 200}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
                {"id": 2, "name": "GH Medical Depot", "latitude": 11.0016, "longitude": 76.9723, "operating_status": "active", "inventory": {"medical_kit": 100}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 500, "vehicles": [{"id": 3, "capacity_units": 200, "availability_status": "available"}]},
            ]
        ),
        
        # 2. Multiple warehouses required for complete stock
        ReliefScenario(
            scenario_id="relief_002",
            incident_id=2,
            items={"food_packet": 500, "drinking_water_litre": 1000, "temporary_tent": 20},
            total_people=300,
            latitude=10.9950,
            longitude=76.9750,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"food_packet": 200, "drinking_water_litre": 500, "temporary_tent": 5}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
                {"id": 3, "name": "NGO Supply Centre", "latitude": 11.0270, "longitude": 77.0062, "operating_status": "active", "inventory": {"food_packet": 300, "drinking_water_litre": 500, "temporary_tent": 15}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
            ]
        ),
        
        # 3. Low stock warehouse
        ReliefScenario(
            scenario_id="relief_003",
            incident_id=3,
            items={"medical_kit": 100},
            total_people=200,
            latitude=11.0016,
            longitude=76.9723,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"medical_kit": 20}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
                {"id": 2, "name": "GH Medical Depot", "latitude": 11.0016, "longitude": 76.9723, "operating_status": "active", "inventory": {"medical_kit": 150}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 500, "vehicles": [{"id": 3, "capacity_units": 200, "availability_status": "available"}]},
            ]
        ),
        
        # 4. Blocked warehouse route
        ReliefScenario(
            scenario_id="relief_004",
            incident_id=4,
            items={"food_packet": 200, "blanket": 100},
            total_people=150,
            latitude=10.9925,
            longitude=76.9600,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"food_packet": 500, "blanket": 200}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
            ]
        ),
        
        # 5. Limited vehicle capacity
        ReliefScenario(
            scenario_id="relief_005",
            incident_id=5,
            items={"food_packet": 500},
            total_people=400,
            latitude=11.0270,
            longitude=77.0062,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"food_packet": 1000}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
            ]
        ),
        
        # 6. Relief shortage - insufficient stock
        ReliefScenario(
            scenario_id="relief_006",
            incident_id=6,
            items={"temporary_tent": 50, "blanket": 100},
            total_people=500,
            latitude=10.9930,
            longitude=76.8290,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"temporary_tent": 10, "blanket": 30}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
                {"id": 4, "name": "Rural Emergency Stock Point", "latitude": 10.9930, "longitude": 76.8290, "operating_status": "active", "inventory": {"temporary_tent": 5, "blanket": 20}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 500, "vehicles": [{"id": 5, "capacity_units": 200, "availability_status": "available"}]},
            ]
        ),
        
        # 7. High warehouse workload
        ReliefScenario(
            scenario_id="relief_007",
            incident_id=7,
            items={"food_packet": 200},
            total_people=200,
            latitude=11.0270,
            longitude=77.0062,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"food_packet": 500}, "current_dispatch_workload": 800, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
            ]
        ),
        
        # 8. Near-expiry inventory
        ReliefScenario(
            scenario_id="relief_008",
            incident_id=8,
            items={"medical_kit": 50},
            total_people=100,
            latitude=11.0016,
            longitude=76.9723,
            warehouses=[
                {"id": 2, "name": "GH Medical Depot", "latitude": 11.0016, "longitude": 76.9723, "operating_status": "active", "inventory": {"medical_kit": 100}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 500, "vehicles": [{"id": 3, "capacity_units": 200, "availability_status": "available"}]},
            ]
        ),
        
        # 9. No complete allocation possible (using supported item types)
        ReliefScenario(
            scenario_id="relief_009",
            incident_id=9,
            items={"emergency_light": 20, "hygiene_kit": 10},
            total_people=50,
            latitude=11.0270,
            longitude=77.0062,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"emergency_light": 5, "hygiene_kit": 2}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
            ]
        ),
        
        # 10. Single warehouse with partial stock
        ReliefScenario(
            scenario_id="relief_010",
            incident_id=10,
            items={"food_packet": 300, "drinking_water_litre": 500},
            total_people=250,
            latitude=10.9950,
            longitude=76.9750,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"food_packet": 200, "drinking_water_litre": 300}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
            ]
        ),
        
        # 11. Large demand single source
        ReliefScenario(
            scenario_id="relief_011",
            incident_id=11,
            items={"food_packet": 1000, "drinking_water_litre": 2000, "blanket": 500},
            total_people=1000,
            latitude=11.0168,
            longitude=76.9558,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"food_packet": 5000, "drinking_water_litre": 10000, "blanket": 2000}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 10000, "vehicles": _std_vehicles()},
            ]
        ),
        
        # 12. Small demand
        ReliefScenario(
            scenario_id="relief_012",
            incident_id=12,
            items={"food_packet": 20},
            total_people=20,
            latitude=11.0094,
            longitude=76.9472,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"food_packet": 500}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
            ]
        ),
        
        # 13. Mixed warehouse status
        ReliefScenario(
            scenario_id="relief_013",
            incident_id=13,
            items={"medical_kit": 30},
            total_people=100,
            latitude=11.0016,
            longitude=76.9723,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"medical_kit": 50}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
                {"id": 2, "name": "GH Medical Depot", "latitude": 11.0016, "longitude": 76.9723, "operating_status": "limited", "inventory": {"medical_kit": 100}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 500, "vehicles": [{"id": 3, "capacity_units": 200, "availability_status": "available"}]},
            ]
        ),
        
        # 14. Zero stock item
        ReliefScenario(
            scenario_id="relief_014",
            incident_id=14,
            items={"baby_supply_kit": 50},
            total_people=50,
            latitude=11.0270,
            longitude=77.0062,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"baby_supply_kit": 0}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
            ]
        ),
        
        # 15. Multiple items with varying availability
        ReliefScenario(
            scenario_id="relief_015",
            incident_id=15,
            items={"food_packet": 100, "hygiene_kit": 50, "baby_supply_kit": 20},
            total_people=100,
            latitude=11.0168,
            longitude=76.9558,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"food_packet": 500, "hygiene_kit": 100}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
                {"id": 3, "name": "NGO Supply Centre", "latitude": 11.0270, "longitude": 77.0062, "operating_status": "active", "inventory": {"baby_supply_kit": 50}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 500, "vehicles": [{"id": 4, "capacity_units": 200, "availability_status": "available"}]},
            ]
        ),
        
        # 16. Emergency medical supplies only
        ReliefScenario(
            scenario_id="relief_016",
            incident_id=16,
            items={"medical_kit": 200, "emergency_light": 50},
            total_people=200,
            latitude=11.0016,
            longitude=76.9723,
            warehouses=[
                {"id": 2, "name": "GH Medical Depot", "latitude": 11.0016, "longitude": 76.9723, "operating_status": "active", "inventory": {"medical_kit": 2000, "emergency_light": 300}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 500, "vehicles": [{"id": 3, "capacity_units": 200, "availability_status": "available"}]},
            ]
        ),
        
        # 17. Shelter supplies
        ReliefScenario(
            scenario_id="relief_017",
            incident_id=17,
            items={"temporary_tent": 30, "blanket": 100, "emergency_light": 20},
            total_people=150,
            latitude=11.0289,
            longitude=77.0270,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"temporary_tent": 100, "blanket": 2000, "emergency_light": 300}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
            ]
        ),
        
        # 18. Split allocation optimal
        ReliefScenario(
            scenario_id="relief_018",
            incident_id=18,
            items={"food_packet": 300},
            total_people=250,
            latitude=10.9950,
            longitude=76.9750,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "active", "inventory": {"food_packet": 150}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
                {"id": 3, "name": "NGO Supply Centre", "latitude": 11.0270, "longitude": 77.0062, "operating_status": "active", "inventory": {"food_packet": 200}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
            ]
        ),
        
        # 19. Limited warehouse
        ReliefScenario(
            scenario_id="relief_019",
            incident_id=19,
            items={"blanket": 50},
            total_people=50,
            latitude=10.9930,
            longitude=76.8290,
            warehouses=[
                {"id": 4, "name": "Rural Emergency Stock Point", "latitude": 10.9930, "longitude": 76.8290, "operating_status": "limited", "inventory": {"blanket": 100}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 500, "vehicles": [{"id": 5, "capacity_units": 200, "availability_status": "available"}]},
            ]
        ),
        
        # 20. Closed warehouse
        ReliefScenario(
            scenario_id="relief_020",
            incident_id=20,
            items={"food_packet": 100},
            total_people=100,
            latitude=11.0270,
            longitude=77.0062,
            warehouses=[
                {"id": 1, "name": "District Relief Warehouse", "latitude": 11.0168, "longitude": 76.9558, "operating_status": "closed", "inventory": {"food_packet": 500}, "current_dispatch_workload": 0, "maximum_dispatch_capacity": 1000, "vehicles": _std_vehicles()},
            ]
        ),
    ]