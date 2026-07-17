"""
Explainability Coverage Evaluation.

Deterministic checks for rescue, relief, and shelter explanation quality.
Does not use an LLM for grading.

These check whether an explanation contains the required structural elements,
NOT whether the content is accurate or human-interpretable.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from evaluation.statistics import descriptive_statistics


@dataclass
class ExplainabilityCheck:
    passed: bool
    element: str
    detail: str


@dataclass
class ExplainabilityCoverageResult:
    module: str
    explanation_count: int
    checked_count: int
    coverage_rate_pct: float
    element_coverage: Dict[str, float]
    checks: List[Dict[str, str]]
    mean_latency_ms: Optional[float]
    synthetic_data_note: str


def check_explanation(explanation: Optional[str]) -> List[ExplainabilityCheck]:
    """Check an explanation for required structural elements.

    Does NOT validate content accuracy or human interpretability.
    Returns a list of per-element pass/fail checks.
    """
    checks = []
    text = (explanation or "").lower()

    has_resource = any(token in text for token in ["team", "warehouse", "shelter", "selected", "chosen", "allocated"])
    checks.append(ExplainabilityCheck(
        passed=has_resource,
        element="resource_name",
        detail="Explanation includes or references a resource name" if has_resource else "No resource name found"
    ))

    has_distance = any(token in text for token in ["km", "kilometer", "distance", "miles", "meters", "m away"])
    checks.append(ExplainabilityCheck(
        passed=has_distance,
        element="distance",
        detail="Distance information present" if has_distance else "No distance information found"
    ))

    has_factor = any(token in text for token in ["because", "due to", "factor", "reason", "since", "based on", "as", "优先级"])
    checks.append(ExplainabilityCheck(
        passed=has_factor,
        element="relevant_factor",
        detail="Relevant decision factor mentioned" if has_factor else "No decision factor found"
    ))

    has_limitation = any(token in text for token in ["limitation", "constraint", "however", "although", "but", "note", "despite"])
    checks.append(ExplainabilityCheck(
        passed=has_limitation,
        element="limitation",
        detail="Limitation or constraint acknowledged" if has_limitation else "No limitation noted"
    ))

    has_route_risk = any(token in text for token in ["route", "road", "blocked", "unsafe", "risk", "blocked route"])
    checks.append(ExplainabilityCheck(
        passed=has_route_risk,
        element="route_risk",
        detail="Route risk or safety mentioned" if has_route_risk else "No route risk information"
    ))

    has_alternative = any(token in text for token in ["alternative", "instead", "other", "option", "another", "vs", "versus", "compared"])
    checks.append(ExplainabilityCheck(
        passed=has_alternative,
        element="alternative_comparison",
        detail="Alternative resource comparison present" if has_alternative else "No alternative comparison"
    ))

    has_explanation = len(explanation or "") > 20
    checks.append(ExplainabilityCheck(
        passed=has_explanation,
        element="explanation_exists",
        detail="Explanation is non-empty and substantive" if has_explanation else "Explanation empty or too short"
    ))

    return checks


def _validate_explanation_against_result(explanation: Optional[str], result: Dict[str, Any]) -> bool:
    """Check if explanation values agree with result data.

    This is a lightweight consistency check, not a deep validation.
    """
    if not explanation or len(explanation) < 10:
        return False

    text = explanation.lower()

    if result.get("selected_team_name") or result.get("selected_resource_name"):
        name = (result.get("selected_team_name") or result.get("selected_resource_name") or "").lower()
        if name and len(name) > 2:
            name_tokens = name.split()
            name_found = any(token in text for token in name_tokens if len(token) > 3)
            if not name_found:
                return False

    return True


def evaluate_rescue_explainability(results: List[Dict[str, Any]]) -> ExplainabilityCoverageResult:
    """Evaluate rescue allocation explanation coverage."""
    checked = []
    for r in results:
        explanation = r.get("explanation") or r.get("explanation_text") or r.get("reason")
        result_dict = {
            "selected_team_name": r.get("selected_team_name"),
            "selected_resource_name": r.get("selected_resource_name"),
            "distance_km": r.get("distance_km"),
        }
        checks = check_explanation(explanation)
        for c in checks:
            checked.append({
                "scenario_id": r.get("scenario_id", ""),
                "element": c.element,
                "passed": c.passed,
                "detail": c.detail,
                "values_agree": _validate_explanation_against_result(explanation, result_dict) if c.passed else False
            })

    return _build_coverage_result("rescue", checked, results)


def evaluate_relief_explainability(results: List[Dict[str, Any]]) -> ExplainabilityCoverageResult:
    """Evaluate relief allocation explanation coverage."""
    checked = []
    for r in results:
        explanation = r.get("explanation") or r.get("explanation_text") or ""
        result_dict = {
            "selected_resource_name": r.get("selected_warehouse_name"),
            "distance_km": r.get("distance_km"),
        }
        checks = check_explanation(explanation)
        for c in checks:
            checked.append({
                "scenario_id": r.get("scenario_id", ""),
                "element": c.element,
                "passed": c.passed,
                "detail": c.detail,
                "values_agree": _validate_explanation_against_result(explanation, result_dict) if c.passed else False
            })

    return _build_coverage_result("relief", checked, results)


def evaluate_shelter_explainability(results: List[Dict[str, Any]]) -> ExplainabilityCoverageResult:
    """Evaluate shelter allocation explanation coverage."""
    checked = []
    for r in results:
        explanation = r.get("explanation") or r.get("explanation_text") or ""
        result_dict = {
            "selected_resource_name": r.get("selected_shelter_name"),
            "distance_km": r.get("distance_km"),
        }
        checks = check_explanation(explanation)
        for c in checks:
            checked.append({
                "scenario_id": r.get("scenario_id", ""),
                "element": c.element,
                "passed": c.passed,
                "detail": c.detail,
                "values_agree": _validate_explanation_against_result(explanation, result_dict) if c.passed else False
            })

    return _build_coverage_result("shelter", checked, results)


def _build_coverage_result(module: str, checks: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> ExplainabilityCoverageResult:
    explanations = [r for r in results if r.get("explanation") or r.get("explanation_text")]
    checked_count = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    coverage_rate = (passed_count / checked_count * 100) if checked_count > 0 else 0.0

    element_names = set(c["element"] for c in checks)
    element_coverage = {}
    for elem in element_names:
        elem_checks = [c for c in checks if c["element"] == elem]
        elem_passed = sum(1 for c in elem_checks if c["passed"])
        element_coverage[elem] = (elem_passed / len(elem_checks) * 100) if elem_checks else 0.0

    latencies = [r.get("computation_time_ms", 0) for r in results if r.get("computation_time_ms") is not None]
    mean_lat = float(sum(latencies) / len(latencies)) if latencies else None

    return ExplainabilityCoverageResult(
        module=module,
        explanation_count=len(explanations),
        checked_count=checked_count,
        coverage_rate_pct=coverage_rate,
        element_coverage=element_coverage,
        checks=checks,
        mean_latency_ms=mean_lat,
        synthetic_data_note=(
            "Explainability coverage measures structural element presence only. "
            "Does not validate content accuracy, relevance, or human interpretability. "
            "Results do not imply real-world explanation quality."
        ),
    )


def run_explainability_evaluation(
    rescue_results: Optional[List[Dict[str, Any]]] = None,
    relief_results: Optional[List[Dict[str, Any]]] = None,
    shelter_results: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, ExplainabilityCoverageResult]:
    """Run explainability evaluation on results from all modules."""
    results = {}

    if rescue_results:
        results["rescue"] = evaluate_rescue_explainability(rescue_results)
    if relief_results:
        results["relief"] = evaluate_relief_explainability(relief_results)
    if shelter_results:
        results["shelter"] = evaluate_shelter_explainability(shelter_results)

    return results


if __name__ == "__main__":
    results = run_explainability_evaluation()
    for module, result in results.items():
        print(f"{module}: coverage={result.coverage_rate_pct:.1f}%, explanations={result.explanation_count}")