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

All baselines use **per-item capped allocation**:
```
allocated[item] = min(requested[item], available_stock[item])
```

Excess of one item NEVER compensates for shortage of another.

**Fulfilment** (per scenario):
```
fulfilment_pct = 100 × sum(allocated[item]) / sum(requested[item])
```

**Macro fulfilment**: mean of scenario fulfilment_pct over ALL scenarios
**Weighted fulfilment**: 100 × sum(allocated) / sum(requested) across all scenarios

**Shortage** (per scenario):
```
shortage = sum(max(0, requested[item] - allocated[item]))
```

**Stock violation**: only when allocated[item] > available_stock[item] (always zero in correct implementations).

**X-DMRA relief** uses production scoring with greedy split allocation across ranked warehouses.

### Shelter Allocation

Shelter baselines use **capacity-capped allocation**:
```
allocated = min(displaced_people, available_capacity)
```

**Coverage** (per scenario):
```
coverage_pct = 100 × allocated / displaced
```

**Macro coverage**: mean of scenario coverage_pct over ALL scenarios
**Weighted coverage**: 100 × sum(allocated) / sum(displaced) across all scenarios

**Critical overcrowding**: projected occupancy >= 95% (fixed threshold).

**Medical/accessibility requirement match**: percentage only over scenarios that require the feature (not all scenarios).

**X-DMRA shelter** uses production scoring with greedy split allocation across ranked shelters.

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

The priority model is evaluated on the **held-out synthetic test set** (549 samples, 20% of 2744 total, `train_test_split(random_state=42, test_size=0.2, stratify=y)`). The model is **not retrained**. Training artifacts are not modified.

### Metrics
- Accuracy: percentage of correct predictions on test set
- Macro precision/recall/F1: unweighted mean of per-class values
- Weighted F1: support-weighted mean of per-class F1
- Per-class precision, recall, F1, and support
- Confusion matrix (true class × predicted class)
- Training accuracy vs. evaluation accuracy gap (flagged as potential overfitting)
- Prediction latency (mean, median, min, max, P95) measured per-sample after warm-up

### Latency Measurement
- Model is loaded once and cached globally
- One warm-up prediction is discarded before timing
- Each subsequent prediction is timed individually with `time.perf_counter()`
- Batch effects are excluded; per-sample timing captures single-incident latency

### Rule-versus-ML Agreement
A simple rule-based priority is computed for each incident:
- Score = affected*1 + injured*3 + trapped*5 + severity_weight
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