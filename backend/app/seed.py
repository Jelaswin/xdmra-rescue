from sqlalchemy.orm import Session
from app.models import Incident, RescueTeam, RouteCondition, IncidentSeverity, IncidentStatus, TeamAvailability, RouteRisk

def seed_db(db: Session):
    # Check if we already seeded to ensure idempotency
    if db.query(Incident).count() > 0 or db.query(RescueTeam).count() > 0:
        return

    # Seed Incidents
    incidents = [
        Incident(
            title="Downtown Flash Flood",
            description="Major street flooding causing vehicles to be stranded.",
            incident_type="Flood",
            latitude=34.0522,
            longitude=-118.2437,
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
            title="River Bank Overflow",
            description="River levels exceeded safe limits, threatening residential areas.",
            incident_type="Flood",
            latitude=34.0622,
            longitude=-118.2537,
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
            title="Subway Station Flooding",
            description="Water rapidly filling the underground station.",
            incident_type="Flood",
            latitude=34.0422,
            longitude=-118.2337,
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
    
    # Seed Rescue Teams
    teams = [
        RescueTeam(
            name="Alpha Water Rescue",
            latitude=34.0122,
            longitude=-118.2137,
            skills=["flood_rescue", "swiftwater_rescue", "first_aid", "medical_support"],
            equipment=["boat", "ropes", "life_jackets", "medical_kit"],
            capacity=15,
            current_workload=0,
            availability_status=TeamAvailability.available
        ),
        RescueTeam(
            name="Bravo Medical Unit",
            latitude=34.0532, # Close to downtown
            longitude=-118.2337,
            skills=["medical_support", "trauma_care"],
            equipment=["ambulance", "medical_kit", "stretchers"],
            capacity=20,
            current_workload=5,
            availability_status=TeamAvailability.available
        ),
        RescueTeam(
            name="Charlie Heavy Lifting",
            latitude=34.0322,
            longitude=-118.2037,
            skills=["debris_removal", "heavy_lifting"],
            equipment=["crane", "bulldozers", "pumps"],
            capacity=10,
            current_workload=10,
            availability_status=TeamAvailability.assigned
        ),
        RescueTeam(
            name="Delta Air Evac",
            latitude=34.0822,
            longitude=-118.2937,
            skills=["air_rescue", "medical_support"],
            equipment=["helicopter", "hoists", "medical_kit"],
            capacity=5,
            current_workload=0,
            availability_status=TeamAvailability.available
        ),
        RescueTeam(
            name="Echo Ground Search",
            latitude=34.0722,
            longitude=-118.2837,
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
            route_name="Main St Bridge",
            origin_label="Downtown",
            destination_label="Eastside",
            risk_level=RouteRisk.high,
            is_blocked=1
        ),
        RouteCondition(
            route_name="Highway 101 North",
            origin_label="South Sector",
            destination_label="Downtown",
            risk_level=RouteRisk.medium,
            is_blocked=0
        )
    ]

    db.add_all(incidents)
    db.add_all(teams)
    db.add_all(routes)
    db.commit()
