"""
ml/train_model.py
Trains the LogisticRegression loan model and saves all ML artifacts.
Run AFTER seed_data.py:  python ml/train_model.py

Outputs (ml/models/):
  loan_model.joblib       — trained LogisticRegression
  scaler.joblib           — StandardScaler (fitted on training set)
  shap_background.npy     — fixed 100-row background for SHAP (deterministic)
  feature_names.json      — ordered feature list
  training_report.json    — accuracy, coefficients, feature importance
"""

import os
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

FEATURES = [
    "age", "income", "loan_amount", "credit_score",
    "pin_code_encoded", "employment_type_encoded", "gender_encoded"
]

HIGH_RISK_PINS = {"221001","221002","241001","845401","845406",
                  "110044","110043","226001","226002","273001"}


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # pin_code: 1 = high-risk (rural UP/Bihar proxy cluster), 0 = low-risk
    df["pin_code_encoded"] = df["pin_code"].astype(str).apply(
        lambda x: 1 if x in HIGH_RISK_PINS else 0
    )

    # employment_type ordinal: informal=0, self_employed=1, salaried=2
    emp_map = {"informal": 0, "self_employed": 1, "salaried": 2}
    df["employment_type_encoded"] = df["employment_type"].map(emp_map).fillna(0).astype(int)

    # gender ordinal: Other=0, F=1, M=2
    gender_map = {"Other": 0, "F": 1, "M": 2}
    df["gender_encoded"] = df["gender"].map(gender_map).fillna(0).astype(int)

    # binary outcome
    df["outcome_binary"] = (df["outcome"] == "APPROVED").astype(int)

    return df


def train():
    print("Loading dataset...")
    df = pd.read_csv("ml/data/loan_dataset.csv")
    df = encode_features(df)

    X = df[FEATURES].values
    y = df["outcome_binary"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # Train
    print("Training LogisticRegression...")
    model = LogisticRegression(
        random_state=42,
        max_iter=1000,
        C=1.0,
        solver="lbfgs"
    )
    model.fit(X_train_s, y_train)

    # Evaluate
    y_pred = model.predict(X_test_s)
    y_prob = model.predict_proba(X_test_s)[:, 1]
    report = classification_report(y_test, y_pred, output_dict=True)
    auc    = roc_auc_score(y_test, y_prob)
    print(f"  Accuracy: {report['accuracy']:.3f}  |  AUC: {auc:.3f}")

    # Fixed SHAP background: 100 random training rows (seed=42, committed to repo)
    rng = np.random.default_rng(42)
    bg_idx = rng.choice(len(X_train_s), size=100, replace=False)
    shap_background = X_train_s[bg_idx]

    # Save artifacts
    os.makedirs("ml/models", exist_ok=True)
    joblib.dump(model,  "ml/models/loan_model.joblib")
    joblib.dump(scaler, "ml/models/scaler.joblib")
    np.save("ml/models/shap_background.npy", shap_background)

    with open("ml/models/feature_names.json", "w") as f:
        json.dump(FEATURES, f)

    # Training report (for transparency / README)
    training_report = {
        "accuracy": round(report["accuracy"], 4),
        "auc_roc":  round(auc, 4),
        "n_train":  len(X_train),
        "n_test":   len(X_test),
        "feature_coefficients": {
            FEATURES[i]: round(float(model.coef_[0][i]), 4)
            for i in range(len(FEATURES))
        },
        "model": "LogisticRegression(C=1.0, solver=lbfgs)",
        "scaler": "StandardScaler",
    }
    with open("ml/models/training_report.json", "w") as f:
        json.dump(training_report, f, indent=2)

    print(f"\nFeature coefficients:")
    for feat, coef in training_report["feature_coefficients"].items():
        direction = "-> APPROVE" if coef > 0 else "-> REJECT"
        print(f"  {feat:<28} {coef:+.4f}  {direction}")

    print(f"  Artifacts saved to ml/models/")
    print(f"  loan_model.joblib, scaler.joblib, shap_background.npy")
    print(f"  feature_names.json, training_report.json")
    print(f"\nRun uvicorn backend.main:app to start the API.")


if __name__ == "__main__":
    train()
