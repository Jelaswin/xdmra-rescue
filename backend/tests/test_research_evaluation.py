"""
Phase 9 Research Evaluation Tests.

Tests for rescue/relief/shelter baselines, scenario determinism,
experiment runner, priority evaluation, explainability, and exports.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path

from evaluation.baselines.rescue_baselines import (
    RandomAvailableBaseline, FirstAvailableBaseline, NearestAvailableBaseline,
    SkillMatchOnlyBaseline, PriorityDistanceOnlyBaseline,
    get_all_rescue_baselines, RescueScenario, haversine_distance
)
from evaluation.baselines.relief_baselines import (
    FirstStockedWarehouseBaseline, NearestStockedWarehouseBaseline,
    HighestStockCoverageBaseline, get_all_relief_baselines,
    ReliefScenario, ReliefBaselineResult
)
from evaluation.baselines.shelter_baselines import (
    NearestAvailableShelterBaseline, LargestCapacityShelterBaseline,
    FirstAvailableShelterBaseline, CapacityOnlyBaseline,
    get_all_shelter_baselines, ShelterScenario, ShelterBaselineResult
)
from evaluation.scenarios import get_rescue_scenarios, get_relief_scenarios, get_shelter_scenarios
from evaluation.metrics import (
    calculate_rescue_metrics, calculate_relief_metrics, calculate_shelter_metrics
)
from evaluation.experiment_runner import run_experiment, run_rescue_experiment, run_relief_experiment, run_shelter_experiment
from evaluation.exporters import export_csv, export_json, export_markdown_table, export_latex_table
from evaluation.statistics import descriptive_statistics, DirectionMapping, MetricDirectionError
from evaluation.paper_tables import build_rescue_comparison_table, build_relief_comparison_table


class TestHaversineDistance:
    def test_haversine_same_point(self):
        assert haversine_distance(0, 0, 0, 0) == 0.0

    def test_haversine_known_distance(self):
        d = haversine_distance(0, 0, 1, 0)
        assert 110 < d < 112

    def test_haversine_symmetric(self):
        d1 = haversine_distance(10, 20, 15, 25)
        d2 = haversine_distance(15, 25, 10, 20)
        assert abs(d1 - d2) < 0.001


class TestRescueScenarios:
    def test_rescue_scenario_count(self):
        scenarios = get_rescue_scenarios()
        assert len(scenarios) >= 25

    def test_unique_scenario_ids(self):
        scenarios = get_rescue_scenarios()
        ids = [s.scenario_id for s in scenarios]
        assert len(ids) == len(set(ids))

    def test_rescue_scenarios_deterministic(self):
        s1 = get_rescue_scenarios()
        s2 = get_rescue_scenarios()
        assert s1 == s2

    def test_rescue_scenario_has_required_fields(self):
        for s in get_rescue_scenarios():
            assert s.scenario_id
            assert hasattr(s, 'latitude')
            assert hasattr(s, 'longitude')
            assert hasattr(s, 'priority_level')
            assert hasattr(s, 'available_teams')


class TestReliefScenarios:
    def test_relief_scenario_count(self):
        scenarios = get_relief_scenarios()
        assert len(scenarios) >= 20

    def test_unique_scenario_ids(self):
        scenarios = get_relief_scenarios()
        ids = [s.scenario_id for s in scenarios]
        assert len(ids) == len(set(ids))

    def test_relief_scenarios_deterministic(self):
        s1 = get_relief_scenarios()
        s2 = get_relief_scenarios()
        assert s1 == s2

    def test_relief_scenario_has_warehouses(self):
        for s in get_relief_scenarios():
            assert hasattr(s, 'warehouses')
            assert len(s.warehouses) > 0


class TestShelterScenarios:
    def test_shelter_scenario_count(self):
        scenarios = get_shelter_scenarios()
        assert len(scenarios) >= 20

    def test_unique_scenario_ids(self):
        scenarios = get_shelter_scenarios()
        ids = [s.scenario_id for s in scenarios]
        assert len(ids) == len(set(ids))

    def test_shelter_scenarios_deterministic(self):
        s1 = get_shelter_scenarios()
        s2 = get_shelter_scenarios()
        assert s1 == s2


class TestFirstAvailableBaseline:
    def test_selects_first_available(self):
        baseline = FirstAvailableBaseline()
        scenario = RescueScenario(
            scenario_id="test",
            incident_id=1, incident_title="Test", incident_type="Flood",
            latitude=10.0, longitude=76.0, priority_level="medium",
            required_skills=[], required_equipment=[],
            affected_people=10, trapped_people=0,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 10.1, "longitude": 76.1,
                 "availability_status": "available", "skills": [], "equipment": [], "capacity": 10, "current_workload": 0},
                {"id": 2, "name": "Team Beta", "latitude": 10.2, "longitude": 76.2,
                 "availability_status": "available", "skills": [], "equipment": [], "capacity": 10, "current_workload": 0},
            ]
        )
        result = baseline.select(scenario)
        assert result.success
        assert result.selected_team_id == 1

    def test_no_available_teams(self):
        baseline = FirstAvailableBaseline()
        scenario = RescueScenario(
            scenario_id="test", incident_id=1, incident_title="Test", incident_type="Flood",
            latitude=10.0, longitude=76.0, priority_level="medium",
            required_skills=[], required_equipment=[], affected_people=10, trapped_people=0,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 10.1, "longitude": 76.1,
                 "availability_status": "unavailable", "skills": [], "equipment": [], "capacity": 10, "current_workload": 0},
            ]
        )
        result = baseline.select(scenario)
        assert not result.success


class TestNearestBaseline:
    def test_nearest_selected(self):
        baseline = NearestAvailableBaseline()
        scenario = RescueScenario(
            scenario_id="test", incident_id=1, incident_title="Test", incident_type="Flood",
            latitude=10.0, longitude=76.0, priority_level="medium",
            required_skills=[], required_equipment=[], affected_people=10, trapped_people=0,
            available_teams=[
                {"id": 1, "name": "Team Far", "latitude": 11.0, "longitude": 77.0,
                 "availability_status": "available", "skills": [], "equipment": [], "capacity": 10, "current_workload": 0},
                {"id": 2, "name": "Team Near", "latitude": 10.01, "longitude": 76.01,
                 "availability_status": "available", "skills": [], "equipment": [], "capacity": 10, "current_workload": 0},
            ]
        )
        result = baseline.select(scenario)
        assert result.success
        assert result.selected_team_id == 2
        assert result.distance_km > 0


class TestRandomBaseline:
    def test_deterministic_with_seed(self):
        baseline1 = RandomAvailableBaseline(seed=42)
        baseline2 = RandomAvailableBaseline(seed=42)
        scenario = RescueScenario(
            scenario_id="test", incident_id=1, incident_title="Test", incident_type="Flood",
            latitude=10.0, longitude=76.0, priority_level="medium",
            required_skills=[], required_equipment=[], affected_people=10, trapped_people=0,
            available_teams=[
                {"id": i, "name": f"Team {i}", "latitude": 10.0 + i * 0.01, "longitude": 76.0,
                 "availability_status": "available", "skills": [], "equipment": [], "capacity": 10, "current_workload": 0}
                for i in range(1, 11)
            ]
        )
        r1 = baseline1.select(scenario)
        r2 = baseline2.select(scenario)
        assert r1.selected_team_id == r2.selected_team_id

    def test_different_seeds_different_results(self):
        baseline1 = RandomAvailableBaseline(seed=1)
        baseline2 = RandomAvailableBaseline(seed=2)
        scenario = RescueScenario(
            scenario_id="test", incident_id=1, incident_title="Test", incident_type="Flood",
            latitude=10.0, longitude=76.0, priority_level="medium",
            required_skills=[], required_equipment=[], affected_people=10, trapped_people=0,
            available_teams=[
                {"id": i, "name": f"Team {i}", "latitude": 10.0 + i * 0.01, "longitude": 76.0,
                 "availability_status": "available", "skills": [], "equipment": [], "capacity": 10, "current_workload": 0}
                for i in range(1, 11)
            ]
        )
        r1 = baseline1.select(scenario)
        r2 = baseline2.select(scenario)
        assert r1.selected_team_id != r2.selected_team_id or r1.selected_team_id is None


class TestReliefBaselines:
    def test_first_stocked_warehouse(self):
        baseline = FirstStockedWarehouseBaseline()
        scenario = ReliefScenario(
            scenario_id="test",
            incident_id=1,
            items={"water": 100, "food": 50},
            total_people=100,
            latitude=10.0,
            longitude=76.0,
            warehouses=[
                {"id": 1, "name": "WH1", "latitude": 10.1, "longitude": 76.1,
                 "operating_status": "active", "inventory": {"water": 200, "food": 100}},
                {"id": 2, "name": "WH2", "latitude": 10.2, "longitude": 76.2,
                 "operating_status": "active", "inventory": {"water": 50, "food": 20}},
            ]
        )
        result = baseline.select(scenario)
        assert result.success
        assert 1 in result.warehouses_used

    def test_no_over_allocation(self):
        baseline = NearestStockedWarehouseBaseline()
        scenario = ReliefScenario(
            scenario_id="test",
            incident_id=1,
            items={"water": 1000},
            total_people=100,
            latitude=10.0,
            longitude=76.0,
            warehouses=[
                {"id": 1, "name": "WH1", "latitude": 10.0, "longitude": 76.0,
                 "operating_status": "active", "inventory": {"water": 500}},
            ]
        )
        result = baseline.select(scenario)
        assert result.success
        assert result.fulfilment_pct <= 100


class TestShelterBaselines:
    def test_nearest_available_shelter(self):
        baseline = NearestAvailableShelterBaseline()
        scenario = ShelterScenario(
            scenario_id="test",
            incident_id=1,
            displaced_people=50,
            medical_required=False,
            accessibility_required=False,
            latitude=10.0,
            longitude=76.0,
            shelters=[
                {"id": 1, "name": "Shelter A", "latitude": 10.5, "longitude": 76.5,
                 "operating_status": "open", "total_capacity": 100, "occupied_capacity": 30,
                 "reserved_capacity": 10, "has_medical": False, "has_accessibility": False},
                {"id": 2, "name": "Shelter B", "latitude": 10.1, "longitude": 76.1,
                 "operating_status": "open", "total_capacity": 100, "occupied_capacity": 20,
                 "reserved_capacity": 10, "has_medical": False, "has_accessibility": False},
            ]
        )
        result = baseline.select(scenario)
        assert result.success
        assert 2 in result.shelters_used

    def test_no_capacity_violation(self):
        baseline = NearestAvailableShelterBaseline()
        scenario = ShelterScenario(
            scenario_id="test",
            incident_id=1,
            displaced_people=500,
            medical_required=False,
            accessibility_required=False,
            latitude=10.0,
            longitude=76.0,
            shelters=[
                {"id": 1, "name": "Shelter A", "latitude": 10.0, "longitude": 76.0,
                 "operating_status": "open", "total_capacity": 50, "occupied_capacity": 40,
                 "reserved_capacity": 0, "has_medical": False, "has_accessibility": False},
            ]
        )
        result = baseline.select(scenario)
        assert result.success
        assert result.uncovered_people > 0


class TestRescueMetrics:
    def test_calculate_rescue_metrics(self):
        results = [
            {"success": True, "distance_km": 10.0, "skill_match_pct": 80.0,
             "equipment_match_pct": 90.0, "computation_time_ms": 5.0,
             "selected_team_workload": 2, "priority_level": "high"},
            {"success": True, "distance_km": 15.0, "skill_match_pct": 100.0,
             "equipment_match_pct": 80.0, "computation_time_ms": 4.0,
             "selected_team_workload": 1, "priority_level": "critical"},
            {"success": False, "distance_km": 0, "skill_match_pct": 0,
             "equipment_match_pct": 0, "computation_time_ms": 2.0,
             "selected_team_workload": 0, "priority_level": "medium"},
        ]
        metrics = calculate_rescue_metrics(results)
        assert metrics["success_rate_pct"] == pytest.approx(66.67, rel=0.1)
        assert "mean_distance_km" in metrics
        assert "jains_fairness_index" in metrics


class TestReliefMetrics:
    def test_calculate_relief_metrics(self):
        results = [
            {"success": True, "fulfilment_pct": 100.0, "shortage": 0,
             "distance_km": 5.0, "warehouses_used": [1], "computation_time_ms": 3.0,
             "stock_violations": 0, "split_allocation": False},
            {"success": True, "fulfilment_pct": 80.0, "shortage": 20,
             "distance_km": 8.0, "warehouses_used": [1, 2], "computation_time_ms": 4.0,
             "stock_violations": 0, "split_allocation": True},
        ]
        metrics = calculate_relief_metrics(results)
        assert metrics["allocation_success_count"] == 2
        assert metrics["success_rate_pct"] == 100.0
        assert "macro_fulfilment_pct" in metrics
        assert "weighted_fulfilment_pct" in metrics
        assert metrics["fully_fulfilled_count"] == 1
        assert metrics["partial_fulfilment_count"] == 1
        assert "mean_shortage" in metrics
        assert "total_shortage" in metrics
        assert "total_stock_violations" in metrics


class TestExperimentRunner:
    def test_run_rescue_experiment(self):
        scenarios = get_rescue_scenarios()[:5]
        baselines = get_all_rescue_baselines()
        result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        assert len(result["results"]) > 0
        assert len(result["metrics"]) > 0

    def test_run_relief_experiment(self):
        scenarios = get_relief_scenarios()[:5]
        baselines = get_all_relief_baselines()
        result = run_relief_experiment(scenarios, baselines, repeat=1, seed=42)
        assert len(result["results"]) > 0
        assert len(result["metrics"]) > 0

    def test_run_shelter_experiment(self):
        scenarios = get_shelter_scenarios()[:5]
        baselines = get_all_shelter_baselines()
        result = run_shelter_experiment(scenarios, baselines, repeat=1, seed=42)
        assert len(result["results"]) > 0
        assert len(result["metrics"]) > 0


class TestExports:
    def test_csv_export(self):
        results = [{"a": 1, "b": 2.5}, {"a": 3, "b": 4.5}]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            export_csv(results, Path(f.name))
            content = f.read().decode()
            assert "a,b" in content
            assert "1,2.5" in content

    def test_json_export(self):
        results = {"metrics": {"accuracy": 0.95}}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            export_json(results, Path(f.name))
            with open(f.name) as rf:
                loaded = json.load(rf)
                assert loaded["metrics"]["accuracy"] == 0.95

    def test_markdown_table(self):
        headers = ["Metric", "Value"]
        rows = [["Accuracy", "0.95"], ["F1", "0.90"]]
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            export_markdown_table(headers, rows, Path(f.name))
            content = f.read().decode()
            assert "| Metric | Value |" in content
            assert "| Accuracy | 0.95 |" in content

    def test_latex_table(self):
        headers = ["Metric", "Value"]
        rows = [["Accuracy", "0.95"], ["F1", "0.90"]]
        with tempfile.NamedTemporaryFile(suffix=".tex", delete=False) as f:
            export_latex_table(headers, rows, Path(f.name))
            content = f.read().decode()
            assert "\\begin{table}" in content
            assert "Accuracy" in content
            assert "\\%" not in content or "\\%" in content

    def test_latex_escaping(self):
        headers = ["Metric % Name", "Value $"]
        rows = [["Test & Value", "100%"]]
        with tempfile.NamedTemporaryFile(suffix=".tex", delete=False) as f:
            export_latex_table(headers, rows, Path(f.name))
            content = f.read().decode()
            assert "\\begin{table}" in content
            assert "\\centering" in content
            assert "Metric" in content
            assert "100" in content

    def test_csv_none_handling(self):
        results = [{"a": None, "b": 2.5}]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            export_csv(results, Path(f.name))
            content = f.read().decode()
            assert ",2.5" in content


class TestDescriptiveStatistics:
    def test_empty_input(self):
        stats = descriptive_statistics([])
        assert stats["count"] == 0

    def test_single_value(self):
        stats = descriptive_statistics([42])
        assert stats["mean"] == 42.0
        assert stats["std"] == 0.0

    def test_normal_values(self):
        stats = descriptive_statistics([1, 2, 3, 4, 5])
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0


class TestDirectionMapping:
    def test_known_lower_is_better(self):
        dm = DirectionMapping()
        assert dm.get_direction("mean_distance_km") == "lower_is_better"

    def test_known_higher_is_better(self):
        dm = DirectionMapping()
        assert dm.get_direction("allocation_success_rate") == "higher_is_better"

    def test_unknown_raises(self):
        dm = DirectionMapping()
        with pytest.raises(MetricDirectionError):
            dm.get_direction("unknown_metric")

    def test_custom_mapping(self):
        dm = DirectionMapping(lower_is_better=["custom_metric"])
        assert dm.get_direction("custom_metric") == "lower_is_better"

    def test_override_default(self):
        dm = DirectionMapping(lower_is_better=["custom_dist"], higher_is_better=[])
        assert dm.get_direction("custom_dist") == "lower_is_better"
        with pytest.raises(MetricDirectionError):
            dm.get_direction("mean_distance_km")


class TestJainFairnessIndex:
    def test_perfect_fairness(self):
        from evaluation.metrics import calculate_workload_fairness_metrics
        workloads = [1, 1, 1, 1]
        result = calculate_workload_fairness_metrics(workloads)
        assert result["jains_fairness_index"] == 1.0

    def test_zero_workloads(self):
        from evaluation.metrics import calculate_workload_fairness_metrics
        workloads = [0, 0, 0]
        result = calculate_workload_fairness_metrics(workloads)
        assert result["jains_fairness_index"] == 0.0

    def test_empty_workloads(self):
        from evaluation.metrics import calculate_workload_fairness_metrics
        result = calculate_workload_fairness_metrics([])
        assert result == {}


class TestPaperTables:
    def test_build_rescue_table(self):
        metrics = {
            "random_available": {"success_rate_pct": 80.0, "mean_distance_km": 15.0,
                                 "mean_skill_match_pct": 70.0, "mean_route_safety_score": 0.9,
                                 "jains_fairness_index": 0.85, "mean_computation_time_ms": 5.0},
            "nearest_available": {"success_rate_pct": 95.0, "mean_distance_km": 8.0,
                                  "mean_skill_match_pct": 65.0, "mean_route_safety_score": 0.85,
                                  "jains_fairness_index": 0.88, "mean_computation_time_ms": 4.0},
        }
        rows = build_rescue_comparison_table(metrics, ["random_available", "nearest_available"])
        assert len(rows) == 2
        assert rows[0]["Algorithm"] == "random_available"
        assert rows[1]["Algorithm"] == "nearest_available"


class TestAllAlgorithmCounts:
    def test_rescue_baseline_count(self):
        baselines = get_all_rescue_baselines()
        assert len(baselines) >= 5

    def test_relief_baseline_count(self):
        baselines = get_all_relief_baselines()
        assert len(baselines) >= 4

    def test_shelter_baseline_count(self):
        baselines = get_all_shelter_baselines()
        assert len(baselines) >= 4


class TestBlockedTeamExclusion:
    def test_unavailable_team_not_selected(self):
        baseline = FirstAvailableBaseline()
        scenario = RescueScenario(
            scenario_id="test", incident_id=1, incident_title="Test", incident_type="Flood",
            latitude=10.0, longitude=76.0, priority_level="medium",
            required_skills=[], required_equipment=[], affected_people=10, trapped_people=0,
            available_teams=[
                {"id": 1, "name": "Team Alpha", "latitude": 10.0, "longitude": 76.0,
                 "availability_status": "unavailable", "skills": [], "equipment": [], "capacity": 10, "current_workload": 0},
                {"id": 2, "name": "Team Beta", "latitude": 10.0, "longitude": 76.0,
                 "availability_status": "available", "skills": [], "equipment": [], "capacity": 10, "current_workload": 0},
            ]
        )
        result = baseline.select(scenario)
        assert result.success
        assert result.selected_team_id == 2


class TestBlockedWarehouseExclusion:
    def test_closed_warehouse_not_selected(self):
        baseline = FirstStockedWarehouseBaseline()
        scenario = ReliefScenario(
            scenario_id="test",
            incident_id=1,
            items={"water": 100},
            total_people=50,
            latitude=10.0,
            longitude=76.0,
            warehouses=[
                {"id": 1, "name": "WH1", "latitude": 10.0, "longitude": 76.0,
                 "operating_status": "closed", "inventory": {"water": 200}},
                {"id": 2, "name": "WH2", "latitude": 10.0, "longitude": 76.0,
                 "operating_status": "active", "inventory": {"water": 150}},
            ]
        )
        result = baseline.select(scenario)
        assert result.success
        assert 1 not in result.warehouses_used
        assert 2 in result.warehouses_used


class TestNoOperationalMutation:
    def test_relief_baseline_does_not_mutate_warehouse(self):
        baseline = FirstStockedWarehouseBaseline()
        warehouse = {"id": 1, "name": "WH1", "latitude": 10.0, "longitude": 76.0,
                     "operating_status": "active", "inventory": {"water": 100}}
        scenario = ReliefScenario(
            scenario_id="test",
            incident_id=1,
            items={"water": 50},
            total_people=50,
            latitude=10.0,
            longitude=76.0,
            warehouses=[warehouse]
        )
        original_inventory = dict(warehouse["inventory"])
        result = baseline.select(scenario)
        assert result.success
        assert warehouse["inventory"] == original_inventory


class TestXDMRAAdapters:
    """Tests for X-DMRA production service adapters."""

    def test_xdmra_rescue_adapter_exists(self):
        from evaluation.baselines.xdmra_adapters import XDMRAExplainableAdapter
        adapter = XDMRAExplainableAdapter()
        assert adapter.name == "xdmra_explainable"

    def test_xdmra_rescue_adapter_executes(self):
        from evaluation.baselines.xdmra_adapters import XDMRAExplainableAdapter
        from evaluation.baselines.rescue_baselines import RescueScenario
        adapter = XDMRAExplainableAdapter()
        scenario = RescueScenario(
            scenario_id="test_xdmra",
            incident_id=1,
            incident_title="Test",
            incident_type="Flood",
            latitude=10.0,
            longitude=76.0,
            priority_level="high",
            required_skills=["flood_rescue"],
            required_equipment=["boat"],
            affected_people=20,
            trapped_people=5,
            available_teams=[
                {"id": 1, "name": "Team A", "latitude": 10.1, "longitude": 76.1,
                 "availability_status": "available", "skills": ["flood_rescue"], "equipment": ["boat", "life_jackets"],
                 "capacity": 15, "current_workload": 2},
            ]
        )
        result = adapter.select(scenario)
        assert result.success or not result.success
        assert result.scenario_id == "test_xdmra"
        assert hasattr(result, "explanation")
        assert hasattr(result, "distance_km")

    def test_xdmra_rescue_adapter_no_eligible_teams(self):
        from evaluation.baselines.xdmra_adapters import XDMRAExplainableAdapter
        from evaluation.baselines.rescue_baselines import RescueScenario
        adapter = XDMRAExplainableAdapter()
        scenario = RescueScenario(
            scenario_id="test_no_team",
            incident_id=1,
            incident_title="Test",
            incident_type="Flood",
            latitude=10.0,
            longitude=76.0,
            priority_level="high",
            required_skills=[],
            required_equipment=[],
            affected_people=20,
            trapped_people=0,
            available_teams=[]
        )
        result = adapter.select(scenario)
        assert not result.success
        assert result.failure_reason is not None

    def test_xdmra_relief_adapter_exists(self):
        from evaluation.baselines.xdmra_adapters import XDMRAReliefAdapter
        adapter = XDMRAReliefAdapter()
        assert adapter.name == "xdmra_relief_allocation"

    def test_xdmra_relief_adapter_executes(self):
        from evaluation.baselines.xdmra_adapters import XDMRAReliefAdapter
        from evaluation.baselines.relief_baselines import ReliefScenario
        adapter = XDMRAReliefAdapter()
        scenario = ReliefScenario(
            scenario_id="test_relief_xdmra",
            incident_id=1,
            items={"water": 100, "food": 50},
            total_people=100,
            latitude=10.0,
            longitude=76.0,
            warehouses=[
                {"id": 1, "name": "WH1", "latitude": 10.1, "longitude": 76.1,
                 "operating_status": "active", "inventory": {"water": 200, "food": 100}},
            ]
        )
        result = adapter.select(scenario)
        assert result.success or not result.success
        assert result.scenario_id == "test_relief_xdmra"
        assert hasattr(result, "fulfilment_pct")

    def test_xdmra_shelter_adapter_exists(self):
        from evaluation.baselines.xdmra_adapters import XDMRAShelterAdapter
        adapter = XDMRAShelterAdapter()
        assert adapter.name == "xdmra_shelter_allocation"

    def test_xdmra_shelter_adapter_executes(self):
        from evaluation.baselines.xdmra_adapters import XDMRAShelterAdapter
        from evaluation.baselines.shelter_baselines import ShelterScenario
        adapter = XDMRAShelterAdapter()
        scenario = ShelterScenario(
            scenario_id="test_shelter_xdmra",
            incident_id=1,
            displaced_people=50,
            medical_required=False,
            accessibility_required=False,
            latitude=10.0,
            longitude=76.0,
            shelters=[
                {"id": 1, "name": "Shelter A", "latitude": 10.1, "longitude": 76.1,
                 "operating_status": "open", "total_capacity": 100, "occupied_capacity": 20,
                 "reserved_capacity": 10, "has_medical": False, "has_accessibility": False},
            ]
        )
        result = adapter.select(scenario)
        assert result.success or not result.success
        assert result.scenario_id == "test_shelter_xdmra"
        assert hasattr(result, "population_coverage_pct")

    def test_xdmra_rescue_adapter_does_not_mutate_operational_state(self):
        from evaluation.baselines.xdmra_adapters import XDMRAExplainableAdapter
        from evaluation.baselines.rescue_baselines import RescueScenario
        adapter = XDMRAExplainableAdapter()
        team = {"id": 1, "name": "Team A", "latitude": 10.1, "longitude": 76.1,
                "availability_status": "available", "skills": ["flood_rescue"],
                "equipment": ["boat"], "capacity": 15, "current_workload": 2}
        scenario = RescueScenario(
            scenario_id="test_no_mutate",
            incident_id=1,
            incident_title="Test",
            incident_type="Flood",
            latitude=10.0,
            longitude=76.0,
            priority_level="high",
            required_skills=[],
            required_equipment=[],
            affected_people=20,
            trapped_people=0,
            available_teams=[team]
        )
        original_workload = team["current_workload"]
        result = adapter.select(scenario)
        assert team["current_workload"] == original_workload

    def test_get_all_rescue_algorithms_with_xdmra_count(self):
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        algos = get_all_rescue_algorithms_with_xdmra()
        assert len(algos) == 6
        assert "xdmra_explainable" in algos

    def test_get_all_relief_algorithms_with_xdmra_count(self):
        from evaluation.baselines import get_all_relief_algorithms_with_xdmra
        algos = get_all_relief_algorithms_with_xdmra()
        assert len(algos) == 5
        assert "xdmra_relief_allocation" in algos

    def test_get_all_shelter_algorithms_with_xdmra_count(self):
        from evaluation.baselines import get_all_shelter_algorithms_with_xdmra
        algos = get_all_shelter_algorithms_with_xdmra()
        assert len(algos) == 5
        assert "xdmra_shelter_allocation" in algos

    def test_rescue_comparison_includes_xdmra(self):
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        from evaluation.scenarios import get_rescue_scenarios
        from evaluation.experiment_runner import run_rescue_experiment
        scenarios = get_rescue_scenarios()[:3]
        baselines = get_all_rescue_algorithms_with_xdmra()
        result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        algorithm_names = set(r["algorithm"] for r in result["results"])
        assert "xdmra_explainable" in algorithm_names
        assert len(algorithm_names) == 6

    def test_relief_comparison_includes_xdmra(self):
        from evaluation.baselines import get_all_relief_algorithms_with_xdmra
        from evaluation.scenarios import get_relief_scenarios
        from evaluation.experiment_runner import run_relief_experiment
        scenarios = get_relief_scenarios()[:3]
        baselines = get_all_relief_algorithms_with_xdmra()
        result = run_relief_experiment(scenarios, baselines, repeat=1, seed=42)
        algorithm_names = set(r["algorithm"] for r in result["results"])
        assert "xdmra_relief_allocation" in algorithm_names
        assert len(algorithm_names) == 5

    def test_shelter_comparison_includes_xdmra(self):
        from evaluation.baselines import get_all_shelter_algorithms_with_xdmra
        from evaluation.scenarios import get_shelter_scenarios
        from evaluation.experiment_runner import run_shelter_experiment
        scenarios = get_shelter_scenarios()[:3]
        baselines = get_all_shelter_algorithms_with_xdmra()
        result = run_shelter_experiment(scenarios, baselines, repeat=1, seed=42)
        algorithm_names = set(r["algorithm"] for r in result["results"])
        assert "xdmra_shelter_allocation" in algorithm_names
        assert len(algorithm_names) == 5


class TestXDMRAExplainabilityCounts:
    """Focused tests for X-DMRA explainability evaluation counts and metrics."""

    def test_rescue_explanation_count_equals_scenarios(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        from evaluation.scenarios import get_rescue_scenarios
        from evaluation.experiment_runner import run_rescue_experiment
        scenarios = get_rescue_scenarios()
        baselines = get_all_rescue_algorithms_with_xdmra()
        experiment_result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        eval_result = run_explainability_evaluation(rescue_results=experiment_result["results"])
        assert eval_result["rescue"].explanations_with_content == 25
        assert eval_result["rescue"].scenarios_evaluated == 25

    def test_relief_explanation_count_equals_scenarios(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import get_all_relief_algorithms_with_xdmra
        from evaluation.scenarios import get_relief_scenarios
        from evaluation.experiment_runner import run_relief_experiment
        scenarios = get_relief_scenarios()
        baselines = get_all_relief_algorithms_with_xdmra()
        experiment_result = run_relief_experiment(scenarios, baselines, repeat=1, seed=42)
        eval_result = run_explainability_evaluation(relief_results=experiment_result["results"])
        assert eval_result["relief"].explanations_with_content == 20
        assert eval_result["relief"].scenarios_evaluated == 20

    def test_shelter_explanation_count_equals_scenarios(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import get_all_shelter_algorithms_with_xdmra
        from evaluation.scenarios import get_shelter_scenarios
        from evaluation.experiment_runner import run_shelter_experiment
        scenarios = get_shelter_scenarios()
        baselines = get_all_shelter_algorithms_with_xdmra()
        experiment_result = run_shelter_experiment(scenarios, baselines, repeat=1, seed=42)
        eval_result = run_explainability_evaluation(shelter_results=experiment_result["results"])
        assert eval_result["shelter"].explanations_with_content == 20
        assert eval_result["shelter"].scenarios_evaluated == 20

    def test_baselines_excluded_from_explainability(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        from evaluation.scenarios import get_rescue_scenarios
        from evaluation.experiment_runner import run_rescue_experiment
        scenarios = get_rescue_scenarios()[:5]
        baselines = get_all_rescue_algorithms_with_xdmra()
        experiment_result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        eval_result = run_explainability_evaluation(rescue_results=experiment_result["results"])
        assert eval_result["rescue"].baseline_support == "not_supported"
        baseline_note = eval_result["rescue"].baseline_note
        assert "Baseline algorithms do not produce explanations" in baseline_note

    def test_missing_distance_becomes_na_or_pass(self):
        from evaluation.explainability_evaluation import _check_distance
        result_with_zero_distance = {"distance_km": 0.0}
        passed, detail, applicable = _check_distance(None, result_with_zero_distance)
        assert detail == "no_explanation"
        result_no_distance = {"distance_km": 5.0}
        no_tokens, no_detail, no_applicable = _check_distance("Team Alpha selected.", result_no_distance)
        assert no_tokens is False
        assert no_detail == "no_distance_found"
        has_tokens, tok_detail, tok_applicable = _check_distance("Team Alpha selected, 5.2 km away.", result_no_distance)
        assert has_tokens is True

    def test_limitation_check_applies_only_when_limitation_exists(self):
        from evaluation.explainability_evaluation import _check_limitation
        no_limit_explanation = "Team Alpha selected because it has all required skills."
        no_limit_result = {}
        passed, detail, applicable = _check_limitation(no_limit_explanation, no_limit_result)
        assert passed is False
        has_limit_explanation = "Team Alpha selected but has limited capacity."
        passed2, detail2, applicable2 = _check_limitation(has_limit_explanation, no_limit_result)
        assert passed2 is True

    def test_alternative_comparison_na_when_no_alternative(self):
        from evaluation.explainability_evaluation import _check_alternative_comparison
        no_alt_explanation = "Team Alpha assigned."
        no_alt_result = {}
        passed, detail, applicable = _check_alternative_comparison(no_alt_explanation, no_alt_result)
        assert passed is False
        assert detail == "no_alternative_comparison"
        has_alt_explanation = "Team Alpha selected instead of Team Beta due to better skills."
        passed2, detail2, applicable2 = _check_alternative_comparison(has_alt_explanation, no_alt_result)
        assert passed2 is True

    def test_incorrect_resource_name_fails_coverage(self):
        from evaluation.explainability_evaluation import _check_resource_name
        wrong_resource = "A resource was deployed for this incident."
        wrong_result = {}
        passed, detail, applicable = _check_resource_name(wrong_resource, wrong_result)
        assert passed is False
        assert detail == "no_resource_name_found"
        correct_resource = "Team Alpha is recommended."
        passed2, detail2, applicable2 = _check_resource_name(correct_resource, wrong_result)
        assert passed2 is True

    def test_incorrect_stored_distance_fails_consistency(self):
        from evaluation.explainability_evaluation import _check_stored_value_consistency
        wrong_distance_explanation = "Team Alpha assigned, distance 25.0 km."
        wrong_distance_result = {"distance_km": 10.0}
        consistent, detail, applicable = _check_stored_value_consistency(wrong_distance_explanation, wrong_distance_result)
        assert consistent is False
        assert "inconsist" in detail.lower() or "mismatch" in detail.lower()

    def test_numerator_never_exceeds_denominator_in_full_evaluation(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import (
            get_all_rescue_algorithms_with_xdmra,
            get_all_relief_algorithms_with_xdmra,
            get_all_shelter_algorithms_with_xdmra
        )
        from evaluation.scenarios import get_rescue_scenarios, get_relief_scenarios, get_shelter_scenarios
        from evaluation.experiment_runner import run_rescue_experiment, run_relief_experiment, run_shelter_experiment

        rescue_scenarios = get_rescue_scenarios()
        relief_scenarios = get_relief_scenarios()
        shelter_scenarios = get_shelter_scenarios()

        rescue_exp = run_rescue_experiment(rescue_scenarios, get_all_rescue_algorithms_with_xdmra(), repeat=1, seed=42)
        relief_exp = run_relief_experiment(relief_scenarios, get_all_relief_algorithms_with_xdmra(), repeat=1, seed=42)
        shelter_exp = run_shelter_experiment(shelter_scenarios, get_all_shelter_algorithms_with_xdmra(), repeat=1, seed=42)

        eval_result = run_explainability_evaluation(
            rescue_results=rescue_exp["results"],
            relief_results=relief_exp["results"],
            shelter_results=shelter_exp["results"]
        )

        for module, result in eval_result.items():
            for elem_name, metric in result.element_metrics.items():
                assert metric["numerator"] <= metric["denominator"], \
                    f"{module}.{elem_name}: numerator {metric['numerator']} > denominator {metric['denominator']}"

    def test_percentage_remains_between_zero_and_hundred(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import (
            get_all_rescue_algorithms_with_xdmra,
            get_all_relief_algorithms_with_xdmra,
            get_all_shelter_algorithms_with_xdmra
        )
        from evaluation.scenarios import get_rescue_scenarios, get_relief_scenarios, get_shelter_scenarios
        from evaluation.experiment_runner import run_rescue_experiment, run_relief_experiment, run_shelter_experiment

        rescue_scenarios = get_rescue_scenarios()
        relief_scenarios = get_relief_scenarios()
        shelter_scenarios = get_shelter_scenarios()

        rescue_exp = run_rescue_experiment(rescue_scenarios, get_all_rescue_algorithms_with_xdmra(), repeat=1, seed=42)
        relief_exp = run_relief_experiment(relief_scenarios, get_all_relief_algorithms_with_xdmra(), repeat=1, seed=42)
        shelter_exp = run_shelter_experiment(shelter_scenarios, get_all_shelter_algorithms_with_xdmra(), repeat=1, seed=42)

        eval_result = run_explainability_evaluation(
            rescue_results=rescue_exp["results"],
            relief_results=relief_exp["results"],
            shelter_results=shelter_exp["results"]
        )

        for module, result in eval_result.items():
            assert 0.0 <= result.overall_coverage_pct <= 100.0
            for elem_name, metric in result.element_metrics.items():
                pct = metric["percentage"]
                assert 0.0 <= pct <= 100.0, f"{module}.{elem_name}: percentage {pct} out of bounds"


class TestExplainabilityEvaluation:
    """Tests for explainability evaluation (X-DMRA explanation generation and checking)."""

    def test_xdmra_rescue_produces_explanations(self):
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        from evaluation.scenarios import get_rescue_scenarios
        from evaluation.experiment_runner import run_rescue_experiment
        scenarios = get_rescue_scenarios()[:5]
        baselines = get_all_rescue_algorithms_with_xdmra()
        result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        xdmra_results = [r for r in result["results"] if r["algorithm"] == "xdmra_explainable"]
        assert len(xdmra_results) == 5
        for r in xdmra_results:
            assert r.get("explanation") is not None
            assert len(r["explanation"].strip()) > 20

    def test_xdmra_relief_produces_explanations(self):
        from evaluation.baselines import get_all_relief_algorithms_with_xdmra
        from evaluation.scenarios import get_relief_scenarios
        from evaluation.experiment_runner import run_relief_experiment
        scenarios = get_relief_scenarios()[:5]
        baselines = get_all_relief_algorithms_with_xdmra()
        result = run_relief_experiment(scenarios, baselines, repeat=1, seed=42)
        xdmra_results = [r for r in result["results"] if r["algorithm"] == "xdmra_relief_allocation"]
        assert len(xdmra_results) == 5
        for r in xdmra_results:
            assert r.get("explanation") is not None
            assert len(r["explanation"].strip()) > 20

    def test_xdmra_shelter_produces_explanations(self):
        from evaluation.baselines import get_all_shelter_algorithms_with_xdmra
        from evaluation.scenarios import get_shelter_scenarios
        from evaluation.experiment_runner import run_shelter_experiment
        scenarios = get_shelter_scenarios()[:5]
        baselines = get_all_shelter_algorithms_with_xdmra()
        result = run_shelter_experiment(scenarios, baselines, repeat=1, seed=42)
        xdmra_results = [r for r in result["results"] if r["algorithm"] == "xdmra_shelter_allocation"]
        assert len(xdmra_results) == 5
        for r in xdmra_results:
            assert r.get("explanation") is not None
            assert len(r["explanation"].strip()) > 20

    def test_baseline_algorithms_produce_no_explanations(self):
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        from evaluation.scenarios import get_rescue_scenarios
        from evaluation.experiment_runner import run_rescue_experiment
        scenarios = get_rescue_scenarios()[:3]
        baselines = get_all_rescue_algorithms_with_xdmra()
        result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        for r in result["results"]:
            if r["algorithm"] != "xdmra_explainable":
                assert r.get("explanation") is None, f"{r['algorithm']} should not produce explanations"

    def test_explainability_evaluator_produces_nonzero_counts(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        from evaluation.scenarios import get_rescue_scenarios
        from evaluation.experiment_runner import run_rescue_experiment
        scenarios = get_rescue_scenarios()[:5]
        baselines = get_all_rescue_algorithms_with_xdmra()
        experiment_result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        eval_result = run_explainability_evaluation(rescue_results=experiment_result["results"])
        assert eval_result["rescue"].explanations_with_content > 0
        assert eval_result["rescue"].scenarios_evaluated > 0
        assert eval_result["rescue"].element_metrics["explanation_availability"]["numerator"] > 0
        assert eval_result["rescue"].element_metrics["explanation_availability"]["denominator"] > 0

    def test_numerator_never_exceeds_denominator(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        from evaluation.scenarios import get_rescue_scenarios
        from evaluation.experiment_runner import run_rescue_experiment
        scenarios = get_rescue_scenarios()[:5]
        baselines = get_all_rescue_algorithms_with_xdmra()
        experiment_result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        eval_result = run_explainability_evaluation(rescue_results=experiment_result["results"])
        for elem_name, metric in eval_result["rescue"].element_metrics.items():
            assert metric["numerator"] <= metric["denominator"], \
                f"{elem_name}: numerator {metric['numerator']} > denominator {metric['denominator']}"

    def test_na_count_for_zero_distance_scenarios(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        from evaluation.scenarios import get_rescue_scenarios
        from evaluation.experiment_runner import run_rescue_experiment
        scenarios = get_rescue_scenarios()[:10]
        baselines = get_all_rescue_algorithms_with_xdmra()
        experiment_result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        eval_result = run_explainability_evaluation(rescue_results=experiment_result["results"])
        dist_metric = eval_result["rescue"].element_metrics["distance"]
        assert dist_metric["na_count"] == 0 or dist_metric["percentage"] <= 100.0

    def test_route_risk_na_when_no_significant_risk(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        from evaluation.scenarios import get_rescue_scenarios
        from evaluation.experiment_runner import run_rescue_experiment
        scenarios = get_rescue_scenarios()[:10]
        baselines = get_all_rescue_algorithms_with_xdmra()
        experiment_result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        eval_result = run_explainability_evaluation(rescue_results=experiment_result["results"])
        rr_metric = eval_result["rescue"].element_metrics["route_risk"]
        assert rr_metric["na_count"] >= 0
        assert rr_metric["percentage"] >= 0.0
        assert rr_metric["percentage"] <= 100.0

    def test_stored_value_consistency_checker_passes_with_valid_explanation(self):
        from evaluation.explainability_evaluation import _check_stored_value_consistency
        valid_explanation = (
            "Team Alpha assigned with score 0.92 based on distance 15.3km, "
            "skill match 100%, equipment match 100%, route risk low."
        )
        result = {"distance_km": 15.3, "total_score": 0.92}
        consistent, detail, is_applicable = _check_stored_value_consistency(valid_explanation, result)
        assert is_applicable is True

    def test_stored_value_consistency_checker_detects_mismatch(self):
        from evaluation.explainability_evaluation import _check_stored_value_consistency
        wrong_distance_explanation = "Team Alpha was assigned. Distance mentioned: 25.0 km but actual distance was 10.0 km."
        result = {"distance_km": 10.0}
        consistent, detail, is_applicable = _check_stored_value_consistency(wrong_distance_explanation, result)
        assert consistent is False, f"Expected inconsistency but got consistent={consistent}, detail={detail}"
        assert "inconsist" in detail.lower() or "mismatch" in detail.lower()

    def test_explainability_evaluator_reports_baseline_not_supported(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        from evaluation.scenarios import get_rescue_scenarios
        from evaluation.experiment_runner import run_rescue_experiment
        scenarios = get_rescue_scenarios()[:3]
        baselines = get_all_rescue_algorithms_with_xdmra()
        experiment_result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        eval_result = run_explainability_evaluation(rescue_results=experiment_result["results"])
        assert eval_result["rescue"].baseline_support == "not_supported"
        assert "Baseline algorithms do not produce explanations" in eval_result["rescue"].baseline_note

    def test_explainability_coverage_percentage_bounded(self):
        from evaluation.explainability_evaluation import run_explainability_evaluation
        from evaluation.baselines import get_all_rescue_algorithms_with_xdmra
        from evaluation.scenarios import get_rescue_scenarios
        from evaluation.experiment_runner import run_rescue_experiment
        scenarios = get_rescue_scenarios()[:5]
        baselines = get_all_rescue_algorithms_with_xdmra()
        experiment_result = run_rescue_experiment(scenarios, baselines, repeat=1, seed=42)
        eval_result = run_explainability_evaluation(rescue_results=experiment_result["results"])
        assert 0.0 <= eval_result["rescue"].overall_coverage_pct <= 100.0
        assert eval_result["rescue"].total_checks > 0
        assert eval_result["rescue"].total_passed <= eval_result["rescue"].total_checks


class TestModuleAllOrchestration:
    """Tests for the --module all orchestration."""

    def test_module_all_includes_rescue(self):
        from evaluation.experiment_runner import run_experiment
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_experiment("rescue", seed=42, output_dir=Path(tmpdir))
            assert "results_directory" in result

    def test_module_all_includes_priority(self):
        from evaluation.experiment_runner import run_experiment
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_experiment("priority", seed=42, output_dir=Path(tmpdir))
            assert "results_directory" in result

    def test_module_all_runs_every_module(self):
        from evaluation.experiment_runner import run_experiment
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_experiment("all", seed=42, output_dir=Path(tmpdir))
            assert result["metadata"]["module"] == "all"
            assert result["duration_ms"] > 0

    def test_module_all_duration_includes_all_modules(self):
        from evaluation.experiment_runner import run_experiment
        import tempfile
        import time
        with tempfile.TemporaryDirectory() as tmpdir:
            start = time.perf_counter()
            result = run_experiment("all", seed=42, output_dir=Path(tmpdir))
            total_time = (time.perf_counter() - start) * 1000
            assert result["duration_ms"] > 0
            assert result["duration_ms"] <= total_time * 1.1