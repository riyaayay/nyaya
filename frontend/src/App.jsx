import { useState } from 'react';
import BiasReport from './components/BiasReport';
import DecisionExplainer from './components/DecisionExplainer';
import AuditDashboard from './components/AuditDashboard';
import HowNyayaWorks from './components/HowNyayaWorks';
import ArchitectureDiagram from './components/ArchitectureDiagram';

const TABS = [
  { id: 'bias', label: 'Institution View' },
  { id: 'explain', label: 'Applicant View' },
  { id: 'audit', label: 'Regulator View' },
  { id: 'arch', label: 'Technical Architecture' },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('bias');
  const [showHowItWorks, setShowHowItWorks] = useState(false);

  return (
    <div className="app-container">
      <header className="header">
        <div className="header-left">
          <div className="header-title">NYAYA</div>
          <div className="header-subtitle">न्याय — Neural Yield Auditing for Your Algorithms</div>
          <hr className="hr-rule" style={{ margin: '8px 0 0 0', width: '100%' }} />
        </div>
        <div className="header-right">
          98 records · Analysis complete · Gemini 1.5 Pro
        </div>
      </header>

      <nav className="nav-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            id={`tab-${tab.id}`}
            className={`nav-tab${activeTab === tab.id ? ' active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', paddingRight: '16px' }}>
          <button
            id="btn-how-it-works"
            className="btn btn-secondary btn-sm"
            onClick={() => setShowHowItWorks(true)}
          >
            How It Works
          </button>
        </div>
      </nav>

      <main className="main-content">
        {activeTab === 'bias' && <BiasReport />}
        {activeTab === 'explain' && <DecisionExplainer />}
        {activeTab === 'audit' && <AuditDashboard />}
        {activeTab === 'arch' && <ArchitectureDiagram />}
      </main>

      <HowNyayaWorks open={showHowItWorks} onClose={() => setShowHowItWorks(false)} />
    </div>
  );
}
