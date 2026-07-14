from sqlalchemy.orm import Session
from app.models import Incident, RescueTeam, RouteCondition, IncidentSeverity, IncidentStatus, TeamAvailability, RouteRisk, LocationAccuracy, LocationSource

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
