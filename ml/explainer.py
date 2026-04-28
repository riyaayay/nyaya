"""
ml/explainer.py
Hardened SHAP pipeline — deterministic, fast, demo-safe.

Design decisions:
  - Module-level singletons: loaded once at startup, never per-request
  - Fixed background array (shap_background.npy, 100 rows, seed=42)
  - shap_values() returns plain ndarray — no Explanation object serialization risk
  - LinearExplainer is analytically exact for LogisticRegression (closed-form)
  - Same input → same SHAP output on every machine
"""

import json
import numpy as np
import joblib
import shap

# ── Feature order MUST match train_model.py ──────────────────────────────────
FEATURES = [
    "age", "income", "loan_amount", "credit_score",
    "pin_code_encoded", "employment_type_encoded", "gender_encoded"
]

HIGH_RISK_PINS = {"221001","221002","241001","845401","845406",
                  "110044","110043","226001","226002","273001"}

# ── Module-level singletons (loaded once at FastAPI startup) ─────────────────
_model     = None
_scaler    = None
_explainer = None  # shap.LinearExplainer with FIXED background


def load_artifacts():
    """
    Call this once from FastAPI lifespan startup hook.
    Subsequent calls are no-ops (singletons already set).
    """
    global _model, _scaler, _explainer
    if _explainer is not None:
        return  # already loaded

    _model  = joblib.load("ml/models/loan_model.joblib")
    _scaler = joblib.load("ml/models/scaler.joblib")

    # Fixed background: same 100 rows on every run → deterministic explanations
    background = np.load("ml/models/shap_background.npy")  # shape (100, 7)
    _explainer = shap.LinearExplainer(_model, background)

    print("SHAP explainer loaded (fixed background, 100 rows)")


def _encode(raw: dict) -> np.ndarray:
    """
    Encode raw applicant features into the model's feature vector.
    Mirrors encode_features() in train_model.py exactly.
    """
    pin_code_encoded = 1 if str(raw.get("pin_code", "")) in HIGH_RISK_PINS else 0

    emp_map = {"informal": 0, "self_employed": 1, "salaried": 2}
    employment_type_encoded = emp_map.get(raw.get("employment_type", "informal"), 0)

    gender_map = {"Other": 0, "F": 1, "M": 2}
    gender_encoded = gender_map.get(raw.get("gender", "Other"), 0)

    return np.array([[
        raw.get("age", 30),
        raw.get("income", 20000),
        raw.get("loan_amount", 100000),
        raw.get("credit_score", 600),
        pin_code_encoded,
        employment_type_encoded,
        gender_encoded,
    ]])


def compute_shap(applicant_features: dict) -> dict:
    """
    Returns SHAP values for a single applicant.
    Deterministic: same input → same output.
    Latency: ~40ms on warm Cloud Run instance.
    """
    if _explainer is None:
        load_artifacts()

    X = _encode(applicant_features)
    X_scaled = _scaler.transform(X)

    # .shap_values() returns ndarray — safe for JSON serialization
    raw_shap = _explainer.shap_values(X_scaled)  # shape (1, 7) or (1, 7) for binary

    # Handle both single-output and multi-output SHAP returns
    if isinstance(raw_shap, list):
        vals = raw_shap[1][0]  # class=1 (APPROVED) SHAP values
    else:
        vals = raw_shap[0]

    return {FEATURES[i]: round(float(vals[i]), 4) for i in range(len(FEATURES))}


def compute_gender_proxy(shap_vals: dict) -> float:
    """
    Composite gender-proxy score:
      = |gender_encoded SHAP| + 0.4 × |pin_code_encoded SHAP|

    Rationale: pin_code is a documented caste/religion proxy (RBI FPC 2015).
    When it contributes significantly, it amplifies the gender-geography
    intersectional signal. Weight 0.4 is conservative (partial attribution).
    """
    return round(
        abs(shap_vals.get("gender_encoded", 0)) +
        0.4 * abs(shap_vals.get("pin_code_encoded", 0)),
        4
    )


def compute_confidence(applicant_features: dict) -> float:
    """
    Model confidence = max predict_proba score.
    Represents how strongly the model leaned toward the predicted outcome.
    Does NOT measure fairness.
    """
    if _model is None:
        load_artifacts()
    X = _encode(applicant_features)
    X_scaled = _scaler.transform(X)
    proba = _model.predict_proba(X_scaled)[0]
    return round(float(max(proba)), 4)


def predict_outcome(applicant_features: dict) -> str:
    """Returns 'APPROVED' or 'REJECTED'."""
    if _model is None:
        load_artifacts()
    X = _encode(applicant_features)
    X_scaled = _scaler.transform(X)
    pred = _model.predict(X_scaled)[0]
    return "APPROVED" if pred == 1 else "REJECTED"


def get_top_factors(shap_vals: dict, n: int = 3) -> list:
    """
    Returns top N features by absolute SHAP value, with direction.
    Used by both Hindi and English explanations.
    """
    sorted_feats = sorted(shap_vals.items(), key=lambda x: abs(x[1]), reverse=True)
    return [
        {
            "feature":   feat,
            "shap":      val,
            "direction": "approval" if val > 0 else "rejection",
        }
        for feat, val in sorted_feats[:n]
    ]
