"""
Phase 6 (Day 37-38): Synthetic dataset preparation + model training.
RESEARCH / DEMONSTRATION ONLY – not clinically validated.
"""
import os
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from app.services.simulator import PatientTelemetrySimulator
from app.services.feature_extractor import extract_features, FEATURE_SCHEMA

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml_models")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")


# ------------------------------------------------------------------
# Day 37 – Dataset builder
# ------------------------------------------------------------------
def build_synthetic_dataset(n_patients=200, window_size=10, random_seed=42):
    """
    Build a labelled dataset from simulated vital windows.
    Labels: 0 = no deterioration, 1 = deterioration onset (synthetic).
    Returns X (ndarray), y (ndarray), and a DataFrame for inspection.
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    stable_scenarios   = ["stable"]
    unstable_scenarios = ["arrhythmia_tachycardia", "desaturation_hypoxia", "septic_shock"]

    rows = []
    for pid in range(1, n_patients + 1):
        deteriorating = random.random() < 0.35   # 35% synthetic deterioration rate
        scenario = random.choice(unstable_scenarios if deteriorating else stable_scenarios)
        window = [
            PatientTelemetrySimulator.generate_reading(patient_id=pid, scenario=scenario)
            for _ in range(window_size)
        ]
        feats = extract_features(window)
        row = dict(zip(FEATURE_SCHEMA, feats))
        row["label"] = int(deteriorating)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Document class distribution
    dist = df["label"].value_counts().to_dict()
    print(f"[Dataset] n={len(df)} | class dist: {dist} | features: {len(FEATURE_SCHEMA)}")
    return df


# ------------------------------------------------------------------
# Day 38 – Training + evaluation
# ------------------------------------------------------------------
def train_and_evaluate(df: pd.DataFrame, random_seed=42):
    """
    Train a RandomForest + optional XGBoost model, evaluate both.
    Returns the best model pipeline + evaluation dict.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score,
        f1_score, roc_auc_score, confusion_matrix, average_precision_score,
    )

    X = df[FEATURE_SCHEMA].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=random_seed
    )

    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
        ("clf",     RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=random_seed,
            n_jobs=-1,
        )),
    ])
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, y_pred).tolist()
    eval_results = {
        "model": "RandomForest",
        "n_train": int(len(X_train)),
        "n_test":  int(len(X_test)),
        "accuracy":   round(float(accuracy_score(y_test, y_pred)),   4),
        "precision":  round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall":     round(float(recall_score(y_test, y_pred, zero_division=0)),    4),
        "f1":         round(float(f1_score(y_test, y_pred, zero_division=0)),        4),
        "auroc":      round(float(roc_auc_score(y_test, y_prob)),     4),
        "auprc":      round(float(average_precision_score(y_test, y_prob)), 4),
        "confusion_matrix": cm,
        "disclaimer": (
            "RESEARCH/DEMONSTRATION ONLY. Trained on synthetic data. "
            "Not clinically validated. Do not use for clinical decisions."
        ),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "feature_schema": FEATURE_SCHEMA,
    }

    # Optional XGBoost if available
    try:
        import xgboost as xgb
        xpipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler",  StandardScaler()),
            ("clf",     xgb.XGBClassifier(
                n_estimators=200,
                eval_metric="logloss",
                random_state=random_seed,
                verbosity=0,
                scale_pos_weight=(y_train == 0).sum() / max((y_train == 1).sum(), 1),
            )),
        ])
        xpipe.fit(X_train, y_train)
        xpred = xpipe.predict(X_test)
        xprob = xpipe.predict_proba(X_test)[:, 1]
        eval_results["xgboost_auroc"] = round(float(roc_auc_score(y_test, xprob)), 4)
        eval_results["xgboost_f1"]    = round(float(f1_score(y_test, xpred, zero_division=0)), 4)

        # Use XGBoost if its AUROC is better
        if eval_results["xgboost_auroc"] > eval_results["auroc"]:
            pipe = xpipe
            eval_results["model"] = "XGBoost"
    except ImportError:
        pass

    return pipe, eval_results
