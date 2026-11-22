"""
Phase 6 (Day 39): Model packaging – train, save, and load.
RESEARCH / DEMONSTRATION ONLY.
"""
import os
import json
import joblib
from datetime import datetime, timezone

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml_models")
MODEL_PATH = os.path.join(MODEL_DIR, "carewatch_model.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")
MODEL_VERSION = "1.0.0-demo"

_model_cache = None


def train_and_save():
    """
    Build synthetic dataset, train model, save to disk.
    Returns evaluation dict.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    from app.services.ml_trainer import build_synthetic_dataset, train_and_evaluate

    df = build_synthetic_dataset(n_patients=300, window_size=10)
    model, eval_results = train_and_evaluate(df)

    # Day 39: save pipeline + metadata
    joblib.dump(model, MODEL_PATH)
    eval_results["version"] = MODEL_VERSION
    eval_results["model_path"] = MODEL_PATH
    with open(METADATA_PATH, "w") as f:
        json.dump(eval_results, f, indent=2)

    global _model_cache
    _model_cache = model
    print(f"[ML] Model saved → {MODEL_PATH}")
    print(f"[ML] AUROC={eval_results['auroc']} F1={eval_results['f1']} Model={eval_results['model']}")
    return eval_results


def load_model():
    """Return cached model or load from disk. Returns None if not trained yet."""
    global _model_cache
    if _model_cache is not None:
        return _model_cache
    if os.path.exists(MODEL_PATH):
        try:
            _model_cache = joblib.load(MODEL_PATH)
            return _model_cache
        except Exception as e:
            print(f"[ML] Failed to load model: {e}")
    return None


def get_metadata():
    """Return model metadata dict or None."""
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return None
