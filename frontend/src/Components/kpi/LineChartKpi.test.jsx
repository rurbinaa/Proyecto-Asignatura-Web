import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { buildMergedLineData } from './lineChartUtils';
import LineChartKpi from './LineChartKpi';

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  LineChart: ({ children }) => <div>{children}</div>,
  Line: ({ data, dataKey }) => <div data-testid={`line-${dataKey}`} data-has-data={data !== undefined} />,
  XAxis: ({ type, interval, minTickGap }) => (
    <div data-testid="x-axis" data-type={type} data-interval={interval} data-min-tick-gap={minTickGap} />
  ),
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div data-testid="legend" />,
}));

afterEach(() => {
  cleanup();
});

describe('LineChartKpi data normalization', () => {
  it('sorts numeric x values numerically (not lexicographically)', () => {
    const series = [
      {
        name: 'AQL',
        data: [
          { x: 10, y: 2.4 },
          { x: 2, y: 1.2 },
          { x: 1, y: 1.0 },
        ],
      },
    ];

    const { allXValues, useNumericXAxis } = buildMergedLineData(series);

    expect(useNumericXAxis).toBe(true);
    expect(allXValues).toEqual([1, 2, 10]);
  });

  it('keeps categorical x values and does not force numeric mode', () => {
    const series = [
      {
        name: 'Categorical',
        data: [
          { x: 'W1', y: 100 },
          { x: 'W2', y: 120 },
        ],
      },
    ];

    const { allXValues, useNumericXAxis } = buildMergedLineData(series);

    expect(useNumericXAxis).toBe(false);
    expect(allXValues).toEqual(['W1', 'W2']);
  });

  it('sorts weekly labels chronologically instead of lexicographically', () => {
    const series = [
      {
        name: 'Pass',
        data: [
          { x: '2025-W31', y: 100 },
          { x: '2025-W9', y: 90 },
          { x: '2025-W26', y: 110 },
          { x: '2024-W52', y: 80 },
        ],
      },
    ];

    const { allXValues, useNumericXAxis } = buildMergedLineData(series);

    expect(useNumericXAxis).toBe(false);
    expect(allXValues).toEqual(['2024-W52', '2025-W9', '2025-W26', '2025-W31']);
  });

  it('uses numeric x axis by default when data is numeric and forceCategoricalXAxis is not set', () => {
    render(
      <LineChartKpi
        series={[
          {
            name: 'Score',
            data: [
              { x: 1, y: 10 },
              { x: 2, y: 12 },
              { x: 3, y: 9 },
            ],
          },
        ]}
      />,
    );

    expect(screen.getByTestId('x-axis')).toHaveAttribute('data-type', 'number');
  });

  it('does not pass redundant data prop to individual Line children', () => {
    render(
      <LineChartKpi
        series={[
          { name: 'Pass', data: [{ x: 'W1', y: 10 }] },
          { name: 'Fail', data: [{ x: 'W1', y: 1 }] },
        ]}
      />,
    );

    // Each Line should NOT receive a `data` prop (redundant — parent LineChart has it)
    const passLine = screen.getByTestId('line-Pass');
    const failLine = screen.getByTestId('line-Fail');
    expect(passLine).toHaveAttribute('data-has-data', 'false');
    expect(failLine).toHaveAttribute('data-has-data', 'false');
  });

  it('renders title when provided', () => {
    render(
      <LineChartKpi
        title="Pass vs Fail"
        series={[
          { name: 'Pass', data: [{ x: 1, y: 10 }] },
        ]}
      />,
    );

    expect(screen.getByText('Pass vs Fail')).toBeInTheDocument();
  });

  it('renders multiple series as separate Line elements', () => {
    render(
      <LineChartKpi
        series={[
          { name: 'Pass', data: [{ x: 'W1', y: 10 }, { x: 'W2', y: 12 }] },
          { name: 'Fail', data: [{ x: 'W1', y: 1 }, { x: 'W2', y: 2 }] },
        ]}
      />,
    );

    expect(screen.getByTestId('line-Pass')).toBeInTheDocument();
    expect(screen.getByTestId('line-Fail')).toBeInTheDocument();
  });

  it('does not pass interval or minTickGap to XAxis', () => {
    render(
      <LineChartKpi
        series={[
          { name: 'A', data: [{ x: 1, y: 10 }] },
        ]}
      />,
    );

    const xAxis = screen.getByTestId('x-axis');
    expect(xAxis).not.toHaveAttribute('data-interval');
    expect(xAxis).not.toHaveAttribute('data-min-tick-gap');
  });

  it('can force categorical x axis even with numeric week values', () => {
    render(
      <LineChartKpi
        forceCategoricalXAxis
        series={[
          {
            name: 'Pass',
            data: [
              { x: 1, y: 10 },
              { x: 5, y: 12 },
              { x: 12, y: 9 },
            ],
          },
        ]}
      />,
    );

    expect(screen.getByTestId('x-axis')).toHaveAttribute('data-type', 'category');
  });
});
