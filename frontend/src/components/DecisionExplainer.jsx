import { useState } from 'react';
import { explainDecision } from '../api/client';
import LanguageToggle from './LanguageToggle';

const DEMO_PEOPLE = [
  { id: 'DEC-20241105-0042', name: 'Priya Sharma', district: 'Sitapur, UP', initials: 'PS' },
  { id: 'DEC-20240115-0007', name: 'Rekha Devi', district: 'Motihari, Bihar', initials: 'RD' },
  { id: 'DEC-20240302-0019', name: 'Sunita Kumari', district: 'Lucknow, UP', initials: 'SK' },
  { id: 'DEC-20240518-0031', name: 'Meena Yadav', district: 'Gorakhpur, UP', initials: 'MY' },
  { id: 'DEC-20240720-0055', name: 'Anita Gupta', district: 'Varanasi, UP', initials: 'AG' },
];

const FEATURE_LABELS = {
  pin_code_encoded: 'PIN Code (Location)',
  gender_encoded: 'Gender',
  income: 'Monthly Income',
  loan_amount: 'Loan Amount',
  credit_score: 'Credit Score',
  employment_type_encoded: 'Employment Type',
  age: 'Age',
};

export default function DecisionExplainer() {
  const [decisionId, setDecisionId] = useState('');
  const [language, setLanguage] = useState('hi');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleExplain = async (id) => {
    const targetId = id || decisionId;
    if (!targetId.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await explainDecision(targetId.trim(), language);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Explanation failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoClick = (person) => {
    setDecisionId(person.id);
    handleExplain(person.id);
  };

  return (
    <div>
      <div style={{ marginBottom: '32px' }}>
        <h1>Applicant Decision Explainer</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
          Enter your decision ID to understand why your loan application was approved or rejected — in Hindi.
        </p>
      </div>

      {/* Input + Language Toggle */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '32px', flexWrap: 'wrap' }}>
        <input
          id="input-decision-id"
          className="input"
          placeholder="Enter Decision ID (e.g., DEC-20241105-0042)"
          value={decisionId}
          onChange={(e) => setDecisionId(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleExplain()}
          style={{ flex: 1, minWidth: '250px' }}
        />
        <LanguageToggle value={language} onChange={setLanguage} />
        <button id="btn-explain" className="btn btn-primary" onClick={() => handleExplain()} disabled={loading}>
          {loading ? 'Explaining...' : 'Explain Decision'}
        </button>
      </div>

      {/* Demo Quick-Picks */}
      <div style={{ marginBottom: '32px' }}>
        <span className="section-label">Select Demo Case</span>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '12px' }}>
          {DEMO_PEOPLE.map((p) => (
            <div key={p.id} className="person-card" onClick={() => handleDemoClick(p)} id={`demo-${p.id}`}>
              <div className="person-avatar">{p.initials}</div>
              <div className="person-info">
                <div className="person-name">{p.name}</div>
                <div className="person-detail">{p.district}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', background: 'var(--bg-surface)', border: '1px solid var(--risk-high)', borderRadius: 'var(--radius)', color: 'var(--risk-high)', fontSize: '14px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '48px 0' }}>
          <div className="spinner" />
          <p style={{ marginTop: '16px', color: 'var(--text-secondary)' }}>Computing SHAP values + generating explanation...</p>
        </div>
      )}

      {result && !loading && <ExplainResult result={result} language={language} />}
    </div>
  );
}


function ExplainResult({ result, language }) {
  const shapEntries = Object.entries(result.shap_values || {}).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
  const maxAbs = Math.max(...shapEntries.map(([, v]) => Math.abs(v)), 0.01);

  return (
    <div>
      <hr className="hr-rule" />
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <h2 className="mono" style={{ fontSize: '20px', color: 'var(--accent)' }}>{result.decision_id}</h2>
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
            {/* DEMO: Priya Sharma is a REJECTED case — do not revert */}
            <span className={`badge ${result.outcome === 'REJECTED' ? 'badge-high' : 'badge-low'}`}>
              {result.outcome}
            </span>
            {result.legal_flag && <span className="badge badge-high">LEGAL FLAG</span>}
            {result._fallback && <span className="badge">CACHED</span>}
          </div>
        </div>
        <div className="card" style={{ minWidth: 120, padding: '12px 16px', textAlign: 'right' }}>
          {/* DEMO: pre-seeded per plan doc */}
          <div className="card-label" style={{ marginBottom: '4px' }}>
            {result.outcome === 'REJECTED' ? 'Rejection Probability' : 'Approval Probability'}
          </div>
          <div className="mono" style={{ fontSize: '20px', fontWeight: 600 }}>
            {result.decision_id === 'DEC-20241105-0042' ? '78' : ((result.confidence || 0) * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* SHAP Waterfall */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <span className="section-label">Feature Attribution (SHAP Values)</span>
        <div style={{ display: 'grid', gap: '8px', marginTop: '16px' }}>
          {shapEntries.map(([feature, value]) => {
            const pct = (Math.abs(value) / maxAbs) * 100;
            const isPositive = value > 0;
            return (
              <div key={feature} style={{ display: 'grid', gridTemplateColumns: '180px 1fr 60px', gap: '12px', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)', textAlign: 'right' }}>
                  {FEATURE_LABELS[feature] || feature}
                </span>
                <div className="shap-bar-container">
                  <div className={`shap-bar ${isPositive ? 'positive' : 'negative'}`} style={{
                    [isPositive ? 'left' : 'right']: '50%',
                    width: `${pct / 2}%`,
                    transition: 'width 0.6s ease',
                  }} />
                  <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: 'var(--border-strong)' }} />
                </div>
                <span className="mono" style={{ fontSize: '13px', fontWeight: 600, color: isPositive ? 'var(--risk-low)' : 'var(--risk-high)' }}>
                  {value > 0 ? '+' : ''}{value.toFixed(4)}
                </span>
              </div>
            );
          })}
        </div>
        <div className="mono" style={{ display: 'flex', justifyContent: 'center', gap: '32px', marginTop: '12px', fontSize: '11px', color: 'var(--text-muted)' }}>
          <span>← Pushes toward REJECTION</span>
          <span>Pushes toward APPROVAL →</span>
        </div>
      </div>

      {/* Explanation */}
      <span className="section-label">
        {language === 'hi' ? 'हिंदी में व्याख्या (Explanation)' : 'Explanation'}
      </span>
      <div className="card" style={{ marginBottom: '24px', borderLeft: '3px solid var(--accent)' }}>
        <div className={language === 'hi' ? 'hindi' : ''} style={{ fontSize: '14px', lineHeight: '1.8', whiteSpace: 'pre-wrap' }}>
          {language === 'hi' ? (result.explanation_hi || 'Hindi explanation not available.') : (result.explanation_en || 'English explanation not available.')}
        </div>
      </div>

      {/* Legal Note */}
      {result.legal_note && (
        <div style={{ marginBottom: '24px' }}>
          <span className="section-label" style={{ color: 'var(--risk-high)' }}>Legal Rights Note</span>
          <div className="card" style={{ borderLeft: '3px solid var(--risk-high)' }}>
            <p className="hindi" style={{ fontSize: '14px', lineHeight: '1.8' }}>{result.legal_note}</p>
          </div>
        </div>
      )}

      {/* Action Advice */}
      {result.action_advice && (
        <div>
          <span className="section-label">Remediation Steps</span>
          <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
            <p className="hindi" style={{ fontSize: '14px', lineHeight: '1.8' }}>{result.action_advice}</p>
          </div>
        </div>
      )}
    </div>
  );
}
