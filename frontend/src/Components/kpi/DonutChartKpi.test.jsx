import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import DonutChartKpi from './DonutChartKpi';

const pieCalls = [];
const tooltipCalls = [];
const legendCalls = [];

vi.mock('recharts', () => ({
  PieChart: ({ children }) => <div data-testid="pie-chart">{children}</div>,
  Pie: (props) => {
    pieCalls.push(props);
    return <div data-testid="pie">{props.children}</div>;
  },
  Cell: () => <div data-testid="cell" />,
  Tooltip: (props) => {
    tooltipCalls.push(props);
    return <div data-testid="tooltip" />;
  },
  Legend: (props) => {
    legendCalls.push(props);
    return <div data-testid="legend" />;
  },
  ResponsiveContainer: ({ children }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
}));

describe('DonutChartKpi', () => {
  beforeEach(() => {
    pieCalls.length = 0;
    tooltipCalls.length = 0;
    legendCalls.length = 0;
  });

  it('renders with donut-chart-kpi class', () => {
    const { container } = render(<DonutChartKpi />);
    expect(container.querySelector('.donut-chart-kpi')).toBeInTheDocument();
  });

  it('renders title when provided', () => {
    render(<DonutChartKpi title="Test Title" />);
    expect(screen.getByText('Test Title')).toBeInTheDocument();
  });

  it('does not render title when not provided', () => {
    const { container } = render(<DonutChartKpi />);
    expect(container.querySelector('h3')).not.toBeInTheDocument();
  });

  it('renders PieChart, Pie, Tooltip and Legend components', () => {
    render(<DonutChartKpi data={[{ name: 'A', value: 10 }]} />);
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    expect(screen.getByTestId('pie')).toBeInTheDocument();
    expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    expect(screen.getByTestId('legend')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('renders a Cell for each data entry', () => {
    const data = [
      { name: 'A', value: 30 },
      { name: 'B', value: 70 },
    ];
    const { container } = render(<DonutChartKpi data={data} />);
    const cells = container.querySelectorAll('[data-testid="cell"]');
    expect(cells.length).toBe(2);
  });

  describe('tooltip', () => {
    it('passes default tooltip formatter when custom not provided', () => {
      const data = [{ name: 'A', value: 10 }];
      render(<DonutChartKpi data={data} />);
      expect(tooltipCalls.length).toBeGreaterThan(0);
      const formatter = tooltipCalls[0].formatter;
      expect(formatter).toBeDefined();
      const result = formatter(10, 'ignored', { payload: { name: 'TestName' } });
      // Default formatter includes percentage: "value · percentage"
      expect(result).toEqual(['10 · 100.0%', 'TestName']);
    });

    it('uses custom tooltipFormatter when provided', () => {
      const customFormatter = vi.fn(() => ['formatted', 'label']);
      render(
        <DonutChartKpi
          data={[{ name: 'A', value: 10 }]}
          tooltipFormatter={customFormatter}
        />,
      );
      expect(tooltipCalls.length).toBeGreaterThan(0);
      expect(tooltipCalls[0].formatter).toBe(customFormatter);
    });

    it('uses custom tooltipLabelFormatter when provided', () => {
      const labelFormatter = vi.fn();
      render(
        <DonutChartKpi
          data={[{ name: 'A', value: 10 }]}
          tooltipLabelFormatter={labelFormatter}
        />,
      );
      expect(tooltipCalls.length).toBeGreaterThan(0);
      expect(tooltipCalls[0].labelFormatter).toBe(labelFormatter);
    });
  });

  describe('legend', () => {
    it('renders legend with verticalAlign bottom', () => {
      render(<DonutChartKpi data={[{ name: 'A', value: 10 }]} />);
      expect(legendCalls.length).toBeGreaterThan(0);
      expect(legendCalls[0].verticalAlign).toBe('bottom');
    });

    it('uses valueFormatter within legend formatter', () => {
      const valueFormatter = vi.fn((v) => `${v}%`);
      render(
        <DonutChartKpi
          data={[{ name: 'A', value: 42 }]}
          valueFormatter={valueFormatter}
        />,
      );
      expect(legendCalls.length).toBeGreaterThan(0);
      const legendFormatter = legendCalls[0].formatter;
      const result = legendFormatter('A', { payload: { value: 42 } });
      expect(valueFormatter).toHaveBeenCalledWith(42);
      // Legend includes percentage: "name (value · percentage)"
      expect(result).toBe('A (42% · 100.0%)');
    });
  });

  describe('monosegment behavior', () => {
    it('sets paddingAngle to 0 for monosegment (single non-zero slice)', () => {
      const data = [
        { name: 'A', value: 100 },
        { name: 'B', value: 0 },
      ];
      render(<DonutChartKpi data={data} />);
      expect(pieCalls.length).toBeGreaterThan(0);
      expect(pieCalls[0].paddingAngle).toBe(0);
    });

    it('sets labelLine to false for monosegment', () => {
      const data = [
        { name: 'A', value: 100 },
        { name: 'B', value: 0 },
      ];
      render(<DonutChartKpi data={data} />);
      expect(pieCalls.length).toBeGreaterThan(0);
      expect(pieCalls[0].labelLine).toBe(false);
    });

    it('sets paddingAngle to 2 for multi-segment', () => {
      const data = [
        { name: 'A', value: 60 },
        { name: 'B', value: 40 },
      ];
      render(<DonutChartKpi data={data} />);
      expect(pieCalls.length).toBeGreaterThan(0);
      expect(pieCalls[0].paddingAngle).toBe(2);
    });

    it('sets labelLine to true for multi-segment', () => {
      const data = [
        { name: 'A', value: 60 },
        { name: 'B', value: 40 },
      ];
      render(<DonutChartKpi data={data} />);
      expect(pieCalls.length).toBeGreaterThan(0);
      expect(pieCalls[0].labelLine).toBe(true);
    });
  });

  describe('slice labels', () => {
    it('returns empty label when showSliceLabels is false', () => {
      const data = [
        { name: 'A', value: 60 },
        { name: 'B', value: 40 },
      ];
      render(<DonutChartKpi data={data} showSliceLabels={false} />);
      expect(pieCalls.length).toBeGreaterThan(0);
      const labelFn = pieCalls[0].label;
      expect(labelFn({ name: 'A', percent: 0.6 })).toBe('');
    });

    it('returns formatted label when showSliceLabels is true and percent >= minLabelPercent', () => {
      const data = [
        { name: 'A', value: 60 },
        { name: 'B', value: 40 },
      ];
      render(<DonutChartKpi data={data} showSliceLabels minLabelPercent={0.05} />);
      expect(pieCalls.length).toBeGreaterThan(0);
      const labelFn = pieCalls[0].label;
      expect(labelFn({ name: 'A', percent: 0.6 })).toBe('A: 60.0%');
    });

    it('returns empty label when percent is below minLabelPercent', () => {
      const data = [
        { name: 'A', value: 95 },
        { name: 'B', value: 5 },
      ];
      render(<DonutChartKpi data={data} showSliceLabels minLabelPercent={0.1} />);
      expect(pieCalls.length).toBeGreaterThan(0);
      const labelFn = pieCalls[0].label;
      expect(labelFn({ name: 'B', percent: 0.05 })).toBe('');
    });

    it('shows label in monosegment when showSliceLabels is true', () => {
      const data = [{ name: 'A', value: 100 }];
      render(<DonutChartKpi data={data} showSliceLabels />);
      expect(pieCalls.length).toBeGreaterThan(0);
      const labelFn = pieCalls[0].label;
      expect(labelFn({ name: 'A', percent: 1.0 })).toBe('A: 100.0%');
    });
  });

  describe('edge cases', () => {
    it('handles empty data without crashing', () => {
      const { container } = render(<DonutChartKpi data={[]} />);
      expect(container.querySelector('.donut-chart-kpi')).toBeInTheDocument();
    });

    it('renders data with string values that convert to number', () => {
      render(<DonutChartKpi data={[{ name: 'A', value: '50' }]} />);
      // Should not crash - the component checks Number(item?.value) > 0
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });

    it('filters out items with missing or zero value', () => {
      render(<DonutChartKpi data={[{ name: 'A' }, { name: 'B', value: 10 }]} />);
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
      const cells = screen.getByTestId('pie').querySelectorAll('[data-testid="cell"]');
      // Entry with no value is filtered out, only entry with value=10 remains
      expect(cells.length).toBe(1);
    });
  });

  describe('Other slice grouping', () => {
    it('RED - shows Other slice name and value in legend', () => {
      const data = [
        { name: 'Cat-A', value: 100 },
        { name: 'Other', value: 85, groupedItems: [{ name: 'Cat-G', value: 40 }, { name: 'Cat-H', value: 45 }] },
      ];
      render(<DonutChartKpi data={data} valueFormatter={(v) => `${v} pcs`} />);
      // Legend should show "Other (85 pcs)"
      expect(legendCalls.length).toBeGreaterThan(0);
      const legendFormatter = legendCalls[legendCalls.length - 1].formatter;
      const result = legendFormatter('Other', { payload: { name: 'Other', value: 85, groupedItems: data[1].groupedItems } });
      // Legend includes percentage: "name (value · percentage)"
      // 85 / (100 + 85) = 45.9%
      expect(result).toBe('Other (85 pcs · 45.9%)');
    });

    it('RED - Other slice tooltip shows grouped member details', () => {
      const data = [
        { name: 'Cat-A', value: 100 },
        { name: 'Other', value: 60, groupedItems: [{ name: 'Cat-B', value: 35 }, { name: 'Cat-C', value: 25 }] },
      ];
      render(<DonutChartKpi data={data} valueFormatter={(v) => `${v} total`} />);
      expect(tooltipCalls.length).toBeGreaterThan(0);
      const formatter = tooltipCalls[tooltipCalls.length - 1].formatter;
      // Default tooltip formatter uses valueFormatter and includes percentage
      const otherPayload = { name: 'Other', value: 60, groupedItems: data[1].groupedItems };
      const result = formatter(60, 'Other', { payload: otherPayload });
      // Should show value, percentage, and name
      // 60 / (100 + 60) = 37.5%
      expect(result[0]).toBe('60 total · 37.5%');
      expect(result[1]).toBe('Other');
    });

    it('RED - renders correct number of cells for data with Other slice', () => {
      const data = [
        { name: 'A', value: 100 },
        { name: 'B', value: 80 },
        { name: 'Other', value: 30, groupedItems: [{ name: 'C', value: 30 }] },
      ];
      const { container } = render(<DonutChartKpi data={data} />);
      const cells = container.querySelectorAll('[data-testid="cell"]');
      expect(cells.length).toBe(3);
    });
  });
});
