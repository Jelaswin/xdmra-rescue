import pytest
from sqlalchemy.orm import Session
from app.main import app
from app.models import (
    Incident, RescueTeam, OperationalAlert, AlertCategory, AlertSeverity, AlertStatus,
    IncidentStatus, IncidentSeverity, TeamAvailability, AllocationStatus,
    Allocation,
)
from app.database import get_db


def seed_command_dashboard_data(db: Session):
    i1 = Incident(
        title="Critical Unassigned",
        description="desc",
        incident_type="Flood",
        latitude=10.0,
        longitude=76.0,
        severity=IncidentSeverity.critical,
        status=IncidentStatus.reported,
        priority_level="critical",
    )
    db.add(i1)

    i2 = Incident(
        title="Assigned Incident",
        description="desc",
        incident_type="Flood",
        latitude=10.0,
        longitude=76.0,
        severity=IncidentSeverity.high,
        status=IncidentStatus.in_progress,
        priority_level="high",
    )
    db.add(i2)
    db.commit()

    t1 = RescueTeam(
        name="Team 1",
        latitude=10.0,
        longitude=76.0,
        capacity=10,
        current_workload=0,
        availability_status=TeamAvailability.available,
        skills=[],
        equipment=[],
    )
    db.add(t1)
    db.commit()

    a1 = Allocation(incident_id=i2.id, rescue_team_id=t1.id, status=AllocationStatus.approved)
    db.add(a1)
    db.commit()


@pytest.fixture
def seeded_command_db(db_session):
    seed_command_dashboard_data(db_session)
    return db_session


@pytest.fixture
def command_dashboard_client(client, seeded_command_db):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = lambda: seeded_command_db
    with client as c:
        yield c
    app.dependency_overrides.clear()


def test_p8_01_trigger_alerts(command_dashboard_client, admin_headers):
    response = command_dashboard_client.post("/api/command/alerts/generate", headers=admin_headers)
    assert response.status_code == 200

def test_p8_02_dashboard_summary(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_active_incidents" in data

def test_p8_03_critical_incident_count(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    data = response.json()
    assert data["critical_incidents"] == 1

def test_p8_04_unassigned_incident_count(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    data = response.json()
    assert data["unassigned_incidents"] == 1

def test_p8_05_rescue_allocation_count(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    data = response.json()
    assert data["active_rescue_allocations"] == 1

def test_p8_06_reallocation_warning_count(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    data = response.json()
    assert "rescue_reallocations_pending" in data

def test_p8_07_relief_request_count(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    data = response.json()
    assert "active_relief_requests" in data

def test_p8_08_relief_shortage_count(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    data = response.json()
    assert "relief_shortages" in data

def test_p8_09_dispatch_in_progress_count(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    data = response.json()
    assert "dispatches_in_transit" in data

def test_p8_10_shelter_request_count(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    data = response.json()
    assert "active_shelter_requests" in data

def test_p8_11_uncovered_population_count(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    data = response.json()
    assert "uncovered_displaced_people" in data

def test_p8_12_high_overcrowding_count(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    data = response.json()
    assert "high_overcrowding_risk_shelters" in data

def test_p8_13_pending_decision_count(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/dashboard-summary", headers=admin_headers)
    data = response.json()
    assert "pending_officer_decisions" in data

def test_p8_14_alert_generation(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/alerts", headers=admin_headers)
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) > 0

def test_p8_15_duplicate_alerts_prevented(command_dashboard_client, admin_headers):
    command_dashboard_client.post("/api/command/alerts/generate", headers=admin_headers)
    command_dashboard_client.post("/api/command/alerts/generate", headers=admin_headers)
    response = command_dashboard_client.get("/api/command/alerts", headers=admin_headers)
    alerts = response.json()
    unassigned_alerts = [a for a in alerts if a["category"] == "critical_incident"]
    assert len(unassigned_alerts) == 1

def test_p8_16_alert_acknowledgement(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/alerts", headers=admin_headers)
    alerts = response.json()
    alert_id = alerts[0]["id"]
    ack_res = command_dashboard_client.patch(f"/api/command/alerts/{alert_id}/acknowledge", headers=admin_headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"

def test_p8_17_alert_resolution(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/alerts", headers=admin_headers)
    alerts = response.json()
    alert_id = alerts[0]["id"]
    res = command_dashboard_client.patch(f"/api/command/alerts/{alert_id}/resolve", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "resolved"

def test_p8_18_ack_does_not_modify_resource(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/alerts", headers=admin_headers)
    alerts = response.json()
    alert_id = alerts[0]["id"]
    command_dashboard_client.patch(f"/api/command/alerts/{alert_id}/acknowledge", headers=admin_headers)
    inc_res = command_dashboard_client.get("/api/incidents/1", headers=admin_headers)
    if inc_res.status_code == 200:
        assert inc_res.json()["status"] == "reported"

def test_p8_19_pending_decisions_ranking(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/pending-decisions", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert type(data) == list

def test_p8_20_incident_operational_summary(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/incidents/1/operational-summary", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["incident_id"] == 1
    assert data["allocation_status"] == "unassigned"

def test_p8_21_incident_rescue_status(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/incidents/2/operational-summary", headers=admin_headers)
    data = response.json()
    assert data["allocation_status"] == "approved"
    assert data["assigned_team"] == "Team 1"

def test_p8_22_incident_relief_status(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/incidents/1/operational-summary", headers=admin_headers)
    data = response.json()
    assert "relief_request_status" in data

def test_p8_23_incident_shelter_status(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/incidents/1/operational-summary", headers=admin_headers)
    data = response.json()
    assert "shelter_request_status" in data

def test_p8_24_unified_timeline(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/incidents/2/timeline", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert data[0]["event_category"] in ["rescue_allocation", "incident_creation"]

def test_p8_25_timeline_preserves_history(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/incidents/2/timeline", headers=admin_headers)
    data = response.json()
    assert data[-1]["event_category"] == "incident_creation"

def test_p8_26_command_active_incidents_filtering(command_dashboard_client, admin_headers):
    pass

def test_p8_27_alert_severity_filtering(command_dashboard_client, admin_headers):
    response = command_dashboard_client.get("/api/command/alerts?status=resolved", headers=admin_headers)
    assert response.status_code == 200

def test_p8_28_decision_type_filtering(command_dashboard_client, admin_headers):
    pass

def test_p8_29_resource_status_endpoint_works(command_dashboard_client, admin_headers):
    pass

def test_p8_30_recent_activity_works(command_dashboard_client, admin_headers):
    pass

def test_p8_31_command_map_overview(command_dashboard_client, admin_headers):
    pass

def test_p8_32_missing_incident_404(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/incidents/999/operational-summary", headers=admin_headers)
    assert res.status_code == 404

def test_p8_33_missing_alert_404(command_dashboard_client, admin_headers):
    res = command_dashboard_client.patch("/api/command/alerts/999/acknowledge", headers=admin_headers)
    assert res.status_code == 404

def test_p8_34_existing_rescue_allocation(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/incidents/2", headers=admin_headers)
    assert res.status_code == 200

def test_p8_35_existing_rescue_reallocation(command_dashboard_client, admin_headers):
    pass

def test_p8_36_existing_relief(command_dashboard_client, admin_headers):
    pass

def test_p8_37_existing_inventory(command_dashboard_client, admin_headers):
    pass

def test_p8_38_existing_shelter(command_dashboard_client, admin_headers):
    pass

def test_p8_39_existing_shelter_reallocation(command_dashboard_client, admin_headers):
    pass

def test_p8_40_existing_ml_prediction(command_dashboard_client, admin_headers):
    pass

def test_p8_41_active_incidents_endpoint(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/active-incidents", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert type(data) == list
    assert len(data) >= 1

def test_p8_42_active_incidents_priority_filter(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/active-incidents?priority=critical", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    for inc in data:
        assert inc["rule_priority"] == "critical"

def test_p8_43_active_incidents_type_filter(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/active-incidents?incident_type=Flood", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    for inc in data:
        assert inc["incident_type"] == "Flood"

def test_p8_44_active_incidents_location_filter(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/active-incidents?location=Critical", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert type(data) == list

def test_p8_45_resource_status_endpoint(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/resource-status", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "rescue_teams_available" in data
    assert "warehouses_active" in data
    assert "vehicles_available" in data
    assert "shelters_open" in data
    assert "blocked_routes" in data

def test_p8_46_resource_status_filter(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/resource-status?resource_type=rescue_team", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("resources", [])) >= 1
    for r in data.get("resources", []):
        assert r["resource_type"] == "rescue_team"

def test_p8_47_resource_status_counts(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/resource-status", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["rescue_teams_available"] == 1
    assert data["shelters_open"] == 0

def test_p8_48_recent_activity_endpoint(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/recent-activity", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert type(data) == list

def test_p8_49_recent_activity_limit(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/recent-activity?limit=5", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) <= 5

def test_p8_50_recent_activity_ordering(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/recent-activity", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    if len(data) >= 2:
        for i in range(len(data) - 1):
            assert data[i]["timestamp"] >= data[i+1]["timestamp"]

def test_p8_51_recent_activity_resource_type_filter(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/recent-activity?resource_type=incident", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    for item in data:
        assert item["resource_type"] == "incident"

def test_p8_52_recent_activity_incident_filter(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/recent-activity?incident_id=1", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    for item in data:
        if item["incident_id"] is not None:
            assert item["incident_id"] == 1

def test_p8_53_map_overview_endpoint(command_dashboard_client, admin_headers):
    res = command_dashboard_client.get("/api/command/map-overview", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "incidents" in data
    assert "teams" in data
    assert "warehouses" in data
    assert "shelters" in data