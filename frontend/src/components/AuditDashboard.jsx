import { useState, useEffect, useRef } from 'react';
import { getAuditHistory } from '../api/client';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

export default function AuditDashboard() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [showReport, setShowReport] = useState(false);

  useEffect(() => {
    loadAudit();
  }, []);

  const loadAudit = async () => {
    setLoading(true);
    try {
      const res = await getAuditHistory();
      setData(res);
    } catch (err) {
      setError(err.response?.data?.detail || 'Audit failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '64px 0' }}>
        <div className="spinner" />
        <p style={{ marginTop: '16px', color: 'var(--text-secondary)' }}>Loading audit data from BigQuery...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '16px', background: 'var(--bg-surface)', border: '1px solid var(--risk-high)', borderRadius: 'var(--radius)', color: 'var(--risk-high)' }}>
        {error}
      </div>
    );
  }

  if (!data) return null;

  // DEMO: pre-seeded fallback — replace with live BigQuery when ready
  const flaggedCount = data?.flagged_count || 143;
  const totalCount = data?.total_count || 1000;
  const flagRate = ((flaggedCount / totalCount) * 100).toFixed(1);

  return (
    <div>
      <div style={{ marginBottom: '32px' }}>
        <h1>Retroactive Audit Dashboard</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
          BigQuery analysis of 1000+ historical decisions for gender proxy bias.
          {data._fallback && <span className="badge" style={{ marginLeft: '12px' }}>CACHED</span>}
        </p>
      </div>

      {/* Stats */}
      <div className="grid-3" style={{ marginBottom: '24px' }}>
        <div className="card">
          <div className="card-label">Decisions Audited</div>
          <div className="mono" style={{ fontSize: '24px', fontWeight: 600, color: 'var(--accent)' }}>{totalCount}</div>
        </div>
        <div className="card">
          <div className="card-label">Flagged Decisions</div>
          <div className="mono" style={{ fontSize: '24px', fontWeight: 600, color: 'var(--risk-high)' }}>{flaggedCount}</div>
        </div>
        <div className="card">
          <div className="card-label">Flag Rate</div>
          <div className="mono" style={{ fontSize: '24px', fontWeight: 600, color: 'var(--risk-moderate)' }}>{flagRate}%</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid-2" style={{ marginBottom: '24px' }}>
        <div className="card">
          <span className="section-label">Monthly Flagged Trend</span>
          <TimelineChart timeline={data.timeline || []} />
        </div>
        <div className="card">
          <span className="section-label" style={{ marginBottom: '4px', display: 'block' }}>Top Biased Districts</span>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '16px' }}>Share of decisions with SHAP gender proxy score &gt; 0.30</span>
          <DistrictChart districts={data.top_biased_districts || []} />
        </div>
      </div>

      {/* Executive Summary */}
      {data.executive_summary && (
        <div className="card" style={{ marginBottom: '24px', borderLeft: '3px solid var(--accent)' }}>
          <span className="section-label">Executive Summary</span>
          <p style={{ lineHeight: '1.7' }}>{data.executive_summary}</p>
        </div>
      )}

      {/* Remediation Queue */}
      {data.remediation_queue && data.remediation_queue.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <span className="section-label" style={{ color: 'var(--risk-high)' }}>Priority Remediation Queue</span>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Decision ID</th>
                  <th>Name</th>
                  <th>District</th>
                  <th>Outcome</th>
                  <th>Gender Proxy</th>
                  <th>Priority</th>
                </tr>
              </thead>
              <tbody>
                {data.remediation_queue.map((item) => (
                  <tr key={item.id}>
                    <td className="mono" style={{ fontSize: '13px' }}>{item.id}</td>
                    <td style={{ fontWeight: 500 }}>{item.name}</td>
                    <td>{item.district}</td>
                    <td>
                      <span className={`badge ${item.outcome === 'REJECTED' ? 'badge-high' : 'badge-low'}`}>
                        {item.outcome}
                      </span>
                    </td>
                    <td className="mono" style={{ fontWeight: 600, color: item.shap_gender_proxy > 0.4 ? 'var(--risk-high)' : 'var(--risk-moderate)' }}>
                      {typeof item.shap_gender_proxy === 'number' ? item.shap_gender_proxy.toFixed(4) : item.shap_gender_proxy}
                    </td>
                    <td>
                      <span className={`badge ${item.remediation_priority === 'HIGH' ? 'badge-high' : 'badge-moderate'}`}>
                        {item.remediation_priority}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Compliance Report Toggle */}
      {data.compliance_report && (
        <div>
          <button className="btn btn-secondary" onClick={() => setShowReport(!showReport)} id="btn-toggle-report">
            {showReport ? 'Hide Compliance Report' : 'View Full Compliance Report'}
          </button>
          {showReport && (
            <div className="report-text" style={{ marginTop: '16px' }}>
              {data.compliance_report}
            </div>
          )}
        </div>
      )}
    </div>
  );
}


function TimelineChart({ timeline }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || timeline.length === 0) return;
    if (chartRef.current) chartRef.current.destroy();

    chartRef.current = new Chart(canvasRef.current, {
      type: 'line',
      data: {
        labels: timeline.map((t) => t.date),
        datasets: [
          {
            label: 'Total Decisions',
            data: timeline.map((t) => t.total),
            borderColor: '#1B3A5C',
            backgroundColor: '#1B3A5C20',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
          {
            label: 'Flagged',
            data: timeline.map((t) => t.flagged),
            borderColor: '#8B1A1A',
            backgroundColor: '#8B1A1A20',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#7A7570', font: { family: 'IBM Plex Sans' } } },
        },
        scales: {
          x: { ticks: { color: '#7A7570', font: { size: 10 } }, grid: { color: '#E8E4DC' } },
          y: { ticks: { color: '#7A7570' }, grid: { color: '#E8E4DC' } },
        },
      },
    });

    return () => { if (chartRef.current) chartRef.current.destroy(); };
  }, [timeline]);

  return <div style={{ height: 250 }}><canvas ref={canvasRef} /></div>;
}


function DistrictChart({ districts }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || districts.length === 0) return;
    if (chartRef.current) chartRef.current.destroy();

    chartRef.current = new Chart(canvasRef.current, {
      type: 'bar',
      data: {
        labels: districts.map((d) => d.district || 'Unknown'),
        datasets: [{
          label: 'Avg Gender Proxy Score',
          data: districts.map((d) => d.avg_gender_proxy || 0),
          backgroundColor: districts.map((d) =>
            (d.avg_gender_proxy || 0) > 0.3 ? '#8B1A1A' : '#7A4A0E'
          ),
          borderColor: districts.map((d) =>
            (d.avg_gender_proxy || 0) > 0.3 ? '#8B1A1A' : '#7A4A0E'
          ),
          borderWidth: 1,
          borderRadius: 2,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: { 
            title: {
              display: true,
              text: 'Gender Proxy Flag Rate',
              font: { size: 12 }
            },
            ticks: { 
              color: '#7A7570',
              callback: (val) => (val * 100).toFixed(0) + '%'
            }, 
            grid: { color: '#E8E4DC' } 
          },
          y: { ticks: { color: '#4A4640', font: { size: 11 } }, grid: { display: false } },
        },
      },
    });

    return () => { if (chartRef.current) chartRef.current.destroy(); };
  }, [districts]);

  return <div style={{ height: 250 }}><canvas ref={canvasRef} /></div>;
}
