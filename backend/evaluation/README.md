# Research Evaluation Module

Phase 9 of X-DMRA adds a comprehensive Research Evaluation framework for reproducible baseline comparison and performance analytics.

## Overview

The evaluation module provides:
- **Deterministic scenario generation** with explicit seeds
- **Baseline algorithm implementations** for rescue, relief, and shelter allocation
- **Comprehensive metrics** including rescue, relief, shelter, priority, and explainability coverage
- **Statistical calculations** with explicit metric-direction mapping and percentage-improvement rules
- **Experiment runner** for reproducible evaluation across all modules
- **Paper-ready export** in CSV, JSON, Markdown, and LaTeX formats

## Architecture

```
backend/evaluation/
├── __init__.py              # Package exports
├── statistics.py            # Statistical calculations and comparison
├── metrics.py               # Rescue, relief, shelter metric calculations
├── models.py                # Evaluation database models
├── experiment_runner.py     # Main orchestrator for all evaluation modules
├── priority_evaluation.py    # ML model evaluation (no retraining)
├── explainability_evaluation.py  # Deterministic explanation structure checks
├── performance_benchmark.py # Latency benchmarking
├── exporters.py             # CSV, JSON, Markdown, LaTeX export
├── paper_tables.py           # Formatted comparison tables
├── baselines/
│   ├── rescue_baselines.py  # 5 rescue baseline algorithms + X-DMRA (6 total)
│   ├── relief_baselines.py  # 4 relief baseline algorithms
│   └── shelter_baselines.py # 4 shelter baseline algorithms
├── scenarios/
│   ├── rescue_scenarios.py   # 25 deterministic rescue scenarios
│   ├── relief_scenarios.py  # 20 deterministic relief scenarios
│   └── shelter_scenarios.py # 20 deterministic shelter scenarios
├── README.md                # This file
└── EVALUATION_METHODOLOGY.md # Detailed methodology documentation
```

## Baseline Algorithms

### Rescue Baselines
- `random_available`: Randomly selects from eligible available teams (deterministic with seed)
- `first_available`: Selects the first available team by ID order
- `nearest_available`: Selects the closest available team using Haversine distance
- `skill_match_only`: Ranks teams by skill and equipment compatibility
- `priority_distance_only`: Ranks by incident priority weight and straight-line distance

### Relief Baselines (5 total with X-DMRA)
- `first_stocked_warehouse`: Selects first warehouse with complete item stock (all-or-nothing)
- `nearest_stocked_warehouse`: Selects nearest warehouse with available stock
- `highest_stock_coverage`: Selects warehouse with best per-item coverage percentage
- `single_warehouse_only`: Always uses single warehouse allocation
- `xdmra_relief_allocation`: X-DMRA production scoring with split allocation across multiple warehouses

### Shelter Baselines (5 total with X-DMRA)
- `nearest_available_shelter`: Selects closest shelter with available capacity
- `largest_capacity_shelter`: Selects shelter with most available capacity
- `first_available_shelter`: Selects first open shelter by ID order
- `capacity_only`: Selects shelter by total capacity regardless of distance
- `xdmra_shelter_allocation`: X-DMRA production scoring with split allocation across multiple shelters

## Scenario Counts

| Module | Count | Purpose |
|--------|-------|---------|
| Rescue | 25 | Low, high, critical incidents; skill/equipment mismatch; blocked routes; no eligible team |
| Relief | 20 | Complete/split allocation; low stock; blocked warehouse; shortage |
| Shelter | 20 | Single/split; medical/accessibility; overcrowding; blocked route |

## Metrics

### Rescue Metrics
- allocation_success_rate, mean_distance_km, median_distance_km
- skill_match_percentage, equipment_match_percentage, route_safety_score
- critical_incident_success_rate, reallocation_success_rate
- blocked_route_selections, overloaded_teams_selected
- workload_standard_deviation, Jain fairness index, mean_latency_ms

### Relief Metrics
- `macro_fulfilment_pct`: Mean scenario fulfilment across ALL scenarios (not just successful)
- `weighted_fulfilment_pct`: Total allocated / total requested across ALL scenarios
- `allocation_success_count`: Scenarios with positive allocation produced
- `fully_fulfilled_count`: Scenarios with zero shortage
- `partial_fulfilment_count`: Scenarios with positive allocation and remaining shortage
- `failed_count`: Scenarios with zero allocation
- `mean_shortage`, `total_shortage`: Shortage statistics
- `total_stock_violations`: Always zero (allocations are correctly capped)
- `total_requested`: Sum of all requested items per scenario
- `split_allocation_count`: Scenarios using multiple warehouses (X-DMRA)
- `mean_latency_ms`, route_safety, mean_distance_km

### Shelter Metrics
- `macro_population_coverage_pct`: Mean coverage over ALL scenarios
- `weighted_population_coverage_pct`: Total allocated / total displaced
- `allocation_success_count`: Scenarios with positive allocation
- `fully_covered_count`: Scenarios with zero uncovered
- `partial_covered_count`: Scenarios with allocation but remaining demand
- `failed_count`: Scenarios with no eligible shelter
- `mean_uncovered_people`, `total_uncovered_people`: Uncovered population statistics
- `critical_overcrowding_cases`: Allocations where projected occupancy >= 95%
- `medical_requirement_match_pct`: Match rate over scenarios with medical requirement
- `accessibility_requirement_match_pct`: Match rate over scenarios with accessibility requirement
- Split shelter allocation supported (multiple shelters per scenario)
- `mean_shelters_used`, route_safety, mean_latency_ms

### Priority Model Metrics
- Accuracy, macro precision, macro recall, macro F1, weighted F1
- Confusion matrix and per-class metrics
- Rule-versus-ML agreement rate and disagreement cases
- Prediction latency (mean, median, min, max, P95)

## Experiment Commands

```bash
# From backend directory
python -m evaluation.experiment_runner --module rescue --seed 42
python -m evaluation.experiment_runner --module relief --seed 42
python -m evaluation.experiment_runner --module shelter --seed 42
python -m evaluation.experiment_runner --module priority --seed 42
python -m evaluation.experiment_runner --module explainability --seed 42
python -m evaluation.experiment_runner --module performance --seed 42
python -m evaluation.experiment_runner --module all --seed 42

# With options
python -m evaluation.experiment_runner --module all --seed 42 --scenario-limit 10 --repeat-count 3 --output-directory evaluation_results
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/evaluation/algorithms | List all evaluation algorithms |
| GET | /api/evaluation/scenarios | List all deterministic scenarios |
| POST | /api/evaluation/experiments | Create and run evaluation experiment |
| GET | /api/evaluation/experiments | List all experiments |
| GET | /api/evaluation/experiments/{id} | Get experiment metadata |
| GET | /api/evaluation/experiments/{id}/results | Get experiment results |
| GET | /api/evaluation/experiments/{id}/metrics | Get aggregated metrics |
| GET | /api/evaluation/comparisons | Get baseline comparison |
| GET | /api/evaluation/priority-model | Get priority model evaluation |
| GET | /api/evaluation/performance | Get performance benchmark |
| GET | /api/evaluation/explainability | Get explainability coverage |
| GET | /api/evaluation/export/{id}?format=csv | Export results as CSV |
| GET | /api/evaluation/export/{id}?format=json | Export results as JSON |
| GET | /api/evaluation/export/{id}?format=markdown | Export results as Markdown |
| GET | /api/evaluation/export/{id}?format=latex | Export results as LaTeX |

## Export Formats

Results are exported in JSON, CSV, Markdown, and LaTeX formats to the configured output directory (default: `evaluation_results/`).

## Runtime Outputs

All experiment outputs are written to `backend/evaluation_results/` which is git-ignored. A separate `ml/evaluation_output/` is used for priority model evaluation results.

## Frontend

The Research Evaluation dashboard is accessible via the "Research Evaluation" tab in the frontend navigation. It provides:
- Module and algorithm selection
- Seed and scenario limit controls
- Rescue, relief, shelter comparison tables
- Priority model evaluation with confusion matrix
- Performance latency benchmarks
- Explainability coverage metrics
- Synthetic data disclaimer

## Synthetic Data Limitation

**Important:** All model training, evaluation scenarios, and baseline comparisons use synthetic/generated data only. Results do not reflect real-world disaster response performance. **No statistical significance claim is made.** The evaluation framework is designed to enable reproducible research comparisons, not to claim operational effectiveness.