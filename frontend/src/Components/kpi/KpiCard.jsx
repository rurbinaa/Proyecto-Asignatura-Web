export default function KpiCard({ title, loading = false, error = null, children, className = '' }) {
  const cardStyle = {
    background: '#fff',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    overflow: 'visible',
    minWidth: 0,
  };

  const headerStyle = {
    padding: '16px',
    borderBottom: '1px solid #e5e7eb',
    fontSize: '16px',
    fontWeight: 600,
    color: '#1f2937',
  };

  const bodyStyle = {
    padding: '0', // Charts handle their own padding for visual consistency
    minHeight: '120px',
    position: 'relative',
    overflowX: 'visible',
    overflowY: 'visible',
  };

  const centerContentStyle = {
    minHeight: '168px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };

  const chartContainerStyle = {
    width: '100%',
    minWidth: 0,
  };

  const spinnerStyle = {
    width: '40px',
    height: '40px',
    border: '4px solid #e5e7eb',
    borderTopColor: '#3b82f6',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  };

  const errorStyle = {
    color: '#ef4444',
    fontSize: '14px',
    textAlign: 'center',
  };

  const emptyStyle = {
    color: '#9ca3af',
    fontSize: '14px',
    textAlign: 'center',
  };

  return (
    <div className={`kpi-card ${className}`} style={cardStyle}>
      {title && <div style={headerStyle}>{title}</div>}
      <div style={bodyStyle}>
        {loading && (
          <div style={centerContentStyle}>
            <div style={spinnerStyle}></div>
          </div>
        )}
        {error && (
          <div style={centerContentStyle}>
            <div style={errorStyle}>Error: {typeof error === 'string' ? error : error?.message || 'Unknown error'}</div>
          </div>
        )}
        {!loading && !error && !children && (
          <div style={centerContentStyle}>
            <div style={emptyStyle}>Sin datos</div>
          </div>
        )}
        {!loading && !error && children && <div style={chartContainerStyle}>{children}</div>}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
