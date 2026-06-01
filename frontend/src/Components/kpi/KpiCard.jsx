import { memo } from 'react';

function KpiCard({ title, loading = false, error = null, children, className = '', bodyMinHeight, loadingLabel }) {
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
    minHeight: bodyMinHeight ?? '120px',
    position: 'relative',
    overflowX: 'visible',
    overflowY: 'visible',
    display: 'flex',
    flexDirection: 'column',
  };

  const loadingBodyStyle = {
    ...bodyStyle,
    alignItems: 'center',
    justifyContent: 'center',
  };

  const chartContainerStyle = {
    width: '100%',
    minWidth: 0,
  };

  const loadingLabelStyle = {
    marginLeft: '12px',
    fontSize: '14px',
    color: '#6b7280',
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
      <div style={loading ? loadingBodyStyle : bodyStyle}>
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="kpi-loader"></div>
            {loadingLabel && <span style={loadingLabelStyle}>{loadingLabel}</span>}
          </div>
        )}
        {error && (
          <div style={{ minHeight: '168px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={errorStyle}>Error: {typeof error === 'string' ? error : error?.message || 'Unknown error'}</div>
          </div>
        )}
        {!loading && !error && !children && (
          <div style={{ minHeight: '168px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={emptyStyle}>No data</div>
          </div>
        )}
        {!loading && !error && children && <div style={chartContainerStyle}>{children}</div>}
      </div>
    </div>
  );
}

export default memo(KpiCard);
