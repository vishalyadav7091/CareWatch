"""
Phase 6 (Day 36-41): ML feature extraction, training, and inference tests.
RESEARCH / DEMONSTRATION ONLY. No clinical validity claims.
"""
import pytest
import numpy as np
from app import create_app, db
from app.services.feature_extractor import extract_features, FEATURE_SCHEMA, N_FEATURES
from app.services.ml_trainer import build_synthetic_dataset, train_and_evaluate


@pytest.fixture(scope="module")
def app():
    application = create_app("testing")
    with application.app_context():
        yield application


# ------------------------------------------------------------------
# Day 36 – Feature extraction
# ------------------------------------------------------------------
def test_feature_schema_length():
    assert len(FEATURE_SCHEMA) == N_FEATURES
    assert N_FEATURES == 35


def test_extract_features_full_window():
    window = [
        {
            "heart_rate": 72, "spo2": 98.0, "systolic_bp": 120,
            "diastolic_bp": 80, "respiratory_rate": 16, "temperature": 36.8,
            "data_quality": "valid",
        }
        for _ in range(10)
    ]
    feats = extract_features(window)
    assert feats.shape == (N_FEATURES,)
    assert not np.all(np.isnan(feats))


def test_extract_features_empty_window():
    feats = extract_features([])
    assert feats.shape == (N_FEATURES,)
    assert np.all(np.isnan(feats))


def test_extract_features_missing_values():
    window = [
        {"heart_rate": None, "spo2": None, "systolic_bp": None,
         "diastolic_bp": None, "respiratory_rate": None, "temperature": None,
         "data_quality": "invalid"}
    ]
    feats = extract_features(window)
    assert feats.shape == (N_FEATURES,)
    # missing flags should be 1.0
    hr_miss_idx = FEATURE_SCHEMA.index("hr_missing_flag")
    assert feats[hr_miss_idx] == 1.0


def test_no_future_data_leakage():
    """Delta should use only first→last ordering (no future values)."""
    window = [
        {"heart_rate": 60 + i, "spo2": 98.0, "systolic_bp": 120,
         "diastolic_bp": 80, "respiratory_rate": 16, "temperature": 36.8,
         "data_quality": "valid"}
        for i in range(5)
    ]
    feats = extract_features(window)
    hr_delta_idx = FEATURE_SCHEMA.index("hr_delta")
    # Last HR = 64, first HR = 60; delta = 4
    assert abs(feats[hr_delta_idx] - 4.0) < 0.001


# ------------------------------------------------------------------
# Day 37-38 – Dataset + training
# ------------------------------------------------------------------
def test_build_synthetic_dataset_shape():
    df = build_synthetic_dataset(n_patients=20, window_size=5, random_seed=0)
    assert len(df) == 20
    assert "label" in df.columns
    assert set(df["label"].unique()).issubset({0, 1})


def test_train_and_evaluate_returns_metrics():
    df = build_synthetic_dataset(n_patients=60, window_size=5, random_seed=42)
    model, metrics = train_and_evaluate(df, random_seed=42)
    assert model is not None
    for key in ("accuracy", "precision", "recall", "f1", "auroc", "auprc"):
        assert key in metrics, f"Missing metric: {key}"
        assert 0.0 <= metrics[key] <= 1.0
    assert "confusion_matrix" in metrics
    assert "disclaimer" in metrics
    assert "RESEARCH" in metrics["disclaimer"]


def test_model_predict_shape():
    df = build_synthetic_dataset(n_patients=50, window_size=5, random_seed=1)
    model, _ = train_and_evaluate(df, random_seed=1)
    sample = np.random.rand(1, N_FEATURES)
    prob = model.predict_proba(sample)
    assert prob.shape == (1, 2)
    assert 0.0 <= prob[0][1] <= 1.0


# ------------------------------------------------------------------
# Day 40 – ML inference API (integration)
# ------------------------------------------------------------------
def test_ml_status_endpoint(app):
    client = app.test_client()
    r = client.get("/api/v1/ml/status")
    assert r.status_code == 200
    data = r.get_json()
    assert "model_ready" in data


def test_ml_train_endpoint(app):
    client = app.test_client()
    r = client.post("/api/v1/ml/train")
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert "auroc" in data["evaluation"]


def test_ml_infer_no_patient(app):
    client = app.test_client()
    r = client.get("/api/v1/ml/infer/999999")
    assert r.status_code == 404


def test_ml_disclaimer_present(app):
    """Every ML endpoint must include the disclaimer text."""
    client = app.test_client()
    r = client.get("/api/v1/ml/status")
    data = r.get_json()
    if data.get("model_ready"):
        assert "RESEARCH" in data.get("disclaimer", "")
