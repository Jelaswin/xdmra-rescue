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
    """Calculate relief allocation evaluation metrics."""
    if not results:
        return {}
    
    successful = [r for r in results if r.get("success", False)]
    
    fulfilment_pcts = [r.get("fulfilment_pct", 0) for r in successful if r.get("fulfilment_pct") is not None]
    shortages = [r.get("shortage", 0) for r in successful if r.get("shortage") is not None]
    distances = [r.get("distance_km", 0) for r in successful if r.get("distance_km") is not None]
    comp_times = [r.get("computation_time_ms", 0) for r in results if r.get("computation_time_ms") is not None]
    warehouses_used = [len(r.get("warehouses_used", [])) for r in successful]
    
    metrics = {
        "total_scenarios": len(results),
        "successful_allocations": len(successful),
        "success_rate_pct": (len(successful) / len(results) * 100) if results else 0,
    }
    
    if fulfilment_pcts:
        metrics.update({
            "mean_fulfilment_pct": statistics.mean(fulfilment_pcts),
            "median_fulfilment_pct": statistics.median(fulfilment_pcts),
            "min_fulfilment_pct": min(fulfilment_pcts),
            "max_fulfilment_pct": max(fulfilment_pcts),
        })
        if len(fulfilment_pcts) > 1:
            metrics["std_fulfilment_pct"] = statistics.stdev(fulfilment_pcts)
    
    if shortages:
        metrics.update({
            "mean_shortage": statistics.mean(shortages),
            "median_shortage": statistics.median(shortages),
            "max_shortage": max(shortages),
        })
        if len(shortages) > 1:
            metrics["std_shortage"] = statistics.stdev(shortages)
    
    if distances:
        metrics.update({
            "mean_distance_km": statistics.mean(distances),
            "median_distance_km": statistics.median(distances),
        })
    
    if comp_times:
        metrics.update({
            "mean_computation_time_ms": statistics.mean(comp_times),
            "median_computation_time_ms": statistics.median(comp_times),
        })
    
    if warehouses_used:
        metrics.update({
            "mean_warehouses_used": statistics.mean(warehouses_used),
            "max_warehouses_used": max(warehouses_used),
        })
    
    split_allocations = len([r for r in successful if r.get("split_allocation", False)])
    metrics["split_allocation_count"] = split_allocations
    metrics["single_source_success_rate_pct"] = ((len(successful) - split_allocations) / len(successful) * 100) if successful else 0
    
    return metrics


def calculate_shelter_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate shelter allocation evaluation metrics."""
    if not results:
        return {}
    
    successful = [r for r in results if r.get("success", False)]
    
    coverage_pcts = [r.get("population_coverage_pct", 0) for r in successful if r.get("population_coverage_pct") is not None]
    uncovered = [r.get("uncovered_people", 0) for r in successful if r.get("uncovered_people") is not None]
    distances = [r.get("distance_km", 0) for r in successful if r.get("distance_km") is not None]
    comp_times = [r.get("computation_time_ms", 0) for r in results if r.get("computation_time_ms") is not None]
    requirement_matches = [r.get("requirement_match_pct", 0) for r in successful if r.get("requirement_match_pct") is not None]
    shelters_used = [len(r.get("shelters_used", [])) for r in successful]
    
    metrics = {
        "total_scenarios": len(results),
        "successful_allocations": len(successful),
        "success_rate_pct": (len(successful) / len(results) * 100) if results else 0,
    }
    
    if coverage_pcts:
        metrics.update({
            "mean_population_coverage_pct": statistics.mean(coverage_pcts),
            "median_population_coverage_pct": statistics.median(coverage_pcts),
            "min_population_coverage_pct": min(coverage_pcts),
            "max_population_coverage_pct": max(coverage_pcts),
        })
        if len(coverage_pcts) > 1:
            metrics["std_population_coverage_pct"] = statistics.stdev(coverage_pcts)
    
    if uncovered:
        metrics.update({
            "mean_uncovered_people": statistics.mean(uncovered),
            "median_uncovered_people": statistics.median(uncovered),
            "max_uncovered_people": max(uncovered),
        })
        if len(uncovered) > 1:
            metrics["std_uncovered_people"] = statistics.stdev(uncovered)
    
    overcrowding_violations = len([r for r in successful if r.get("overcrowding_violations", 0) > 0])
    metrics["overcrowding_violation_count"] = overcrowding_violations
    metrics["overcrowding_violation_rate_pct"] = (overcrowding_violations / len(successful) * 100) if successful else 0
    
    if distances:
        metrics.update({
            "mean_distance_km": statistics.mean(distances),
            "median_distance_km": statistics.median(distances),
        })
    
    if comp_times:
        metrics.update({
            "mean_computation_time_ms": statistics.mean(comp_times),
            "median_computation_time_ms": statistics.median(comp_times),
        })
    
    if requirement_matches:
        metrics.update({
            "mean_requirement_match_pct": statistics.mean(requirement_matches),
            "median_requirement_match_pct": statistics.median(requirement_matches),
        })
    
    if shelters_used:
        metrics.update({
            "mean_shelters_used": statistics.mean(shelters_used),
            "max_shelters_used": max(shelters_used),
        })
    
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