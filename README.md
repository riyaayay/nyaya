# NYAYA

**India's AI Accountability Infrastructure**

Detect bias in AI datasets before deployment. Explain automated decisions to affected citizens in Hindi. Retroactively audit historical decisions across millions of rows to ensure compliance with the **Digital Personal Data Protection Act (DPDPA) 2023** and **Article 14** of the Constitution.

---

## 🏛 The Three Pillars of NYAYA

1. **Bias Genome Scanner (Data Owner)**: Upload a dataset. NYAYA uses deterministic statistical analysis (Pearson correlations, Disparate Impact Ratio) combined with Gemini 1.5 Pro to identify intersectional bias and proxy discriminators (e.g., PIN code acting as a proxy for caste/religion).
2. **Citizen Explainer (Citizen)**: Enter a decision ID. NYAYA computes mathematically rigorous SHAP feature attributions and uses Gemini to generate a plain-language explanation in Hindi, including a legal rights note under DPDPA Section 12(2).
3. **Retroactive Audit (Regulator)**: BigQuery scans historical decisions, flagging those where the "gender proxy score" exceeds acceptable thresholds. Gemini generates a formal compliance report and remediation queue.

---

## 🚀 Quick Start (Local Demo)

You can run the entire MVP locally on your machine. It uses pre-computed demo caches so it works **without a Gemini API key or GCP account**.

### Prerequisites
- Python 3.11+
- Node.js 20+

### 1. Start the Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```
The API will run at `http://localhost:8000`

### 2. Start the Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
The UI will open at `http://localhost:5173`

---

## 🧪 Running the Demo

### Scenario 1: The Data Owner
1. Navigate to the **Data Owner** tab.
2. Upload the `ml/data/demo_dataset.csv` file.
3. Review the Bias Genome Report, noting how `pin_code` acts as a proxy discriminator and the compounding intersectional bias for rural women.

### Scenario 2: The Citizen
1. Navigate to the **Citizen** tab.
2. Click on the demo case for **Priya Sharma** (or enter `DEC-20241105-0042`).
3. See how the SHAP waterfall explains exactly why she was rejected, and read the plain-language Hindi explanation and DPDPA rights note.

### Scenario 3: The Regulator
1. Navigate to the **Regulator** tab.
2. Review the timeline of flagged decisions.
3. See how decisions are triaged into a remediation queue based on their gender proxy scores.
4. Expand the formal compliance report.

---

## 🏗 Architecture & Tech Stack

### MVP Layer (Currently Implemented)
- **Frontend**: React + Vite + Chart.js (Dark/Gold Design System)
- **Backend**: FastAPI (Python)
- **AI/ML Base**: scikit-learn LogisticRegression + SHAP LinearExplainer
- **LLM Engine**: Gemini 1.5 Pro (via Google AI Studio or Vertex AI)
- **Database**: Firestore (decisions) + BigQuery (analytical scans)

### Roadmap Layer
- Pub/Sub for real-time decision ingestion
- Vector Search for semantic similarity matching of bias cases
- IVR integration for rural citizen access

---

## 📚 Machine Learning Pipeline

If you wish to retrain the model or regenerate the synthetic data:

```bash
# 1. Generate new synthetic data with deliberate bias patterns
python ml/seed_data.py

# 2. Train the LogisticRegression model and save SHAP artifacts
python ml/train_model.py
```

### Why SHAP + Gemini?
Raw SHAP values are mathematically rigorous but incomprehensible to a citizen. Gemini bridges the gap between ground-truth attribution and human understanding, translating `pin_code_encoded: -0.34` into a legally empowering explanation in the citizen's native language.

---

*Built for the DPDPA 2023 era.*
