import pytest
import statistics
from evaluation.statistics import (
    safe_divide,
    calculate_percentage_improvement,
    calculate_absolute_improvement,
    descriptive_statistics,
    compare_single_metric,
    compare_algorithms,
    compare_algorithms_lenient,
    generate_comparison_table,
    format_markdown_table,
    format_latex_table,
    DirectionMapping,
    MetricDirectionError,
    DEFAULT_LOWER_IS_BETTER,
    DEFAULT_HIGHER_IS_BETTER,
    MetricDirection,
    ComparisonResult,
)


class TestSafeDivide:
    def test_normal_division(self):
        assert safe_divide(10, 2) == 5.0

    def test_division_by_zero(self):
        assert safe_divide(10, 0) == 0.0

    def test_division_by_zero_custom_default(self):
        assert safe_divide(10, 0, default=-1.0) == -1.0

    def test_zero_numerator(self):
        assert safe_divide(0, 2) == 0.0


class TestCalculatePercentageImprovement:
    def test_lower_is_better_improvement(self):
        result = calculate_percentage_improvement(100, 80, lower_is_better=True)
        assert result == 20.0

    def test_lower_is_better_regression(self):
        result = calculate_percentage_improvement(100, 120, lower_is_better=True)
        assert result == -20.0

    def test_higher_is_better_improvement(self):
        result = calculate_percentage_improvement(100, 120, lower_is_better=False)
        assert result == 20.0

    def test_higher_is_better_regression(self):
        result = calculate_percentage_improvement(100, 80, lower_is_better=False)
        assert result == -20.0

    def test_unchanged(self):
        result = calculate_percentage_improvement(100, 100, lower_is_better=True)
        assert result == 0.0

    def test_baseline_zero_xdmra_zero(self):
        result = calculate_percentage_improvement(0, 0, lower_is_better=True)
        assert result == 0.0

    def test_baseline_zero_xdmra_positive(self):
        result = calculate_percentage_improvement(0, 50, lower_is_better=True)
        assert result is None

    def test_baseline_zero_xdmra_negative(self):
        result = calculate_percentage_improvement(0, -50, lower_is_better=True)
        assert result is None

    def test_negative_baseline_positive_xdmra_lower_better(self):
        result = calculate_percentage_improvement(-100, 50, lower_is_better=True)
        assert result == 150.0

    def test_negative_values(self):
        result = calculate_percentage_improvement(-50, -100, lower_is_better=True)
        assert result == -100.0


class TestCalculateAbsoluteImprovement:
    def test_lower_is_better_improvement(self):
        assert calculate_absolute_improvement(100, 80, lower_is_better=True) == 20.0

    def test_lower_is_better_regression(self):
        assert calculate_absolute_improvement(100, 120, lower_is_better=True) == -20.0

    def test_higher_is_better_improvement(self):
        assert calculate_absolute_improvement(100, 120, lower_is_better=False) == 20.0

    def test_higher_is_better_regression(self):
        assert calculate_absolute_improvement(100, 80, lower_is_better=False) == -20.0


class TestDescriptiveStatistics:
    def test_normal_values(self):
        stats = descriptive_statistics([1, 2, 3, 4, 5])
        assert stats["count"] == 5
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0
        assert stats["std"] == pytest.approx(1.5811, rel=0.01)
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0

    def test_empty_values(self):
        stats = descriptive_statistics([])
        assert stats["count"] == 0
        assert stats["mean"] == 0.0
        assert stats["median"] == 0.0
        assert stats["std"] == 0.0
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0

    def test_single_value(self):
        stats = descriptive_statistics([42])
        assert stats["count"] == 1
        assert stats["mean"] == 42.0
        assert stats["median"] == 42.0
        assert stats["std"] == 0.0
        assert stats["min"] == 42.0
        assert stats["max"] == 42.0

    def test_two_values(self):
        stats = descriptive_statistics([1, 3])
        assert stats["count"] == 2
        assert stats["mean"] == 2.0
        assert stats["median"] == 2.0
        assert stats["std"] == pytest.approx(1.414, rel=0.01)


class TestDirectionMapping:
    def test_default_lower_is_better(self):
        dm = DirectionMapping()
        assert dm.get_direction("mean_distance_km") == "lower_is_better"
        assert dm.get_direction("latency_ms") == "lower_is_better"

    def test_default_higher_is_better(self):
        dm = DirectionMapping()
        assert dm.get_direction("allocation_success_rate") == "higher_is_better"
        assert dm.get_direction("workload_fairness") == "higher_is_better"

    def test_unknown_metric_raises(self):
        dm = DirectionMapping()
        with pytest.raises(MetricDirectionError):
            dm.get_direction("unknown_metric")

    def test_unknown_metric_or_none(self):
        dm = DirectionMapping()
        assert dm.get_direction_or_none("unknown_metric") is None

    def test_custom_mapping(self):
        dm = DirectionMapping(
            lower_is_better=["custom_lower"],
            higher_is_better=["custom_higher"]
        )
        assert dm.get_direction("custom_lower") == "lower_is_better"
        assert dm.get_direction("custom_higher") == "higher_is_better"

    def test_override_default(self):
        dm = DirectionMapping(
            lower_is_better=["my_distance"],
            higher_is_better=[]
        )
        assert "mean_distance_km" in DEFAULT_LOWER_IS_BETTER
        assert dm.get_direction("my_distance") == "lower_is_better"
        with pytest.raises(MetricDirectionError):
            dm.get_direction("mean_distance_km")


class TestCompareSingleMetric:
    def test_lower_better_improved(self):
        result = compare_single_metric(100, 80, "lower_is_better")
        assert result.status == "improved"
        assert result.absolute_improvement == 20.0
        assert result.improvement_pct == 20.0

    def test_lower_better_regressed(self):
        result = compare_single_metric(100, 120, "lower_is_better")
        assert result.status == "regressed"
        assert result.absolute_improvement == -20.0

    def test_lower_better_unchanged(self):
        result = compare_single_metric(100, 100, "lower_is_better")
        assert result.status == "unchanged"
        assert result.absolute_improvement == 0.0
        assert result.improvement_pct == 0.0

    def test_higher_better_improved(self):
        result = compare_single_metric(100, 120, "higher_is_better")
        assert result.status == "improved"
        assert result.absolute_improvement == 20.0

    def test_higher_better_regressed(self):
        result = compare_single_metric(100, 80, "higher_is_better")
        assert result.status == "regressed"
        assert result.absolute_improvement == -20.0

    def test_baseline_zero_xdmra_zero(self):
        result = compare_single_metric(0, 0, "lower_is_better")
        assert result.status == "unchanged"
        assert result.absolute_improvement == 0.0
        assert result.improvement_pct == 0.0

    def test_baseline_zero_xdmra_positive_undefined(self):
        result = compare_single_metric(0, 50, "lower_is_better")
        assert result.status == "regressed"
        assert result.absolute_improvement == -50.0
        assert result.improvement_pct is None

    def test_to_dict(self):
        result = compare_single_metric(100, 80, "lower_is_better")
        d = result.to_dict()
        assert d["baseline_value"] == 100
        assert d["xdmra_value"] == 80
        assert d["status"] == "improved"


class TestCompareAlgorithms:
    def test_normal_comparison(self):
        baseline = {"mean_distance_km": 100}
        xdmra = {"mean_distance_km": 80}
        results = compare_algorithms(baseline, xdmra)
        assert results["mean_distance_km"]["status"] == "improved"
        assert results["mean_distance_km"]["improvement_pct"] == 20.0

    def test_missing_baseline(self):
        baseline = {}
        xdmra = {"mean_distance_km": 80}
        results = compare_algorithms(baseline, xdmra)
        assert results["mean_distance_km"]["status"] == "not_comparable"

    def test_unknown_metric_raises(self):
        baseline = {"unknown_metric": 100}
        xdmra = {"unknown_metric": 80}
        dm = DirectionMapping()
        with pytest.raises(MetricDirectionError):
            compare_algorithms(baseline, xdmra, dm)


class TestCompareAlgorithmsLenient:
    def test_unknown_metric_not_comparable(self):
        baseline = {"unknown_metric": 100}
        xdmra = {"unknown_metric": 80}
        results = compare_algorithms_lenient(baseline, xdmra)
        assert results["unknown_metric"]["status"] == "not_comparable"
        assert "error" in results["unknown_metric"]


class TestGenerateComparisonTable:
    def test_improved(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": 100.0,
                "xdmra_value": 80.0,
                "absolute_improvement": 20.0,
                "improvement_pct": 20.0,
                "status": "improved",
            }
        }
        table = generate_comparison_table(comparisons)
        assert table[0]["Improvement"] == "20.0%"
        assert table[0]["Status"] == "improved"

    def test_regressed(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": 100.0,
                "xdmra_value": 120.0,
                "absolute_improvement": -20.0,
                "improvement_pct": -20.0,
                "status": "regressed",
            }
        }
        table = generate_comparison_table(comparisons)
        assert table[0]["Improvement"] == "-20.0%"
        assert table[0]["Status"] == "regressed"

    def test_unchanged(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": 100.0,
                "xdmra_value": 100.0,
                "absolute_improvement": 0.0,
                "improvement_pct": 0.0,
                "status": "unchanged",
            }
        }
        table = generate_comparison_table(comparisons)
        assert table[0]["Improvement"] == "0.0%"
        assert table[0]["Status"] == "unchanged"

    def test_not_comparable(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": None,
                "xdmra_value": 80.0,
                "absolute_improvement": None,
                "improvement_pct": None,
                "status": "not_comparable",
            }
        }
        table = generate_comparison_table(comparisons)
        assert table[0]["Improvement"] == "N/A"
        assert table[0]["Baseline"] == "N/A"

    def test_undefined_percentage(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": 0.0,
                "xdmra_value": 50.0,
                "absolute_improvement": -50.0,
                "improvement_pct": None,
                "status": "regressed",
            }
        }
        table = generate_comparison_table(comparisons)
        assert table[0]["Improvement"] == "N/A"

    def test_empty(self):
        table = generate_comparison_table({})
        assert len(table) == 0


class TestFormatMarkdownTable:
    def test_improved(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": 100.0,
                "xdmra_value": 80.0,
                "improvement_pct": 20.0,
                "status": "improved",
            }
        }
        md = format_markdown_table(comparisons)
        assert "| mean_distance_km | 100.00 | 80.00 | 20.0% | improved |" in md

    def test_regressed(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": 100.0,
                "xdmra_value": 120.0,
                "improvement_pct": -20.0,
                "status": "regressed",
            }
        }
        md = format_markdown_table(comparisons)
        assert "| mean_distance_km | 100.00 | 120.00 | -20.0% | regressed |" in md

    def test_unchanged_no_arrow(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": 100.0,
                "xdmra_value": 100.0,
                "improvement_pct": 0.0,
                "status": "unchanged",
            }
        }
        md = format_markdown_table(comparisons)
        assert "unchanged" in md
        assert "$\\uparrow" not in md
        assert "$\\downarrow" not in md

    def test_not_comparable_na(self):
        comparisons = {
            "unknown_metric": {
                "baseline_value": None,
                "xdmra_value": 80.0,
                "improvement_pct": None,
                "status": "not_comparable",
            }
        }
        md = format_markdown_table(comparisons)
        assert "N/A" in md

    def test_empty_table(self):
        md = format_markdown_table({})
        assert "No data" in md

    def test_valid_markdown_syntax(self):
        comparisons = {
            "distance": {"baseline_value": 10.0, "xdmra_value": 8.0, "improvement_pct": 20.0, "status": "improved"},
            "success_rate": {"baseline_value": 0.8, "xdmra_value": 0.9, "improvement_pct": 12.5, "status": "improved"},
        }
        md = format_markdown_table(comparisons)
        lines = md.split("\n")
        assert len(lines) == 4
        assert lines[0].startswith("|")
        assert lines[0].endswith("|")
        header_cols = lines[0].split("|")
        assert len(header_cols) == 7


class TestFormatLatexTable:
    def test_escapes_special_characters(self):
        comparisons = {
            "mean_distance_km & 100": {
                "baseline_value": 100.0,
                "xdmra_value": 80.0,
                "improvement_pct": 20.0,
                "status": "improved",
            }
        }
        latex = format_latex_table(comparisons, caption="Test & Comparison", label="tab:test")
        assert "\\&" in latex
        assert "Test \\& Comparison" in latex

    def test_improved_arrow(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": 100.0,
                "xdmra_value": 80.0,
                "improvement_pct": 20.0,
                "status": "improved",
            }
        }
        latex = format_latex_table(comparisons)
        assert "$\\uparrow$" in latex

    def test_regressed_arrow(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": 100.0,
                "xdmra_value": 120.0,
                "improvement_pct": -20.0,
                "status": "regressed",
            }
        }
        latex = format_latex_table(comparisons)
        assert "$\\downarrow$" in latex

    def test_unchanged_no_arrow(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": 100.0,
                "xdmra_value": 100.0,
                "improvement_pct": 0.0,
                "status": "unchanged",
            }
        }
        latex = format_latex_table(comparisons)
        assert "$\\leftrightarrow$" in latex

    def test_na_for_undefined(self):
        comparisons = {
            "mean_distance_km": {
                "baseline_value": 0.0,
                "xdmra_value": 50.0,
                "improvement_pct": None,
                "status": "regressed",
            }
        }
        latex = format_latex_table(comparisons)
        assert "N/A" in latex

    def test_empty_comparisons(self):
        latex = format_latex_table({}, caption="Empty", label="tab:empty")
        assert "\\begin{table}" in latex
        assert "No data" in latex

    def test_not_comparable_na(self):
        comparisons = {
            "unknown_metric": {
                "baseline_value": None,
                "xdmra_value": 80.0,
                "improvement_pct": None,
                "status": "not_comparable",
            }
        }
        latex = format_latex_table(comparisons)
        assert "N/A" in latex


class TestMetricDirectionError:
    def test_is_value_error(self):
        dm = DirectionMapping()
        with pytest.raises(MetricDirectionError) as exc_info:
            dm.get_direction("totally_unknown")
        assert "Unknown metric direction" in str(exc_info.value)