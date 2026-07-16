"""
Statistical Calculations for Evaluation.

Descriptive statistics and baseline comparison calculations.
"""

from typing import Dict, Any, List, Optional, Tuple, Literal
from dataclasses import dataclass, field
import statistics


MetricDirection = Literal["lower_is_better", "higher_is_better"]


DEFAULT_LOWER_IS_BETTER: set = {
    "mean_distance_km",
    "median_distance_km",
    "latency_ms",
    "shortage_quantity",
    "uncovered_population",
    "capacity_violations",
    "stock_violations",
    "overloaded_teams_selected",
    "blocked_route_selections",
    "critical_overcrowding_cases",
    "number_of_warehouses_used",
    "number_of_shelters_used",
}

DEFAULT_HIGHER_IS_BETTER: set = {
    "allocation_success_rate",
    "fulfilment_percentage",
    "population_coverage_percentage",
    "skill_match_percentage",
    "equipment_match_percentage",
    "route_safety_score",
    "workload_fairness",
    "explanation_availability_rate",
    "medical_support_match_percentage",
    "accessibility_support_match_percentage",
}


class MetricDirectionError(ValueError):
    """Raised when a metric has no configured direction."""
    pass


class DirectionMapping:
    """Configurable metric direction mapping."""

    def __init__(
        self,
        lower_is_better: Optional[List[str]] = None,
        higher_is_better: Optional[List[str]] = None,
    ):
        self._lower: set = set(lower_is_better) if lower_is_better else DEFAULT_LOWER_IS_BETTER.copy()
        self._higher: set = set(higher_is_better) if higher_is_better else DEFAULT_HIGHER_IS_BETTER.copy()

    def get_direction(self, metric_name: str) -> MetricDirection:
        """Get the direction for a metric, raising if unknown."""
        if metric_name in self._lower:
            return "lower_is_better"
        if metric_name in self._higher:
            return "higher_is_better"
        raise MetricDirectionError(
            f"Unknown metric direction for '{metric_name}'. "
            f"Provide explicit direction mapping or add to known metrics."
        )

    def get_direction_or_none(self, metric_name: str) -> Optional[MetricDirection]:
        """Get the direction for a metric, returning None if unknown."""
        if metric_name in self._lower:
            return "lower_is_better"
        if metric_name in self._higher:
            return "higher_is_better"
        return None

    def is_lower_better(self, metric_name: str) -> bool:
        """Check if lower is better for the metric."""
        return metric_name in self._lower

    def is_higher_better(self, metric_name: str) -> bool:
        """Check if higher is better for the metric."""
        return metric_name in self._higher


@dataclass
class ComparisonResult:
    """Result of comparing baseline vs X-DMRA for a single metric."""
    baseline_value: float
    xdmra_value: float
    absolute_improvement: float
    improvement_pct: Optional[float]
    direction: MetricDirection
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_value": self.baseline_value,
            "xdmra_value": self.xdmra_value,
            "absolute_improvement": self.absolute_improvement,
            "improvement_pct": self.improvement_pct,
            "direction": self.direction,
            "status": self.status,
        }


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide, returning default if denominator is zero."""
    return numerator / denominator if denominator != 0 else default


def calculate_percentage_improvement(
    baseline_value: float,
    xdmra_value: float,
    lower_is_better: bool,
) -> Optional[float]:
    """Calculate percentage improvement between baseline and X-DMRA values.

    Args:
        baseline_value: The baseline metric value
        xdmra_value: The X-DMRA metric value
        lower_is_better: True if lower values are better (e.g., distance)

    Returns:
        Percentage improvement as float, or None if mathematically undefined.
        When both values are zero, returns 0.0.
    """
    if baseline_value == 0:
        if xdmra_value == 0:
            return 0.0
        return None

    if lower_is_better:
        return ((baseline_value - xdmra_value) / baseline_value) * 100
    else:
        return ((xdmra_value - baseline_value) / baseline_value) * 100


def calculate_absolute_improvement(
    baseline_value: float,
    xdmra_value: float,
    lower_is_better: bool,
) -> float:
    """Calculate absolute improvement between baseline and X-DMRA values."""
    if lower_is_better:
        return baseline_value - xdmra_value
    else:
        return xdmra_value - baseline_value


def descriptive_statistics(values: List[float]) -> Dict[str, float]:
    """Calculate descriptive statistics for a list of values."""
    if not values:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    n = len(values)
    mean = statistics.mean(values)
    median = statistics.median(values)
    std = statistics.stdev(values) if n > 1 else 0.0
    min_val = min(values)
    max_val = max(values)

    return {
        "count": n,
        "mean": mean,
        "median": median,
        "std": std,
        "min": min_val,
        "max": max_val,
    }


def compare_single_metric(
    baseline_value: float,
    xdmra_value: float,
    direction: MetricDirection,
) -> ComparisonResult:
    """Compare baseline and X-DMRA values for a single metric."""
    lower_is_better = direction == "lower_is_better"

    abs_imp = calculate_absolute_improvement(baseline_value, xdmra_value, lower_is_better)
    pct_imp = calculate_percentage_improvement(baseline_value, xdmra_value, lower_is_better)

    if abs_imp > 0:
        status = "improved"
    elif abs_imp < 0:
        status = "regressed"
    else:
        status = "unchanged"

    return ComparisonResult(
        baseline_value=baseline_value,
        xdmra_value=xdmra_value,
        absolute_improvement=abs_imp,
        improvement_pct=pct_imp,
        direction=direction,
        status=status,
    )


def compare_algorithms(
    baseline_metrics: Dict[str, float],
    xdmra_metrics: Dict[str, float],
    direction_mapping: Optional[DirectionMapping] = None,
) -> Dict[str, Dict[str, Any]]:
    """Compare baseline and X-DMRA metrics.

    Args:
        baseline_metrics: Dict of metric_name -> baseline value
        xdmra_metrics: Dict of metric_name -> X-DMRA value
        direction_mapping: Optional custom direction mapping

    Returns:
        Dict of metric_name -> comparison result dict

    Raises:
        MetricDirectionError: If a metric has no configured direction.
    """
    if direction_mapping is None:
        direction_mapping = DirectionMapping()

    results = {}

    for key in xdmra_metrics:
        if key not in baseline_metrics:
            results[key] = {
                "baseline_value": None,
                "xdmra_value": xdmra_metrics[key],
                "absolute_improvement": None,
                "improvement_pct": None,
                "direction": None,
                "status": "not_comparable",
                "error": f"Metric '{key}' not found in baseline metrics",
            }
            continue

        direction = direction_mapping.get_direction(key)
        comparison = compare_single_metric(baseline_metrics[key], xdmra_metrics[key], direction)
        results[key] = comparison.to_dict()

    return results


def compare_algorithms_lenient(
    baseline_metrics: Dict[str, float],
    xdmra_metrics: Dict[str, float],
    direction_mapping: Optional[DirectionMapping] = None,
) -> Dict[str, Dict[str, Any]]:
    """Compare baseline and X-DMRA metrics, marking unknown metrics as not_comparable.

    Args:
        baseline_metrics: Dict of metric_name -> baseline value
        xdmra_metrics: Dict of metric_name -> X-DMRA value
        direction_mapping: Optional custom direction mapping

    Returns:
        Dict of metric_name -> comparison result dict
    """
    if direction_mapping is None:
        direction_mapping = DirectionMapping()

    results = {}

    for key in xdmra_metrics:
        if key not in baseline_metrics:
            results[key] = {
                "baseline_value": None,
                "xdmra_value": xdmra_metrics[key],
                "absolute_improvement": None,
                "improvement_pct": None,
                "direction": None,
                "status": "not_comparable",
                "error": f"Metric '{key}' not found in baseline metrics",
            }
            continue

        direction = direction_mapping.get_direction_or_none(key)
        if direction is None:
            results[key] = {
                "baseline_value": baseline_metrics[key],
                "xdmra_value": xdmra_metrics[key],
                "absolute_improvement": None,
                "improvement_pct": None,
                "direction": None,
                "status": "not_comparable",
                "error": f"Unknown metric direction for '{key}'",
            }
            continue

        comparison = compare_single_metric(baseline_metrics[key], xdmra_metrics[key], direction)
        results[key] = comparison.to_dict()

    return results


def generate_comparison_table(
    comparisons: Dict[str, Dict[str, Any]]
) -> List[Dict[str, str]]:
    """Generate a formatted table of algorithm comparisons."""
    table = []

    for metric_name, data in comparisons.items():
        status = data.get("status", "not_comparable")

        if status == "not_comparable":
            pct_display = "N/A"
            direction_arrow = ""
        elif data.get("improvement_pct") is None:
            pct_display = "N/A"
            direction_arrow = ""
        elif status == "improved":
            pct_display = f"{data['improvement_pct']:.1f}%"
            direction_arrow = "improved"
        elif status == "regressed":
            pct_display = f"{data['improvement_pct']:.1f}%"
            direction_arrow = "regressed"
        else:
            pct_display = "0.0%"
            direction_arrow = "unchanged"

        row = {
            "Metric": metric_name,
            "Baseline": f"{data['baseline_value']:.2f}" if data.get("baseline_value") is not None else "N/A",
            "X-DMRA": f"{data['xdmra_value']:.2f}" if data.get("xdmra_value") is not None else "N/A",
            "Improvement": pct_display,
            "Status": direction_arrow,
        }
        table.append(row)

    return table


def _escape_latex(text: str) -> str:
    """Escape LaTeX special characters."""
    replacements = {
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
    }
    for char, escaped in replacements.items():
        text = text.replace(char, escaped)
    return text


def format_latex_table(
    comparisons: Dict[str, Dict[str, Any]],
    caption: str = "",
    label: str = ""
) -> str:
    """Format comparison results as LaTeX table."""
    if not comparisons:
        return "\\begin{table}[h]\n\\centering\n\\caption{No data}\n\\label{tab:no-data}\n\\end{table}"

    lines = [
        "\\begin{table}[h]",
        "\\centering",
        f"\\caption{{{_escape_latex(caption)}}}",
        f"\\label{{{_escape_latex(label)}}}",
        "\\begin{tabular}{|l|c|c|c|c|}",
        "\\hline",
        "Metric & Baseline & X-DMRA & Improvement & Status \\\\ ",
        "\\hline"
    ]

    for metric_name, data in comparisons.items():
        status = data.get("status", "not_comparable")

        baseline_str = f"{data['baseline_value']:.2f}" if data.get("baseline_value") is not None else "N/A"
        xdmra_str = f"{data['xdmra_value']:.2f}" if data.get("xdmra_value") is not None else "N/A"

        if status == "not_comparable" or data.get("improvement_pct") is None:
            improvement_str = "N/A"
            status_str = "---"
        else:
            improvement_str = f"{data['improvement_pct']:.1f}\\%"
            if status == "improved":
                status_str = "$\\uparrow$"
            elif status == "regressed":
                status_str = "$\\downarrow$"
            else:
                status_str = "$\\leftrightarrow$"

        lines.append(
            f"{_escape_latex(metric_name)} & {baseline_str} & {xdmra_str} & {improvement_str} & {status_str} \\\\ "
        )

    lines.extend([
        "\\hline",
        "\\end{tabular}",
        "\\end{table}"
    ])

    return "\n".join(lines)


def format_markdown_table(
    comparisons: Dict[str, Dict[str, Any]]
) -> str:
    """Format comparison results as Markdown table."""
    if not comparisons:
        return "| Metric | Baseline | X-DMRA | Improvement | Status |\n|---------|----------|--------|------------|--------|\n| No data | N/A | N/A | N/A | N/A |"

    lines = [
        "| Metric | Baseline | X-DMRA | Improvement | Status |",
        "|---------|----------|--------|------------|--------|"
    ]

    for metric_name, data in comparisons.items():
        status = data.get("status", "not_comparable")

        baseline_str = f"{data['baseline_value']:.2f}" if data.get("baseline_value") is not None else "N/A"
        xdmra_str = f"{data['xdmra_value']:.2f}" if data.get("xdmra_value") is not None else "N/A"

        if status == "not_comparable" or data.get("improvement_pct") is None:
            improvement_str = "N/A"
            status_str = "N/A"
        elif status == "improved":
            improvement_str = f"{data['improvement_pct']:.1f}%"
            status_str = "improved"
        elif status == "regressed":
            improvement_str = f"{data['improvement_pct']:.1f}%"
            status_str = "regressed"
        else:
            improvement_str = "0.0%"
            status_str = "unchanged"

        lines.append(f"| {metric_name} | {baseline_str} | {xdmra_str} | {improvement_str} | {status_str} |")

    return "\n".join(lines)