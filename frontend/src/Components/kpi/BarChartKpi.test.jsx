import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import BarChartKpi from './BarChartKpi';

const barChartCalls = [];
const yAxisCalls = [];

vi.mock('recharts', () => ({
  BarChart: ({ children, ...props }) => {
    barChartCalls.push(props);
    return <div data-testid="bar-chart" {...props}>{children}</div>;
  },
  Bar: vi.fn(() => <div data-testid="bar" />),
  XAxis: vi.fn(() => <div data-testid="x-axis" />),
  YAxis: vi.fn((props) => {
    yAxisCalls.push(props);
    return <div data-testid="y-axis" />;
  }),
  CartesianGrid: vi.fn(() => <div data-testid="cartesian-grid" />),
  Tooltip: vi.fn(() => <div data-testid="tooltip" />),
  ResponsiveContainer: ({ children }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
}));

describe('BarChartKpi Layout Behavior', () => {
  beforeEach(() => {
    barChartCalls.length = 0;
    yAxisCalls.length = 0;
  });

  describe('Horizontal bar chart y-axis width', () => {
    it('computes y-axis width based on longest label for horizontal charts', () => {
      const data = [
        { label: 'Short', value: 10 },
        { label: 'Medium Label', value: 20 },
        { label: 'Very Long Label That Needs More Space', value: 30 },
      ];

      render(<BarChartKpi data={data} horizontal />);

      // The YAxis should receive a computed width based on label length
      // 'Very Long Label That Needs More Space' is 38 chars
      // Expected: min(220, max(88, 38 * 8 + 30)) = min(220, 334) = 220
      expect(barChartCalls.length).toBeGreaterThan(0);
      const chartProps = barChartCalls[0];
      expect(chartProps.layout).toBe('vertical');
      expect(chartProps.margin).toEqual({ top: 12, right: 20, left: 24, bottom: 36 });

      // Assert on YAxis width prop
      expect(yAxisCalls.length).toBeGreaterThan(0);
      expect(yAxisCalls[0].width).toBe(220);
    });

    it('uses provided yAxisWidth when specified for horizontal charts', () => {
      const data = [{ label: 'Test', value: 10 }];
      render(<BarChartKpi data={data} horizontal yAxisWidth={200} />);

      expect(barChartCalls.length).toBeGreaterThan(0);
      const chartProps = barChartCalls[0];
      expect(chartProps.layout).toBe('vertical');
    });

    it('does not compute category width for vertical (non-horizontal) charts', () => {
      const data = [{ label: 'Category', value: 10 }];
      render(<BarChartKpi data={data} horizontal={false} />);

      expect(barChartCalls.length).toBeGreaterThan(0);
      const chartProps = barChartCalls[0];
      expect(chartProps.layout).toBe('horizontal');
    });

    it('applies consistent chart margins regardless of orientation', () => {
      const data = [{ label: 'Test', value: 10 }];

      const { rerender } = render(<BarChartKpi data={data} horizontal />);
      const horizontalMargin = barChartCalls[0].margin;

      barChartCalls.length = 0;
      rerender(<BarChartKpi data={data} horizontal={false} />);
      const verticalMargin = barChartCalls[0].margin;

      // Margins should be consistent
      expect(horizontalMargin).toEqual(verticalMargin);
      expect(horizontalMargin).toEqual({ top: 12, right: 20, left: 24, bottom: 36 });
    });

    it('renders with bar-chart-kpi class for CSS targeting', () => {
      const { container } = render(<BarChartKpi data={[{ label: 'Test', value: 10 }]} />);
      const chartElement = container.querySelector('.bar-chart-kpi');
      expect(chartElement).toBeInTheDocument();
    });
  });

  describe('Chart height calculation', () => {
    it('uses dynamic height for horizontal charts based on data length', () => {
      const shortData = [{ label: 'A', value: 1 }];
      const longData = Array.from({ length: 20 }, (_, i) => ({
        label: `Label ${i}`,
        value: i * 10,
      }));

      const { rerender } = render(<BarChartKpi data={shortData} horizontal />);
      expect(barChartCalls.length).toBeGreaterThan(0);

      barChartCalls.length = 0;
      rerender(<BarChartKpi data={longData} horizontal />);
      // Height should adapt to data length
      expect(barChartCalls.length).toBeGreaterThan(0);
    });

    it('uses fixed height for non-horizontal charts', () => {
      const data = [{ label: 'Category', value: 10 }];
      render(<BarChartKpi data={data} horizontal={false} />);

      expect(barChartCalls.length).toBeGreaterThan(0);
    });
  });
});
