"""
backend/services/bias_stats.py
Deterministic statistical pre-processing layer for /analyze-dataset.

All bias metrics are computed here using pandas/scipy — no AI involved.
Gemini only receives these pre-computed numbers and interprets them.
This makes every risk score independently verifiable.

Dual-signal approach:
  - SHAP = predictive weight (how much a feature affects the model output)
  - PCI  = proxy signal (how strongly a feature correlates with a protected attribute)
  A feature with high SHAP AND high PCI is a proxy discriminator.
"""

import json
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency, pointbiserialr
from sklearn.linear_model import LinearRegression
from typing import Any

HIGH_RISK_PINS = {"221001","221002","241001","845401","845406",
                  "110044","110043","226001","226002","273001"}

FEATURE_DISPLAY_NAMES = {
    "age":             "Age",
    "income":          "Monthly Income (₹)",
    "loan_amount":     "Loan Amount Requested (₹)",
    "credit_score":    "Credit Score",
    "pin_code":        "PIN Code",
    "employment_type": "Employment Type",
    "gender":          "Gender",
}


# ── Core formula (from implementation plan §5) ────────────────────────────────
def correlation_to_risk(correlation: float) -> float:
    """
    Deterministic monotonic mapping: Pearson |r| → risk score [0, 1].

    Formula:  risk = min(1.0, |r| × 2.2)

    Calibration table:
      |r| = 0.00 → 0.00  (no association)
      |r| = 0.25 → 0.55  (flag threshold — moderate risk)
      |r| = 0.41 → 0.90  (pin_code in demo dataset)
      |r| = 0.45 → 0.99  (strong proxy — near-certain bias)

    Verbal: "Multiply the correlation by 2.2, cap at 1."
    """
    return round(min(1.0, abs(correlation) * 2.2), 2)


def risk_band(score: float) -> str:
    if score < 0.40:
        return "LOW"
    elif score < 0.70:
        return "MODERATE"
    return "HIGH"


# ── Proxy Correlation Index (PCI) ─────────────────────────────────────────────
def compute_proxy_correlation_index(df: pd.DataFrame, feature_col: str, protected_col: str) -> tuple:
    """
    Measures the statistical dependence between a feature and a protected attribute.
    This is DISTINCT from SHAP importance — it answers the question:
    'Does this feature carry protected-attribute signal?'

    Uses Cramér's V for categorical/ordinal features.
    Returns (cramers_v, p_value).

    Interpretation:
      PCI > 0.5 = strong proxy signal — feature smuggles protected info into the model
      PCI 0.2–0.5 = moderate proxy risk
      PCI < 0.2 = weak/no proxy signal
    """
    try:
        contingency = pd.crosstab(df[feature_col].fillna(0), df[protected_col].fillna(0))
        if contingency.shape[0] < 2 or contingency.shape[1] < 2:
            return 0.0, 1.0
        chi2, p, dof, expected = chi2_contingency(contingency)
        n = contingency.sum().sum()
        min_dim = min(contingency.shape) - 1
        if min_dim == 0 or n == 0:
            return 0.0, 1.0
        cramers_v = np.sqrt(chi2 / (n * min_dim))
        return round(float(cramers_v), 3), round(float(p), 4)
    except Exception:
        return 0.0, 1.0


# ── Main analysis function ────────────────────────────────────────────────────
def compute_bias_metrics(df: pd.DataFrame) -> dict:
    """
    Runs all deterministic statistical analysis on the uploaded dataset.
    Returns a structured dict to be passed into the Gemini prompt.

    Steps:
      1. Encode categorical features
      2. Pearson correlation: each feature vs binary outcome
      3. Group acceptance rates by gender
      4. Disparate Impact Ratio
      5. Acceptance rate by geography (pin_code rural/urban bucket)
      6. Intersectional matrix: gender × geography
      7. Flag features with |corr| > 0.25
    """
    df = df.copy()

    # Require outcome column
    if "outcome" not in df.columns:
        raise ValueError("Dataset must contain an 'outcome' column (APPROVED/REJECTED).")

    df["outcome_binary"] = (df["outcome"].str.upper() == "APPROVED").astype(int)

    # ── Encode for correlation ────────────────────────────────────────────────
    df["pin_code_encoded"] = df["pin_code"].astype(str).apply(
        lambda x: 1 if x in HIGH_RISK_PINS else 0
    )
    emp_map = {"informal": 0, "self_employed": 1, "salaried": 2}
    df["employment_type_encoded"] = df["employment_type"].map(emp_map).fillna(0)
    gender_map = {"Other": 0, "F": 1, "M": 2}
    df["gender_encoded"] = df["gender"].map(gender_map).fillna(0)

    numeric_features = {
        "age":                     "age",
        "income":                  "income",
        "loan_amount":             "loan_amount",
        "credit_score":            "credit_score",
        "pin_code":                "pin_code_encoded",
        "employment_type":         "employment_type_encoded",
        "gender":                  "gender_encoded",
    }

    # ── VIF Computation ──────────────────────────────────────────────────────
    vifs = {}
    # Use all numeric columns for VIF to capture multilinear dependencies
    vif_features = [col for col in numeric_features.values() if col in df.columns]
    for target in vif_features:
        y = df[target].fillna(0)
        X = df[[f for f in vif_features if f != target]].fillna(0)
        if np.var(y) == 0:
            vifs[target] = 1.0
        else:
            model = LinearRegression().fit(X, y)
            r2 = model.score(X, y)
            if r2 >= 0.999:
                vifs[target] = float('inf')
            else:
                vifs[target] = round(1.0 / (1.0 - r2), 2)

    # ── PCI Computation: proxy signal for each feature vs gender ───────────
    pci_scores = {}
    for display_name, col in numeric_features.items():
        if col in df.columns and col != "gender_encoded":
            pci_v, pci_p = compute_proxy_correlation_index(df, col, "gender_encoded")
            pci_scores[display_name] = {"pci_score": pci_v, "pci_p_value": pci_p}
        else:
            pci_scores[display_name] = {"pci_score": 0.0, "pci_p_value": 1.0}

    correlations = {}
    for display_name, col in numeric_features.items():
        if col in df.columns:
            r, p = stats.pearsonr(df[col].fillna(0), df["outcome_binary"])
            
            if np.isnan(r): r = 0.0
            if np.isnan(p): p = 1.0
            
            pci_data = pci_scores.get(display_name, {"pci_score": 0.0, "pci_p_value": 1.0})
            risk = correlation_to_risk(r)
            is_proxy = bool(pci_data["pci_score"] > 0.3 and risk > 0.4)

            correlations[display_name] = {
                "pearson_r":  round(float(r), 4),
                "p_value":    round(float(p), 4),
                "risk_score": risk,
                "risk_band":  risk_band(risk),
                "flagged":    bool(abs(r) > 0.25),
                "vif_score":  vifs.get(col, 1.0),
                "pci_score":  pci_data["pci_score"],
                "pci_p_value": pci_data["pci_p_value"],
                "is_proxy_discriminator": is_proxy,
            }

    # Sort by |r| descending
    correlations = dict(
        sorted(correlations.items(), key=lambda x: abs(x[1]["pearson_r"]), reverse=True)
    )

    # ── PCI Matrix: intersectional proxy analysis ────────────────────────────
    # rows = protected attributes, columns = model features
    protected_cols = {"gender": "gender_encoded", "caste_proxy (pin_code)": "pin_code_encoded"}
    feature_cols = {k: v for k, v in numeric_features.items() if v not in ["gender_encoded", "pin_code_encoded"]}
    pci_matrix = {}
    for prot_name, prot_col in protected_cols.items():
        pci_matrix[prot_name] = {}
        for feat_name, feat_col in feature_cols.items():
            if feat_col in df.columns and prot_col in df.columns:
                v, _ = compute_proxy_correlation_index(df, feat_col, prot_col)
                pci_matrix[prot_name][feat_name] = v
            else:
                pci_matrix[prot_name][feat_name] = 0.0

    # ── 2. Gender acceptance rates ───────────────────────────────────────────
    gender_rates = {}
    for g in ["M", "F", "Other"]:
        subset = df[df["gender"] == g]
        if len(subset) > 0:
            rate = subset["outcome_binary"].mean()
            gender_rates[g] = {
                "count":          int(len(subset)),
                "approved":       int(subset["outcome_binary"].sum()),
                "acceptance_rate": round(float(rate) * 100, 1),
            }

    # ── 3. Disparate Impact Ratio ────────────────────────────────────────────
    dir_score = None
    if "F" in gender_rates and "M" in gender_rates and gender_rates["M"]["acceptance_rate"] > 0:
        dir_score = round(
            gender_rates["F"]["acceptance_rate"] / gender_rates["M"]["acceptance_rate"], 3
        )
    # DIR < 0.80 = 4/5ths rule violation (standard legal threshold)
    dir_flag = bool(dir_score is not None and dir_score < 0.80)

    # ── 4. Geography acceptance rates ────────────────────────────────────────
    df["geo_bucket"] = df["pin_code"].astype(str).apply(
        lambda x: "Rural (High-Risk)" if x in HIGH_RISK_PINS else "Urban (Low-Risk)"
    )
    geo_rates = {}
    for bucket in ["Rural (High-Risk)", "Urban (Low-Risk)"]:
        subset = df[df["geo_bucket"] == bucket]
        if len(subset) > 0:
            geo_rates[bucket] = {
                "count":           int(len(subset)),
                "acceptance_rate": round(float(subset["outcome_binary"].mean()) * 100, 1),
            }

    # ── 5. Intersectional matrix: gender × geography ─────────────────────────
    matrix = {}
    for g in ["M", "F", "Other"]:
        matrix[g] = {}
        for bucket in ["Rural (High-Risk)", "Urban (Low-Risk)"]:
            subset = df[(df["gender"] == g) & (df["geo_bucket"] == bucket)]
            if len(subset) > 0:
                matrix[g][bucket] = round(float(subset["outcome_binary"].mean()) * 100, 1)
            else:
                matrix[g][bucket] = None

    # ── 6. Dataset summary ───────────────────────────────────────────────────
    total          = len(df)
    total_approved = int(df["outcome_binary"].sum())
    flagged_feats  = [k for k, v in correlations.items() if v["flagged"]]

    return {
        "dataset_summary": {
            "total_records":    total,
            "total_approved":   total_approved,
            "overall_approval_rate": round(total_approved / total * 100, 1),
            "gender_distribution": df["gender"].value_counts().to_dict(),
        },
        "correlations":           correlations,
        "gender_acceptance_rates": gender_rates,
        "disparate_impact_ratio": {
            "value":    dir_score,
            "flagged":  dir_flag,
            "threshold": 0.80,
            "note":      "< 0.80 triggers EEOC 4/5ths rule violation — legally actionable",
        },
        "geography_acceptance_rates": geo_rates,
        "intersectional_matrix":  matrix,
        "pci_matrix":             pci_matrix,
        "flagged_features":       flagged_feats,
        "top_risky_features": [
            {
                "feature":    feat,
                "risk_score": data["risk_score"],
                "risk_band":  data["risk_band"],
                "pearson_r":  data["pearson_r"],
                "flagged":    data["flagged"],
                "pci_score":  data.get("pci_score", 0.0),
                "is_proxy_discriminator": data.get("is_proxy_discriminator", False),
            }
            for feat, data in list(correlations.items())[:5]
        ],
    }
