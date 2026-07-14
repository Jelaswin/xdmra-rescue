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
            status=IncidentStatus.in_progress
        )
    ]
    
    # Seed Rescue Teams
    teams = [
        RescueTeam(
            name="Alpha Water Rescue",
            latitude=34.0122,
            longitude=-118.2137,
            skills=["swiftwater_rescue", "first_aid", "diving"],
            equipment=["boats", "ropes", "life_jackets"],
            capacity=15,
            current_workload=0,
            availability_status=TeamAvailability.available
        ),
        RescueTeam(
            name="Bravo Medical Unit",
            latitude=34.0222,
            longitude=-118.2237,
            skills=["paramedic", "trauma_care"],
            equipment=["ambulances", "medical_kits"],
            capacity=20,
            current_workload=5,
            availability_status=TeamAvailability.available
        ),
        RescueTeam(
            name="Charlie Heavy Lifting",
            latitude=34.0322,
            longitude=-118.2037,
            skills=["debris_removal", "heavy_machinery"],
            equipment=["cranes", "bulldozers"],
            capacity=10,
            current_workload=10,
            availability_status=TeamAvailability.assigned
        ),
        RescueTeam(
            name="Delta Air Evac",
            latitude=34.0822,
            longitude=-118.2937,
            skills=["helicopter_pilot", "air_rescue"],
            equipment=["helicopters", "hoists"],
            capacity=5,
            current_workload=0,
            availability_status=TeamAvailability.available
        ),
        RescueTeam(
            name="Echo Ground Search",
            latitude=34.0722,
            longitude=-118.2837,
            skills=["search_and_rescue", "k9_unit"],
            equipment=["radios", "search_dogs"],
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
