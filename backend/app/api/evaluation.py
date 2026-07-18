"""
Evaluation API Routes.

Provides endpoints for running experiments, retrieving results,
and exporting evaluation data.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import uuid
import time

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.security import get_current_active_user, require_role, UserRole, User

from evaluation.experiment_runner import run_experiment
from evaluation.priority_evaluation import run_priority_evaluation
from evaluation.explainability_evaluation import run_explainability_evaluation
from evaluation.performance_benchmark import run_performance_benchmark
from evaluation.scenarios import get_rescue_scenarios, get_relief_scenarios, get_shelter_scenarios
from evaluation.baselines.rescue_baselines import get_all_rescue_baselines
from evaluation.baselines.relief_baselines import get_all_relief_baselines
from evaluation.baselines.shelter_baselines import get_all_shelter_baselines
from evaluation.paper_tables import (
    export_rescue_table, export_relief_table, export_shelter_table, export_priority_table
)

router = APIRouter(prefix="/evaluation", tags=["Research Evaluation"])

EXPERIMENTS_DIR = Path(__file__).parent.parent.parent / "evaluation_results"
EXPERIMENTS_DIR.mkdir(exist_ok=True, parents=True)

EVALUATION_OUTPUT_DIR = Path(__file__).parent.parent.parent / "ml" / "evaluation_output"
EVALUATION_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

_running_experiments: set = set()


class ExperimentCreateRequest(BaseModel):
    module: str = Field(..., description="rescue, relief, shelter, priority, explainability, performance, all")
    seed: Optional[int] = Field(42, description="Random seed for reproducibility")
    scenario_limit: Optional[int] = Field(None, description="Limit number of scenarios")
    repeat_count: int = Field(1, ge=1, le=10)
    algorithms: Optional[List[str]] = Field(None, description="Specific algorithms to evaluate")
    output_subdir: Optional[str] = Field(None, description="Subdirectory name for results")


class ExperimentRunResponse(BaseModel):
    experiment_id: str
    status: str
    results_directory: str
    duration_ms: float


class AlgorithmInfo(BaseModel):
    name: str
    module: str
    description: str


class ScenarioInfo(BaseModel):
    scenario_id: str
    module: str
    description: str
    seed: int


def _validate_path_traversal(path: str) -> bool:
    dangerous = ["..", "~", ":", "\\", "//", "\\\\", "/"]
    return not any(d in path for d in dangerous)


def _get_experiment_path(experiment_id: str) -> Optional[Path]:
    if not _validate_path_traversal(experiment_id):
        return None
    exp_dir = EXPERIMENTS_DIR / experiment_id
    if exp_dir.exists() and exp_dir.is_dir():
        return exp_dir
    return None


@router.get("/algorithms", response_model=List[AlgorithmInfo])
def list_algorithms(current_user: User = Depends(get_current_active_user)):
    """List all available evaluation algorithms by module."""
    rescue_algos = list(get_all_rescue_baselines().keys())
    relief_algos = list(get_all_relief_baselines().keys())
    shelter_algos = list(get_all_shelter_baselines().keys())

    descriptions = {
        "random_available": "Randomly selects from eligible available teams",
        "first_available": "Selects the first available team by ID order",
        "nearest_available": "Selects the closest available team by Haversine distance",
        "skill_match_only": "Ranks teams by skill and equipment match only",
        "priority_distance_only": "Ranks by incident priority and distance",
        "first_stocked_warehouse": "Selects first warehouse with complete stock",
        "nearest_stocked_warehouse": "Selects nearest warehouse with stock",
        "highest_stock_coverage": "Selects warehouse with best coverage",
        "single_warehouse_only": "Always uses single warehouse",
        "nearest_available_shelter": "Selects closest shelter with capacity",
        "largest_capacity_shelter": "Selects shelter with most available capacity",
        "first_available_shelter": "Selects first open shelter",
        "capacity_only": "Selects shelter by capacity regardless of distance",
    }

    algorithms = []
    for name in rescue_algos:
        algorithms.append(AlgorithmInfo(
            name=name, module="rescue",
            description=descriptions.get(name, "Rescue baseline algorithm")
        ))
    for name in relief_algos:
        algorithms.append(AlgorithmInfo(
            name=name, module="relief",
            description=descriptions.get(name, "Relief baseline algorithm")
        ))
    for name in shelter_algos:
        algorithms.append(AlgorithmInfo(
            name=name, module="shelter",
            description=descriptions.get(name, "Shelter baseline algorithm")
        ))

    return algorithms


@router.get("/scenarios", response_model=List[ScenarioInfo])
def list_scenarios(module: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    """List all deterministic evaluation scenarios."""
    scenarios = []

    if module in (None, "rescue"):
        for sc in get_rescue_scenarios():
            scenarios.append(ScenarioInfo(
                scenario_id=sc.scenario_id,
                module="rescue",
                description=sc.incident_title or sc.scenario_id,
                seed=42
            ))

    if module in (None, "relief"):
        for sc in get_relief_scenarios():
            scenarios.append(ScenarioInfo(
                scenario_id=sc.scenario_id,
                module="relief",
                description=f"Relief scenario {sc.scenario_id}",
                seed=42
            ))

    if module in (None, "shelter"):
        for sc in get_shelter_scenarios():
            scenarios.append(ScenarioInfo(
                scenario_id=sc.scenario_id,
                module="shelter",
                description=f"Shelter scenario {sc.scenario_id}",
                seed=42
            ))

    return scenarios


@router.post("/experiments", response_model=ExperimentRunResponse)
def create_experiment(req: ExperimentCreateRequest, current_user: User = Depends(require_role(UserRole.admin, UserRole.command_officer))):
    """Create and run a new evaluation experiment."""
    if req.module not in ("rescue", "relief", "shelter", "priority", "explainability", "performance", "all"):
        raise HTTPException(status_code=400, detail=f"Invalid module: {req.module}")

    if req.output_subdir:
        if not _validate_path_traversal(req.output_subdir):
            raise HTTPException(status_code=400, detail="Invalid output_subdir: path traversal detected")
        subdir_key = req.output_subdir
    else:
        subdir_key = None

    if subdir_key and subdir_key in _running_experiments:
        raise HTTPException(status_code=409, detail="Experiment with this output_subdir is already running")

    experiment_id = str(uuid.uuid4())[:8]

    if req.output_subdir:
        output_dir = EXPERIMENTS_DIR / req.output_subdir
    else:
        output_dir = EXPERIMENTS_DIR / experiment_id

    output_dir.mkdir(parents=True, exist_ok=True)

    if subdir_key:
        _running_experiments.add(subdir_key)

    start = time.perf_counter()
    try:
        result = run_experiment(
            module=req.module,
            seed=req.seed,
            scenario_limit=req.scenario_limit,
            output_dir=output_dir,
            repeat_count=req.repeat_count,
            algorithms=req.algorithms,
        )
    except Exception as e:
        if subdir_key:
            _running_experiments.discard(subdir_key)
        raise HTTPException(status_code=500, detail=f"Experiment failed: {str(e)}")

    if subdir_key:
        _running_experiments.discard(subdir_key)

    duration_ms = (time.perf_counter() - start) * 1000

    meta = {
        "experiment_id": experiment_id,
        "module": req.module,
        "seed": req.seed,
        "scenario_limit": req.scenario_limit,
        "repeat_count": req.repeat_count,
        "algorithms": req.algorithms,
        "output_dir": str(output_dir),
        "duration_ms": duration_ms,
    }

    with open(output_dir / "experiment_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    return ExperimentRunResponse(
        experiment_id=experiment_id,
        status="completed",
        results_directory=str(output_dir),
        duration_ms=duration_ms,
    )


@router.get("/experiments")
def list_experiments(current_user: User = Depends(get_current_active_user)):
    """List all evaluation experiments."""
    experiments = []
    if not EXPERIMENTS_DIR.exists():
        return experiments

    for exp_dir in EXPERIMENTS_DIR.iterdir():
        if exp_dir.is_dir():
            meta_file = exp_dir / "experiment_meta.json"
            if meta_file.exists():
                with open(meta_file) as f:
                    meta = json.load(f)
                experiments.append({
                    "experiment_id": meta.get("experiment_id", exp_dir.name),
                    "module": meta.get("module", "unknown"),
                    "seed": meta.get("seed", 0),
                    "status": "completed",
                    "duration_ms": meta.get("duration_ms", 0),
                    "results_directory": str(exp_dir),
                })
            else:
                experiments.append({
                    "experiment_id": exp_dir.name,
                    "module": "unknown",
                    "seed": 0,
                    "status": "unknown",
                    "duration_ms": 0,
                    "results_directory": str(exp_dir),
                })
    return experiments


@router.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str, current_user: User = Depends(get_current_active_user)):
    """Get experiment metadata."""
    path = _get_experiment_path(experiment_id)
    if not path:
        raise HTTPException(status_code=404, detail="Experiment not found")

    meta_file = path / "experiment_meta.json"
    if meta_file.exists():
        with open(meta_file) as f:
            return json.load(f)

    return {"experiment_id": experiment_id, "status": "unknown"}


@router.get("/experiments/{experiment_id}/results")
def get_experiment_results(experiment_id: str, current_user: User = Depends(get_current_active_user)):
    """Get experiment results."""
    path = _get_experiment_path(experiment_id)
    if not path:
        raise HTTPException(status_code=404, detail="Experiment not found")

    result_files = ["rescue_comparison.json", "relief_comparison.json", "shelter_comparison.json"]
    results = {}
    for fname in result_files:
        fpath = path / fname
        if fpath.exists():
            with open(fpath) as f:
                results[fname.replace(".json", "")] = json.load(f)

    priority_file = EVALUATION_OUTPUT_DIR / "priority_model_evaluation.json"
    if priority_file.exists():
        with open(priority_file) as f:
            results["priority_model"] = json.load(f)

    return results if results else {"status": "no_results"}


@router.get("/experiments/{experiment_id}/metrics")
def get_experiment_metrics(experiment_id: str, current_user: User = Depends(get_current_active_user)):
    """Get aggregated metrics from experiment results."""
    path = _get_experiment_path(experiment_id)
    if not path:
        raise HTTPException(status_code=404, detail="Experiment not found")

    metrics = {}
    for module in ["rescue", "relief", "shelter"]:
        json_file = path / f"{module}_comparison.json"
        if json_file.exists():
            with open(json_file) as f:
                data = json.load(f)
                metrics[module] = data.get("metrics", {})

    return metrics


@router.get("/comparisons")
def get_comparisons(
    module: str = Query(..., description="rescue, relief, or shelter"),
    seed: int = Query(42),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.command_officer)),
):
    """Get baseline comparison results for a module."""
    if module not in ("rescue", "relief", "shelter"):
        raise HTTPException(status_code=400, detail="Invalid module")

    output_dir = EXPERIMENTS_DIR / f"comparison_{module}_{seed}"
    output_dir.mkdir(exist_ok=True, parents=True)

    run_experiment(module=module, seed=seed, output_dir=output_dir)

    json_file = output_dir / f"{module}_comparison.json"
    if json_file.exists():
        with open(json_file) as f:
            return json.load(f)
    return {"status": "error", "message": "Failed to generate comparison"}


@router.get("/priority-model")
def get_priority_model_evaluation(current_user: User = Depends(get_current_active_user)):
    """Get priority model evaluation results."""
    priority_file = EVALUATION_OUTPUT_DIR / "priority_model_evaluation.json"
    if not priority_file.exists():
        result = run_priority_evaluation(output_dir=EVALUATION_OUTPUT_DIR)
        if result.total_samples == 0:
            return JSONResponse(content={"error": "Priority evaluation not available"}, status_code=503)

    with open(priority_file) as f:
        return json.load(f)


@router.get("/performance")
def get_performance_benchmark(current_user: User = Depends(get_current_active_user)):
    """Get performance benchmark results."""
    perf_file = EXPERIMENTS_DIR / "performance_benchmark.json"
    if not perf_file.exists():
        relief = get_relief_scenarios()
        shelter = get_shelter_scenarios()
        result = run_performance_benchmark(relief_scenarios=relief, shelter_scenarios=shelter, iterations=50)
        with open(perf_file, "w") as f:
            json.dump(result, f, default=str)

    with open(perf_file) as f:
        return json.load(f)


@router.get("/explainability")
def get_explainability_coverage(current_user: User = Depends(get_current_active_user)):
    """Get explainability coverage results for rescue, relief, and shelter."""
    exp_dir = EXPERIMENTS_DIR / "explainability_latest"
    exp_dir.mkdir(exist_ok=True, parents=True)

    rescue_scenarios = get_rescue_scenarios()
    relief_scenarios = get_relief_scenarios()
    shelter_scenarios = get_shelter_scenarios()

    from evaluation.baselines import (
        get_all_rescue_algorithms_with_xdmra,
        get_all_relief_algorithms_with_xdmra,
        get_all_shelter_algorithms_with_xdmra,
    )
    from evaluation.experiment_runner import (
        run_rescue_experiment,
        run_relief_experiment,
        run_shelter_experiment,
    )

    rescue_baselines = get_all_rescue_algorithms_with_xdmra()
    relief_baselines = get_all_relief_algorithms_with_xdmra()
    shelter_baselines = get_all_shelter_algorithms_with_xdmra()

    rescue_exp = run_rescue_experiment(rescue_scenarios, rescue_baselines, repeat=1, seed=42)
    relief_exp = run_relief_experiment(relief_scenarios, relief_baselines, repeat=1, seed=42)
    shelter_exp = run_shelter_experiment(shelter_scenarios, shelter_baselines, repeat=1, seed=42)

    explain_results = run_explainability_evaluation(
        rescue_results=rescue_exp["results"],
        relief_results=relief_exp["results"],
        shelter_results=shelter_exp["results"],
    )

    result = {}
    for mod_name, exp_result in explain_results.items():
        result[mod_name] = {
            "scenarios_evaluated": exp_result.scenarios_evaluated,
            "explanations_with_content": exp_result.explanations_with_content,
            "total_checks": exp_result.total_checks,
            "total_passed": exp_result.total_passed,
            "overall_coverage_pct": exp_result.overall_coverage_pct,
            "element_metrics": exp_result.element_metrics,
            "baseline_support": exp_result.baseline_support,
            "baseline_note": exp_result.baseline_note,
        }

    return result


@router.get("/export/{experiment_id}")
def export_experiment(
    experiment_id: str,
    format: str = Query("json", description="json, csv, markdown, or latex"),
    current_user: User = Depends(get_current_active_user),
):
    """Export experiment results in the specified format."""
    path = _get_experiment_path(experiment_id)
    if not path:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if format == "json":
        json_files = list(path.glob("*.json"))
        if not json_files:
            raise HTTPException(status_code=404, detail="No JSON results found")
        if len(json_files) == 1:
            return FileResponse(json_files[0], media_type="application/json")
        return JSONResponse(content={"files": [f.name for f in json_files]})

    elif format == "csv":
        csv_files = list(path.glob("*.csv"))
        if not csv_files:
            raise HTTPException(status_code=404, detail="No CSV results found")
        return JSONResponse(content={"files": [f.name for f in csv_files]})

    elif format == "markdown":
        md_files = list(path.glob("*.md"))
        if not md_files:
            raise HTTPException(status_code=404, detail="No Markdown results found")
        return JSONResponse(content={"files": [f.name for f in md_files]})

    elif format == "latex":
        tex_files = list(path.glob("*.tex"))
        if not tex_files:
            raise HTTPException(status_code=404, detail="No LaTeX results found")
        return JSONResponse(content={"files": [f.name for f in tex_files]})

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")