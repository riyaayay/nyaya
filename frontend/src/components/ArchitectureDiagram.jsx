export default function ArchitectureDiagram() {
  const mvpNodes = [
    { label: 'React + Vite', sub: 'Firebase Hosting', x: 80, y: 60, w: 140 },
    { label: 'FastAPI', sub: 'Cloud Run', x: 320, y: 60, w: 140 },
    { label: 'Gemini 1.5 Pro', sub: 'Vertex AI', x: 200, y: 200, w: 160 },
    { label: 'Firestore', sub: '1000+ decisions', x: 440, y: 200, w: 140 },
    { label: 'BigQuery', sub: 'Analytical queries', x: 320, y: 330, w: 160 },
    { label: 'SHAP', sub: 'LinearExplainer', x: 80, y: 200, w: 130 },
    { label: 'scikit-learn', sub: 'LogisticRegression', x: 80, y: 330, w: 150 },
  ];

  const roadmapNodes = [
    { label: 'Pub/Sub' }, { label: 'HDBSCAN' }, { label: 'Vector Search' },
    { label: 'Cloud Armor' }, { label: 'IVR' }, { label: 'LangChain' },
  ];

  const connections = [
    [0, 1], [1, 2], [1, 3], [1, 4], [1, 5], [5, 6],
  ];

  return (
    <div>
      <div style={{ marginBottom: '32px' }}>
        <h1>System Architecture</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
          NYAYA's technical architecture — MVP layer (built) vs Roadmap (planned).
        </p>
      </div>

      {/* MVP Layer */}
      <div className="card" style={{ marginBottom: '24px', padding: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
          <h2 style={{ color: 'var(--accent)' }}>MVP Layer (Built & Deployed)</h2>
        </div>

        <svg viewBox="0 0 620 420" style={{ width: '100%', maxWidth: 620 }}>
          {/* Connection lines */}
          {connections.map(([from, to], i) => {
            const a = mvpNodes[from], b = mvpNodes[to];
            const ax = a.x + a.w / 2, ay = a.y + 25;
            const bx = b.x + b.w / 2, by = b.y + 25;
            return (
              <line key={i} x1={ax} y1={ay} x2={bx} y2={by}
                stroke="#B8B2A8" strokeWidth="1.5" strokeDasharray="6,4" />
            );
          })}

          {/* Nodes */}
          {mvpNodes.map((node, i) => (
            <g key={i}>
              <rect x={node.x} y={node.y} width={node.w} height={50} rx="4"
                fill="#FFFFFF" stroke="#1B3A5C" strokeWidth="1.5" />
              <text x={node.x + node.w / 2} y={node.y + 22} textAnchor="middle"
                fill="#1A1916" fontSize="12" fontWeight="500" fontFamily="IBM Plex Sans">{node.label}</text>
              <text x={node.x + node.w / 2} y={node.y + 38} textAnchor="middle"
                fill="#7A7570" fontSize="10" fontFamily="IBM Plex Mono">{node.sub}</text>
            </g>
          ))}

          {/* API endpoints */}
          <text x="390" y="50" fill="#7A4A0E" fontSize="9" fontFamily="IBM Plex Mono">/analyze-dataset</text>
          <text x="390" y="95" fill="#7A4A0E" fontSize="9" fontFamily="IBM Plex Mono">/explain-decision</text>
          <text x="390" y="108" fill="#7A4A0E" fontSize="9" fontFamily="IBM Plex Mono">/audit-history</text>
        </svg>
      </div>

      {/* Roadmap Layer */}
      <div className="card" style={{ background: 'var(--bg-surface-secondary)', borderStyle: 'dashed' }}>
        <span className="section-label" style={{ marginBottom: '16px' }}>Roadmap Layer (Not Built)</span>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
          {roadmapNodes.map((node) => (
            <div key={node.label} className="arch-node roadmap">{node.label}</div>
          ))}
        </div>
        <p style={{ marginTop: '16px', fontSize: '13px', color: 'var(--text-muted)' }}>
          These components represent planned extensions: real-time event streaming, anomaly detection,
          semantic search across decisions, DDoS protection, voice-based IVR for rural access, and LLM orchestration.
        </p>
      </div>

      {/* Tech Stack */}
      <div style={{ marginTop: '32px' }}>
        <span className="section-label">Tech Stack Justification</span>
        <div className="table-container" style={{ marginTop: '16px' }}>
          <table>
            <thead>
              <tr><th>Technology</th><th>Why Used</th><th>Alternative Rejected</th></tr>
            </thead>
            <tbody>
              <tr><td style={{ fontWeight: 500 }}>Gemini 1.5 Pro</td><td>1M token context window accepts full dataset; function calling enables SHAP integration</td><td>GPT-4 (non-Google)</td></tr>
              <tr><td style={{ fontWeight: 500 }}>Cloud Run</td><td>Serverless, scales to zero, fast cold start</td><td>GKE (overkill)</td></tr>
              <tr><td style={{ fontWeight: 500 }}>Firestore</td><td>Real-time reads, flexible schema for decisions</td><td>Cloud SQL (rigid)</td></tr>
              <tr><td style={{ fontWeight: 500 }}>BigQuery</td><td>Columnar scan for SHAP threshold queries across 1M+ rows</td><td>Firestore (slow analytics)</td></tr>
              <tr><td style={{ fontWeight: 500 }}>SHAP LinearExplainer</td><td>Ground-truth feature attribution for LogisticRegression</td><td>LIME (less stable)</td></tr>
              <tr><td style={{ fontWeight: 500 }}>React + Vite</td><td>Fast dev, Chart.js ecosystem</td><td>Flutter Web (slower)</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Competitive Differentiation */}
      <div style={{ marginTop: '32px' }}>
        <span className="section-label">Competitive Differentiation</span>
        <div className="table-container" style={{ marginTop: '16px' }}>
          <table>
            <thead>
              <tr><th>Feature</th><th>NYAYA</th><th>Legacy Tools (e.g., AIF360)</th><th>Manual Audit</th></tr>
            </thead>
            <tbody>
              <tr><td style={{ fontWeight: 500 }}>Legal Alignment</td><td>Native DPDPA 2023 & Article 14 mapping</td><td>None (Academic focus)</td><td>High subjectivity</td></tr>
              <tr><td style={{ fontWeight: 500 }}>Citizen Explanations</td><td>Automated, localized (Hindi/English)</td><td>None (Developer focus)</td><td>Extremely slow</td></tr>
              <tr><td style={{ fontWeight: 500 }}>Scale</td><td>BigQuery powered (1M+ rows)</td><td>In-memory (Pandas limits)</td><td>Sample-based only</td></tr>
              <tr><td style={{ fontWeight: 500 }}>Bias Detection</td><td>Intersectional proxy detection (e.g., PIN code + Gender)</td><td>Basic single-feature parity</td><td>Prone to human error</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
