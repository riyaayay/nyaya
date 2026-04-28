export default function HowNyayaWorks({ open, onClose }) {
  return (
    <div className={`slide-over-backdrop${open ? ' open' : ''}`} onClick={onClose}>
      <div className="slide-over" onClick={(e) => e.stopPropagation()}>
        <button className="slide-over-close" onClick={onClose} id="close-how-it-works">×</button>

        <h2 style={{ marginBottom: '8px', fontSize: '20px', color: 'var(--accent)' }}>
          How NYAYA Works
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '32px', fontSize: '14px' }}>
          Three layers of AI accountability for India's automated decision systems.
        </p>

        {/* Step 1 */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <div className="mono" style={{ width: 28, height: 28, border: '1px solid var(--border-strong)', borderRadius: '4px', background: 'var(--bg-surface-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, color: 'var(--text-primary)', flexShrink: 0 }}>1</div>
            <h3>Bias Genome Scanner</h3>
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: '1.7', paddingLeft: '40px' }}>
            A data owner uploads their loan decision CSV. NYAYA computes <strong style={{ color: 'var(--text-primary)' }}>Pearson correlations</strong> between
            every feature and the outcome (deterministic, verifiable). These statistical findings are then sent to
            <strong style={{ color: 'var(--accent)' }}> Gemini 1.5 Pro</strong> which interprets them in legal context — identifying proxy
            discriminators (like PIN code → caste), rating legal exposure under DPDPA 2023, and generating an executive summary.
          </p>
          <div style={{ paddingLeft: '40px', marginTop: '8px', fontSize: '13px', color: 'var(--text-muted)' }}>
            <strong>Without Gemini:</strong> Raw correlation numbers only. No legal interpretation, no proxy identification, no executive summary.
          </div>
        </div>

        {/* Step 2 */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <div className="mono" style={{ width: 28, height: 28, border: '1px solid var(--border-strong)', borderRadius: '4px', background: 'var(--bg-surface-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, color: 'var(--text-primary)', flexShrink: 0 }}>2</div>
            <h3>Citizen Explainer</h3>
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: '1.7', paddingLeft: '40px' }}>
            A citizen enters their decision ID. NYAYA runs <strong style={{ color: 'var(--text-primary)' }}>SHAP LinearExplainer</strong> to
            compute exact feature attributions (mathematically proven, not AI-generated). These SHAP values are sent to
            <strong style={{ color: 'var(--accent)' }}> Gemini</strong> which translates them into a plain-language explanation in
            <strong style={{ color: 'var(--text-primary)' }}> Hindi</strong> — including a legal rights note citing DPDPA Section 12(2).
          </p>
          <div style={{ paddingLeft: '40px', marginTop: '8px', fontSize: '13px', color: 'var(--text-muted)' }}>
            <strong>Without Gemini:</strong> Raw SHAP float values. Technically accurate but incomprehensible to a citizen and legally insufficient.
          </div>
        </div>

        {/* Step 3 */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <div className="mono" style={{ width: 28, height: 28, border: '1px solid var(--border-strong)', borderRadius: '4px', background: 'var(--bg-surface-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, color: 'var(--text-primary)', flexShrink: 0 }}>3</div>
            <h3>Retroactive Audit</h3>
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: '1.7', paddingLeft: '40px' }}>
            A regulator queries historical decisions. <strong style={{ color: 'var(--text-primary)' }}>BigQuery</strong> runs
            3 analytical queries: monthly trend, district hotspots, feature distribution. Summary statistics are sent to
            <strong style={{ color: 'var(--accent)' }}> Gemini</strong> to generate a formal DPDPA compliance report with
            remediation steps.
          </p>
          <div style={{ paddingLeft: '40px', marginTop: '8px', fontSize: '13px', color: 'var(--text-muted)' }}>
            <strong>Without Gemini:</strong> Raw SQL aggregates. No compliance narrative, no legal exposure assessment, no remediation plan.
          </div>
        </div>

        {/* DPDPA Alignment */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <h3 style={{ marginBottom: '12px' }}>DPDPA 2023 Alignment</h3>
          <div style={{ display: 'grid', gap: '8px', fontSize: '14px' }}>
            <div><strong>Section 4:</strong> Fair and reasonable processing → Bias Genome Scanner</div>
            <div><strong>Section 12(2):</strong> Right to explanation → Citizen Explainer (Hindi)</div>
            <div><strong>Section 44:</strong> Penalties for violations → Retroactive Audit</div>
            <div><strong>Article 14:</strong> Equality before law → All three features</div>
          </div>
        </div>

        {/* Limitation */}
        <div style={{ padding: '16px', background: 'var(--bg-surface)', borderLeft: '3px solid var(--risk-moderate)', fontSize: '13px', color: 'var(--text-secondary)' }}>
          <strong style={{ color: 'var(--risk-moderate)' }}>Limitation:</strong> NYAYA detects statistical bias patterns — it does not determine legal guilt.
          These findings are inputs to institutional review, not replacements for it.
        </div>
      </div>
    </div>
  );
}
