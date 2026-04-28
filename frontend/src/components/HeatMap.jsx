export default function HeatMap() {
  const data = [
    { row: 'Male', metro: '91%', tier2: '78%', rural: '44%' },
    { row: 'Female', metro: '79%', tier2: '61%', rural: '22%' }
  ];

  const getStyle = (val) => {
    const num = parseInt(val.replace('%', ''), 10);
    if (num >= 70) return { background: '#EAF0E8', color: '#1A4A2E' };
    if (num >= 40) return { background: '#F5F0E6', color: '#7A4A0E' };
    return { background: '#F5E8E8', color: '#8B1A1A' };
  };

  return (
    <div className="table-container" style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead style={{ background: 'var(--accent)', color: '#FFFFFF', fontFamily: 'var(--font-mono)', fontSize: '12px', textTransform: 'uppercase' }}>
          <tr>
            <th style={{ padding: '12px 16px', fontWeight: 500 }}></th>
            <th style={{ padding: '12px 16px', fontWeight: 500 }}>Metro (110xxx, 400xxx, 600xxx)</th>
            <th style={{ padding: '12px 16px', fontWeight: 500 }}>Tier-2 (226xxx, 500xxx)</th>
            <th style={{ padding: '12px 16px', fontWeight: 500 }}>Rural (462xxx)</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.row} style={{ borderTop: '1px solid var(--rule)' }}>
              <td style={{ padding: '12px 16px', fontWeight: 500, fontSize: '14px', background: 'var(--bg-surface)' }}>
                {row.row}
              </td>
              <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: 600, ...getStyle(row.metro) }}>
                {row.metro}
              </td>
              <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: 600, ...getStyle(row.tier2) }}>
                {row.tier2}
              </td>
              <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: 600, ...getStyle(row.rural) }}>
                {row.rural}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
