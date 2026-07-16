"""
Evaluation Experiment Runner.

Orchestrates evaluation experiments across rescue, relief, shelter,
priority, explainability, performance, and all modules.

Usage:
    python -m evaluation.experiment_runner --module rescue
    python -m evaluation.experiment_runner --module relief
    python -m evaluation.experiment_runner --module shelter
    python -m evaluation.experiment_runner --module priority
    python -m evaluation.experiment_runner --module explainability
    python -m evaluation.experiment_runner --module performance
    python -m evaluation.experiment_runner --module all
"""

import argparse
import json
import os
import random
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.scenarios import get_rescue_scenarios, get_relief_scenarios, get_shelter_scenarios
from evaluation.baselines import (
    get_all_rescue_algorithms_with_xdmra,
    get_all_relief_algorithms_with_xdmra,
    get_all_shelter_algorithms_with_xdmra,
)
from evaluation.metrics import (
    calculate_rescue_metrics, calculate_relief_metrics, calculate_shelter_metrics
)
from evaluation.statistics import descriptive_statistics, DirectionMapping, compare_algorithms
from evaluation.paper_tables import (
    export_rescue_table, export_relief_table, export_shelter_table, export_priority_table
)
from evaluation.exporters import export_json, export_csv


def utcnow():
    return datetime.now(timezone.utc)


def setup_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def load_rescue_scenarios(limit: Optional[int] = None) -> List[Any]:
    scenarios = get_rescue_scenarios()
    if limit:
        scenarios = scenarios[:limit]
    return scenarios


def load_relief_scenarios(limit: Optional[int] = None) -> List[Any]:
    scenarios = get_relief_scenarios()
    if limit:
        scenarios = scenarios[:limit]
    return scenarios


def load_shelter_scenarios(limit: Optional[int] = None) -> List[Any]:
    scenarios = get_shelter_scenarios()
    if limit:
        scenarios = scenarios[:limit]
    return scenarios


def run_rescue_experiment(
    scenarios: List[Any],
    baselines: Dict[str, Any],
    algorithms: Optional[List[str]] = None,
    repeat: int = 1,
    seed: int = 42,
) -> Dict[str, Any]:
    if algorithms is None:
        algorithms = list(baselines.keys())

    all_results = []
    all_metrics = {}

    for algo_name in algorithms:
        if algo_name not in baselines:
            continue
        baseline = baselines[algo_name]
        rng = random.Random(seed)

        algo_results = []
        for iteration in range(repeat):
            scenario_results = []
            for scenario in scenarios:
                result = baseline.select(scenario)
                scenario_results.append({
                    "algorithm": result.algorithm,
                    "scenario_id": result.scenario_id,
                    "success": result.success,
                    "selected_team_id": result.selected_team_id,
                    "selected_team_name": result.selected_team_name,
                    "distance_km": result.distance_km,
                    "skill_match_pct": result.skill_match_pct,
                    "equipment_match_pct": result.equipment_match_pct,
                    "route_blocked": result.route_blocked,
                    "score": result.score,
                    "computation_time_ms": result.computation_time_ms,
                    "failure_reason": result.failure_reason,
                    "priority_level": getattr(scenario, "priority_level", "unknown"),
                    "iteration": iteration,
                })
            algo_results.extend(scenario_results)

        algo_metrics = calculate_rescue_metrics(algo_results)
        all_metrics[algo_name] = algo_metrics
        all_results.extend(algo_results)

    return {
        "results": all_results,
        "metrics": all_metrics,
        "scenario_count": len(scenarios),
        "algorithms": algorithms,
    }


def run_relief_experiment(
    scenarios: List[Any],
    baselines: Dict[str, Any],
    algorithms: Optional[List[str]] = None,
    repeat: int = 1,
    seed: int = 42,
) -> Dict[str, Any]:
    if algorithms is None:
        algorithms = list(baselines.keys())

    all_results = []
    all_metrics = {}

    for algo_name in algorithms:
        if algo_name not in baselines:
            continue
        baseline = baselines[algo_name]

        algo_results = []
        for iteration in range(repeat):
            scenario_results = []
            for scenario in scenarios:
                result = baseline.select(scenario)
                scenario_results.append({
                    "algorithm": result.algorithm,
                    "scenario_id": result.scenario_id,
                    "success": result.success,
                    "warehouses_used": result.warehouses_used,
                    "fulfilment_pct": result.fulfilment_pct,
                    "shortage": result.shortage,
                    "distance_km": result.distance_km,
                    "stock_violations": result.stock_violations,
                    "split_allocation": result.split_allocation,
                    "computation_time_ms": result.computation_time_ms,
                    "failure_reason": result.failure_reason,
                    "iteration": iteration,
                })
            algo_results.extend(scenario_results)

        algo_metrics = calculate_relief_metrics(algo_results)
        all_metrics[algo_name] = algo_metrics
        all_results.extend(algo_results)

    return {
        "results": all_results,
        "metrics": all_metrics,
        "scenario_count": len(scenarios),
        "algorithms": algorithms,
    }


def run_shelter_experiment(
    scenarios: List[Any],
    baselines: Dict[str, Any],
    algorithms: Optional[List[str]] = None,
    repeat: int = 1,
    seed: int = 42,
) -> Dict[str, Any]:
    if algorithms is None:
        algorithms = list(baselines.keys())

    all_results = []
    all_metrics = {}

    for algo_name in algorithms:
        if algo_name not in baselines:
            continue
        baseline = baselines[algo_name]

        algo_results = []
        for iteration in range(repeat):
            scenario_results = []
            for scenario in scenarios:
                result = baseline.select(scenario)
                scenario_results.append({
                    "algorithm": result.algorithm,
                    "scenario_id": result.scenario_id,
                    "success": result.success,
                    "shelters_used": result.shelters_used,
                    "population_coverage_pct": result.population_coverage_pct,
                    "uncovered_people": result.uncovered_people,
                    "overcrowding_violations": result.overcrowding_violations,
                    "requirement_match_pct": result.requirement_match_pct,
                    "distance_km": result.distance_km,
                    "computation_time_ms": result.computation_time_ms,
                    "failure_reason": result.failure_reason,
                    "iteration": iteration,
                })
            algo_results.extend(scenario_results)

        algo_metrics = calculate_shelter_metrics(algo_results)
        all_metrics[algo_name] = algo_metrics
        all_results.extend(algo_results)

    return {
        "results": all_results,
        "metrics": all_metrics,
        "scenario_count": len(scenarios),
        "algorithms": algorithms,
    }


def run_experiment(
    module: str,
    seed: int = 42,
    scenario_limit: Optional[int] = None,
    output_dir: Optional[Path] = None,
    repeat_count: int = 1,
    algorithms: Optional[List[str]] = None,
    export_format: str = "json"
) -> Dict[str, Any]:
    setup_seed(seed)
    results_dir = output_dir or Path("evaluation_results")
    results_dir.mkdir(exist_ok=True, parents=True)

    start_time = time.perf_counter()

    metadata = {
        "module": module,
        "seed": seed,
        "scenario_limit": scenario_limit,
        "repeat_count": repeat_count,
        "algorithms": algorithms,
        "timestamp": utcnow().isoformat(),
        "git_commit": _get_git_commit(),
    }

    print(f"\n{'='*60}")
    print(f"Running {module.upper()} evaluation (seed={seed})")
    print(f"{'='*60}")

    if module in ("rescue", "all"):
        print("\n--- Rescue Evaluation ---")
        scenarios = load_rescue_scenarios(scenario_limit)
        baselines = get_all_rescue_algorithms_with_xdmra()
        exp_results = run_rescue_experiment(scenarios, baselines, None, repeat_count, seed)

        export_json({"metadata": metadata, **exp_results}, results_dir / "rescue_comparison.json")
        export_csv(exp_results["results"], results_dir / "rescue_comparison.csv")

        export_rescue_table(exp_results["metrics"], exp_results["algorithms"], results_dir)
        print(f"  Scenarios: {exp_results['scenario_count']}, Algorithms: {len(exp_results['algorithms'])}, Results: {len(exp_results['results'])}")

    if module in ("relief", "all"):
        print("\n--- Relief Evaluation ---")
        scenarios = load_relief_scenarios(scenario_limit)
        baselines = get_all_relief_algorithms_with_xdmra()
        exp_results = run_relief_experiment(scenarios, baselines, None, repeat_count, seed)

        export_json({"metadata": metadata, **exp_results}, results_dir / "relief_comparison.json")
        export_csv(exp_results["results"], results_dir / "relief_comparison.csv")

        export_relief_table(exp_results["metrics"], exp_results["algorithms"], results_dir)
        print(f"  Scenarios: {exp_results['scenario_count']}, Algorithms: {len(exp_results['algorithms'])}, Results: {len(exp_results['results'])}")

    if module in ("shelter", "all"):
        print("\n--- Shelter Evaluation ---")
        scenarios = load_shelter_scenarios(scenario_limit)
        baselines = get_all_shelter_algorithms_with_xdmra()
        exp_results = run_shelter_experiment(scenarios, baselines, None, repeat_count, seed)

        export_json({"metadata": metadata, **exp_results}, results_dir / "shelter_comparison.json")
        export_csv(exp_results["results"], results_dir / "shelter_comparison.csv")

        export_shelter_table(exp_results["metrics"], exp_results["algorithms"], results_dir)
        print(f"  Scenarios: {exp_results['scenario_count']}, Algorithms: {len(exp_results['algorithms'])}, Results: {len(exp_results['results'])}")

    if module in ("priority", "all"):
        print("\n--- Priority Model Evaluation ---")
        try:
            from evaluation.priority_evaluation import run_priority_evaluation
            result = run_priority_evaluation(output_dir=results_dir)
            priority_dict = asdict(result) if hasattr(result, "__dataclass_fields__") else result
            export_json(priority_dict, results_dir / "priority_model_evaluation.json")
            export_priority_table(priority_dict, results_dir)
            print(f"  Priority model evaluated successfully")
        except Exception as e:
            print(f"  Priority evaluation failed: {e}")

    if module in ("explainability", "all"):
        print("\n--- Explainability Evaluation ---")
        try:
            from evaluation.explainability_evaluation import run_explainability_evaluation

            rescue_scenarios = load_rescue_scenarios(scenario_limit)
            baselines = get_all_rescue_algorithms_with_xdmra()
            rescue_data = run_rescue_experiment(rescue_scenarios, baselines, None, repeat_count, seed)
            relief_scenarios = load_relief_scenarios(scenario_limit)
            baselines_relief = get_all_relief_algorithms_with_xdmra()
            relief_data = run_relief_experiment(relief_scenarios, baselines_relief, None, repeat_count, seed)
            shelter_scenarios = load_shelter_scenarios(scenario_limit)
            baselines_shelter = get_all_shelter_algorithms_with_xdmra()
            shelter_data = run_shelter_experiment(shelter_scenarios, baselines_shelter, None, repeat_count, seed)

            explain_results = run_explainability_evaluation(
                rescue_results=rescue_data["results"],
                relief_results=relief_data["results"],
                shelter_results=shelter_data["results"],
            )
            for mod_name, exp_result in explain_results.items():
                exp_dict = asdict(exp_result) if hasattr(exp_result, "__dataclass_fields__") else exp_result
                export_json(exp_dict, results_dir / f"explainability_{mod_name}.json")
            print(f"  Explainability coverage evaluated")
        except Exception as e:
            print(f"  Explainability evaluation failed: {e}")

    if module in ("performance", "all"):
        print("\n--- Performance Benchmark ---")
        try:
            from evaluation.performance_benchmark import run_performance_benchmark
            relief_scenarios = load_relief_scenarios(scenario_limit)
            shelter_scenarios = load_shelter_scenarios(scenario_limit)
            perf_result = run_performance_benchmark(
                relief_scenarios=relief_scenarios,
                shelter_scenarios=shelter_scenarios,
                iterations=100,
            )
            export_json(perf_result, results_dir / "performance_benchmark.json")
            print(f"  Performance benchmarks completed")
        except Exception as e:
            print(f"  Performance benchmark failed: {e}")

    duration_ms = (time.perf_counter() - start_time) * 1000

    export_json(metadata, results_dir / "experiment_metadata.json")

    print(f"\n{'='*60}")
    print(f"Completed in {duration_ms:.2f}ms")
    print(f"Results saved to: {results_dir.absolute()}")
    print(f"{'='*60}\n")

    return {
        "metadata": metadata,
        "duration_ms": duration_ms,
        "results_directory": str(results_dir.absolute()),
    }


def _get_git_commit() -> str:
    try:
        import subprocess
        result = subprocess.run(
            ["git", "-C", str(Path(__file__).parent.parent.parent), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def main():
    parser = argparse.ArgumentParser(description="X-DMRA Research Evaluation Experiment Runner")
    parser.add_argument("--module", required=True,
                        choices=["rescue", "relief", "shelter", "priority", "explainability", "performance", "all"],
                        help="Evaluation module to run")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    parser.add_argument("--scenario-limit", type=int, default=None,
                        help="Limit number of scenarios")
    parser.add_argument("--output-directory", type=str, default="evaluation_results",
                        help="Output directory for results")
    parser.add_argument("--repeat-count", type=int, default=1,
                        help="Number of times to repeat each experiment")
    parser.add_argument("--algorithm", action="append", dest="algorithms",
                        help="Specific algorithm(s) to evaluate")
    parser.add_argument("--export-format", default="all",
                        choices=["json", "csv", "markdown", "all"],
                        help="Export format")

    args = parser.parse_args()

    try:
        output_dir = Path(args.output_directory) if args.output_directory else None
        result = run_experiment(
            module=args.module,
            seed=args.seed,
            scenario_limit=args.scenario_limit,
            output_dir=output_dir,
            repeat_count=args.repeat_count,
            algorithms=args.algorithms,
            export_format=args.export_format,
        )
        print(json.dumps(result, indent=2, default=str))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())