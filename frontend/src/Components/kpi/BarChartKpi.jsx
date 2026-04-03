import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function BarChartKpi({ data = [], title, horizontal = false, color = '#3b82f6' }) {
  const chartStyle = { margin: { top: 5, right: 30, left: 20, bottom: 5 } };

  if (horizontal) {
    return (
      <div style={{ padding: '16px' }}>
        {title && <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>{title}</h3>}
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} layout="vertical" margin={chartStyle}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="label" type="category" width={100} />
            <Tooltip />
            <Bar dataKey="value" fill={color} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div style={{ padding: '16px' }}>
      {title && <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={chartStyle}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill={color} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
