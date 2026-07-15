from sqlalchemy.orm import Session
from app.models import (
    Warehouse, ReliefInventory, DeliveryVehicle, WarehouseOperatingStatus, 
    VehicleAvailability, Incident, RescueTeam, RouteCondition, IncidentSeverity, 
    IncidentStatus, TeamAvailability, RouteRisk, LocationAccuracy, LocationSource,
    EmergencyShelter, ShelterOperatingStatus, ShelterRouteCondition
)

def seed_db(db: Session):
    # Check if we already seeded to ensure idempotency
    if db.query(Incident).count() > 0 or db.query(RescueTeam).count() > 0:
        return

    # Seed Incidents (Demonstration Data - Coimbatore Region)
    incidents = [
        Incident(
            title="Ukkadam Flash Flood",
            description="Major street flooding causing vehicles to be stranded near Ukkadam Lake.",
            incident_type="Flood",
            latitude=10.9925,
            longitude=76.9600,
            location_name="Ukkadam, Coimbatore",
            location_accuracy=LocationAccuracy.approximate_area,
            location_source=LocationSource.map_click,
            location_notes="Demonstration data",
            severity=IncidentSeverity.critical,
            affected_people=150,
            injured_people=5,
            vulnerable_people=20,
            trapped_people=10,
            children_count=15,
            elderly_count=5,
            required_skills=["flood_rescue", "medical_support"],
            required_equipment=["boat", "life_jackets", "medical_kit"],
            status=IncidentStatus.reported
        ),
        Incident(
            title="Noyyal River Overflow",
            description="River levels exceeded safe limits, threatening residential areas along the bank.",
            incident_type="Flood",
            latitude=10.9950,
            longitude=76.9750,
            location_name="Noyyal River Bank",
            location_accuracy=LocationAccuracy.approximate_area,
            location_source=LocationSource.imported_report,
            location_notes="Demonstration data",
            severity=IncidentSeverity.high,
            affected_people=300,
            injured_people=0,
            vulnerable_people=50,
            trapped_people=0,
            children_count=30,
            elderly_count=20,
            required_skills=["flood_rescue", "evacuation_coordination"],
            required_equipment=["boat", "transport_vehicles"],
            status=IncidentStatus.verified
        ),
        Incident(
            title="Karunya Nagar Landslide",
            description="Mudslide blocking main access road near Karunya Institute.",
            incident_type="Landslide",
            latitude=10.9378,
            longitude=76.7455,
            location_name="Karunya Nagar",
            location_accuracy=LocationAccuracy.exact_gps,
            location_source=LocationSource.manual_coordinates,
            location_notes="Demonstration data",
            severity=IncidentSeverity.critical,
            affected_people=40,
            injured_people=12,
            vulnerable_people=5,
            trapped_people=25,
            children_count=2,
            elderly_count=3,
            required_skills=["swiftwater_rescue", "medical_support", "heavy_lifting"],
            required_equipment=["ropes", "medical_kit", "pumps"],
            status=IncidentStatus.in_progress
        )
    ]
    
    # Seed Rescue Teams (Demonstration Data)
    teams = [
        RescueTeam(
            name="CBE Disaster Response Team",
            latitude=11.0168,
            longitude=76.9558,
            skills=["flood_rescue", "swiftwater_rescue", "first_aid", "medical_support"],
            equipment=["boat", "ropes", "life_jackets", "medical_kit"],
            capacity=15,
            current_workload=0,
            availability_status=TeamAvailability.available
        ),
        RescueTeam(
            name="GH Medical Unit",
            latitude=11.0016, # Near Govt Hospital Coimbatore
            longitude=76.9723,
            skills=["medical_support", "trauma_care"],
            equipment=["ambulance", "medical_kit", "stretchers"],
            capacity=20,
            current_workload=5,
            availability_status=TeamAvailability.available
        ),
        RescueTeam(
            name="Sulur Air Base Lift",
            latitude=11.0101,
            longitude=77.1643,
            skills=["debris_removal", "heavy_lifting"],
            equipment=["crane", "bulldozers", "pumps"],
            capacity=10,
            current_workload=10,
            availability_status=TeamAvailability.assigned
        ),
        RescueTeam(
            name="Siruvani Forest Rangers",
            latitude=10.9392,
            longitude=76.6800,
            skills=["air_rescue", "medical_support"],
            equipment=["helicopter", "hoists", "medical_kit"],
            capacity=5,
            current_workload=0,
            availability_status=TeamAvailability.available
        ),
        RescueTeam(
            name="TNFRS Station 1",
            latitude=11.0200,
            longitude=76.9600,
            skills=["search_and_rescue", "evacuation_coordination"],
            equipment=["radio", "transport_vehicles"],
            capacity=30,
            current_workload=0,
            availability_status=TeamAvailability.available
        )
    ]

    # Seed Route Conditions
    routes = [
        RouteCondition(
            incident_id=1,
            warehouse_id=1,
            risk_level=RouteRisk.high,
            is_blocked=0,
            estimated_delay_minutes=45,
            description="Flooded underpass on route from District Warehouse"
        ),
        RouteCondition(
            incident_id=1,
            rescue_team_id=1,
            risk_level=RouteRisk.high,
            is_blocked=0,
            estimated_delay_minutes=5,
            description="Main St Bridge Traffic"
        ),
        RouteCondition(
            incident_id=2,
            rescue_team_id=2,
            risk_level=RouteRisk.medium,
            is_blocked=0,
            estimated_delay_minutes=0,
            description="Highway 101 North"
        )
    ]

    db.add_all(incidents)
    db.add_all(teams)
    db.add_all(routes)
    db.commit()

    # Seed Warehouses
    warehouses = [
        Warehouse(
            name="District Relief Warehouse",
            location_name="Coimbatore Central",
            latitude=11.0168,
            longitude=76.9558,
            warehouse_type="Government",
            operating_status=WarehouseOperatingStatus.active,
            maximum_dispatch_capacity=1000,
            current_dispatch_workload=50
        ),
        Warehouse(
            name="GH Medical Depot",
            location_name="Coimbatore Medical College",
            latitude=11.0016,
            longitude=76.9723,
            warehouse_type="Hospital",
            operating_status=WarehouseOperatingStatus.active,
            maximum_dispatch_capacity=500,
            current_dispatch_workload=10
        ),
        Warehouse(
            name="NGO Supply Centre",
            location_name="Peelamedu",
            latitude=11.0270,
            longitude=77.0062,
            warehouse_type="NGO",
            operating_status=WarehouseOperatingStatus.limited,
            maximum_dispatch_capacity=200,
            current_dispatch_workload=150
        ),
        Warehouse(
            name="Rural Emergency Stock Point",
            location_name="Thondamuthur",
            latitude=10.9930,
            longitude=76.8290,
            warehouse_type="Local",
            operating_status=WarehouseOperatingStatus.active,
            maximum_dispatch_capacity=100,
            current_dispatch_workload=0
        )
    ]
    db.add_all(warehouses)
    db.commit()

    # Seed Inventory for Warehouse 1 (District Relief)
    inventory = [
        ReliefInventory(warehouse_id=1, item_type="food_packet", display_name="Food Packets", unit="packets", quantity_available=5000, reorder_level=500),
        ReliefInventory(warehouse_id=1, item_type="drinking_water_litre", display_name="Drinking Water", unit="litres", quantity_available=10000, reorder_level=1000),
        ReliefInventory(warehouse_id=1, item_type="medical_kit", display_name="Medical Kits", unit="kits", quantity_available=50, reorder_level=100), # low stock
        ReliefInventory(warehouse_id=1, item_type="blanket", display_name="Blankets", unit="items", quantity_available=2000, reorder_level=200),
        ReliefInventory(warehouse_id=1, item_type="hygiene_kit", display_name="Hygiene Kits", unit="kits", quantity_available=1000, reorder_level=100),
        ReliefInventory(warehouse_id=1, item_type="baby_supply_kit", display_name="Baby Supply Kits", unit="kits", quantity_available=500, reorder_level=50),
        ReliefInventory(warehouse_id=1, item_type="emergency_light", display_name="Emergency Lights", unit="items", quantity_available=300, reorder_level=50),
        ReliefInventory(warehouse_id=1, item_type="temporary_tent", display_name="Temporary Tents", unit="tents", quantity_available=100, reorder_level=20),
        
        # Seed Inventory for Warehouse 2 (Medical)
        ReliefInventory(warehouse_id=2, item_type="medical_kit", display_name="Medical Kits", unit="kits", quantity_available=2000, reorder_level=500),
        ReliefInventory(warehouse_id=2, item_type="hygiene_kit", display_name="Hygiene Kits", unit="kits", quantity_available=1500, reorder_level=200),
        ReliefInventory(warehouse_id=2, item_type="baby_supply_kit", display_name="Baby Supply Kits", unit="kits", quantity_available=800, reorder_level=100),
        
        # Seed Inventory for Warehouse 3 (NGO)
        ReliefInventory(warehouse_id=3, item_type="food_packet", display_name="Food Packets", unit="packets", quantity_available=2000, reorder_level=200),
        ReliefInventory(warehouse_id=3, item_type="drinking_water_litre", display_name="Drinking Water", unit="litres", quantity_available=3000, reorder_level=500),
        ReliefInventory(warehouse_id=3, item_type="blanket", display_name="Blankets", unit="items", quantity_available=500, reorder_level=100),
        
        # Seed Inventory for Warehouse 4 (Rural)
        ReliefInventory(warehouse_id=4, item_type="food_packet", display_name="Food Packets", unit="packets", quantity_available=500, reorder_level=100),
        ReliefInventory(warehouse_id=4, item_type="temporary_tent", display_name="Temporary Tents", unit="tents", quantity_available=20, reorder_level=5)
    ]
    db.add_all(inventory)
    db.commit()

    # Seed Vehicles
    vehicles = [
        DeliveryVehicle(warehouse_id=1, name="District Truck Alpha", vehicle_type="Heavy Truck", capacity_units=2000, availability_status=VehicleAvailability.available),
        DeliveryVehicle(warehouse_id=1, name="District Truck Beta", vehicle_type="Medium Truck", capacity_units=1000, availability_status=VehicleAvailability.assigned, current_workload=800),
        DeliveryVehicle(warehouse_id=2, name="Med-Transport 1", vehicle_type="Van", capacity_units=500, availability_status=VehicleAvailability.available),
        DeliveryVehicle(warehouse_id=2, name="Med-Transport 2", vehicle_type="Van", capacity_units=500, availability_status=VehicleAvailability.unavailable),
        DeliveryVehicle(warehouse_id=3, name="NGO Pickup", vehicle_type="Pickup", capacity_units=300, availability_status=VehicleAvailability.available),
        DeliveryVehicle(warehouse_id=4, name="Rural Tractor", vehicle_type="Tractor", capacity_units=200, availability_status=VehicleAvailability.available)
    ]
    db.add_all(vehicles)
    db.commit()

    # Seed Emergency Shelters
    shelters = [
        EmergencyShelter(
            name="Codissia Trade Fair Complex",
            shelter_type="Large Event Space",
            location_name="Avinashi Road",
            latitude=11.0289,
            longitude=77.0270,
            operating_status=ShelterOperatingStatus.open,
            total_capacity=5000,
            maximum_daily_intake=1000,
            has_medical_support=1,
            has_accessibility_support=1,
            has_women_child_safe_area=1,
            has_food=1,
            has_drinking_water=1,
            has_power_backup=1,
            has_sanitation=1,
            supports_long_term_stay=1
        ),
        EmergencyShelter(
            name="Government College of Technology (GCT)",
            shelter_type="Educational Institution",
            location_name="Thadagam Road",
            latitude=11.0180,
            longitude=76.9360,
            operating_status=ShelterOperatingStatus.open,
            total_capacity=1500,
            maximum_daily_intake=400,
            has_medical_support=1,
            has_accessibility_support=1,
            has_women_child_safe_area=1,
            has_food=1,
            has_drinking_water=1,
            has_power_backup=1,
            has_sanitation=1,
            supports_long_term_stay=0
        ),
        EmergencyShelter(
            name="PSG College of Arts and Science",
            shelter_type="Educational Institution",
            location_name="Civil Aerodrome Post",
            latitude=11.0312,
            longitude=77.0374,
            operating_status=ShelterOperatingStatus.open,
            total_capacity=2000,
            maximum_daily_intake=500,
            has_medical_support=1,
            has_accessibility_support=1,
            has_women_child_safe_area=1,
            has_food=1,
            has_drinking_water=1,
            has_power_backup=1,
            has_sanitation=1,
            supports_long_term_stay=1
        ),
        EmergencyShelter(
            name="Corporation Community Hall, RS Puram",
            shelter_type="Community Center",
            location_name="RS Puram",
            latitude=11.0094,
            longitude=76.9472,
            operating_status=ShelterOperatingStatus.open,
            total_capacity=300,
            maximum_daily_intake=100,
            has_medical_support=0,
            has_accessibility_support=0,
            has_women_child_safe_area=1,
            has_food=1,
            has_drinking_water=1,
            has_power_backup=0,
            has_sanitation=1,
            supports_long_term_stay=0
        )
    ]
    db.add_all(shelters)
    db.commit()

    # Seed Shelter Route Conditions (Codissia to Flood is high risk, others low)
    shelter_routes = [
        ShelterRouteCondition(
            incident_id=1,
            shelter_id=1, # Codissia
            risk_level=RouteRisk.high,
            is_blocked=0,
            estimated_delay_minutes=30,
            description="Avinashi Road Waterlogging"
        )
    ]
    db.add_all(shelter_routes)
    db.commit()
