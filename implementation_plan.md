# NYAYA — India's AI Accountability Infrastructure
## Complete Implementation Plan

---

## 1. Problem Statement & Vision

India's public and private sectors increasingly use AI-driven systems for high-stakes decisions: loan approvals, welfare eligibility, job screening, and sentencing risk scores. These systems operate as black boxes — unaccountable, often discriminatory, and legally unchallenged. The **Digital Personal Data Protection Act 2023 (DPDPA)** and **Article 14** of the Constitution mandate fairness, yet no practical audit infrastructure exists.

**NYAYA** ("justice" in Sanskrit) fills this gap: an open, deployable AI accountability layer that detects bias before deployment, explains decisions to affected citizens in Hindi, and enables retroactive audits across historical decision datasets.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MVP LAYER (DEMO)                            │
│                                                                     │
│  ┌──────────┐    ┌──────────────────────────────────────────────┐  │
│  │ Frontend  │───▶│           Cloud Run (FastAPI)                │  │
│  │ (React)   │    │  /analyze-dataset                           │  │
│  │ Firebase  │    │  /explain-decision                          │  │
│  │ Hosting   │    │  /audit-history                             │  │
│  └──────────┘    └────────┬──────────────────────┬─────────────┘  │
│                           │                      │                 │
│                  ┌────────▼──────┐    ┌──────────▼──────────────┐ │
│                  │  Vertex AI    │    │  Firestore               │ │
│                  │  Gemini 1.5   │    │  /decisions (1000+ docs) │ │
│                  │  Pro          │    │  /audit_reports          │ │
│                  └───────────────┘    └──────────────────────────┘ │
│                           │                      │                 │
│                  ┌────────▼──────────────────────▼─────────────┐  │
│                  │           BigQuery                           │  │
│                  │  dataset: nyaya_decisions                    │  │
│                  │  table: decisions, shap_values              │  │
│                  └─────────────────────────────────────────────┘  │
│                                                                     │
│  ML Layer (local to Cloud Run):                                    │
│  • scikit-learn LogisticRegression                                 │
│  • SHAP TreeExplainer / LinearExplainer                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       ROADMAP LAYER (NOT BUILT)                     │
│  Pub/Sub │ HDBSCAN │ Vector Search │ Cloud Armor │ IVR │ LangChain  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. API Design

### POST `/analyze-dataset`
```
Request:
  multipart/form-data
  file: CSV file (synthetic loan dataset)

Processing:
  1. Parse CSV → pandas DataFrame
  2. Compute basic stats (missing values, class distribution per feature)
  3. Build prompt with full dataset summary + sample rows → Gemini 1.5 Pro
  4. Gemini returns structured JSON

Response (JSON):
{
  "top_risky_features": [
    {"feature": "pin_code", "risk_score": 0.91, "reason": "..."},
    ...
  ],
  "bias_heatmap": {
    "gender_x_geography": [[...], ...],
    "labels_x": ["Urban", "Semi-Urban", "Rural"],
    "labels_y": ["Male", "Female", "Other"]
  },
  "representation_gaps": [...],
  "intersectional_findings": "...",
  "confidence": 0.87,
  "report_text": "..."
}
```

### POST `/explain-decision`
```
Request (JSON):
{
  "decision_id": "DEC-20241105-0042",
  "applicant_features": {
    "age": 28, "gender": "F", "income": 18000,
    "loan_amount": 150000, "pin_code": "110044",
    "employment_type": "informal", "credit_score": 612
  },
  "outcome": "REJECTED"
}

Processing:
  1. Run LogisticRegression predict_proba
  2. Compute SHAP values (LinearExplainer)
  3. Build Gemini function-calling payload:
     - Function: generate_explanation(shap_values, outcome, lang)
  4. Gemini generates Hindi + English explanation

Response (JSON):
{
  "decision_id": "DEC-20241105-0042",
  "outcome": "REJECTED",
  "confidence": 0.78,
  "shap_values": {
    "pin_code": 0.34, "income": -0.18, "credit_score": -0.12, ...
  },
  "explanation_hi": "आपका आवेदन अस्वीकार किया गया क्योंकि...",
  "explanation_en": "Your application was rejected because...",
  "legal_note": "This decision may be challengeable under DPDPA Section 12(2)",
  "top_factors": [...]
}
```

### GET `/audit-history`
```
Query params:
  gender_proxy_threshold: float (default 0.30)
  start_date: ISO date string
  end_date: ISO date string
  limit: int (default 100)

Processing:
  1. Query BigQuery: SELECT * FROM decisions WHERE shap_gender_proxy > threshold
  2. Fetch named individuals from Firestore
  3. Send summary stats to Gemini → compliance report text

Response (JSON):
{
  "flagged_count": 143,
  "timeline": [
    {"date": "2024-01", "flagged": 12, "total": 89},
    ...
  ],
  "flagged_cases": [
    {
      "id": "DEC-20240115-0007",
      "name": "Priya Sharma",
      "district": "Sitapur, UP",
      "outcome": "REJECTED",
      "shap_gender_proxy": 0.41,
      "remediation_priority": "HIGH"
    },
    ...
  ],
  "remediation_queue": [...top 10 affected...],
  "compliance_report": "...(Gemini-generated, PDF-style text)..."
}
```

---

## 4. Data Schemas

### Firestore: `/decisions/{decision_id}`
```json
{
  "id": "DEC-20241105-0042",
  "timestamp": "2024-11-05T09:23:11Z",
  "applicant_name": "Priya Sharma",
  "district": "Sitapur, UP",
  "state": "Uttar Pradesh",
  "age": 28,
  "gender": "F",
  "income": 18000,
  "loan_amount": 150000,
  "pin_code": "110044",
  "employment_type": "informal",
  "credit_score": 612,
  "outcome": "REJECTED",
  "shap_values": {
    "pin_code": 0.34,
    "income": -0.18,
    "credit_score": -0.12,
    "gender_proxy": 0.31,
    "employment_type": 0.09
  },
  "explanation_hi": "...",
  "explanation_en": "...",
  "legal_flag": true,
  "audit_status": "PENDING_REVIEW"
}
```

### BigQuery Table: `nyaya_decisions.decisions`
```sql
CREATE TABLE nyaya_decisions.decisions (
  decision_id STRING,
  timestamp TIMESTAMP,
  applicant_name STRING,
  district STRING,
  state STRING,
  age INT64,
  gender STRING,
  income FLOAT64,
  loan_amount FLOAT64,
  pin_code STRING,
  employment_type STRING,
  credit_score INT64,
  outcome STRING,
  shap_pin_code FLOAT64,
  shap_income FLOAT64,
  shap_credit_score FLOAT64,
  shap_gender_proxy FLOAT64,
  shap_employment_type FLOAT64,
  model_version STRING,
  created_at TIMESTAMP
)
PARTITION BY DATE(timestamp);
```

### Synthetic CSV (uploaded by Data Owner)
```
age,gender,income,loan_amount,pin_code,employment_type,credit_score,outcome
28,F,18000,150000,110044,informal,612,REJECTED
45,M,65000,500000,400001,salaried,720,APPROVED
...
```

---

## 5. Gemini Prompt Design

### Feature 1 — Bias Genome Prompt
```
You are an AI fairness auditor. Analyze this loan application dataset for systemic bias.

Dataset statistics:
{dataset_stats_json}

Sample rows (first 50):
{sample_csv_rows}

Identify:
1. Proxy discriminator features (features that correlate with protected attributes like caste, religion, gender)
2. Demographic representation gaps
3. Intersectional bias patterns (e.g., gender × geography interactions)

For each finding, provide:
- Feature name
- Risk score (0.0–1.0)
- Evidence from data
- Legal risk under DPDPA 2023

CRITICAL: pin_code is a known caste/religion proxy in Indian lending. Look especially for this pattern.

Return ONLY valid JSON matching this schema:
{schema}
```

### Feature 2 — Explainability Function Calling

**Function definition (sent to Gemini):**
```json
{
  "name": "generate_citizen_explanation",
  "description": "Generate a plain-language explanation of an AI credit decision",
  "parameters": {
    "type": "object",
    "properties": {
      "shap_values": {"type": "object"},
      "outcome": {"type": "string"},
      "applicant_context": {"type": "object"},
      "language": {"type": "string", "enum": ["hi", "en"]}
    }
  }
}
```

**System prompt:**
```
You are a legal-rights advocate explaining AI decisions to Indian citizens.
When called with SHAP values and a loan outcome, generate:
1. A plain-language explanation at 10th-grade reading level
2. The top 3 contributing factors
3. A legal rights note referencing DPDPA 2023 or Article 14 if gender/location bias is detected
4. If language=hi, respond entirely in Hindi (Devanagari script)
```

### Feature 3 — Compliance Report Prompt
```
You are a DPDPA compliance officer generating an audit report.

Audit results:
- Total decisions audited: {total}
- Flagged decisions (gender proxy SHAP > 0.30): {flagged}
- Date range: {start} to {end}
- Affected districts: {districts}
- Most affected individuals: {top_cases}

Generate a formal compliance report including:
1. Executive summary
2. Systemic pattern description  
3. Legal exposure under DPDPA Section 12, Article 14
4. Recommended remediation steps
5. Priority remediation queue with individual case summaries

Format as a structured report with sections.
```

---

## 6. SHAP Pipeline

```python
# ml/explainer.py

import shap
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib

FEATURES = ['age', 'income', 'loan_amount', 'credit_score',
            'pin_code_encoded', 'employment_type_encoded', 'gender_encoded']

def load_model():
    return joblib.load('ml/models/loan_model.joblib')

def compute_shap(applicant_features: dict) -> dict:
    model = load_model()
    scaler = joblib.load('ml/models/scaler.joblib')
    
    X = np.array([[applicant_features[f] for f in FEATURES]])
    X_scaled = scaler.transform(X)
    
    # LinearExplainer for LogisticRegression
    explainer = shap.LinearExplainer(model, shap.maskers.Independent(X_scaled))
    shap_values = explainer(X_scaled)
    
    return {
        FEATURES[i]: float(shap_values.values[0][i])
        for i in range(len(FEATURES))
    }

# Gender proxy = SHAP value of gender_encoded + (0.4 * pin_code_encoded)
def compute_gender_proxy(shap_vals: dict) -> float:
    return abs(shap_vals.get('gender_encoded', 0)) + \
           0.4 * abs(shap_vals.get('pin_code_encoded', 0))
```

The model is trained on-startup from the pre-seeded dataset. SHAP values are computed per-request (~50ms). Gemini is called with SHAP values via function calling — removing Gemini degrades the system to raw numbers with no explanation (proving real AI dependency).

---

## 7. Build Order (Day-wise)

### Days 1–3: ML Foundation + Bias Scanner API

**Day 1:**
- [ ] Generate synthetic loan dataset (1000 rows) with deliberate bias patterns
  - pin_code → correlates with caste proxy → correlates with rejection
  - gender=F → subtle negative weight
- [ ] Train LogisticRegression model, save with joblib
- [ ] Seed Firestore with 1000+ pre-computed decisions
- [ ] Load BigQuery table from seeded data

**Day 2:**
- [ ] Build FastAPI backend skeleton
- [ ] Implement `/analyze-dataset` endpoint
- [ ] Design Gemini bias detection prompt (iterating until output is clean JSON)
- [ ] Add dataset stat computation (pandas)

**Day 3:**
- [ ] Test `/analyze-dataset` end-to-end
- [ ] Pre-cache bias report for demo CSV
- [ ] Write unit tests for dataset parsing

---

### Days 4–6: SHAP + Explainability API

**Day 4:**
- [ ] Implement `ml/explainer.py` with SHAP LinearExplainer
- [ ] Implement gender-proxy composite score
- [ ] Test SHAP values against expected bias patterns

**Day 5:**
- [ ] Implement `/explain-decision` endpoint
- [ ] Design Gemini function-calling schema
- [ ] Test Hindi output quality

**Day 6:**
- [ ] Pre-seed 5 named demo cases (Priya Sharma, Rekha Devi, etc.)
- [ ] Verify legal note generation
- [ ] Test English/Hindi toggle

---

### Days 7–9: Firestore + BigQuery Audit

**Day 7:**
- [ ] Finalize Firestore schema, seed 1000+ docs
- [ ] Implement BigQuery query in `/audit-history`

**Day 8:**
- [ ] Implement timeline aggregation
- [ ] Build remediation queue logic
- [ ] Generate Gemini compliance report

**Day 9:**
- [ ] Test full audit pipeline
- [ ] Pre-cache audit results for demo
- [ ] Validate all BigQuery queries

---

### Days 10–12: Frontend

**Day 10:**
- [ ] React app scaffold (Vite)
- [ ] Design system: dark theme + gold accents + Devanagari font support
- [ ] Layout: 3-tab navigation (Data Owner / Citizen / Regulator)

**Day 11:**
- [ ] Feature 1 UI: CSV upload → loading state → Bias Genome Report
  - Bias heatmap (Chart.js)
  - Top 5 risky features with risk scores
- [ ] Feature 2 UI: Decision ID input → SHAP waterfall → Hindi explanation

**Day 12:**
- [ ] Feature 3 UI: Audit timeline (Chart.js) → flagged cases table → compliance report
- [ ] Hindi/English toggle
- [ ] Architecture diagram page (roadmap vs MVP)
- [ ] Responsive polish

---

### Days 13–14: Demo Stabilization

**Day 13:**
- [ ] Containerize backend (Dockerfile)
- [ ] Cloud Run deployment
- [ ] Firebase Hosting deployment
- [ ] End-to-end smoke test all 3 flows

**Day 14:**
- [ ] Final demo run (3 full passes, timed)
- [ ] README with setup instructions + demo script
- [ ] Pre-warm all cache endpoints
- [ ] Record backup demo video

---

## 8. File Structure

```
C:\nyaya\
├── README.md
├── .gitignore
├── frontend\
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src\
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── components\
│       │   ├── BiasReport.jsx
│       │   ├── DecisionExplainer.jsx
│       │   ├── AuditTimeline.jsx
│       │   ├── HeatMap.jsx
│       │   ├── LanguageToggle.jsx
│       │   └── ArchitectureDiagram.jsx
│       └── api\
│           └── client.js
├── backend\
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py              ← FastAPI app
│   ├── routers\
│   │   ├── bias.py          ← /analyze-dataset
│   │   ├── explain.py       ← /explain-decision
│   │   └── audit.py         ← /audit-history
│   ├── services\
│   │   ├── gemini_service.py
│   │   ├── firestore_service.py
│   │   └── bigquery_service.py
│   └── config.py
├── ml\
│   ├── train_model.py       ← one-time training script
│   ├── explainer.py         ← SHAP logic
│   ├── seed_data.py         ← generate + seed 1000+ decisions
│   ├── models\
│   │   ├── loan_model.joblib
│   │   └── scaler.joblib
│   └── data\
│       ├── loan_dataset.csv       ← 1000-row synthetic dataset
│       └── demo_dataset.csv       ← pre-seeded demo CSV
└── docs\
    ├── architecture.md
    ├── api_reference.md
    ├── demo_script.md
    └── dpdpa_alignment.md
```

---

## 9. Demo Script (3 Minutes)

**0:00 — Hook (20s)**
> "Every day, 50 million Indians are denied loans, welfare, and jobs by AI systems they cannot question. NYAYA changes that."
> [Show homepage with tagline]

**0:20 — Feature 1: Bias Genome Report (45s)**
> "We're a government data officer. We upload our loan approval dataset."
> [Upload demo_dataset.csv → loading spinner 8-12s → Bias Report appears]
> "Gemini finds that pin_code — a postal code — is acting as a caste proxy, flagging 91% correlation. Feature risk scores appear. Heatmap shows women in rural UP face 3x rejection rates."

**1:05 — Feature 2: Citizen Explanation (40s)**
> "Now I'm Priya Sharma from Sitapur, UP. My loan was rejected. I enter my decision ID."
> [Enter DEC-20241105-0042 → explanation appears in Hindi]
> "In her language, she learns that her pin code — not her creditworthiness — drove the rejection. And a legal note: this may be challengeable under DPDPA Section 12(2)."
> [Toggle to English]

**1:45 — Feature 3: Retroactive Audit (50s)**
> "A regulator now asks: how many decisions like Priya's happened in 2024?"
> [Click Audit tab → timeline appears → 143 flagged cases highlighted]
> "BigQuery scans 1000+ decisions. 143 had gender proxy scores above 0.30. Gemini generates a compliance report recommending remediation."
> [Show remediation queue with Priya at top]

**2:35 — Architecture (15s)**
> [Show architecture diagram — MVP vs Roadmap clearly separated]
> "Cloud Run, Firestore, BigQuery, Vertex AI. Fully deployable today. Pub/Sub and vector search on the roadmap."

**2:50 — Closing (10s)**
> "NYAYA: Detect bias before it harms. Explain decisions in Hindi. Audit the past to fix the future."

---

## 10. Tech Stack Justification

| Technology | Why Used | Alternative Rejected |
|------------|----------|---------------------|
| Gemini 1.5 Pro | 1M token context window accepts full dataset; function calling enables SHAP integration | GPT-4 (non-Google) |
| Cloud Run | Serverless, scales to zero, fast cold start | GKE (overkill for MVP) |
| Firestore | Real-time reads, flexible schema for decisions | Cloud SQL (rigid schema) |
| BigQuery | Columnar scan for SHAP threshold queries across 1M+ rows | Firestore queries (slow for analytics) |
| SHAP LinearExplainer | Ground-truth feature attribution for LogisticRegression | LIME (less stable) |
| React + Vite | Fast dev, Chart.js ecosystem | Flutter Web (slower build) |
| Firebase Hosting | Zero-config CDN, pairs with Firestore | Cloud Storage (manual) |

---

## 11. DPDPA & Legal Alignment

| NYAYA Feature | Legal Basis |
|--------------|-------------|
| Bias Genome Report | DPDPA 2023, Section 4 (fair processing); Schedule II, Item 7 |
| Hindi Explanation | DPDPA 2023, Section 12(2) (right to explanation) |
| Retroactive Audit | Article 14, Constitution (equality before law); DPDPA Section 44 |
| Remediation Queue | DPDPA Section 12(4) (data principal grievance) |

---

## 12. Open Questions for User

> [!IMPORTANT]
> **GCP Project**: Do you have an existing GCP project, or should setup instructions assume a fresh project? I'll generate all Terraform/gcloud commands either way.

> [!IMPORTANT]
> **Gemini API Key**: Will you use Vertex AI (recommended, needs GCP billing) or Google AI Studio API key (free tier)? The backend will support both via env variable.

> [!NOTE]
> **Execution Mode**: I will now build the full codebase file-by-file, starting with Day 1 tasks. Confirm to proceed, or let me know any adjustments to the plan first.

---

## 13. Verification Plan

### Automated
- `pytest backend/tests/` — API endpoint unit tests with mocked Gemini + Firestore
- `npm run build` — Frontend build succeeds
- `docker build -t nyaya-backend .` — Container builds clean

### Manual (Demo Dry Run)
1. Upload `demo_dataset.csv` → verify bias report JSON + heatmap renders
2. Enter decision ID `DEC-20241105-0042` → verify Hindi explanation appears
3. Open Audit tab → verify 143+ flagged cases + timeline chart
4. Toggle Hindi↔English → verify both render without flash

### Performance Gates
- `/analyze-dataset`: ≤ 12s (Gemini latency)
- `/explain-decision`: ≤ 5s
- `/audit-history`: ≤ 2s (precomputed BigQuery)
- Frontend First Contentful Paint: ≤ 1.5s
