"""
Priority Model Evaluation.

Evaluates the existing trained priority model without retraining.
Does not modify model artifacts or write to stable directories.

SYNTHETIC DATA DISCLAIMER:
All model training and evaluation uses synthetic/generated data.
Results do not represent real-world operational performance.
No claim of statistical significance is made.
"""

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.priority_predictor import load_model, _model_pipeline, _model_metadata


MODEL_ARTIFACT_DIR = Path(__file__).parent.parent / "ml" / "artifacts"
ML_DATA_DIR = Path(__file__).parent.parent / "ml" / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "ml" / "evaluation_output"


@dataclass
class PriorityEvaluationResult:
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float
    confusion_matrix: Dict[str, int]
    per_class_metrics: Dict[str, Dict[str, float]]
    training_accuracy: Optional[float]
    evaluation_accuracy: Optional[float]
    prediction_latency_ms_mean: float
    prediction_latency_ms_median: float
    prediction_latency_ms_std: float
    prediction_latency_ms_min: float
    prediction_latency_ms_max: float
    prediction_latency_ms_p95: float
    rule_ml_agreement_rate: float
    rule_ml_disagreement_count: int
    total_samples: int
    synthetic_data_note: str
    overfitting_concern_note: str
    evaluation_timestamp: str


def _build_confusion_matrix(predictions: List[str], actuals: List[str]) -> Dict[str, int]:
    classes = sorted(set(predictions + actuals))
    matrix = {}
    for true_cls in classes:
        for pred_cls in classes:
            key = f"true_{true_cls}_pred_{pred_cls}"
            matrix[key] = sum(1 for p, a in zip(predictions, actuals) if a == true_cls and p == pred_cls)
    return matrix


def _calculate_latency_stats(latencies: List[float]) -> Dict[str, float]:
    if not latencies:
        return {"mean": 0.0, "median": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0}
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    return {
        "mean": float(np.mean(latencies)),
        "median": float(np.median(latencies)),
        "std": float(np.std(latencies)) if n > 1 else 0.0,
        "min": float(np.min(latencies)),
        "max": float(np.max(latencies)),
        "p95": float(np.percentile(latencies, 95)),
    }


def _rule_based_priority(row: pd.Series) -> str:
    affected = int(row.get("affected_people", 0) or 0)
    injured = int(row.get("injured_people", 0) or 0)
    trapped = int(row.get("trapped_people", 0) or 0)
    severity = str(row.get("severity", "medium") or "medium").lower()

    score = affected * 1 + injured * 3 + trapped * 5

    if severity == "critical" or score >= 200:
        return "critical"
    elif severity == "high" or score >= 100:
        return "high"
    elif severity == "medium" or score >= 30:
        return "medium"
    else:
        return "low"


def evaluate_priority_model(
    dataset_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> PriorityEvaluationResult:
    """Evaluate the priority model on the synthetic dataset.

    Uses the production model loading from app.services.priority_predictor.
    Does NOT retrain, regenerate data, or modify artifacts.
    """
    dataset_path = dataset_path or (ML_DATA_DIR / "incident_priority_synthetic.csv")
    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if not load_model():
        return _error_result("Failed to load production model")

    if not dataset_path.exists():
        return _error_result(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)
    df.columns = df.columns.str.strip()

    required_cols = ["affected_people", "injured_people", "trapped_people", "priority_level"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return _error_result(f"Missing columns: {missing}")

    feature_cols = [
        "affected_people", "injured_people", "trapped_people",
        "vulnerable_people", "children_count", "elderly_count",
        "waiting_time_hours", "incident_type", "severity"
    ]
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0

    X = df[feature_cols].copy()
    y_true = df["priority_level"].tolist()

    predictions = []
    latencies = []

    for i in range(len(X)):
        row_df = X.iloc[i:i+1].copy()
        for col in ["incident_type", "severity"]:
            if col in row_df.columns:
                row_df[col] = [str(row_df[col].iloc[0])]

        start = time.perf_counter()
        try:
            pred = _model_pipeline.predict(row_df)[0]
        except Exception:
            pred = "medium"
        latency_ms = (time.perf_counter() - start) * 1000
        predictions.append(str(pred))
        latencies.append(latency_ms)

    actual_labels = [str(l) for l in y_true]
    classes = sorted(set(actual_labels))

    correct = sum(1 for p, a in zip(predictions, actual_labels) if p == a)
    accuracy = (correct / len(actual_labels)) * 100 if actual_labels else 0.0

    class_metrics = {}
    for cls in classes:
        tp = sum(1 for p, a in zip(predictions, actual_labels) if p == cls and a == cls)
        fp = sum(1 for p, a in zip(predictions, actual_labels) if p == cls and a != cls)
        fn = sum(1 for p, a in zip(predictions, actual_labels) if p != cls and a == cls)

        precision_val = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall_val = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_val = 2 * (precision_val * recall_val) / (precision_val + recall_val) if (precision_val + recall_val) > 0 else 0.0

        class_metrics[cls] = {
            "precision": float(precision_val),
            "recall": float(recall_val),
            "f1_score": float(f1_val),
            "support": int(actual_labels.count(cls)),
        }

    macro_precision = float(np.mean([m["precision"] for m in class_metrics.values()])) if class_metrics else 0.0
    macro_recall = float(np.mean([m["recall"] for m in class_metrics.values()])) if class_metrics else 0.0
    macro_f1 = float(np.mean([m["f1_score"] for m in class_metrics.values()])) if class_metrics else 0.0

    weights = [class_metrics[c]["support"] for c in classes]
    weight_sum = sum(weights)
    weighted_f1 = float(sum(class_metrics[c]["f1_score"] * class_metrics[c]["support"] for c in classes) / weight_sum) if weight_sum > 0 else 0.0

    confusion = _build_confusion_matrix(predictions, actual_labels)

    lat_stats = _calculate_latency_stats(latencies)

    rule_predictions = [_rule_based_priority(row) for _, row in df.iterrows()]
    agreement_count = sum(1 for r, p in zip(rule_predictions, predictions) if r == p)
    agreement_rate = (agreement_count / len(predictions)) * 100 if predictions else 0.0
    disagreement_count = len(predictions) - agreement_count

    training_accuracy = None
    if _model_metadata:
        best_metrics = _model_metadata.get("best_metrics", {})
        training_accuracy = best_metrics.get("accuracy")

    result = PriorityEvaluationResult(
        accuracy=float(accuracy),
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        macro_f1=macro_f1,
        weighted_f1=weighted_f1,
        confusion_matrix=confusion,
        per_class_metrics=class_metrics,
        training_accuracy=training_accuracy,
        evaluation_accuracy=float(accuracy),
        prediction_latency_ms_mean=lat_stats["mean"],
        prediction_latency_ms_median=lat_stats["median"],
        prediction_latency_ms_std=lat_stats["std"],
        prediction_latency_ms_min=lat_stats["min"],
        prediction_latency_ms_max=lat_stats["max"],
        prediction_latency_ms_p95=lat_stats["p95"],
        rule_ml_agreement_rate=agreement_rate,
        rule_ml_disagreement_count=disagreement_count,
        total_samples=len(predictions),
        synthetic_data_note=(
            "Model trained and evaluated on synthetic/generated data only. "
            "Results do not reflect real-world disaster response performance. "
            "No statistical significance claim is made."
        ),
        overfitting_concern_note=(
            f"Training accuracy ({training_accuracy:.1f}%) vs "
            f"Evaluation accuracy ({accuracy:.1f}%). "
            f"Difference may indicate overfitting when using synthetic data."
        ) if training_accuracy else "Training accuracy not available for comparison.",
        evaluation_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    output_file = output_dir / "priority_model_evaluation.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(asdict(result), f, indent=2, default=str)

    return result


def _error_result(message: str) -> PriorityEvaluationResult:
    return PriorityEvaluationResult(
        accuracy=0.0, macro_precision=0.0, macro_recall=0.0, macro_f1=0.0, weighted_f1=0.0,
        confusion_matrix={}, per_class_metrics={}, training_accuracy=None,
        evaluation_accuracy=None, prediction_latency_ms_mean=0.0,
        prediction_latency_ms_median=0.0, prediction_latency_ms_std=0.0,
        prediction_latency_ms_min=0.0, prediction_latency_ms_max=0.0,
        prediction_latency_ms_p95=0.0, rule_ml_agreement_rate=0.0,
        rule_ml_disagreement_count=0, total_samples=0,
        synthetic_data_note="Evaluation failed: " + message,
        overfitting_concern_note="",
        evaluation_timestamp=datetime.now(timezone.utc).isoformat(),
    )


def run_priority_evaluation(output_dir: Optional[Path] = None) -> PriorityEvaluationResult:
    """Convenience function to run priority evaluation with defaults."""
    return evaluate_priority_model(output_dir=output_dir)


if __name__ == "__main__":
    result = run_priority_evaluation()
    print(json.dumps(asdict(result), indent=2, default=str))