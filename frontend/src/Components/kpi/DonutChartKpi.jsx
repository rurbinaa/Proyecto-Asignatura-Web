import { memo } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const identity = (value) => value;

function DonutChartKpi({
  data = [],
  title,
  valueFormatter = identity,
  tooltipFormatter,
  tooltipLabelFormatter,
  showSliceLabels = true,
  minLabelPercent = 0.05,
}) {
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];
  const nonZeroSlices = data.filter((item) => Number(item?.value) > 0);
  const isMonosegment = nonZeroSlices.length <= 1;
  const total = nonZeroSlices.reduce((acc, item) => acc + Number(item?.value || 0), 0);

  const getPercentText = (rawValue) => {
    if (!total) return '0.0%';
    return `${((Number(rawValue || 0) / total) * 100).toFixed(1)}%`;
  };

  const renderLabel = ({ name, percent }) => {
    if (!showSliceLabels || percent < minLabelPercent) return '';
    return `${name}: ${(percent * 100).toFixed(1)}%`;
  };

  const defaultTooltipFormatter = (value, _name, entry) => [
    `${valueFormatter(value)} · ${getPercentText(value)}`,
    entry?.payload?.name || '',
  ];

  return (
    <div className="donut-chart-kpi" style={{ padding: '16px', boxSizing: 'border-box' }}>
      {title && <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 }}>{title}</h3>}
      <ResponsiveContainer width="100%" height={340}>
        <PieChart>
          <Pie
            data={nonZeroSlices}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={isMonosegment ? 0 : 2}
            label={renderLabel}
            labelLine={!isMonosegment}
          >
            {nonZeroSlices.map((entry, index) => (
              <Cell key={`${entry?.name ?? 'slice'}-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={tooltipFormatter || defaultTooltipFormatter}
            labelFormatter={tooltipLabelFormatter}
          />
          <Legend
            verticalAlign="bottom"
            height={72}
            iconType="circle"
            formatter={(value, entry) => {
              const raw = Number(entry?.payload?.value ?? 0);
              return `${value} (${valueFormatter(raw)} · ${getPercentText(raw)})`;
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export default memo(DonutChartKpi);
