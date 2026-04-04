export default function HeatmapKpi({ data = [], title }) {
  if (!data || data.length === 0) {
    return (
      <div className="heatmap-kpi" style={{ padding: '16px', boxSizing: 'border-box' }}>
        {title && <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 }}>{title}</h3>}
        <div style={{ textAlign: 'center', color: '#666' }}>Sin datos</div>
      </div>
    );
  }

  const xLabels = [...new Set(data.map(d => d.x))].sort();
  const yLabels = [...new Set(data.map(d => d.y))].sort();
  const validValues = data.map(d => d.value).filter(v => v != null && !isNaN(v));
  const maxValue = validValues.length > 0 ? Math.max(...validValues) : 0;
  const minValue = validValues.length > 0 ? Math.min(...validValues) : 0;

  const getColor = (value) => {
    if (value == null) return '#e5e7eb';
    if (maxValue === minValue) return '#22c55e';
    const ratio = (value - minValue) / (maxValue - minValue);
    if (ratio < 0.5) {
      const r = Math.round(34 + (235 - 34) * (ratio * 2));
      const g = Math.round(197 + (173 - 197) * (ratio * 2));
      const b = Math.round(34 + (34 - 34) * (ratio * 2));
      return `rgb(${r}, ${g}, ${b})`;
    } else {
      const r = Math.round(235 + (239 - 235) * ((ratio - 0.5) * 2));
      const g = Math.round(173 - 173 * ((ratio - 0.5) * 2));
      const b = Math.round(34 + (68 - 34) * ((ratio - 0.5) * 2));
      return `rgb(${r}, ${g}, ${b})`;
    }
  };

  const getValue = (x, y) => {
    const item = data.find(d => d.x === x && d.y === y);
    return item ? item.value : null;
  };

  const cellStyle = {
    width: '60px',
    height: '40px',
    textAlign: 'center',
    verticalAlign: 'middle',
    fontSize: '12px',
    fontWeight: 500,
    border: '1px solid #e5e7eb',
  };

  return (
    <div className="heatmap-kpi" style={{ padding: '16px', boxSizing: 'border-box' }}>
      {title && <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 }}>{title}</h3>}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ ...cellStyle, background: '#f9fafb' }}></th>
              {xLabels.map(x => (
                <th key={x} style={{ ...cellStyle, background: '#f9fafb' }}>{x}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {yLabels.map(y => (
              <tr key={y}>
                <td style={{ ...cellStyle, background: '#f9fafb', fontWeight: 600 }}>{y}</td>
                {xLabels.map(x => {
                  const value = getValue(x, y);
                  return (
                    <td
                      key={x}
                      style={{ ...cellStyle, background: getColor(value), color: value != null ? '#fff' : '#9ca3af' }}
                    >
                      {value != null ? value.toFixed(1) : '—'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
