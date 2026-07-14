import os
import json
from datetime import datetime, timezone
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def train_models():
    # Load data
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'incident_priority_synthetic.csv')
    df = pd.read_csv(data_path)

    # Features and Target
    X = df.drop(columns=['priority_level'])
    y = df['priority_level']

    # Preprocessing
    categorical_features = ['incident_type', 'severity']
    numeric_features = ['affected_people', 'injured_people', 'trapped_people', 
                        'vulnerable_people', 'children_count', 'elderly_count', 'waiting_time_hours']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    # Models to evaluate
    models = {
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
        'DecisionTree': DecisionTreeClassifier(random_state=42),
        'RandomForest': RandomForestClassifier(random_state=42),
        'GradientBoosting': GradientBoostingClassifier(random_state=42)
    }

    results = {}
    best_model_name = None
    best_f1 = -1
    best_pipeline = None

    print("Training and evaluating models...")
    for name, model in models.items():
        pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                   ('classifier', model)])
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='macro', zero_division=0)
        rec = recall_score(y_test, y_pred, average='macro', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
        
        # Save results
        results[name] = {
            'accuracy': round(acc, 4),
            'macro_precision': round(prec, 4),
            'macro_recall': round(rec, 4),
            'macro_f1': round(f1, 4)
        }
        
        print(f"[{name}] Acc: {acc:.4f}, F1: {f1:.4f}")
        
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_pipeline = pipeline

    print(f"\nSelected Best Model: {best_model_name} (F1: {best_f1:.4f})")

    # Artifact paths
    artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # Save pipeline
    model_path = os.path.join(artifacts_dir, 'priority_model.joblib')
    joblib.dump(best_pipeline, model_path)
    
    # Save evaluation metrics
    metrics_path = os.path.join(artifacts_dir, 'evaluation_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)

    # Save metadata
    metadata = {
        'model_name': best_model_name,
        'model_version': '1.0.0',
        'training_date': datetime.now(timezone.utc).isoformat(),
        'feature_names': numeric_features + categorical_features,
        'class_names': sorted(y.unique().tolist()),
        'training_size': len(X_train),
        'test_size': len(X_test),
        'best_metrics': results[best_model_name],
        'random_seed': 42
    }
    
    metadata_path = os.path.join(artifacts_dir, 'model_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print("Training complete. Artifacts saved.")

if __name__ == '__main__':
    train_models()
