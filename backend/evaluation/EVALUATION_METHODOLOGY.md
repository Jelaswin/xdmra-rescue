# Evaluation Methodology

## Research Questions

The X-DMRA Research Evaluation framework is designed to address:

1. **Baseline Comparison**: How does X-DMRA's allocation decisions compare against simple baseline strategies across rescue, relief, and shelter scenarios?
2. **Deterministic Reproducibility**: Can evaluation results be exactly reproduced given the same seed?
3. **Metric-Driven Assessment**: What is the performance profile across multiple operational dimensions (distance, skill match, fairness, latency)?
4. **Model Evaluation**: How does the trained priority model perform on held-out synthetic data?
5. **Explainability Coverage**: Do recommendation explanations contain required structural elements?
6. **Performance Characteristics**: What are the latency profiles of key X-DMRA operations?

## Baseline Algorithm Design

### Rescue Allocation

All rescue baselines operate on the same principle:
1. Filter teams by availability status
2. Apply algorithm-specific ranking or selection
3. Return selected team with distance and match metrics

The **X-DMRA Explainable baseline** is not a separate algorithm but refers to X-DMRA's production recommendation system when invoked through the evaluation framework.

### Relief Allocation

Relief baselines operate on warehouse inventory and demand requirements:
1. Filter warehouses by operating status
2. Check inventory availability against item requirements
3. Apply algorithm-specific selection logic
4. Never allocate more than available stock

### Shelter Allocation

Shelter baselines operate on shelter capacity and displaced population:
1. Filter shelters by operating status and available capacity
2. Apply algorithm-specific selection
3. Never admit more people than available capacity allows
4. Track uncovered population when total capacity is insufficient

## Scenario Design

### Rescue Scenarios (25 total)
- Covers low (5), high (10), and critical (10) priority incidents
- Includes skill mismatch cases
- Includes equipment mismatch cases
- Includes blocked-route scenarios
- Includes no-eligible-team scenarios
- All scenarios are deterministic and seeded

### Relief Scenarios (20 total)
- Complete single-source stock (5 cases)
- Split allocation scenarios (5 cases)
- Low stock shortage (4 cases)
- Blocked warehouse exclusion (3 cases)
- High demand with limited inventory (3 cases)

### Shelter Scenarios (20 total)
- Single shelter allocation (5 cases)
- Split shelter allocation (5 cases)
- Medical requirement mandatory (3 cases)
- Accessibility requirement mandatory (3 cases)
- Critical overcrowding (4 cases)

## Metric Direction Mapping

Each metric has an explicit direction configuration. Guessing direction from substring matching is deliberately avoided.

### Lower-is-Better Metrics
- mean_distance_km, median_distance_km
- latency_ms
- shortage_quantity, uncovered_population
- capacity_violations, stock_violations
- overloaded_teams_selected, blocked_route_selections
- critical_overcrowding_cases
- number_of_warehouses_used, number_of_shelters_used

### Higher-is-Better Metrics
- allocation_success_rate
- fulfilment_percentage, population_coverage_percentage
- skill_match_percentage, equipment_match_percentage
- route_safety_score
- workload_fairness
- explanation_availability_rate

## Percentage Improvement Rules

Percentage improvement between baseline and X-DMRA is calculated as:

```
improvement_pct = ((baseline_value - xdmra_value) / baseline_value) * 100  (lower_is_better)
improvement_pct = ((xdmra_value - baseline_value) / baseline_value) * 100   (higher_is_better)
```

**Undefined Cases:**
- When baseline_value == 0 and xdmra_value == 0: returns 0.0%
- When baseline_value == 0 and xdmra_value != 0: returns None (N/A)
- Absolute improvement is always calculated and available

## Jain's Fairness Index

Jain's fairness index for workload distribution:

```
J = (sum(w_i))^2 / (n * sum(w_i^2))

where w_i is the workload of team i and n is the number of teams.
```

**Safe Handling:**
- Empty workload list: returns empty dict
- All-zero workloads: returns jains_fairness_index = 0
- Single team: returns std = 0

## Priority Model Evaluation

The priority model is evaluated on the synthetic training dataset without retraining.

### Metrics
- Accuracy, macro precision, macro recall, macro F1, weighted F1
- Per-class precision, recall, F1, and support
- Confusion matrix (class × predicted)
- Training accuracy vs. evaluation accuracy (overfitting indicator)

### Rule-versus-ML Agreement
A simple rule-based priority is computed for each incident:
- Score = affected*1 + injured*3 + trapped*5
- Threshold-based classification into low/medium/high/critical

Agreement rate and disagreement count are reported separately.

### Known Limitations
- Evaluation uses only synthetic data
- Training score vs. evaluation score difference is flagged as potential overfitting
- No claim of real-world operational accuracy is made

## Explainability Coverage

Explanation quality is assessed via deterministic structural checks (NOT content grading):

1. **resource_name**: Explanation references team/warehouse/shelter
2. **distance**: Distance information is present
3. **relevant_factor**: A decision factor is mentioned
4. **limitation**: A constraint or limitation is acknowledged
5. **route_risk**: Route safety or blocked route mentioned
6. **alternative_comparison**: Alternative resource is referenced

These checks verify structural presence, not content accuracy or human interpretability.

## Performance Benchmarking

Latency is measured using `time.perf_counter()` (high-resolution timer):

Operations benchmarked:
- Rule priority calculation
- ML prediction
- Rescue recommendation
- Relief recommendation
- Shelter recommendation

Statistics reported: mean, median, min, max, std, P95.

Application startup time and migration time are excluded unless separately labelled.

## Export Formats

### CSV
- UTF-8 encoded
- Excel-compatible
- Stable column ordering
- None values represented as empty strings

### JSON
- UTF-8 encoded
- Indented (pretty-printed)
- All values serializable

### Markdown
- Standard GFM table syntax
- Pipes and hyphens for alignment

### LaTeX
- Booktabs-style tables
- Special characters escaped (\ & % $ # _ { } ~ ^)
- Backslash escaped as \textbackslash{}

## Reproducibility

All experiments accept a `--seed` parameter:
- Python's `random.seed(seed)` for baseline selection
- NumPy's `np.random.seed(seed)` for any statistical sampling
- Results are deterministic for the same seed

Scenario definitions do not use randomness - they are fixed templates.

## Evaluation API Security

- Experiment identifiers are validated
- Path traversal attempts are rejected
- Export cannot read arbitrary files
- No arbitrary command execution
- Runtime outputs written only to configured directory
- No modification of model artifacts or source code

## Database Storage

Evaluation models (Experiment, ScenarioResult, MetricSummary) are defined but database storage is optional. File-based evaluation with JSON/CSV exports is the default. Database storage is used only when API persistence is required.

## Runtime Output Safety

All generated evaluation files are written to:
- `backend/evaluation_results/` (git-ignored)
- `backend/ml/evaluation_output/` (git-ignored)

These directories are never committed and contain only transient runtime outputs.

## Known Limitations

1. **Synthetic Data Only**: All scenarios and training data are synthetic. Real-world effectiveness cannot be inferred.
2. **Single Seed Per Experiment**: Cross-seed statistical analysis is not implemented.
3. **No Confidence Intervals**: Point estimates only; no uncertainty quantification.
4. **No Statistical Significance Testing**: Comparative claims require formal hypothesis testing.
5. **No Temporal Validation**: Time-series split or forward-validation not implemented.
6. **Baseline Exclusivity**: Baseline algorithms are evaluation-only and do not share production code paths.