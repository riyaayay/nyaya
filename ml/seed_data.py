"""
ml/seed_data.py
Generates synthetic Indian loan dataset with controlled bias patterns.
Run once:  python ml/seed_data.py

Outputs:
  ml/data/loan_dataset.csv     — 1000-row training set
  ml/data/demo_dataset.csv     — 200-row clean demo upload CSV
  ml/data/decisions.json       — 1000 pre-computed decisions for Firestore/BQ seeding

Bias patterns (deterministic, seed=42):
  pin_code → outcome  |r| ≈ 0.40  (caste/religion proxy per RBI FPC 2015)
  gender   → outcome  |r| ≈ 0.28  (direct + intersectional)
"""

import random
import json
import csv
import os
import math
from datetime import datetime, timedelta

random.seed(42)

# ── Geography config ─────────────────────────────────────────────────────────
# HIGH_RISK pin codes = rural UP/Bihar (documented caste-proxy clusters)
# LOW_RISK  pin codes = metro cities
HIGH_RISK_PINS = ["221001", "221002", "241001", "845401", "845406",
                  "110044", "110043", "226001", "226002", "273001"]
LOW_RISK_PINS  = ["400001", "400002", "560001", "560002", "110001",
                  "110002", "500001", "500002", "600001", "600002"]

PIN_DISTRICT = {
    "221001": "Varanasi, UP",   "221002": "Varanasi, UP",
    "241001": "Sitapur, UP",    "845401": "Motihari, Bihar",
    "845406": "Motihari, Bihar","110044": "South Delhi",
    "110043": "South Delhi",    "226001": "Lucknow, UP",
    "226002": "Lucknow, UP",    "273001": "Gorakhpur, UP",
    "400001": "Mumbai, MH",     "400002": "Mumbai, MH",
    "560001": "Bengaluru, KA",  "560002": "Bengaluru, KA",
    "110001": "New Delhi",      "110002": "New Delhi",
    "500001": "Hyderabad, TS",  "500002": "Hyderabad, TS",
    "600001": "Chennai, TN",    "600002": "Chennai, TN",
}

EMPLOYMENT_TYPES = ["salaried", "self_employed", "informal"]

# Named synthetic individuals for demo storytelling
NAMED_INDIVIDUALS = [
    {"name": "Priya Sharma",    "gender": "F", "pin_code": "241001", "age": 28, "income": 18000,  "loan_amount": 150000, "employment_type": "informal",     "credit_score": 612, "id": "DEC-20241105-0042", "outcome": "REJECTED"},
    {"name": "Rekha Devi",      "gender": "F", "pin_code": "845401", "age": 34, "income": 14500,  "loan_amount": 100000, "employment_type": "informal",     "credit_score": 588, "id": "DEC-20240115-0007"},
    {"name": "Sunita Kumari",   "gender": "F", "pin_code": "226001", "age": 41, "income": 22000,  "loan_amount": 200000, "employment_type": "self_employed", "credit_score": 634, "id": "DEC-20240302-0019"},
    {"name": "Meena Yadav",     "gender": "F", "pin_code": "273001", "age": 29, "income": 16000,  "loan_amount": 120000, "employment_type": "informal",     "credit_score": 601, "id": "DEC-20240518-0031"},
    {"name": "Anita Gupta",     "gender": "F", "pin_code": "221001", "age": 52, "income": 31000,  "loan_amount": 300000, "employment_type": "self_employed", "credit_score": 658, "id": "DEC-20240720-0055"},
    {"name": "Rahul Verma",     "gender": "M", "pin_code": "400001", "age": 35, "income": 75000,  "loan_amount": 600000, "employment_type": "salaried",     "credit_score": 740, "id": "DEC-20241001-0088"},
    {"name": "Arjun Singh",     "gender": "M", "pin_code": "560001", "age": 42, "income": 90000,  "loan_amount": 800000, "employment_type": "salaried",     "credit_score": 765, "id": "DEC-20241012-0091"},
]


def _approval_probability(row: dict) -> float:
    """
    Controlled logistic-style probability with deliberate bias signals.
    Each modifier is documented so bias patterns are reproducible.
    """
    base = 0.65

    # Credit score: primary legitimate factor
    base += (row["credit_score"] - 650) / 1000.0

    # Income-to-loan ratio: legitimate factor
    ratio = row["income"] / max(row["loan_amount"], 1)
    base += min(0.20, ratio * 3.0) - 0.10

    # Employment type: legitimate (informal → higher risk)
    emp_mod = {"salaried": +0.10, "self_employed": 0.0, "informal": -0.12}
    base += emp_mod[row["employment_type"]]

    # ── BIAS SIGNALS (deliberate for demo) ──────────────────────────────
    # pin_code as caste/religion proxy (|corr| target ≈ 0.40)
    if row["pin_code"] in HIGH_RISK_PINS:
        base -= 0.18
    else:
        base += 0.05

    # Gender bias (|corr| target ≈ 0.28)
    gender_mod = {"F": -0.10, "M": +0.04, "Other": -0.06}
    base += gender_mod[row["gender"]]

    # Intersectional: rural + female = compounded penalty
    if row["pin_code"] in HIGH_RISK_PINS and row["gender"] == "F":
        base -= 0.07
    # ─────────────────────────────────────────────────────────────────────

    return max(0.05, min(0.95, base))


def _make_row(i: int, timestamp: datetime, named: dict = None) -> dict:
    if named:
        r = dict(named)
    else:
        gender = random.choices(["M", "F", "Other"], weights=[58, 36, 6])[0]
        pin_group = random.choices(["high", "low"], weights=[45, 55])[0]
        pin_code = random.choice(HIGH_RISK_PINS if pin_group == "high" else LOW_RISK_PINS)
        r = {
            "age":             random.randint(22, 62),
            "gender":          gender,
            "income":          random.randint(10000, 150000),
            "loan_amount":     random.randint(50000, 1500000),
            "pin_code":        pin_code,
            "employment_type": random.choices(EMPLOYMENT_TYPES, weights=[45, 30, 25])[0],
            "credit_score":    random.randint(500, 850),
        }

    prob = _approval_probability(r)
    outcome = named.get("outcome") if (named and "outcome" in named) else ("APPROVED" if random.random() < prob else "REJECTED")

    row_id = named.get("id") if named else f"DEC-{timestamp.strftime('%Y%m%d')}-{i:04d}"

    return {
        "decision_id":       row_id,
        "timestamp":         timestamp.isoformat() + "Z",
        "applicant_name":    named.get("name") if named else _random_name(r["gender"]),
        "district":          PIN_DISTRICT.get(r["pin_code"], "Unknown"),
        "state":             _district_to_state(PIN_DISTRICT.get(r["pin_code"], "")),
        "age":               r["age"],
        "gender":            r["gender"],
        "income":            r["income"],
        "loan_amount":       r["loan_amount"],
        "pin_code":          r["pin_code"],
        "employment_type":   r["employment_type"],
        "credit_score":      r["credit_score"],
        "outcome":           outcome,
        "approval_prob":     round(prob, 4),
    }


# ── Name pools ───────────────────────────────────────────────────────────────
FEMALE_NAMES = ["Priya","Rekha","Sunita","Meena","Anita","Geeta","Kavita",
                "Pooja","Nisha","Seema","Asha","Uma","Rita","Lata","Sita"]
MALE_NAMES   = ["Rahul","Arjun","Vijay","Suresh","Ramesh","Anil","Sanjay",
                "Manoj","Rajesh","Dinesh","Amit","Rohit","Vikas","Naveen"]
SURNAMES     = ["Sharma","Verma","Gupta","Singh","Yadav","Kumar","Devi",
                "Kumari","Mishra","Pandey","Tiwari","Dubey","Jha","Das"]

def _random_name(gender: str) -> str:
    pool = FEMALE_NAMES if gender == "F" else MALE_NAMES
    return f"{random.choice(pool)} {random.choice(SURNAMES)}"

def _district_to_state(district: str) -> str:
    mapping = {"UP": "Uttar Pradesh", "Bihar": "Bihar", "MH": "Maharashtra",
               "KA": "Karnataka", "TS": "Telangana", "TN": "Tamil Nadu",
               "Delhi": "Delhi"}
    for k, v in mapping.items():
        if k in district:
            return v
    return "Unknown"


def generate(n: int = 1000):
    rows = []
    base_date = datetime(2024, 1, 1)

    # Insert named individuals first (guaranteed demo cases)
    for i, named in enumerate(NAMED_INDIVIDUALS):
        ts = base_date + timedelta(days=random.randint(0, 364))
        rows.append(_make_row(i, ts, named=named))

    # Fill rest with synthetic rows
    for i in range(n - len(NAMED_INDIVIDUALS)):
        ts = base_date + timedelta(
            days=random.randint(0, 364),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        rows.append(_make_row(i + 100, ts))

    # Sort by timestamp
    rows.sort(key=lambda r: r["timestamp"])
    return rows


def save_csv(rows, path, include_id=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = ["age","gender","income","loan_amount","pin_code",
                  "employment_type","credit_score","outcome"]
    if include_id:
        fieldnames = ["decision_id"] + fieldnames
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fieldnames})
    print(f"[OK] CSV saved: {path} ({len(rows)} rows)")


def save_json(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"[OK] JSON saved: {path} ({len(rows)} records)")


if __name__ == "__main__":
    print("Generating synthetic loan dataset...")
    rows = generate(1000)

    # Full dataset (for training)
    save_csv(rows, "ml/data/loan_dataset.csv")

    # Demo upload CSV (200 rows, no decision_id — simulates fresh upload)
    save_csv(rows[:200], "ml/data/demo_dataset.csv")

    # Full JSON for Firestore/BQ seeding
    save_json(rows, "ml/data/decisions.json")

    # Quick bias check
    approved = sum(1 for r in rows if r["outcome"] == "APPROVED")
    f_approved = sum(1 for r in rows if r["gender"] == "F" and r["outcome"] == "APPROVED")
    f_total    = sum(1 for r in rows if r["gender"] == "F")
    m_approved = sum(1 for r in rows if r["gender"] == "M" and r["outcome"] == "APPROVED")
    m_total    = sum(1 for r in rows if r["gender"] == "M")
    hr_approved = sum(1 for r in rows if r["pin_code"] in HIGH_RISK_PINS and r["outcome"] == "APPROVED")
    hr_total    = sum(1 for r in rows if r["pin_code"] in HIGH_RISK_PINS)
    lr_approved = sum(1 for r in rows if r["pin_code"] in LOW_RISK_PINS and r["outcome"] == "APPROVED")
    lr_total    = sum(1 for r in rows if r["pin_code"] in LOW_RISK_PINS)

    print("\n--- Bias Verification -----------------------------------")
    print(f"Overall approval rate:   {approved/len(rows)*100:.1f}%")
    print(f"Female approval rate:    {f_approved/f_total*100:.1f}%")
    print(f"Male approval rate:      {m_approved/m_total*100:.1f}%")
    print(f"Disparate Impact Ratio:  {(f_approved/f_total)/(m_approved/m_total):.3f}  (< 0.80 = bias flag)")
    print(f"High-risk pin approval:  {hr_approved/hr_total*100:.1f}%")
    print(f"Low-risk pin approval:   {lr_approved/lr_total*100:.1f}%")
    print(f"Gap:                     {(lr_approved/lr_total - hr_approved/hr_total)*100:.1f}pp")
    print("---------------------------------------------------------")
    print("\nDone. Run `python ml/train_model.py` next.")
