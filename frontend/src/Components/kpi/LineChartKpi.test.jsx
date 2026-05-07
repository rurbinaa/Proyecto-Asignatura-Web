import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { buildMergedLineData } from './lineChartUtils';
import LineChartKpi from './LineChartKpi';

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  LineChart: ({ children }) => <div>{children}</div>,
  Line: () => <div />,
  XAxis: ({ type }) => <div data-testid="x-axis" data-type={type} />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div />,
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
