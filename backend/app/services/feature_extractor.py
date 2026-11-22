"""
Phase 6 (Day 36): Time-windowed feature extraction for AI early-warning.
All features are for RESEARCH / DEMONSTRATION purposes only.
"""
import numpy as np


FEATURE_SCHEMA = [
    "hr_mean", "hr_std", "hr_min", "hr_max", "hr_delta",
    "spo2_mean", "spo2_std", "spo2_min", "spo2_max", "spo2_delta",
    "sbp_mean", "sbp_std", "sbp_min", "sbp_max", "sbp_delta",
    "dbp_mean", "dbp_std", "dbp_min", "dbp_max", "dbp_delta",
    "rr_mean",  "rr_std",  "rr_min",  "rr_max",  "rr_delta",
    "temp_mean","temp_std","temp_min","temp_max","temp_delta",
    "shock_index_mean",    # sbp / hr (experimental, requires both valid)
    "hr_missing_flag",
    "spo2_missing_flag",
    "sbp_missing_flag",
    "data_quality_valid_ratio",
]

N_FEATURES = len(FEATURE_SCHEMA)


def _safe_stats(vals):
    """Return (mean, std, min, max, delta) for a 1-D array; NaN when empty."""
    arr = np.array([v for v in vals if v is not None], dtype=float)
    if len(arr) == 0:
        return np.nan, np.nan, np.nan, np.nan, np.nan
    delta = float(arr[-1] - arr[0]) if len(arr) > 1 else 0.0
    return float(arr.mean()), float(arr.std()), float(arr.min()), float(arr.max()), delta


def extract_features(vitals_window: list) -> np.ndarray:
    """
    Extract FEATURE_SCHEMA features from a list of VitalObservation.to_dict() records.
    Window is expected in ascending time order.
    Returns a 1-D numpy array of length N_FEATURES.
    For research / demonstration only – not clinically validated.
    """
    if not vitals_window:
        return np.full(N_FEATURES, np.nan)

    hr   = [v.get("heart_rate")       for v in vitals_window]
    spo2 = [v.get("spo2")             for v in vitals_window]
    sbp  = [v.get("systolic_bp")      for v in vitals_window]
    dbp  = [v.get("diastolic_bp")     for v in vitals_window]
    rr   = [v.get("respiratory_rate") for v in vitals_window]
    temp = [v.get("temperature")      for v in vitals_window]
    qual = [v.get("data_quality")     for v in vitals_window]

    hr_stats   = _safe_stats(hr)
    spo2_stats = _safe_stats(spo2)
    sbp_stats  = _safe_stats(sbp)
    dbp_stats  = _safe_stats(dbp)
    rr_stats   = _safe_stats(rr)
    temp_stats = _safe_stats(temp)

    # Shock index: mean(sbp) / mean(hr) — experimental only
    si_vals = []
    for h, s in zip(hr, sbp):
        if h and s and float(h) > 0:
            si_vals.append(float(s) / float(h))
    si_mean = float(np.mean(si_vals)) if si_vals else np.nan

    n = len(vitals_window)
    hr_miss   = sum(1 for v in hr   if v is None) / n
    spo2_miss = sum(1 for v in spo2 if v is None) / n
    sbp_miss  = sum(1 for v in sbp  if v is None) / n
    quality_ratio = sum(1 for q in qual if q == "valid") / n

    features = [
        *hr_stats, *spo2_stats, *sbp_stats,
        *dbp_stats, *rr_stats,  *temp_stats,
        si_mean,
        hr_miss, spo2_miss, sbp_miss,
        quality_ratio,
    ]
    return np.array(features, dtype=float)
