<div align="center">

# NYAYA
### Neural fairness Auditing for Your Algorithms

**India's AI Accountability Infrastructure**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-nyaya--seven.vercel.app-1a1a2e?style=for-the-badge&logo=vercel&logoColor=white)](https://nyaya-seven.vercel.app/)
[![Demo Video](https://img.shields.io/badge/Demo%20Video-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/eFdDRsVFMiI)
[![Built with Gemini](https://img.shields.io/badge/Gemini%201.5%20Pro-Google%20AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![DPDPA 2023](https://img.shields.io/badge/DPDPA%202023-Compliant%20Architecture-138808?style=for-the-badge)](https://www.meity.gov.in/)

---

*200 million AI-driven financial decisions are made in India every year.*
*Most are never explained. Many are discriminatory. None have been provably challenged.*

**Until now.**

</div>

---

## The Problem

In 2024, an AI loan system approved **91% of applications from metro men** and **22% from rural women** — with identical credit profiles. The only difference was a PIN code.

PIN codes in India are documented proxies for caste, religion, and geography. When an AI model learns from historical lending data, it inherits every structural inequality encoded in that history. The result is algorithmic discrimination that is invisible, scalable, and — under the Digital Personal Data Protection Act 2023 and Article 14 of the Indian Constitution — **illegal**.

The problem isn't that the AI is broken. The problem is that no tool exists to prove it.

NYAYA is that tool.

---

## What NYAYA Does

NYAYA is a three-sided accountability platform built for India's DPDPA 2023 era. It serves three actors who all face the same crisis from different angles.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DATA OWNER    │    │     CITIZEN     │    │   REGULATOR     │
│                 │    │                 │    │                 │
│  Upload dataset │    │  Enter decision │    │  Scan 1M+ past  │
│  Detect proxy   │    │  ID. Understand │    │  decisions.     │
│  discriminators │    │  rejection in   │    │  Generate DPDPA │
│  before deploy  │    │  Hindi. Know    │    │  compliance     │
│                 │    │  your rights.   │    │  audit report.  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## The Three Pillars

### 🔬 Pillar 1 — Bias Genome Scanner *(Data Owner)*

Upload a historical decision dataset. NYAYA runs deterministic statistical analysis — Pearson correlations, Disparate Impact Ratio, VIF multicollinearity detection — combined with Gemini 1.5 Pro reasoning to surface:

- **Proxy discriminators**: features that have never seen a protected attribute but statistically encode one (e.g., `pin_code` → caste/geography)
- **Intersectional bias**: compounded penalties for applicants who belong to multiple marginalized groups simultaneously
- **Regulatory exposure**: per-feature DPDPA Section 4 and RBI Fair Practices Code risk annotations

The gender × geography approval matrix reveals the compounded penalty. A 37 percentage point gap between metro men and rural women is not a model error. It is a pattern the model learned to replicate.

---

### 📋 Pillar 2 — Citizen Decision Explainer *(Affected Citizen)*

Enter a decision ID. NYAYA computes SHAP (SHapley Additive exPlanations) feature attributions — mathematically ground-truth values for why a specific decision went the way it did — and then does something no other fairness tool does:

It explains the result **in Hindi**, in plain language, to the person it affected.

Not a technical report. Not a dashboard for developers. A legally empowering explanation that tells Anita Gupta from Varanasi:

- Why her application was rejected (PIN code was the primary driver, not income or credit score)
- What her rights are under DPDPA 2023 Section 12(2)
- How to contest the decision, and where to file a complaint with the RBI Ombudsman

> *Raw SHAP values are mathematically rigorous and humanly incomprehensible. Gemini bridges the gap — translating `pin_code_encoded: -0.34` into a rights-preserving explanation in the citizen's native language.*

---

### 🏛 Pillar 3 — Retroactive Audit Dashboard *(Regulator)*

BigQuery scans historical decision logs at scale, flagging every decision where the gender proxy score — a composite of gender SHAP attribution and PIN code attribution weighted by the EEOC 4/5ths rule — exceeds the 0.30 threshold.

Output:
- **Timeline visualization** of systemic bias drift across 2024
- **Prioritized remediation queue** of affected applicants by district and severity
- **One-click DPDPA compliance audit report** — a formal document naming the bias metric, the flagging threshold, the affected demographic, the regulatory obligation, and the remediation steps required

This is what DPDPA 2023 mandates. This is what no institution currently produces.

---

## Live Demo

**→ [nyaya-seven.vercel.app](https://nyaya-seven.vercel.app/)**

**→ [Watch the 2-minute demo on YouTube](https://youtu.be/eFdDRsVFMiI)**

### Demo Walkthrough

| Step | Tab | What to do | What you'll see |
|------|-----|-----------|-----------------|
| 1 | Institution View | Upload `ml/data/demo_dataset.csv` | Overall risk: HIGH, Gini 0.71, `pin_code` flagged as proxy |
| 2 | Institution View | Scroll to intersectional table | 91% metro men vs 22% rural women — 37pt gap |
| 3 | Applicant View | Click **Anita Gupta** (Varanasi, UP) | SHAP waterfall: PIN code as primary rejection driver |
| 4 | Applicant View | Scroll to explanation block | Full Hindi explanation + DPDPA rights note + remediation steps |
| 5 | Regulator View | Review dashboard | 1,009 decisions scanned, 143 flagged, remediation queue |
| 6 | Regulator View | Click "View Full Compliance Report" | Court-ready DPDPA audit document |
| 7 | Technical Architecture | Review stack | MVP vs roadmap layer, competitive differentiation table |

---

## Quick Start

Run the entire MVP locally. Pre-computed demo caches mean it works **without a Gemini API key or GCP account**.

### Prerequisites
- Python 3.11+
- Node.js 20+

### 1. Clone and start the backend

```bash
git clone https://github.com/your-org/nyaya.git
cd nyaya/backend
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
# API running at http://localhost:8000
```

### 2. Start the frontend

```bash
cd ../frontend
npm install
npm run dev
# UI running at http://localhost:5173
```

---

## Architecture

### MVP Layer — Built & Deployed

```
┌──────────────────────────────────────────────────────────┐
│                    React + Vite                           │
│         Chart.js · SHAP waterfall · Hindi i18n           │
└──────────────┬───────────────────────────────────────────┘
               │ REST
┌──────────────▼───────────────────────────────────────────┐
│                   FastAPI (Python)                        │
│     scikit-learn LogisticRegression · SHAP LinearExplainer│
└──────────┬───────────────────────┬───────────────────────┘
           │                       │
┌──────────▼──────────┐ ┌──────────▼──────────┐
│   Gemini 1.5 Pro    │ │  Firestore + BigQuery│
│  Explanation + Audit│ │  Decisions + Scans   │
└─────────────────────┘ └─────────────────────┘
```

### Tech Stack

| Layer | Technology | Why — not alternative |
|-------|-----------|----------------------|
| Frontend | React + Vite | Fast dev · Chart.js ecosystem · not Flutter Web (slower cold start) |
| Backend | FastAPI | Async · auto OpenAPI docs · not Django (overkill) |
| LLM | Gemini 1.5 Pro | 1M token context window for full dataset reasoning · not GPT-4 (non-Google) |
| Explanations | SHAP LinearExplainer | Ground-truth feature attribution for LogisticRegression · not LIME (less stable) |
| Analytics | BigQuery | Columnar scan of SHAP thresholds across 1M+ rows · not Firestore (slow analytics) |
| Decisions DB | Firestore | Real-time reads, flexible schema, immutable append-only rules |
| Hosting | Cloud Run + Vercel | Serverless, scales to zero, no infrastructure management |

### Roadmap Layer *(Not Yet Built)*

- **Pub/Sub** — real-time decision ingestion stream
- **Vector Search** — semantic similarity matching of bias patterns across cases
- **HDBSCAN** — unsupervised bias cluster detection at scale
- **IVR integration** — voice-based citizen access for rural users without smartphones
- **Cloud Armor + VPC Service Controls** — production security posture

---

## ML Pipeline

To retrain the model or regenerate synthetic data with deliberate bias patterns:

```bash
# Generate synthetic dataset with embedded proxy discrimination
python ml/seed_data.py

# Train LogisticRegression and save SHAP artifacts
python ml/train_model.py
```

The synthetic dataset encodes three bias patterns observed in real Indian lending data: PIN code as caste/geography proxy, employment type as informal-sector penalty, and the intersectional compound effect for rural women. The model learns these patterns from the data — exactly as production models do.

---

## Competitive Differentiation

| Feature | NYAYA | Aequitas / AI Fairness 360 | Manual Audit |
|---------|-------|---------------------------|--------------|
| Legal alignment | DPDPA 2023 + Article 14 native | None (US-framed) | High subjectivity |
| Citizen explanation | Automated, localized Hindi | None (developer-only) | Extremely slow |
| Historical scan scale | BigQuery · 1M+ rows | In-memory · Pandas limits | Sample-based only |
| Intersectional detection | PIN code × Gender compound | Single-feature parity | Prone to human error |
| Regulatory output | Court-ready DPDPA report | None | Unstructured |
| User types served | Compliance officer + Citizen + Regulator | Developer only | Legal team only |

---

## SDG Alignment

- **SDG 5** — Gender equality: surfacing and quantifying gender-based discrimination in automated systems
- **SDG 10** — Reduced inequalities: intersectional analysis for rural and marginalized communities
- **SDG 16** — Justice and strong institutions: enabling citizens to contest decisions and regulators to enforce compliance

---

## Regulatory Foundation

NYAYA's architecture is grounded in three specific legal instruments:

- **DPDPA 2023 Section 4** — fair and reasonable processing requirement
- **DPDPA 2023 Section 12(2)** — citizen right to explanation of automated decisions
- **DPDPA 2023 Section 13** — right to contest and seek remediation
- **Article 14, Constitution of India** — equality before law, prohibiting arbitrary state action
- **RBI Fair Practices Code 2015** — prohibiting location-based discrimination that proxies protected attributes

---

## Built For

Google Developer Groups — Solution Challenge 2026

*This is not a dashboard. This is justice infrastructure.*

---

<div align="center">

Made with Gemini · BigQuery · Cloud Run · Firestore · FastAPI · React

**[Live Demo](https://nyaya-seven.vercel.app/) · [Demo Video](https://youtu.be/eFdDRsVFMiI)**

</div>
