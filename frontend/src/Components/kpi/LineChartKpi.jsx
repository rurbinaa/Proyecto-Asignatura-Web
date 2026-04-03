import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const SERIES_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function LineChartKpi({ series = [], title, showDots = true }) {
  const chartStyle = { margin: { top: 5, right: 30, left: 20, bottom: 5 } };

  return (
    <div style={{ padding: '16px' }}>
      {title && <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={series[0]?.data || []} margin={chartStyle}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x" />
          <YAxis />
          <Tooltip />
          <Legend />
          {series.map((s, index) => (
            <Line
              key={s.name}
              name={s.name}
              data={s.data}
              dataKey="y"
              stroke={SERIES_COLORS[index % SERIES_COLORS.length]}
              dot={showDots}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
