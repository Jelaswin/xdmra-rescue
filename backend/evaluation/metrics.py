"""
Evaluation Metrics Calculation.

Calculate rescue, relief, shelter, priority, and explainability metrics.
"""

from typing import List, Dict, Any, Optional
import statistics


def calculate_rescue_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate rescue allocation evaluation metrics."""
    if not results:
        return {}
    
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]
    
    distances = [r.get("distance_km", 0) for r in successful if r.get("distance_km") is not None]
    skill_matches = [r.get("skill_match_pct", 0) for r in successful if r.get("skill_match_pct") is not None]
    equip_matches = [r.get("equipment_match_pct", 0) for r in successful if r.get("equipment_match_pct") is not None]
    comp_times = [r.get("computation_time_ms", 0) for r in results if r.get("computation_time_ms") is not None]
    
    workloads = [r.get("selected_team_workload", 0) for r in successful if r.get("selected_team_workload") is not None]
    
    metrics = {
        "total_scenarios": len(results),
        "successful_allocations": len(successful),
        "failed_allocations": len(failed),
        "success_rate_pct": (len(successful) / len(results) * 100) if results else 0,
    }
    
    if distances:
        metrics.update({
            "mean_distance_km": statistics.mean(distances),
            "median_distance_km": statistics.median(distances),
            "min_distance_km": min(distances),
            "max_distance_km": max(distances),
        })
        if len(distances) > 1:
            metrics["std_distance_km"] = statistics.stdev(distances)
    
    if skill_matches:
        metrics.update({
            "mean_skill_match_pct": statistics.mean(skill_matches),
            "median_skill_match_pct": statistics.median(skill_matches),
        })
    
    if equip_matches:
        metrics.update({
            "mean_equipment_match_pct": statistics.mean(equip_matches),
            "median_equipment_match_pct": statistics.median(equip_matches),
        })
    
    if comp_times:
        metrics.update({
            "mean_computation_time_ms": statistics.mean(comp_times),
            "median_computation_time_ms": statistics.median(comp_times),
            "min_computation_time_ms": min(comp_times),
            "max_computation_time_ms": max(comp_times),
        })
        if len(comp_times) > 1:
            metrics["std_computation_time_ms"] = statistics.stdev(comp_times)
    
    if workloads:
        metrics.update(calculate_workload_fairness_metrics(workloads))
    
    critical_scenarios = [r for r in results if r.get("priority_level") == "critical"]
    if critical_scenarios:
        critical_success = len([r for r in critical_scenarios if r.get("success")])
        metrics["critical_allocation_success_rate_pct"] = (critical_success / len(critical_scenarios) * 100) if critical_scenarios else 0
    
    return metrics


def calculate_workload_fairness_metrics(workloads: List[int]) -> Dict[str, Any]:
    """Calculate workload fairness metrics including Jain's fairness index."""
    if not workloads:
        return {}
    
    n = len(workloads)
    if n == 0:
        return {}
    
    mean_workload = statistics.mean(workloads)
    max_workload = max(workloads)
    min_workload = min(workloads)
    workload_range = max_workload - min_workload
    
    std_workload = statistics.stdev(workloads) if n > 1 else 0
    
    if mean_workload > 0:
        jain_numerator = sum(workloads) ** 2
        jain_denominator = n * sum(w ** 2 for w in workloads)
        jains_fairness = jain_numerator / jain_denominator if jain_denominator > 0 else 0
    else:
        jains_fairness = 0
    
    return {
        "mean_team_workload": mean_workload,
        "max_team_workload": max_workload,
        "min_team_workload": min_workload,
        "workload_range": workload_range,
        "std_team_workload": std_workload,
        "jains_fairness_index": jains_fairness,
    }


def calculate_relief_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate relief allocation evaluation metrics.

    Metrics cover ALL scenarios (not only successful ones) to avoid
    internal inconsistencies between reported fulfilment and shortage.

    Definitions:
    - allocation_success: positive total allocated (produced a usable plan)
    - fully_fulfilled: total_shortage == 0
    - partial_fulfilment: allocated > 0 and shortage > 0
    - failed: allocated == 0 with positive demand
    """
    if not results:
        return {}

    total = len(results)

    # Every scenario has fulfilment_pct and shortage from the experiment runner.
    all_fulfilments = [r.get("fulfilment_pct", 0) for r in results if r.get("fulfilment_pct") is not None]
    all_shortages = [r.get("shortage", 0) for r in results if r.get("shortage") is not None]

    # Count by fulfilment category (all scenarios, not just successful)
    fully_fulfilled_count = sum(1 for r in results if r.get("shortage", 0) == 0 and r.get("success", False))
    partial_fulfilment_count = sum(
        1 for r in results if r.get("success", False) and r.get("shortage", 0) > 0
    )
    failed_count = sum(1 for r in results if not r.get("success", False))
    allocation_success_count = sum(1 for r in results if r.get("success", False))

    # Macro fulfilment: mean over ALL scenarios
    macro_fulfilment = statistics.mean(all_fulfilments) if all_fulfilments else 0.0

    # Weighted fulfilment: total allocated / total requested across all scenarios.
    # When results contain total_requested, use it directly.
    # Otherwise derive from fulfilment_pct and shortage (inverse of fulfilment formula).
    total_allocated = 0.0
    total_requested = 0.0
    fulfilment_sum_for_weighted = 0.0
    for r in results:
        req = r.get("total_requested", 0)
        fulf = r.get("fulfilment_pct", 0)
        short = r.get("shortage", 0)
        if req > 0:
            total_requested += req
            total_allocated += req * (fulf / 100.0)
        elif fulf < 100:
            derived_req = short / (1 - fulf / 100.0) if fulf < 100 else short
            total_requested += derived_req
            total_allocated += derived_req * (fulf / 100.0)
        else:
            fulfilment_sum_for_weighted += fulf

    if total_requested > 0:
        weighted_fulfilment = (total_allocated / total_requested * 100)
    elif fulfilment_sum_for_weighted > 0:
        count_100 = sum(1 for r in results if r.get("total_requested", 0) == 0 and r.get("fulfilment_pct", 0) == 100)
        weighted_fulfilment = fulfilment_sum_for_weighted / len(results) if len(results) > 0 else 0.0
    else:
        weighted_fulfilment = macro_fulfilment

    weighted_fulfilment = round(weighted_fulfilment, 4)

    # Shortage stats over all scenarios
    mean_shortage = statistics.mean(all_shortages) if all_shortages else 0.0
    total_shortage = sum(all_shortages)

    successful = [r for r in results if r.get("success", False)]
    distances = [r.get("distance_km", 0) for r in successful if r.get("distance_km") is not None]
    comp_times = [r.get("computation_time_ms", 0) for r in results if r.get("computation_time_ms") is not None]
    warehouses_used = [len(r.get("warehouses_used", [])) for r in successful]

    metrics = {
        "total_scenarios": total,
        "allocation_success_count": allocation_success_count,
        "fully_fulfilled_count": fully_fulfilled_count,
        "partial_fulfilment_count": partial_fulfilment_count,
        "failed_count": failed_count,
        "success_rate_pct": (allocation_success_count / total * 100) if total else 0,
        # Macro: mean fulfilment over ALL scenarios
        "macro_fulfilment_pct": round(macro_fulfilment, 4),
        # Weighted: total allocated / total requested
        "weighted_fulfilment_pct": round(weighted_fulfilment, 4),
        # Shortage
        "mean_shortage": round(mean_shortage, 4),
        "total_shortage": int(total_shortage),
        "max_shortage": max(all_shortages) if all_shortages else 0,
    }

    if len(all_fulfilments) > 1:
        metrics["std_fulfilment_pct"] = round(statistics.stdev(all_fulfilments), 4)

    if len(all_shortages) > 1:
        metrics["std_shortage"] = round(statistics.stdev(all_shortages), 4)

    if distances:
        metrics.update({
            "mean_distance_km": round(statistics.mean(distances), 4),
            "median_distance_km": round(statistics.median(distances), 4),
        })

    if comp_times:
        metrics.update({
            "mean_computation_time_ms": round(statistics.mean(comp_times), 4),
            "median_computation_time_ms": round(statistics.median(comp_times), 4),
            "min_computation_time_ms": round(min(comp_times), 4),
            "max_computation_time_ms": round(max(comp_times), 4),
        })

    if warehouses_used:
        metrics.update({
            "mean_warehouses_used": round(statistics.mean(warehouses_used), 4),
            "max_warehouses_used": max(warehouses_used),
        })

    stock_violations = sum(r.get("stock_violations", 0) for r in results)
    metrics["total_stock_violations"] = stock_violations

    split_allocations = len([r for r in successful if r.get("split_allocation", False)])
    metrics["split_allocation_count"] = split_allocations
    metrics["single_source_success_rate_pct"] = (
        ((allocation_success_count - split_allocations) / allocation_success_count * 100)
        if allocation_success_count else 0
    )

    return metrics


def calculate_shelter_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate shelter allocation evaluation metrics.

    Metrics cover ALL scenarios (not only successful ones) to avoid
    internal inconsistencies between reported coverage and uncovered.

    Definitions:
    - allocation_success: positive allocated population (produced a usable plan)
    - fully_covered: uncovered == 0 and allocation_success
    - partially_covered: uncovered > 0 and allocation_success
    - failed: no allocation with positive demand
    """
    if not results:
        return {}

    total = len(results)

    all_coverages = [r.get("population_coverage_pct", 0) for r in results if r.get("population_coverage_pct") is not None]
    all_uncovered = [r.get("uncovered_people", 0) for r in results if r.get("uncovered_people") is not None]

    # Macro coverage: mean over ALL scenarios
    macro_coverage = statistics.mean(all_coverages) if all_coverages else 0.0

    # Weighted coverage: total allocated / total displaced
    total_displaced = 0.0
    total_allocated = 0.0
    for r in results:
        disp = r.get("total_displaced_people", 0)
        alloc = r.get("total_allocated_population", 0)
        if disp > 0:
            total_displaced += disp
            total_allocated += alloc
        elif not r.get("success", False):
            total_displaced += r.get("uncovered_people", 0)

    weighted_coverage = (total_allocated / total_displaced * 100) if total_displaced > 0 else 0.0

    allocation_success_count = sum(1 for r in results if r.get("success", False))
    fully_covered_count = sum(1 for r in results if r.get("success", False) and r.get("uncovered_people", 0) == 0)
    partial_covered_count = sum(
        1 for r in results if r.get("success", False) and r.get("uncovered_people", 0) > 0
    )
    failed_count = sum(1 for r in results if not r.get("success", False))

    mean_uncovered = statistics.mean(all_uncovered) if all_uncovered else 0.0
    total_uncovered = sum(all_uncovered)

    successful = [r for r in results if r.get("success", False)]
    distances = [r.get("distance_km", 0) for r in successful if r.get("distance_km") is not None]
    comp_times = [r.get("computation_time_ms", 0) for r in results if r.get("computation_time_ms") is not None]
    shelters_used = [len(r.get("shelters_used", [])) for r in successful]

    # Medical requirement: only over scenarios that require it
    med_required = [r for r in results if r.get("total_displaced_people", 0) > 0 and
                    r.get("population_coverage_pct", 0) >= 0]
    med_denom = sum(1 for r in results if r.get("total_displaced_people", 0) > 0)
    med_sat_count = sum(1 for r in results if r.get("medical_requirement_satisfied", False))
    med_match_pct = (med_sat_count / med_denom * 100) if med_denom > 0 else None

    # Accessibility requirement: only over scenarios that require it
    acc_denom = med_denom
    acc_sat_count = sum(1 for r in results if r.get("accessibility_requirement_satisfied", False))
    acc_match_pct = (acc_sat_count / acc_denom * 100) if acc_denom > 0 else None

    metrics = {
        "total_scenarios": total,
        "allocation_success_count": allocation_success_count,
        "fully_covered_count": fully_covered_count,
        "partial_covered_count": partial_covered_count,
        "failed_count": failed_count,
        "success_rate_pct": (allocation_success_count / total * 100) if total else 0,
        # Macro: mean coverage over ALL scenarios
        "macro_population_coverage_pct": round(macro_coverage, 4),
        # Weighted: total allocated / total displaced
        "weighted_population_coverage_pct": round(weighted_coverage, 4),
        # Uncovered
        "mean_uncovered_people": round(mean_uncovered, 4),
        "total_uncovered_people": int(total_uncovered),
        "max_uncovered_people": max(all_uncovered) if all_uncovered else 0,
    }

    if len(all_coverages) > 1:
        metrics["std_population_coverage_pct"] = round(statistics.stdev(all_coverages), 4)

    if len(all_uncovered) > 1:
        metrics["std_uncovered_people"] = round(statistics.stdev(all_uncovered), 4)

    critical_cases = sum(1 for r in successful if r.get("overcrowding_risk_level") == "critical")
    metrics["critical_overcrowding_cases"] = critical_cases

    overcrowding_violations = sum(r.get("overcrowding_violations", 0) for r in successful)
    metrics["overcrowding_violation_count"] = overcrowding_violations
    metrics["overcrowding_violation_rate_pct"] = (
        (overcrowding_violations / allocation_success_count * 100) if allocation_success_count else 0
    )

    if distances:
        metrics.update({
            "mean_distance_km": round(statistics.mean(distances), 4),
            "median_distance_km": round(statistics.median(distances), 4),
        })

    if comp_times:
        metrics.update({
            "mean_computation_time_ms": round(statistics.mean(comp_times), 4),
            "median_computation_time_ms": round(statistics.median(comp_times), 4),
            "min_computation_time_ms": round(min(comp_times), 4),
            "max_computation_time_ms": round(max(comp_times), 4),
        })

    if shelters_used:
        metrics.update({
            "mean_shelters_used": round(statistics.mean(shelters_used), 4),
            "max_shelters_used": max(shelters_used),
        })

    if med_match_pct is not None:
        metrics["medical_requirement_match_pct"] = round(med_match_pct, 4)
    else:
        metrics["medical_requirement_match_pct"] = None

    if acc_match_pct is not None:
        metrics["accessibility_requirement_match_pct"] = round(acc_match_pct, 4)
    else:
        metrics["accessibility_requirement_match_pct"] = None

    return metrics


def calculate_priority_model_metrics(predictions: List[Dict[str, Any]], actual_labels: List[str]) -> Dict[str, Any]:
    """Calculate priority model evaluation metrics."""
    if not predictions or not actual_labels:
        return {}
    
    if len(predictions) != len(actual_labels):
        return {"error": "Predictions and actuals must have same length"}
    
    correct = sum(1 for p, a in zip(predictions, actual_labels) if p == a)
    accuracy = (correct / len(actual_labels)) * 100 if actual_labels else 0
    
    classes = sorted(set(actual_labels))
    class_metrics = {}
    
    for cls in classes:
        true_positives = sum(1 for p, a in zip(predictions, actual_labels) if p == cls and a == cls)
        false_positives = sum(1 for p, a in zip(predictions, actual_labels) if p == cls and a != cls)
        false_negatives = sum(1 for p, a in zip(predictions, actual_labels) if p != cls and a == cls)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        class_metrics[cls] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "support": actual_labels.count(cls)
        }
    
    macro_precision = statistics.mean([m["precision"] for m in class_metrics.values()])
    macro_recall = statistics.mean([m["recall"] for m in class_metrics.values()])
    macro_f1 = statistics.mean([m["f1_score"] for m in class_metrics.values()])
    
    weights = [class_metrics[c]["support"] for c in classes]
    weight_sum = sum(weights)
    weighted_f1 = sum(class_metrics[c]["f1_score"] * class_metrics[c]["support"] for c in classes) / weight_sum if weight_sum > 0 else 0
    
    confusion = {}
    for true_cls in classes:
        confusion[true_cls] = {}
        for pred_cls in classes:
            confusion[true_cls][pred_cls] = sum(1 for p, a in zip(predictions, actual_labels) if p == pred_cls and a == true_cls)
    
    return {
        "accuracy": accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1_score": macro_f1,
        "weighted_f1_score": weighted_f1,
        "per_class_metrics": class_metrics,
        "confusion_matrix": confusion,
        "total_samples": len(actual_labels),
        "class_count": len(classes),
    }


def calculate_explainability_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate explainability coverage metrics."""
    if not results:
        return {}
    
    total = len(results)
    with_explanation = len([r for r in results if r.get("has_explanation", False)])
    
    explanation_presence_pct = (with_explanation / total * 100) if total > 0 else 0
    
    has_resource_name = len([r for r in results if r.get("has_resource_name", False)])
    has_distance = len([r for r in results if r.get("has_distance_info", False)])
    has_factors = len([r for r in results if r.get("has_factors_list", False)])
    has_limitations = len([r for r in results if r.get("has_limitations", False)])
    has_route_risk = len([r for r in results if r.get("has_route_risk", False)])
    has_alternatives = len([r for r in results if r.get("has_alternatives", False)])
    is_consistent = len([r for r in results if r.get("is_consistent", False)])
    
    return {
        "total_recommendations": total,
        "with_explanation_count": with_explanation,
        "explanation_availability_pct": explanation_presence_pct,
        "has_resource_name_pct": (has_resource_name / total * 100) if total > 0 else 0,
        "has_distance_info_pct": (has_distance / total * 100) if total > 0 else 0,
        "has_factors_list_pct": (has_factors / total * 100) if total > 0 else 0,
        "has_limitations_pct": (has_limitations / total * 100) if total > 0 else 0,
        "has_route_risk_pct": (has_route_risk / total * 100) if total > 0 else 0,
        "has_alternatives_pct": (has_alternatives / total * 100) if total > 0 else 0,
        "consistency_rate_pct": (is_consistent / total * 100) if total > 0 else 0,
    }


def calculate_latency_summary(latencies: List[float]) -> Dict[str, Any]:
    """Calculate latency statistics summary."""
    if not latencies:
        return {}
    
    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)
    
    p95_idx = int(n * 0.95)
    p95 = sorted_latencies[p95_idx] if p95_idx < n else sorted_latencies[-1]
    
    return {
        "mean_ms": statistics.mean(latencies),
        "median_ms": statistics.median(latencies),
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "std_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
        "p95_ms": p95,
        "count": len(latencies),
    }