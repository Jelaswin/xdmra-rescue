"""
Explainability Coverage Evaluation for X-DMRA.

Evaluates X-DMRA algorithm results only. Baseline algorithms (which do not
produce explanations) are reported separately as not supported.

Deterministic structural checks; no LLM grading.

Each metric reports: numerator, denominator, and percentage.
N/A is reported when a check is not applicable to the specific scenario
(e.g., route_risk when no route is involved, limitation when demand is fully met).
"""

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Tuple
import re

XDMRA_ALGORITHMS = {
    "rescue": "xdmra_explainable",
    "relief": "xdmra_relief_allocation",
    "shelter": "xdmra_shelter_allocation",
}


@dataclass
class ElementMetric:
    numerator: int
    denominator: int
    percentage: float
    na_count: int
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "numerator": self.numerator,
            "denominator": self.denominator,
            "percentage": round(self.percentage, 2),
            "na_count": self.na_count,
            "detail": self.detail,
        }


@dataclass
class ExplainabilityCoverageResult:
    module: str
    xdmra_algorithm: str
    scenarios_evaluated: int
    explanations_with_content: int
    total_checks: int
    total_passed: int
    overall_coverage_pct: float
    element_metrics: Dict[str, Dict[str, Any]]
    baseline_support: str
    baseline_note: str
    checks: List[Dict[str, Any]]
    synthetic_data_note: str


def _filter_xdmra_results(results: List[Dict[str, Any]], module: str) -> List[Dict[str, Any]]:
    target = XDMRA_ALGORITHMS.get(module, "")
    return [r for r in results if r.get("algorithm") == target]


def _extract_number(text: str, pattern: str) -> Optional[float]:
    match = re.search(pattern, text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except (ValueError, IndexError):
            pass
    return None


def _normalize_for_check(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value).lower()


def _check_explanation_availability(explanation: Optional[str], result: Dict[str, Any]) -> Tuple[bool, Optional[str], bool]:
    if explanation and len(explanation.strip()) > 20:
        return True, "present", True
    return False, "missing_or_too_short", False


def _check_resource_name(explanation: Optional[str], result: Dict[str, Any]) -> Tuple[bool, Optional[str], bool]:
    if not explanation:
        return False, "no_explanation", False
    text = explanation.lower()

    resource_tokens = ["team", "warehouse", "shelter", "selected", "chosen", "allocated",
                       "recommended", "assigned"]
    found = any(token in text for token in resource_tokens)
    if found:
        return True, "resource_name_present", True

    return False, "no_resource_name_found", False


def _check_distance(explanation: Optional[str], result: Dict[str, Any]) -> Tuple[bool, Optional[str], bool]:
    if not explanation:
        return False, "no_explanation", False
    text = explanation.lower()

    distance_tokens = ["km", "kilometer", "distance", "miles", "m away", "meters away"]
    found = any(token in text for token in distance_tokens)
    if found:
        return True, "distance_present", True

    dist_in_result = result.get("distance_km")
    if dist_in_result is not None and dist_in_result == 0.0:
        return False, "not_applicable_zero_distance", True

    return False, "no_distance_found", False


def _check_relevant_factor(explanation: Optional[str], result: Dict[str, Any]) -> Tuple[bool, Optional[str], bool]:
    if not explanation:
        return False, "no_explanation", False
    text = explanation.lower()

    factor_tokens = [
        "because", "due to", "factor", "reason", "since", "based on",
        "matching", "coverage", "sufficient", "available", "close",
        "skills", "capacity", "distance", "ranked", "score"
    ]
    found = any(token in text for token in factor_tokens)
    if found:
        return True, "relevant_factor_present", True

    return False, "no_decision_factor_found", False


def _check_limitation(explanation: Optional[str], result: Dict[str, Any]) -> Tuple[bool, Optional[str], bool]:
    if not explanation:
        return False, "no_explanation", False
    text = explanation.lower()

    limitation_tokens = [
        "limitation", "constraint", "however", "although", "but", "note",
        "despite", "shortage", "uncovered", "missing", "insufficient",
        "cannot", "not enough", "no warehouse", "no shelter"
    ]
    found = any(token in text for token in limitation_tokens)
    if found:
        return True, "limitation_acknowledged", True

    return False, "no_limitation_noted", False


def _check_route_risk(explanation: Optional[str], result: Dict[str, Any]) -> Tuple[bool, Optional[str], bool]:
    if not explanation:
        return False, "no_explanation", False

    result_route_blocked = result.get("route_blocked")
    result_route_risk = result.get("route_risk", "").lower() if result.get("route_risk") else ""

    if result_route_blocked is True or result_route_risk in ("high", "medium", "blocked"):
        text = explanation.lower()
        risk_tokens = ["route", "road", "blocked", "unsafe", "risk", "high risk", "medium risk"]
        found = any(token in text for token in risk_tokens)
        if found:
            return True, "route_risk_mentioned", True
        return False, "route_risk_not_mentioned_but_present", False

    return False, "not_applicable_no_significant_route_risk", True


def _check_alternative_comparison(explanation: Optional[str], result: Dict[str, Any]) -> Tuple[bool, Optional[str], bool]:
    if not explanation:
        return False, "no_explanation", False
    text = explanation.lower()

    alt_tokens = [
        "alternative", "instead", "other", "option", "another",
        "vs", "versus", "compared", "rather than", "split across",
        "multiple"
    ]
    found = any(token in text for token in alt_tokens)
    if found:
        return True, "alternative_comparison_present", True

    return False, "no_alternative_comparison", False


def _check_stored_value_consistency(
    explanation: Optional[str],
    result: Dict[str, Any]
) -> Tuple[bool, Optional[str], bool]:
    if not explanation or len(explanation) < 10:
        return False, "no_explanation_for_consistency_check", False

    text = explanation

    distance_in_result = result.get("distance_km")
    coverage_in_result = (
        result.get("population_coverage_pct") or
        result.get("fulfilment_pct") or
        result.get("coverage_pct")
    )
    shortage_in_result = result.get("shortage")
    uncovered_in_result = result.get("uncovered_people")

    has_inconsistency = False

    if distance_in_result is not None and distance_in_result > 0:
        dist_in_text = _extract_number(text, r"(\d+\.?\d*)\s*km")
        if dist_in_text is not None and abs(dist_in_text - distance_in_result) > 1.0:
            has_inconsistency = True

    if coverage_in_result is not None and coverage_in_result > 0:
        pct_in_text = _extract_number(text, r"(\d+\.?\d*)\s*%")
        if pct_in_text is not None and abs(pct_in_text - coverage_in_result) > 5.0:
            has_inconsistency = True

    if shortage_in_result is not None and shortage_in_result > 0:
        short_in_text = _extract_number(text, rf"(\d+)\s*(?:unit|item)s?\s*short")
        if short_in_text is not None and abs(short_in_text - shortage_in_result) > 2:
            has_inconsistency = True

    if uncovered_in_result is not None and uncovered_in_result > 0:
        uncov_in_text = _extract_number(text, rf"(\d+)\s*(?:uncovered|remaining)")
        if uncov_in_text is not None and abs(uncov_in_text - uncovered_in_result) > 2:
            has_inconsistency = True

    if has_inconsistency:
        return False, "inconsistency_detected", False

    return True, "values_consistent_within_tolerance", True


ELEMENT_CHECKS = {
    "explanation_availability": _check_explanation_availability,
    "resource_name": _check_resource_name,
    "distance": _check_distance,
    "relevant_factor": _check_relevant_factor,
    "limitation": _check_limitation,
    "route_risk": _check_route_risk,
    "alternative_comparison": _check_alternative_comparison,
    "stored_value_consistency": _check_stored_value_consistency,
}

ELEMENT_LABELS = {
    "explanation_availability": "Explanation availability",
    "resource_name": "Resource-name coverage",
    "distance": "Distance coverage",
    "relevant_factor": "Relevant-factor coverage",
    "limitation": "Limitation coverage",
    "route_risk": "Route-risk coverage",
    "alternative_comparison": "Alternative-comparison coverage",
    "stored_value_consistency": "Stored-value consistency",
}


def evaluate_xdmra_module(
    results: List[Dict[str, Any]],
    module: str,
) -> ExplainabilityCoverageResult:
    xdmra_results = _filter_xdmra_results(results, module)
    target_algo = XDMRA_ALGORITHMS.get(module, "")

    element_raw = {elem: {"passed": 0, "na": 0, "failed": 0} for elem in ELEMENT_CHECKS}
    all_checks = []

    for r in xdmra_results:
        explanation = r.get("explanation")
        has_content = explanation and len(explanation.strip()) > 20

        for elem_name, check_fn in ELEMENT_CHECKS.items():
            passed, detail, applicable = check_fn(explanation, r)

            if not applicable:
                element_raw[elem_name]["na"] += 1
                status = "na"
            elif passed:
                element_raw[elem_name]["passed"] += 1
                status = "pass"
            else:
                element_raw[elem_name]["failed"] += 1
                status = "fail"

            all_checks.append({
                "scenario_id": r.get("scenario_id", ""),
                "algorithm": r.get("algorithm", ""),
                "element": elem_name,
                "status": status,
                "detail": detail,
            })

    element_metrics = {}
    total_passed = 0
    total_denom = 0

    for elem_name, counts in element_raw.items():
        denom = counts["passed"] + counts["failed"]
        na = counts["na"]
        passed = counts["passed"]

        if denom > 0:
            pct = (passed / denom) * 100
        else:
            pct = 0.0

        element_metrics[elem_name] = {
            "numerator": passed,
            "denominator": denom,
            "percentage": round(pct, 2),
            "na_count": na,
            "detail": ELEMENT_LABELS.get(elem_name, elem_name),
        }

        total_passed += passed
        total_denom += denom

    overall_pct = (total_passed / total_denom * 100) if total_denom > 0 else 0.0

    return ExplainabilityCoverageResult(
        module=module,
        xdmra_algorithm=target_algo,
        scenarios_evaluated=len(xdmra_results),
        explanations_with_content=sum(
            1 for r in xdmra_results
            if r.get("explanation") and len(r.get("explanation", "").strip()) > 20
        ),
        total_checks=len(all_checks),
        total_passed=total_passed,
        overall_coverage_pct=round(overall_pct, 2),
        element_metrics=element_metrics,
        baseline_support="not_supported",
        baseline_note="Baseline algorithms do not produce explanations. Only X-DMRA results are evaluated.",
        checks=all_checks,
        synthetic_data_note=(
            "Explainability coverage measures structural element presence only. "
            "Does not validate content accuracy, relevance, or human interpretability. "
            "Results do not imply real-world explanation quality."
        ),
    )


def evaluate_rescue_explainability(results: List[Dict[str, Any]]) -> ExplainabilityCoverageResult:
    return evaluate_xdmra_module(results, "rescue")


def evaluate_relief_explainability(results: List[Dict[str, Any]]) -> ExplainabilityCoverageResult:
    return evaluate_xdmra_module(results, "relief")


def evaluate_shelter_explainability(results: List[Dict[str, Any]]) -> ExplainabilityCoverageResult:
    return evaluate_xdmra_module(results, "shelter")


def run_explainability_evaluation(
    rescue_results: Optional[List[Dict[str, Any]]] = None,
    relief_results: Optional[List[Dict[str, Any]]] = None,
    shelter_results: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, ExplainabilityCoverageResult]:
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
        print(f"{module}: scenarios={result.scenarios_evaluated}, "
              f"explanations={result.explanations_with_content}, "
              f"coverage={result.overall_coverage_pct}%")