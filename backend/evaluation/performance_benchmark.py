"""
Performance Benchmarking for X-DMRA Operations.

Measures latency (mean, median, min, max, std, P95) for key operations.
Uses time.perf_counter() for high-resolution timing.

Application startup and migration time are excluded unless separately labelled.
All benchmarks use isolated test data or in-memory operations.

WARNING: Uses test database for benchmarks. Do not run against production database.
"""

import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class LatencyResult:
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    std_ms: float
    p95_ms: float
    sample_count: int


def _compute_latency_stats(latencies_ms: List[float]) -> LatencyResult:
    if not latencies_ms:
        return LatencyResult(0, 0, 0, 0, 0, 0, 0)
    return LatencyResult(
        mean_ms=float(np.mean(latencies_ms)),
        median_ms=float(np.median(latencies_ms)),
        min_ms=float(np.min(latencies_ms)),
        max_ms=float(np.max(latencies_ms)),
        std_ms=float(np.std(latencies_ms) if len(latencies_ms) > 1 else 0),
        p95_ms=float(np.percentile(latencies_ms, 95)),
        sample_count=len(latencies_ms),
    )


@dataclass
class BenchmarkReport:
    operation: str
    latencies_ms: LatencyResult
    metadata: Dict[str, Any]


def benchmark_rule_priority(incident_data: List[Dict[str, Any]], iterations: int = 100) -> LatencyResult:
    """Benchmark rule-based priority calculation latency."""
    from app.services.priority_service import calculate_priority_score

    latencies = []
    for _ in range(iterations):
        for incident in incident_data:
            start = time.perf_counter()
            calculate_priority_score(incident)
            latencies.append((time.perf_counter() - start) * 1000)
    return _compute_latency_stats(latencies)


def benchmark_ml_prediction(incident_data: List[Dict[str, Any]], iterations: int = 100) -> LatencyResult:
    """Benchmark ML model prediction latency."""
    from app.services.priority_predictor import get_prediction

    latencies = []
    for _ in range(iterations):
        for incident in incident_data:
            start = time.perf_counter()
            try:
                get_prediction(incident)
            except Exception:
                pass
            latencies.append((time.perf_counter() - start) * 1000)
    return _compute_latency_stats(latencies)


def benchmark_rescue_recommendation(incidents: List[Dict[str, Any]], teams: List[Dict[str, Any]], iterations: int = 50) -> LatencyResult:
    """Benchmark rescue team recommendation latency."""
    from evaluation.baselines.rescue_baselines import NearestAvailableBaseline, RescueScenario

    baseline = NearestAvailableBaseline()
    latencies = []

    for _ in range(iterations):
        for incident, team_list in zip(incidents, [teams] * len(incidents)):
            scenario = RescueScenario(
                scenario_id=f"bench_{id(incident)}",
                incident_id=incident.get("id", 0),
                incident_title=incident.get("title", ""),
                incident_type=incident.get("incident_type", ""),
                latitude=incident.get("latitude", 11.0),
                longitude=incident.get("longitude", 77.0),
                priority_level=incident.get("priority_level", "medium"),
                required_skills=incident.get("required_skills", []),
                required_equipment=incident.get("required_equipment", []),
                affected_people=incident.get("affected_people", 0),
                trapped_people=incident.get("trapped_people", 0),
                available_teams=team_list,
            )
            start = time.perf_counter()
            baseline.select(scenario)
            latencies.append((time.perf_counter() - start) * 1000)

    return _compute_latency_stats(latencies)


def benchmark_relief_recommendation(scenarios: List[Any], iterations: int = 50) -> LatencyResult:
    """Benchmark relief recommendation latency."""
    from evaluation.baselines.relief_baselines import NearestStockedWarehouseBaseline

    baseline = NearestStockedWarehouseBaseline()
    latencies = []

    for _ in range(iterations):
        for scenario in scenarios:
            start = time.perf_counter()
            baseline.select(scenario)
            latencies.append((time.perf_counter() - start) * 1000)

    return _compute_latency_stats(latencies)


def benchmark_shelter_recommendation(scenarios: List[Any], iterations: int = 50) -> LatencyResult:
    """Benchmark shelter recommendation latency."""
    from evaluation.baselines.shelter_baselines import NearestAvailableShelterBaseline

    baseline = NearestAvailableShelterBaseline()
    latencies = []

    for _ in range(iterations):
        for scenario in scenarios:
            start = time.perf_counter()
            baseline.select(scenario)
            latencies.append((time.perf_counter() - start) * 1000)

    return _compute_latency_stats(latencies)


def run_performance_benchmark(
    rescue_scenarios: Optional[List[Any]] = None,
    relief_scenarios: Optional[List[Any]] = None,
    shelter_scenarios: Optional[List[Any]] = None,
    iterations: int = 100,
) -> Dict[str, Any]:
    """Run all performance benchmarks and return a report."""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "iterations": iterations,
        "benchmarks": {},
    }

    incident_data = [
        {"id": i, "title": f"Incident {i}", "incident_type": "Flood", "latitude": 11.0 + i * 0.01,
         "longitude": 77.0 + i * 0.01, "priority_level": "high",
         "affected_people": 20 * i, "injured_people": i, "trapped_people": i,
         "severity": "high", "required_skills": [], "required_equipment": []}
        for i in range(1, 21)
    ]

    teams_data = [
        {"id": i, "name": f"Team {i}", "latitude": 11.0 + i * 0.005, "longitude": 77.0 + i * 0.005,
         "availability_status": "available", "skills": ["flood_rescue"], "equipment": ["boat"],
         "current_workload": i % 5, "capacity": 10}
        for i in range(1, 11)
    ]

    print("Running performance benchmarks...")

    try:
        rule_lat = benchmark_rule_priority(incident_data, iterations)
        report["benchmarks"]["rule_priority_latency"] = asdict(rule_lat)
        print(f"  Rule priority: mean={rule_lat.mean_ms:.4f}ms")
    except Exception as e:
        report["benchmarks"]["rule_priority_latency"] = {"error": str(e)}

    try:
        ml_lat = benchmark_ml_prediction(incident_data, iterations)
        report["benchmarks"]["ml_prediction_latency"] = asdict(ml_lat)
        print(f"  ML prediction: mean={ml_lat.mean_ms:.4f}ms")
    except Exception as e:
        report["benchmarks"]["ml_prediction_latency"] = {"error": str(e)}

    try:
        rescue_lat = benchmark_rescue_recommendation(incident_data[:10], teams_data, iterations // 2)
        report["benchmarks"]["rescue_recommendation_latency"] = asdict(rescue_lat)
        print(f"  Rescue recommendation: mean={rescue_lat.mean_ms:.4f}ms")
    except Exception as e:
        report["benchmarks"]["rescue_recommendation_latency"] = {"error": str(e)}

    if relief_scenarios:
        try:
            relief_lat = benchmark_relief_recommendation(relief_scenarios[:10], iterations // 2)
            report["benchmarks"]["relief_recommendation_latency"] = asdict(relief_lat)
            print(f"  Relief recommendation: mean={relief_lat.mean_ms:.4f}ms")
        except Exception as e:
            report["benchmarks"]["relief_recommendation_latency"] = {"error": str(e)}

    if shelter_scenarios:
        try:
            shelter_lat = benchmark_shelter_recommendation(shelter_scenarios[:10], iterations // 2)
            report["benchmarks"]["shelter_recommendation_latency"] = asdict(shelter_lat)
            print(f"  Shelter recommendation: mean={shelter_lat.mean_ms:.4f}ms")
        except Exception as e:
            report["benchmarks"]["shelter_recommendation_latency"] = {"error": str(e)}

    return report


if __name__ == "__main__":
    from evaluation.scenarios import get_relief_scenarios, get_shelter_scenarios

    relief = get_relief_scenarios()
    shelter = get_shelter_scenarios()

    result = run_performance_benchmark(
        relief_scenarios=relief,
        shelter_scenarios=shelter,
        iterations=100,
    )

    import json
    print(json.dumps(result, indent=2, default=str))