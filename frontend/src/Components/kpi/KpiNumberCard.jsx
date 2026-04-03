export default function KpiNumberCard({ label, value, unit = '', title }) {
  const displayValue = typeof value === 'number' && Number.isFinite(value) ? value.toFixed(2) : '—';

  return (
    <div style={{
      padding: '24px',
      background: '#fff',
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      textAlign: 'center',
    }}>
      {title && <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 500, color: '#6b7280' }}>{title}</h3>}
      <div style={{ fontSize: '48px', fontWeight: 700, color: '#1f2937', lineHeight: 1 }}>
        {displayValue}
        {unit && <span style={{ fontSize: '24px', fontWeight: 500, color: '#6b7280' }}>{unit}</span>}
      </div>
      {label && <div style={{ marginTop: '8px', fontSize: '14px', color: '#6b7280' }}>{label}</div>}
    </div>
  );
}
