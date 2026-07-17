"""
Paper-Ready Formatted Comparison Tables.

Generates rescue, relief, shelter, and priority comparison tables
in CSV, Markdown, and LaTeX formats.

Do not fabricate missing values. Empty comparisons return controlled empty results.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from evaluation.exporters import (
    export_csv, export_json, export_markdown_table, export_latex_table,
    format_value, LaTeXEscaper
)


def build_rescue_comparison_table(
    all_metrics: Dict[str, Dict[str, Any]],
    algorithms: List[str],
) -> List[Dict[str, str]]:
    """Build rescue comparison table rows from per-algorithm metrics."""
    rows = []
    for algo in algorithms:
        m = all_metrics.get(algo, {})
        if not m:
            continue
        rows.append({
            "Algorithm": algo,
            "Allocation Success (%)": format_value(m.get("success_rate_pct", 0), "pct"),
            "Mean Distance (km)": format_value(m.get("mean_distance_km", 0), "km"),
            "Skill Match (%)": format_value(m.get("mean_skill_match_pct", 0), "pct"),
            "Route Safety": format_value(m.get("mean_route_safety_score", 0)),
            "Workload Fairness": format_value(m.get("jains_fairness_index", 0)),
            "Mean Latency (ms)": format_value(m.get("mean_computation_time_ms", 0), "ms"),
        })
    return rows


def build_relief_comparison_table(
    all_metrics: Dict[str, Dict[str, Any]],
    algorithms: List[str],
) -> List[Dict[str, str]]:
    """Build relief comparison table rows from per-algorithm metrics."""
    rows = []
    for algo in algorithms:
        m = all_metrics.get(algo, {})
        if not m:
            continue
        rows.append({
            "Algorithm": algo,
            "Demand Fulfilment (%)": format_value(m.get("mean_fulfilment_pct", 0), "pct"),
            "Mean Shortage": format_value(m.get("mean_shortage", 0)),
            "Warehouses Used": format_value(m.get("mean_warehouses_used", 0)),
            "Stock Violations": format_value(m.get("stock_violation_count", 0)),
            "Mean Latency (ms)": format_value(m.get("mean_computation_time_ms", 0), "ms"),
        })
    return rows


def build_shelter_comparison_table(
    all_metrics: Dict[str, Dict[str, Any]],
    algorithms: List[str],
) -> List[Dict[str, str]]:
    """Build shelter comparison table rows from per-algorithm metrics."""
    rows = []
    for algo in algorithms:
        m = all_metrics.get(algo, {})
        if not m:
            continue
        rows.append({
            "Algorithm": algo,
            "Population Coverage (%)": format_value(m.get("mean_population_coverage_pct", 0), "pct"),
            "Uncovered Population": format_value(m.get("mean_uncovered_people", 0)),
            "Critical Overcrowding": format_value(m.get("overcrowding_violation_count", 0)),
            "Requirement Match (%)": format_value(m.get("mean_requirement_match_pct", 0), "pct"),
            "Mean Latency (ms)": format_value(m.get("mean_computation_time_ms", 0), "ms"),
        })
    return rows


def build_priority_comparison_table(
    result: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Build priority model evaluation table."""
    rows = []
    if not result:
        return rows

    rows.append({"Metric": "Accuracy", "Value": format_value(result.get("accuracy", 0), "pct")})
    rows.append({"Metric": "Macro Precision", "Value": format_value(result.get("macro_precision", 0), "pct")})
    rows.append({"Metric": "Macro Recall", "Value": format_value(result.get("macro_recall", 0), "pct")})
    rows.append({"Metric": "Macro F1", "Value": format_value(result.get("macro_f1", 0), "pct")})
    rows.append({"Metric": "Weighted F1", "Value": format_value(result.get("weighted_f1", 0), "pct")})
    rows.append({"Metric": "Prediction Latency (mean, ms)", "Value": format_value(result.get("prediction_latency_ms_mean", 0), "ms")})
    rows.append({"Metric": "Prediction Latency (P95, ms)", "Value": format_value(result.get("prediction_latency_ms_p95", 0), "ms")})
    rows.append({"Metric": "Rule-ML Agreement (%)", "Value": format_value(result.get("rule_ml_agreement_rate", 0), "pct")})
    rows.append({"Metric": "Training Accuracy (%)", "Value": format_value(result.get("training_accuracy", 0), "pct")})
    rows.append({"Metric": "Total Samples", "Value": format_value(result.get("total_samples", 0))})

    return rows


def export_rescue_table(
    all_metrics: Dict[str, Dict[str, Any]],
    algorithms: List[str],
    output_dir: Path,
    title: str = "Rescue Allocation Comparison",
) -> None:
    rows = build_rescue_comparison_table(all_metrics, algorithms)
    if not rows:
        return

    headers = list(rows[0].keys()) if rows else []
    data_rows = [[row[h] for h in headers] for row in rows]

    output_dir.mkdir(parents=True, exist_ok=True)

    export_json({"algorithms": algorithms, "metrics": all_metrics}, output_dir / "rescue_table.json")

    export_csv([dict(zip(headers, r)) for r in data_rows], output_dir / "rescue_table.csv")

    export_markdown_table(headers, data_rows, output_dir / "rescue_table.md", title=title)

    export_latex_table(
        headers, data_rows,
        output_dir / "rescue_table.tex",
        caption=title, label="tab:rescue-comparison"
    )


def export_relief_table(
    all_metrics: Dict[str, Dict[str, Any]],
    algorithms: List[str],
    output_dir: Path,
    title: str = "Relief Allocation Comparison",
) -> None:
    rows = build_relief_comparison_table(all_metrics, algorithms)
    if not rows:
        return

    headers = list(rows[0].keys()) if rows else []
    data_rows = [[row[h] for h in headers] for row in rows]

    output_dir.mkdir(parents=True, exist_ok=True)

    export_json({"algorithms": algorithms, "metrics": all_metrics}, output_dir / "relief_table.json")
    export_csv([dict(zip(headers, r)) for r in data_rows], output_dir / "relief_table.csv")
    export_markdown_table(headers, data_rows, output_dir / "relief_table.md", title=title)
    export_latex_table(
        headers, data_rows,
        output_dir / "relief_table.tex",
        caption=title, label="tab:relief-comparison"
    )


def export_shelter_table(
    all_metrics: Dict[str, Dict[str, Any]],
    algorithms: List[str],
    output_dir: Path,
    title: str = "Shelter Allocation Comparison",
) -> None:
    rows = build_shelter_comparison_table(all_metrics, algorithms)
    if not rows:
        return

    headers = list(rows[0].keys()) if rows else []
    data_rows = [[row[h] for h in headers] for row in rows]

    output_dir.mkdir(parents=True, exist_ok=True)

    export_json({"algorithms": algorithms, "metrics": all_metrics}, output_dir / "shelter_table.json")
    export_csv([dict(zip(headers, r)) for r in data_rows], output_dir / "shelter_table.csv")
    export_markdown_table(headers, data_rows, output_dir / "shelter_table.md", title=title)
    export_latex_table(
        headers, data_rows,
        output_dir / "shelter_table.tex",
        caption=title, label="tab:shelter-comparison"
    )


def export_priority_table(
    result: Dict[str, Any],
    output_dir: Path,
    title: str = "Priority Model Evaluation",
) -> None:
    rows = build_priority_comparison_table(result)
    if not rows:
        return

    headers = ["Metric", "Value"]
    data_rows = [[row["Metric"], row["Value"]] for row in rows]

    output_dir.mkdir(parents=True, exist_ok=True)

    export_json(result, output_dir / "priority_table.json")
    export_csv([{"Metric": r["Metric"], "Value": r["Value"]} for r in rows], output_dir / "priority_table.csv")
    export_markdown_table(headers, data_rows, output_dir / "priority_table.md", title=title)
    export_latex_table(
        headers, data_rows,
        output_dir / "priority_table.tex",
        caption=title, label="tab:priority-model"
    )