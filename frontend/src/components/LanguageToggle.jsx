export default function LanguageToggle({ value, onChange }) {
  return (
    <div style={{
      display: 'inline-flex', borderRadius: 'var(--radius)',
      background: 'var(--bg-surface-secondary)', border: '1px solid var(--border)',
      overflow: 'hidden',
    }}>
      <button
        id="lang-hi"
        onClick={() => onChange('hi')}
        style={{
          padding: '8px 16px', border: 'none', cursor: 'pointer',
          fontFamily: "'Noto Sans Devanagari', 'IBM Plex Sans', sans-serif",
          fontSize: '13px', fontWeight: 500,
          background: value === 'hi' ? 'var(--accent)' : 'transparent',
          color: value === 'hi' ? '#FFFFFF' : 'var(--text-secondary)',
        }}
      >
        हिंदी
      </button>
      <button
        id="lang-en"
        onClick={() => onChange('en')}
        style={{
          padding: '8px 16px', border: 'none', cursor: 'pointer',
          fontFamily: "'IBM Plex Sans', sans-serif",
          fontSize: '13px', fontWeight: 500,
          background: value === 'en' ? 'var(--accent)' : 'transparent',
          color: value === 'en' ? '#FFFFFF' : 'var(--text-secondary)',
        }}
      >
        English
      </button>
    </div>
  );
}
