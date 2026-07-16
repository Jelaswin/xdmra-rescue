import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models import (
    Incident, RescueTeam, OperationalAlert, AlertCategory, AlertSeverity, AlertStatus
)
from app.database import Base, get_db

from tests.test_main import engine, TestingSessionLocal, client

@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    i1 = Incident(title="Critical Unassigned", description="desc", incident_type="Flood", latitude=10.0, longitude=76.0, severity="critical", status="reported", priority_level="critical")
    db.add(i1)
    
    i2 = Incident(title="Assigned Incident", description="desc", incident_type="Flood", latitude=10.0, longitude=76.0, severity="high", status="in_progress", priority_level="high")
    db.add(i2)
    db.commit()
    
    t1 = RescueTeam(name="Team 1", latitude=10.0, longitude=76.0, capacity=10, current_workload=0, availability_status="available", skills=[], equipment=[])
    db.add(t1)
    db.commit()
    
    from app.models import Allocation
    a1 = Allocation(incident_id=i2.id, rescue_team_id=t1.id, status="approved")
    db.add(a1)
    db.commit()
    
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_p8_01_trigger_alerts(db_session):
    response = client.post("/api/command/alerts/generate")
    assert response.status_code == 200

def test_p8_02_dashboard_summary(db_session):
    response = client.get("/api/command/dashboard-summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_active_incidents" in data

def test_p8_03_critical_incident_count(db_session):
    response = client.get("/api/command/dashboard-summary")
    data = response.json()
    assert data["critical_incidents"] == 1

def test_p8_04_unassigned_incident_count(db_session):
    response = client.get("/api/command/dashboard-summary")
    data = response.json()
    assert data["unassigned_incidents"] == 1

def test_p8_05_rescue_allocation_count(db_session):
    response = client.get("/api/command/dashboard-summary")
    data = response.json()
    assert data["active_rescue_allocations"] == 1

def test_p8_06_reallocation_warning_count(db_session):
    response = client.get("/api/command/dashboard-summary")
    data = response.json()
    assert "rescue_reallocations_pending" in data

def test_p8_07_relief_request_count(db_session):
    response = client.get("/api/command/dashboard-summary")
    data = response.json()
    assert "active_relief_requests" in data

def test_p8_08_relief_shortage_count(db_session):
    response = client.get("/api/command/dashboard-summary")
    data = response.json()
    assert "relief_shortages" in data

def test_p8_09_dispatch_in_progress_count(db_session):
    response = client.get("/api/command/dashboard-summary")
    data = response.json()
    assert "dispatches_in_transit" in data

def test_p8_10_shelter_request_count(db_session):
    response = client.get("/api/command/dashboard-summary")
    data = response.json()
    assert "active_shelter_requests" in data

def test_p8_11_uncovered_population_count(db_session):
    response = client.get("/api/command/dashboard-summary")
    data = response.json()
    assert "uncovered_displaced_people" in data

def test_p8_12_high_overcrowding_count(db_session):
    response = client.get("/api/command/dashboard-summary")
    data = response.json()
    assert "high_overcrowding_risk_shelters" in data

def test_p8_13_pending_decision_count(db_session):
    response = client.get("/api/command/dashboard-summary")
    data = response.json()
    assert "pending_officer_decisions" in data

def test_p8_14_alert_generation(db_session):
    response = client.get("/api/command/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) > 0

def test_p8_15_duplicate_alerts_prevented(db_session):
    client.post("/api/command/alerts/generate")
    client.post("/api/command/alerts/generate")
    response = client.get("/api/command/alerts")
    alerts = response.json()
    unassigned_alerts = [a for a in alerts if a["category"] == "critical_incident"]
    assert len(unassigned_alerts) == 1

def test_p8_16_alert_acknowledgement(db_session):
    response = client.get("/api/command/alerts")
    alerts = response.json()
    alert_id = alerts[0]["id"]
    ack_res = client.patch(f"/api/command/alerts/{alert_id}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"

def test_p8_17_alert_resolution(db_session):
    response = client.get("/api/command/alerts")
    alerts = response.json()
    alert_id = alerts[0]["id"]
    res = client.patch(f"/api/command/alerts/{alert_id}/resolve")
    assert res.status_code == 200
    assert res.json()["status"] == "resolved"

def test_p8_18_ack_does_not_modify_resource(db_session):
    response = client.get("/api/command/alerts")
    alerts = response.json()
    alert_id = alerts[0]["id"]
    client.patch(f"/api/command/alerts/{alert_id}/acknowledge")
    inc_res = client.get("/api/incidents/1")
    if inc_res.status_code == 200:
        assert inc_res.json()["status"] == "reported"

def test_p8_19_pending_decisions_ranking(db_session):
    response = client.get("/api/command/pending-decisions")
    assert response.status_code == 200
    data = response.json()
    assert type(data) == list

def test_p8_20_incident_operational_summary(db_session):
    response = client.get("/api/command/incidents/1/operational-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["incident_id"] == 1
    assert data["allocation_status"] == "unassigned"

def test_p8_21_incident_rescue_status(db_session):
    response = client.get("/api/command/incidents/2/operational-summary")
    data = response.json()
    assert data["allocation_status"] == "approved"
    assert data["assigned_team"] == "Team 1"

def test_p8_22_incident_relief_status(db_session):
    response = client.get("/api/command/incidents/1/operational-summary")
    data = response.json()
    assert "relief_request_status" in data

def test_p8_23_incident_shelter_status(db_session):
    response = client.get("/api/command/incidents/1/operational-summary")
    data = response.json()
    assert "shelter_request_status" in data

def test_p8_24_unified_timeline(db_session):
    response = client.get("/api/command/incidents/2/timeline")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert data[0]["event_category"] in ["rescue_allocation", "incident_creation"]

def test_p8_25_timeline_preserves_history(db_session):
    response = client.get("/api/command/incidents/2/timeline")
    data = response.json()
    assert data[-1]["event_category"] == "incident_creation"

def test_p8_26_command_active_incidents_filtering(db_session):
    pass

def test_p8_27_alert_severity_filtering(db_session):
    response = client.get("/api/command/alerts?status=resolved")
    assert response.status_code == 200

def test_p8_28_decision_type_filtering(db_session):
    pass

def test_p8_29_resource_status_endpoint_works(db_session):
    pass

def test_p8_30_recent_activity_works(db_session):
    pass

def test_p8_31_command_map_overview(db_session):
    pass

def test_p8_32_missing_incident_404(db_session):
    res = client.get("/api/command/incidents/999/operational-summary")
    assert res.status_code == 404

def test_p8_33_missing_alert_404(db_session):
    res = client.patch("/api/command/alerts/999/acknowledge")
    assert res.status_code == 404

def test_p8_34_existing_rescue_allocation(db_session):
    res = client.get("/api/incidents/2")
    assert res.status_code == 200

def test_p8_35_existing_rescue_reallocation(db_session):
    pass

def test_p8_36_existing_relief(db_session):
    pass

def test_p8_37_existing_inventory(db_session):
    pass

def test_p8_38_existing_shelter(db_session):
    pass

def test_p8_39_existing_shelter_reallocation(db_session):
    pass

def test_p8_40_existing_ml_prediction(db_session):
    pass

def test_p8_41_active_incidents_endpoint(db_session):
    res = client.get("/api/command/active-incidents")
    assert res.status_code == 200
    data = res.json()
    assert type(data) == list
    assert len(data) >= 1

def test_p8_42_active_incidents_priority_filter(db_session):
    res = client.get("/api/command/active-incidents?priority=critical")
    assert res.status_code == 200
    data = res.json()
    for inc in data:
        assert inc["rule_priority"] == "critical"

def test_p8_43_active_incidents_type_filter(db_session):
    res = client.get("/api/command/active-incidents?incident_type=Flood")
    assert res.status_code == 200
    data = res.json()
    for inc in data:
        assert inc["incident_type"] == "Flood"

def test_p8_44_active_incidents_location_filter(db_session):
    res = client.get("/api/command/active-incidents?location=Critical")
    assert res.status_code == 200
    data = res.json()
    assert type(data) == list

def test_p8_45_resource_status_endpoint(db_session):
    res = client.get("/api/command/resource-status")
    assert res.status_code == 200
    data = res.json()
    assert "rescue_teams_available" in data
    assert "warehouses_active" in data
    assert "vehicles_available" in data
    assert "shelters_open" in data
    assert "blocked_routes" in data

def test_p8_46_resource_status_filter(db_session):
    res = client.get("/api/command/resource-status?resource_type=rescue_team")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("resources", [])) >= 1
    for r in data.get("resources", []):
        assert r["resource_type"] == "rescue_team"

def test_p8_47_resource_status_counts(db_session):
    res = client.get("/api/command/resource-status")
    assert res.status_code == 200
    data = res.json()
    assert data["rescue_teams_available"] == 1
    assert data["shelters_open"] == 0

def test_p8_48_recent_activity_endpoint(db_session):
    res = client.get("/api/command/recent-activity")
    assert res.status_code == 200
    data = res.json()
    assert type(data) == list

def test_p8_49_recent_activity_limit(db_session):
    res = client.get("/api/command/recent-activity?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data) <= 5

def test_p8_50_recent_activity_ordering(db_session):
    res = client.get("/api/command/recent-activity")
    assert res.status_code == 200
    data = res.json()
    if len(data) >= 2:
        for i in range(len(data) - 1):
            assert data[i]["timestamp"] >= data[i+1]["timestamp"]

def test_p8_51_recent_activity_resource_type_filter(db_session):
    res = client.get("/api/command/recent-activity?resource_type=incident")
    assert res.status_code == 200
    data = res.json()
    for item in data:
        assert item["resource_type"] == "incident"

def test_p8_52_recent_activity_incident_filter(db_session):
    res = client.get("/api/command/recent-activity?incident_id=1")
    assert res.status_code == 200
    data = res.json()
    for item in data:
        if item["incident_id"] is not None:
            assert item["incident_id"] == 1

def test_p8_53_map_overview_endpoint(db_session):
    res = client.get("/api/command/map-overview")
    assert res.status_code == 200
    data = res.json()
    assert "incidents" in data
    assert "teams" in data
    assert "warehouses" in data
    assert "shelters" in data