import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { buildMergedLineData } from './lineChartUtils';

const SERIES_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const identity = (value) => value;

export default function LineChartKpi({
  series = [],
  title,
  showDots = true,
  xAxisLabel,
  showXAxisLabel = false,
  yAxisLabel,
  xTickFormatter,
  yTickFormatter,
  valueFormatter = identity,
  tooltipFormatter,
  tooltipLabelFormatter,
  legendVerticalAlign = 'top',
  legendAlign = 'right',
  lineColors,
}) {
  // Unified chart margin for consistent spacing (same as BarChartKpi)
  const chartMargin = { top: 12, right: 20, left: 24, bottom: 36 };

  const { mergedData, allXValues, useNumericXAxis } = buildMergedLineData(series);

  const defaultTooltipFormatter = (value, seriesName) => [valueFormatter(value), seriesName];

  return (
    <div className="line-chart-kpi" style={{ padding: '16px', boxSizing: 'border-box' }}>
      {title && <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 }}>{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={mergedData} margin={chartMargin}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="x"
            type={useNumericXAxis ? 'number' : 'category'}
            domain={useNumericXAxis ? ['dataMin', 'dataMax'] : undefined}
            tickCount={useNumericXAxis ? Math.min(8, Math.max(3, allXValues.length)) : undefined}
            allowDecimals={false}
            interval="preserveStartEnd"
            minTickGap={24}
            tickFormatter={xTickFormatter}
            label={showXAxisLabel && xAxisLabel ? { value: xAxisLabel, position: 'bottom', offset: 8 } : undefined}
          />
          <YAxis
            tickFormatter={yTickFormatter}
            label={
              yAxisLabel
                ? { value: yAxisLabel, angle: -90, position: 'insideLeft', dx: -8, style: { textAnchor: 'middle' } }
                : undefined
            }
          />
          <Tooltip
            formatter={tooltipFormatter || defaultTooltipFormatter}
            labelFormatter={tooltipLabelFormatter}
          />
          <Legend
            verticalAlign={legendVerticalAlign}
            align={legendAlign}
            wrapperStyle={{ fontSize: '12px', paddingBottom: '4px' }}
          />
          {series.map((s, index) => (
            <Line
              key={s.name}
              name={s.name}
              data={mergedData}
              dataKey={s.name}
              stroke={(lineColors || SERIES_COLORS)[index % (lineColors || SERIES_COLORS).length]}
              dot={showDots}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
