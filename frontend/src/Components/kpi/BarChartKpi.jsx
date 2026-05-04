import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const identity = (value) => value;

export default function BarChartKpi({
  data = [],
  title,
  horizontal = false,
  color = '#3b82f6',
  xAxisLabel,
  yAxisLabel,
  xTickFormatter,
  yTickFormatter,
  valueFormatter = identity,
  tooltipFormatter,
  tooltipLabelFormatter,
  yAxisWidth,
  showAllCategoryTicks = false,
  chartHeight,
}) {
  // Unified chart margin for consistent spacing across all bar charts
  const chartMargin = { top: 12, right: 20, left: 24, bottom: 36 };
  const defaultTooltipFormatter = (value, name) => [valueFormatter(value), name];

  // Compute y-axis width for horizontal bar charts based on actual label content
  // Uses a more generous calculation to prevent label truncation in masonry layouts
  const computedHorizontalCategoryWidth = (() => {
    if (!horizontal) return undefined;
    const longestLabel = data.reduce((max, item) => {
      const current = String(item?.label ?? '').length;
      return Math.max(max, current);
    }, 0);
    // Allow up to 220px for long labels, minimum 88px
    return Math.min(220, Math.max(88, longestLabel * 8 + 30));
  })();
  const categoryWidth = yAxisWidth ?? computedHorizontalCategoryWidth;
  const xTickInterval = showAllCategoryTicks ? 0 : 'preserveStartEnd';
  const resolvedChartHeight = chartHeight ?? (horizontal
    ? Math.min(560, Math.max(280, data.length * 28 + 140))
    : 300);
  const horizontalCategoryInterval = showAllCategoryTicks
    ? 0
    : (data.length <= 12 ? 0 : 'preserveStartEnd');

  return (
    <div className="bar-chart-kpi" style={{ padding: '16px', boxSizing: 'border-box' }}>
      {title && <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 }}>{title}</h3>}
      <ResponsiveContainer width="100%" height={resolvedChartHeight}>
        <BarChart data={data} layout={horizontal ? 'vertical' : 'horizontal'} margin={chartMargin}>
          <CartesianGrid strokeDasharray="3 3" />
          {horizontal ? (
            <>
              <XAxis
                type="number"
                tickFormatter={xTickFormatter}
                label={xAxisLabel ? { value: xAxisLabel, position: 'bottom', offset: 8 } : undefined}
              />
              <YAxis
                dataKey="label"
                type="category"
                width={categoryWidth}
                tickFormatter={yTickFormatter}
                interval={horizontalCategoryInterval}
                minTickGap={8}
                label={
                  yAxisLabel
                    ? { value: yAxisLabel, angle: -90, position: 'insideLeft', dx: -8, style: { textAnchor: 'middle' } }
                    : undefined
                }
              />
            </>
          ) : (
            <>
              <XAxis
                dataKey="label"
                tickFormatter={xTickFormatter}
                interval={xTickInterval}
                minTickGap={14}
                angle={showAllCategoryTicks ? -20 : 0}
                textAnchor={showAllCategoryTicks ? 'end' : 'middle'}
                height={showAllCategoryTicks ? 60 : 36}
                label={xAxisLabel ? { value: xAxisLabel, position: 'bottom', offset: 8 } : undefined}
              />
              <YAxis
                tickFormatter={yTickFormatter}
                label={
                  yAxisLabel
                    ? { value: yAxisLabel, angle: -90, position: 'insideLeft', dx: -8, style: { textAnchor: 'middle' } }
                    : undefined
                }
              />
            </>
          )}
          <Tooltip
            formatter={tooltipFormatter || defaultTooltipFormatter}
            labelFormatter={tooltipLabelFormatter}
          />
          <Bar dataKey="value" fill={color} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
