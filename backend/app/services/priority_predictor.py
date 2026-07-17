import os
import json
import joblib
import pandas as pd
from datetime import datetime, timezone
from app.models import Incident
from pydantic import BaseModel
from typing import Dict, Any, Optional

class MLPredictionResponse(BaseModel):
    predicted_priority: str
    confidence: float
    class_probabilities: Dict[str, float]
    model_name: str
    model_version: str

# Global cache for the model and metadata
_model_pipeline = None
_model_metadata = None

def load_model():
    global _model_pipeline, _model_metadata
    if _model_pipeline is not None and _model_metadata is not None:
        return True

    artifacts_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'artifacts')
    model_path = os.path.join(artifacts_dir, 'priority_model.joblib')
    metadata_path = os.path.join(artifacts_dir, 'model_metadata.json')

    if not os.path.exists(model_path) or not os.path.exists(metadata_path):
        return False

    try:
        _model_pipeline = joblib.load(model_path)
        with open(metadata_path, 'r') as f:
            _model_metadata = json.load(f)
        return True
    except Exception as e:
        print(f"Failed to load ML model: {e}")
        return False

def get_model_pipeline():
    """Return the cached model pipeline, loading it if necessary. Raises if not available."""
    if not load_model():
        raise RuntimeError(
            f"Priority model not loaded. Ensure artifacts exist at: "
            f"'{os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'artifacts')}'. "
            f"Required files: priority_model.joblib, model_metadata.json"
        )
    return _model_pipeline


def get_model_info() -> Dict[str, Any]:
    loaded = load_model()
    if not loaded:
        return {"loaded": False, "message": "Model artifacts not found or failed to load."}
        
    return {
        "loaded": True,
        "model_name": _model_metadata.get("model_name", "Unknown"),
        "model_version": _model_metadata.get("model_version", "Unknown"),
        "features": _model_metadata.get("feature_names", []),
        "classes": _model_metadata.get("class_names", []),
        "evaluation_metrics": _model_metadata.get("best_metrics", {}),
        "training_dataset_type": "Synthetic (Development only)",
        "training_dataset_size": _model_metadata.get("training_size", 0)
    }

def calculate_waiting_time_hours(created_at: datetime) -> float:
    if not created_at:
        return 0.0
    now = datetime.now(timezone.utc)
    created_utc = created_at.replace(tzinfo=timezone.utc) if created_at.tzinfo is None else created_at
    delta_seconds = (now - created_utc).total_seconds()
    return max(0.0, delta_seconds / 3600.0)

def predict_priority(incident: Incident) -> Optional[MLPredictionResponse]:
    if not load_model():
        return None

    # Prepare feature dictionary matching training data
    waiting_time = calculate_waiting_time_hours(incident.created_at)
    
    features = {
        'incident_type': [incident.incident_type],
        'severity': [incident.severity.value if hasattr(incident.severity, 'value') else incident.severity],
        'affected_people': [incident.affected_people],
        'injured_people': [incident.injured_people],
        'trapped_people': [incident.trapped_people],
        'vulnerable_people': [incident.vulnerable_people],
        'children_count': [incident.children_count],
        'elderly_count': [incident.elderly_count],
        'waiting_time_hours': [waiting_time]
    }
    
    df = pd.DataFrame(features)
    
    try:
        # Predict
        pred_class_idx = _model_pipeline.predict(df)[0]
        # Some sklearn models return directly the string if it was fitted with strings
        pred_class = str(pred_class_idx)
        
        # Probabilities
        if hasattr(_model_pipeline, "predict_proba"):
            probas = _model_pipeline.predict_proba(df)[0]
            classes = _model_pipeline.classes_
            class_probs = {str(c): round(float(p), 4) for c, p in zip(classes, probas)}
            confidence = class_probs.get(pred_class, 0.0)
        else:
            class_probs = {pred_class: 1.0}
            confidence = 1.0
            
        return MLPredictionResponse(
            predicted_priority=pred_class,
            confidence=confidence,
            class_probabilities=class_probs,
            model_name=_model_metadata.get("model_name", "Unknown"),
            model_version=_model_metadata.get("model_version", "Unknown")
        )
    except Exception as e:
        print(f"Prediction failed: {e}")
        return None

def compare_priorities(rule_level: str, ml_level: str) -> Dict[str, Any]:
    levels = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
    
    rule_idx = levels.get(rule_level.lower(), 0)
    ml_idx = levels.get(ml_level.lower(), 0)
    
    diff = abs(rule_idx - ml_idx)
    
    if diff == 0:
        status = "agreement"
        req_review = False
        msg = "Rule-based engine and ML model completely agree on the priority level."
    elif diff == 1:
        status = "minor_disagreement"
        req_review = True
        msg = "The ML model predicts a priority level one step different than the rule-based engine."
    else:
        status = "major_disagreement"
        req_review = True
        msg = f"Major disagreement! The ML model differs by {diff} levels from the rule-based engine."
        
    return {
        "agreement_status": status,
        "requires_officer_review": req_review,
        "comparison_message": msg
    }
