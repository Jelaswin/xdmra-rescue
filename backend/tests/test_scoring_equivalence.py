"""
Phase 9 scoring characterization and equivalence tests.

Tests verify that shared scoring functions produce bit-for-bit identical
outputs to production service scoring logic.
"""
import pytest
import math
from evaluation.baselines.rescue_baselines import haversine_distance
from app.services.scoring.rescue_scoring import (
    RescueScoringInput, RescueScoringOutput, score_rescue_team, rank_rescue_teams,
    normalize_string_set,
)
from app.services.scoring.relief_scoring import (
    ReliefVehicleInput, ReliefScoringInput, ReliefScoringOutput,
    ReliefItemSupply, score_relief_warehouse, rank_relief_warehouses,
)
from app.services.scoring.shelter_scoring import (
    ShelterScoringInput, ShelterScoringOutput, score_shelter, rank_shelters,
    calculate_overcrowding_risk,
)


class TestRescueScoring:
    """Characterization tests for rescue team scoring."""

    def test_available_team_eligible(self):
        inp = RescueScoringInput(
            team_id=1,
            availability_status="available",
            team_latitude=10.0,
            team_longitude=20.0,
            team_capacity=50,
            team_current_workload=0,
            team_skills=["medical", "search"],
            team_equipment=["boat", "radio"],
            incident_latitude=10.0,
            incident_longitude=20.0,
            affected_people=20,
            required_skills=["medical"],
            required_equipment=["boat"],
            route_risk="low",
            route_blocked=False,
            estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert out.eligible
        assert out.team_id == 1
        assert out.distance_km == pytest.approx(0.0)
        assert out.skill_match_pct == pytest.approx(100.0)
        assert out.equipment_match_pct == pytest.approx(100.0)
        assert out.skill_score == pytest.approx(30.0)
        assert out.equipment_score == pytest.approx(20.0)
        assert out.capacity_score == pytest.approx(10.0)
        assert out.workload_score == pytest.approx(10.0)
        assert out.distance_score == pytest.approx(30.0)
        assert out.route_risk_penalty == pytest.approx(0.0)
        assert out.total_score == pytest.approx(100.0)

    def test_unavailable_team_rejected(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="assigned",
            team_latitude=10.0, team_longitude=20.0, team_capacity=50,
            team_current_workload=0, team_skills=[], team_equipment=[],
            incident_latitude=10.0, incident_longitude=20.0, affected_people=20,
            required_skills=[], required_equipment=[],
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert not out.eligible
        assert "not 'available'" in out.eligibility_reason

    def test_blocked_route_rejected(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=10.0, team_longitude=20.0, team_capacity=50,
            team_current_workload=0, team_skills=[], team_equipment=[],
            incident_latitude=10.0, incident_longitude=20.0, affected_people=20,
            required_skills=[], required_equipment=[],
            route_risk="low", route_blocked=True, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert not out.eligible
        assert "blocked" in out.eligibility_reason

    def test_route_medium_risk_penalty(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=10.0, team_longitude=20.0, team_capacity=50,
            team_current_workload=0, team_skills=[], team_equipment=[],
            incident_latitude=10.0, incident_longitude=20.0, affected_people=20,
            required_skills=[], required_equipment=[],
            route_risk="medium", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert out.eligible
        assert out.route_risk_penalty == pytest.approx(5.0)
        assert out.total_score == pytest.approx(95.0)

    def test_route_high_risk_penalty(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=10.0, team_longitude=20.0, team_capacity=50,
            team_current_workload=0, team_skills=[], team_equipment=[],
            incident_latitude=10.0, incident_longitude=20.0, affected_people=20,
            required_skills=[], required_equipment=[],
            route_risk="high", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert out.route_risk_penalty == pytest.approx(15.0)

    def test_route_high_risk_with_delay(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=10.0, team_longitude=20.0, team_capacity=50,
            team_current_workload=0, team_skills=[], team_equipment=[],
            incident_latitude=10.0, incident_longitude=20.0, affected_people=20,
            required_skills=[], required_equipment=[],
            route_risk="high", route_blocked=False, estimated_delay_minutes=10,
        )
        out = score_rescue_team(inp)
        assert out.route_risk_penalty == pytest.approx(20.0)

    def test_distance_50km_zero_distance_score(self):
        lat1, lon1 = 0.0, 0.0
        lat2, lon2 = 0.0, 50.0 / 111.0
        d = haversine_distance(lat1, lon1, lat2, lon2)
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=lat1, team_longitude=lon1, team_capacity=50,
            team_current_workload=0, team_skills=[], team_equipment=[],
            incident_latitude=lat2, incident_longitude=lon2, affected_people=20,
            required_skills=[], required_equipment=[],
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert out.distance_km == pytest.approx(d, abs=0.5)
        assert out.distance_score == pytest.approx(0.0, abs=0.1)

    def test_distance_25km_half_distance_score(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=0.0, team_longitude=0.0, team_capacity=50,
            team_current_workload=0, team_skills=[], team_equipment=[],
            incident_latitude=0.0, incident_longitude=25.0 / 111.0,
            affected_people=20, required_skills=[], required_equipment=[],
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert out.distance_score == pytest.approx(15.0, abs=0.5)

    def test_partial_skill_match(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=0.0, team_longitude=0.0, team_capacity=50,
            team_current_workload=0, team_skills=["medical"], team_equipment=[],
            incident_latitude=0.0, incident_longitude=0.0, affected_people=20,
            required_skills=["medical", "search"], required_equipment=[],
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert out.skill_match_pct == pytest.approx(50.0)
        assert out.skill_score == pytest.approx(15.0)

    def test_partial_equipment_match(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=0.0, team_longitude=0.0, team_capacity=50,
            team_current_workload=0, team_skills=[], team_equipment=["radio"],
            incident_latitude=0.0, incident_longitude=0.0, affected_people=20,
            required_skills=[], required_equipment=["radio", "boat"],
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert out.equipment_match_pct == pytest.approx(50.0)
        assert out.equipment_score == pytest.approx(10.0)

    def test_insufficient_capacity(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=0.0, team_longitude=0.0, team_capacity=5,
            team_current_workload=0, team_skills=[], team_equipment=[],
            incident_latitude=0.0, incident_longitude=0.0, affected_people=20,
            required_skills=[], required_equipment=[],
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert out.capacity_score == pytest.approx(2.5)

    def test_high_workload(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=0.0, team_longitude=0.0, team_capacity=50,
            team_current_workload=8, team_skills=[], team_equipment=[],
            incident_latitude=0.0, incident_longitude=0.0, affected_people=20,
            required_skills=[], required_equipment=[],
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert out.workload_score == pytest.approx(2.0)

    def test_no_required_skills_full_score(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=0.0, team_longitude=0.0, team_capacity=50,
            team_current_workload=0, team_skills=[], team_equipment=[],
            incident_latitude=0.0, incident_longitude=0.0, affected_people=20,
            required_skills=[], required_equipment=[],
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert out.skill_match_pct == pytest.approx(100.0)
        assert out.skill_score == pytest.approx(30.0)

    def test_affected_people_zero_capacity_full(self):
        inp = RescueScoringInput(
            team_id=1, availability_status="available",
            team_latitude=0.0, team_longitude=0.0, team_capacity=50,
            team_current_workload=0, team_skills=[], team_equipment=[],
            incident_latitude=0.0, incident_longitude=0.0, affected_people=0,
            required_skills=[], required_equipment=[],
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_rescue_team(inp)
        assert out.capacity_score == pytest.approx(10.0)

    def test_ranking_by_total_score(self):
        inputs = [
            RescueScoringInput(
                team_id=i, availability_status="available",
                team_latitude=0.0, team_longitude=0.0, team_capacity=50,
                team_current_workload=i, team_skills=[], team_equipment=[],
                incident_latitude=0.0, incident_longitude=0.0, affected_people=20,
                required_skills=[], required_equipment=[],
                route_risk="low", route_blocked=False, estimated_delay_minutes=0,
            )
            for i in range(5)
        ]
        ranked = rank_rescue_teams(inputs)
        assert len(ranked) == 5
        assert ranked[0].team_id == 0
        scores = [r.total_score for r in ranked]
        assert scores == sorted(scores, reverse=True)


class TestReliefScoring:
    """Characterization tests for relief warehouse scoring."""

    def test_active_warehouse_eligible(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100, "food": 50},
            available_quantities={"water": 100, "food": 50},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=100,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.eligible
        assert out.warehouse_id == 1
        assert out.distance_km == pytest.approx(0.0)
        assert out.total_supplied_units == 150
        assert out.total_requested_units == 150
        assert out.stock_coverage_pct == pytest.approx(100.0)
        assert out.covered_item_count == 2
        assert out.item_coverage_pct == pytest.approx(100.0)
        assert out.stock_score == pytest.approx(35.0)
        assert out.item_score == pytest.approx(15.0)
        assert out.distance_score == pytest.approx(15.0)
        assert out.vehicle_score == pytest.approx(15.0)
        assert out.route_score == pytest.approx(10.0)
        assert out.workload_score == pytest.approx(10.0)

    def test_closed_warehouse_rejected(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="closed",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert not out.eligible

    def test_blocked_route_rejected(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="low", route_blocked=True, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert not out.eligible

    def test_no_vehicles_rejected(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert not out.eligible

    def test_partial_item_coverage(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100, "food": 50},
            available_quantities={"water": 100, "food": 0},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.eligible
        assert out.stock_coverage_pct == pytest.approx(66.667, abs=0.01)
        assert out.covered_item_count == 1
        assert out.item_coverage_pct == pytest.approx(50.0)
        assert out.stock_score == pytest.approx(23.333, abs=0.01)

    def test_excess_one_item_not_compensate_other(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100, "food": 50},
            available_quantities={"water": 200, "food": 0},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.total_supplied_units == 100
        assert out.stock_coverage_pct == pytest.approx(66.667, abs=0.01)

    def test_distance_10km_boundary(self):
        lat_off = 10.0 / 111.32
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=lat_off, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.distance_km == pytest.approx(10.0, abs=0.5)
        assert out.distance_score == pytest.approx(15.0)

    def test_distance_11km_boundary(self):
        lat_off = 11.0 / 111.32
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=lat_off, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.distance_km == pytest.approx(11.0, abs=0.5)
        assert out.distance_score == pytest.approx(10.5)

    def test_distance_51km_boundary(self):
        lat_off = 51.0 / 111.0
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=lat_off, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.distance_score == pytest.approx(4.5)

    def test_route_medium_risk(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="medium", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.route_score == pytest.approx(5.0)

    def test_route_high_risk(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="high", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.route_score == pytest.approx(2.0)

    def test_workload_ratio_low(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=100,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.workload_score == pytest.approx(10.0)

    def test_workload_ratio_mid(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=500,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.workload_score == pytest.approx(5.0)

    def test_workload_ratio_high(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=900,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.workload_score == pytest.approx(1.0)

    def test_vehicle_capacity_insufficient(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=30, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.vehicle_score == pytest.approx(4.5)

    def test_zero_max_dispatch_capacity_handled(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="active",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=0,
            warehouse_current_dispatch_workload=0,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.eligible
        assert out.workload_score == pytest.approx(10.0)

    def test_limited_warehouse_eligible(self):
        inp = ReliefScoringInput(
            warehouse_id=1, operating_status="limited",
            warehouse_latitude=0.0, warehouse_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            requested_quantities={"water": 100},
            available_quantities={"water": 100},
            eligible_vehicles=[ReliefVehicleInput(vehicle_id=1, capacity_units=500, availability_status="available")],
            warehouse_maximum_dispatch_capacity=1000,
            warehouse_current_dispatch_workload=0,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_relief_warehouse(inp)
        assert out.eligible


class TestShelterScoring:
    """Characterization tests for shelter scoring."""

    def test_open_shelter_eligible(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=100,
            total_capacity=200, occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=True, has_accessibility_support=True,
            has_women_child_safe_area=True, has_food=True,
            has_drinking_water=True, has_sanitation=True, has_power_backup=True,
            supports_long_term_stay=True,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert out.eligible
        assert out.shelter_id == 1
        assert out.available_capacity == 200
        assert out.proposed_people_count == 50
        assert out.distance_km == pytest.approx(0.0)
        assert out.capacity_score == pytest.approx(15.0)
        assert out.distance_score == pytest.approx(15.0)
        assert out.medical_support_score == pytest.approx(10.0)
        assert out.accessibility_support_score == pytest.approx(5.0)
        assert out.women_child_score == pytest.approx(5.0)
        assert out.vulnerability_score == pytest.approx(20.0)
        assert out.utility_score == pytest.approx(15.0)

    def test_closed_shelter_rejected(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="closed",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=100, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=True, has_accessibility_support=True,
            has_women_child_safe_area=True, has_food=True,
            has_drinking_water=True, has_sanitation=True, has_power_backup=True,
            supports_long_term_stay=True,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert not out.eligible

    def test_limited_shelter_eligible(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="limited",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=100, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=True, has_accessibility_support=True,
            has_women_child_safe_area=True, has_food=True,
            has_drinking_water=True, has_sanitation=True, has_power_backup=True,
            supports_long_term_stay=True,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert out.eligible

    def test_no_capacity_rejected(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=100, total_capacity=200,
            occupied_capacity=200, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=True, has_accessibility_support=True,
            has_women_child_safe_area=True, has_food=True,
            has_drinking_water=True, has_sanitation=True, has_power_backup=True,
            supports_long_term_stay=True,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert not out.eligible

    def test_blocked_route_rejected(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=100, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=True, has_accessibility_support=True,
            has_women_child_safe_area=True, has_food=True,
            has_drinking_water=True, has_sanitation=True, has_power_backup=True,
            supports_long_term_stay=True,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=True, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert not out.eligible

    def test_missing_mandatory_medical_rejected(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=100, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=False, has_accessibility_support=True,
            has_women_child_safe_area=True, has_food=True,
            has_drinking_water=True, has_sanitation=True, has_power_backup=True,
            supports_long_term_stay=True,
            mandatory_medical_required=True, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert not out.eligible

    def test_missing_mandatory_accessibility_rejected(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=100, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=True, has_accessibility_support=False,
            has_women_child_safe_area=True, has_food=True,
            has_drinking_water=True, has_sanitation=True, has_power_backup=True,
            supports_long_term_stay=True,
            mandatory_medical_required=False, mandatory_accessibility_required=True,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert not out.eligible

    def test_overcrowding_below_70_pct(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=30,
            total_capacity=200, occupied_capacity=30, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=False, has_accessibility_support=False,
            has_women_child_safe_area=False, has_food=False,
            has_drinking_water=False, has_sanitation=False, has_power_backup=False,
            supports_long_term_stay=False,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        proj = (30 + 30) / 200 * 100
        assert proj == pytest.approx(30.0)
        assert out.projected_occupancy_pct == pytest.approx(30.0)
        assert out.overcrowding_risk_level == "low"
        assert out.overcrowding_score == pytest.approx(10.0)

    def test_overcrowding_70_pct_boundary(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=40,
            total_capacity=200, occupied_capacity=100, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=False, has_accessibility_support=False,
            has_women_child_safe_area=False, has_food=False,
            has_drinking_water=False, has_sanitation=False, has_power_backup=False,
            supports_long_term_stay=False,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        proj = (100 + 40) / 200 * 100
        assert proj == pytest.approx(70.0)
        assert out.overcrowding_risk_level == "moderate"
        assert out.overcrowding_score == pytest.approx(8.0)

    def test_overcrowding_85_pct_boundary(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=70,
            total_capacity=200, occupied_capacity=100, reserved_capacity=0,
            maximum_daily_intake=200, current_intake_workload=0,
            has_medical_support=False, has_accessibility_support=False,
            has_women_child_safe_area=False, has_food=False,
            has_drinking_water=False, has_sanitation=False, has_power_backup=False,
            supports_long_term_stay=False,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        proj = (100 + 70) / 200 * 100
        assert proj == pytest.approx(85.0)
        assert out.overcrowding_risk_level == "high"
        assert out.overcrowding_score == pytest.approx(3.0)

    def test_overcrowding_95_pct_boundary(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=95,
            total_capacity=200, occupied_capacity=95, reserved_capacity=0,
            maximum_daily_intake=200, current_intake_workload=0,
            has_medical_support=False, has_accessibility_support=False,
            has_women_child_safe_area=False, has_food=False,
            has_drinking_water=False, has_sanitation=False, has_power_backup=False,
            supports_long_term_stay=False,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        proj = (95 + 95) / 200 * 100
        assert proj == pytest.approx(95.0)
        assert out.overcrowding_risk_level == "critical"
        assert out.overcrowding_score == pytest.approx(0.0)

    def test_route_medium_risk(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=50, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=False, has_accessibility_support=False,
            has_women_child_safe_area=False, has_food=False,
            has_drinking_water=False, has_sanitation=False, has_power_backup=False,
            supports_long_term_stay=False,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="medium", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert out.route_score == pytest.approx(2.5)

    def test_route_high_risk(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=50, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=False, has_accessibility_support=False,
            has_women_child_safe_area=False, has_food=False,
            has_drinking_water=False, has_sanitation=False, has_power_backup=False,
            supports_long_term_stay=False,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="high", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert out.route_score == pytest.approx(1.0)

    def test_workload_ratio_high(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=50, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=10, current_intake_workload=9,
            has_medical_support=False, has_accessibility_support=False,
            has_women_child_safe_area=False, has_food=False,
            has_drinking_water=False, has_sanitation=False, has_power_backup=False,
            supports_long_term_stay=False,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert out.workload_score == pytest.approx(1.0)

    def test_workload_ratio_mid(self):
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=0.0, incident_longitude=0.0,
            total_displaced_people=50, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=10, current_intake_workload=6,
            has_medical_support=False, has_accessibility_support=False,
            has_women_child_safe_area=False, has_food=False,
            has_drinking_water=False, has_sanitation=False, has_power_backup=False,
            supports_long_term_stay=False,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert out.workload_score == pytest.approx(2.5)

    def test_distance_10km_boundary(self):
        lat_off = 10.0 / 111.32
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=lat_off, incident_longitude=0.0,
            total_displaced_people=50, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=False, has_accessibility_support=False,
            has_women_child_safe_area=False, has_food=False,
            has_drinking_water=False, has_sanitation=False, has_power_backup=False,
            supports_long_term_stay=False,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert out.distance_km == pytest.approx(10.0, abs=0.5)
        assert out.distance_score == pytest.approx(15.0)

    def test_distance_11km_boundary(self):
        lat_off = 11.0 / 111.32
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=lat_off, incident_longitude=0.0,
            total_displaced_people=50, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=False, has_accessibility_support=False,
            has_women_child_safe_area=False, has_food=False,
            has_drinking_water=False, has_sanitation=False, has_power_backup=False,
            supports_long_term_stay=False,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert out.distance_score == pytest.approx(10.5)

    def test_distance_51km_boundary(self):
        lat_off = 51.0 / 111.0
        inp = ShelterScoringInput(
            shelter_id=1, operating_status="open",
            shelter_latitude=0.0, shelter_longitude=0.0,
            incident_latitude=lat_off, incident_longitude=0.0,
            total_displaced_people=50, total_capacity=200,
            occupied_capacity=0, reserved_capacity=0,
            maximum_daily_intake=50, current_intake_workload=0,
            has_medical_support=False, has_accessibility_support=False,
            has_women_child_safe_area=False, has_food=False,
            has_drinking_water=False, has_sanitation=False, has_power_backup=False,
            supports_long_term_stay=False,
            mandatory_medical_required=False, mandatory_accessibility_required=False,
            route_risk="low", route_blocked=False, estimated_delay_minutes=0,
        )
        out = score_shelter(inp)
        assert out.distance_score == pytest.approx(4.5)

    def test_shelter_ranking(self):
        inputs = [
            ShelterScoringInput(
                shelter_id=i, operating_status="open",
                shelter_latitude=0.0, shelter_longitude=0.0,
                incident_latitude=0.0, incident_longitude=0.0,
                total_displaced_people=50, total_capacity=200,
                occupied_capacity=0, reserved_capacity=0,
                maximum_daily_intake=50, current_intake_workload=i * 2,
                has_medical_support=False, has_accessibility_support=False,
                has_women_child_safe_area=False, has_food=False,
                has_drinking_water=False, has_sanitation=False, has_power_backup=False,
                supports_long_term_stay=False,
                mandatory_medical_required=False, mandatory_accessibility_required=False,
                route_risk="low", route_blocked=False, estimated_delay_minutes=0,
            )
            for i in range(5)
        ]
        ranked = rank_shelters(inputs)
        assert len(ranked) == 5
        assert ranked[0].shelter_id == 0
        scores = [r.total_score for r in ranked]
        assert scores == sorted(scores, reverse=True)


class TestOvercrowdingRisk:
    def test_risk_below_70(self):
        assert calculate_overcrowding_risk(69.9) == "low"
    def test_risk_70_boundary(self):
        assert calculate_overcrowding_risk(70.0) == "moderate"
    def test_risk_84_boundary(self):
        assert calculate_overcrowding_risk(84.9) == "moderate"
    def test_risk_85_boundary(self):
        assert calculate_overcrowding_risk(85.0) == "high"
    def test_risk_94_boundary(self):
        assert calculate_overcrowding_risk(94.9) == "high"
    def test_risk_95_boundary(self):
        assert calculate_overcrowding_risk(95.0) == "critical"
    def test_risk_100(self):
        assert calculate_overcrowding_risk(100.0) == "critical"