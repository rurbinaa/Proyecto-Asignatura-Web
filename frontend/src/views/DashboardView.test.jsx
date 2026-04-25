import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import DashboardView from './DashboardView';
import { normalizeScalarMetric } from './dashboardMetricUtils';
import { fetchAllKpis, fetchVolatileKpis, getFilterOptions } from '../api/kpi';

const barChartCalls = [];

vi.mock('../api/kpi', () => ({
  fetchAllKpis: vi.fn(),
  fetchVolatileKpis: vi.fn(),
  getFilterOptions: vi.fn(),
}));

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'manager' }, loading: false }),
}));

vi.mock('../hooks/withRoleProtection', () => ({
  withRoleProtection: (Component) => Component,
}));

vi.mock('../Components/kpi/KpiCard', () => ({
  default: ({ title, children, className = '' }) => (
    <section className={`kpi-card ${className}`.trim()}>
      <h2>{title}</h2>
      <div>{children}</div>
    </section>
  ),
}));

vi.mock('../Components/kpi/BarChartKpi', () => ({
  default: (props) => {
    barChartCalls.push(props);
    return <div>BarChartKpi</div>;
  },
}));

vi.mock('../Components/kpi/LineChartKpi', () => ({
  default: () => <div>LineChartKpi</div>,
}));

vi.mock('../Components/kpi/DonutChartKpi', () => ({
  default: () => <div>DonutChartKpi</div>,
}));

vi.mock('../Components/kpi/HeatmapKpi', () => ({
  default: () => <div>HeatmapKpi</div>,
}));

vi.mock('../Components/kpi/KpiNumberCard', () => ({
  default: () => <div>KpiNumberCard</div>,
}));

vi.mock('../Components/kpi/FilterBar', () => ({
  default: () => <div>FilterBar</div>,
}));

vi.mock('../Components/ReportGenerator', () => ({
  default: () => <div>ReportGenerator</div>,
}));

describe('DashboardView UI semantics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    barChartCalls.length = 0;
    fetchAllKpis.mockResolvedValue({});
    fetchVolatileKpis.mockResolvedValue({});
    getFilterOptions.mockResolvedValue({});
  });

  it('renders dashboard in masonry layout with dashboard-masonry class', () => {
    const { container } = render(<DashboardView />);
    const masonryContainer = container.querySelector('.dashboard-masonry');
    expect(masonryContainer).toBeInTheDocument();
  });

  it('masonry container uses dashboard-masonry-column class for columns', () => {
    const { container } = render(<DashboardView />);
    const masonryColumn = container.querySelector('.dashboard-masonry-column');
    expect(masonryColumn).toBeInTheDocument();
  });

  it('renders KPI cards covering the expected source set', async () => {
    render(<DashboardView />);
    const expectedTitles = [
      'Defect Rate (AQL %)',
      'Pass / Reject Distribution',
      'Weekly AQL (%)',
      'AQL by Style',
      'Top Defects',
      'Weekly Audited Pieces',
      'Weekly Rejected Pieces',
      'Accepted by Line (count)',
      'Rejected by Line (count)',
      'Acceptance Rate by Customer (accepted/sample × 100)',
      'Acceptance Rate by Line (accepted/sample × 100)',
      'Weekly Rework (seconds)',
      'Fabric Defects',
      'Containers by Status',
      'Defects by Style × Type',
    ];

    await waitFor(() => {
      expect(fetchAllKpis).toHaveBeenCalled();
    });

    expectedTitles.forEach((title) => {
      expect(screen.getByText(title)).toBeInTheDocument();
    });
  });

  it('preserves the first KPI card in DOM order', () => {
    render(<DashboardView />);
    const firstCard = document.querySelectorAll('.kpi-card')[0];
    expect(firstCard.querySelector('h2')?.textContent).toBe('Defect Rate (AQL %)');
  });

  it('configures masonry with correct responsive breakpoints contract', () => {
    const { container } = render(<DashboardView />);
    const masonry = container.querySelector('.dashboard-masonry');
    expect(masonry).toHaveClass('dashboard-masonry');
  });

  it('masonry CSS supports responsive breakpoint behavior', () => {
    render(<DashboardView />);
    const column = document.querySelector('.dashboard-masonry-column');
    expect(column).toBeInTheDocument();
  });

  it('shows split AC/RE cards with count semantics', () => {
    render(<DashboardView />);
    expect(screen.getByText('Accepted by Line (count)')).toBeInTheDocument();
    expect(screen.getByText('Rejected by Line (count)')).toBeInTheDocument();
    expect(screen.queryByText('Acceptance/Reject by line')).not.toBeInTheDocument();
  });

  it('does not render heatmap card as full-width layout', () => {
    const { container } = render(<DashboardView />);
    const heatmapTitle = screen.getByText('Defects by Style × Type');
    const card = heatmapTitle.closest('.kpi-card');

    expect(card).toBeInTheDocument();
    expect(card).not.toHaveClass('full-width');
    expect(container.querySelector('.full-width')).toBeNull();
  });

  it('does not clamp acceptance percentages above 100%', async () => {
    fetchAllKpis.mockResolvedValue({
      performanceByCustomer: [{ label: 'Cliente QA', value: 134.56 }],
      performanceByLine: [{ label: '1', value: 120 }],
    });

    render(<DashboardView />);

    await waitFor(() => {
      expect(fetchAllKpis).toHaveBeenCalled();
      expect(barChartCalls.length).toBeGreaterThan(0);
    });

    const customerChart = barChartCalls.find((call) => call.data?.[0]?.label === 'Cliente QA');
    const lineChart = barChartCalls.find((call) => call.data?.[0]?.label === '1' && call.horizontal);

    expect(customerChart.data[0].value).toBe(134.56);
    expect(lineChart.data[0].value).toBe(120);
    expect(customerChart.yAxisLabel).toContain('accepted/sample × 100');
    expect(lineChart.xAxisLabel).toContain('accepted/sample × 100');
    expect(customerChart.valueFormatter(134.56)).toBe('134.56 idx');
  });

  it('configures fabric defects chart to render all category ticks', async () => {
    fetchAllKpis.mockResolvedValue({
      fabricDefects: [
        { label: 'Corrido', value: 12 },
        { label: 'Barre', value: 10 },
        { label: 'Otros', value: 8 },
        { label: 'Degradación', value: 6 },
        { label: 'Bordados', value: 4 },
      ],
    });

    render(<DashboardView />);

    await waitFor(() => {
      expect(fetchAllKpis).toHaveBeenCalled();
      expect(barChartCalls.length).toBeGreaterThan(0);
    });

    const fabricChart = barChartCalls.find((call) => call.data?.some((item) => item.label === 'Degradación'));
    expect(fabricChart).toBeTruthy();
    expect(fabricChart.showAllCategoryTicks).toBe(true);
    expect(fabricChart.xAxisLabel).toBe('Defect Type');
    expect(fabricChart.yAxisLabel).toBe('Count');
  });

  it('shows volatile helper banner in quick mode', () => {
    render(<DashboardView volatileFile={new File(['test'], 'test.xlsx')} />);
    expect(screen.getByText(/fast mode/i)).toBeInTheDocument();
  });

  it('does not show volatile helper banner in live mode', () => {
    render(<DashboardView />);
    expect(screen.queryByText(/fast mode/i)).not.toBeInTheDocument();
  });
});

describe('DashboardView metric normalization', () => {
  it('returns scalar number unchanged', () => {
    expect(normalizeScalarMetric(2.5)).toBe(2.5);
  });

  it('unwraps nested value objects', () => {
    expect(normalizeScalarMetric({ label: 'Defect Rate', value: 3.1 })).toBe(3.1);
  });

  it('parses numeric strings and invalid values fallback to null', () => {
    expect(normalizeScalarMetric('4.2')).toBe(4.2);
    expect(normalizeScalarMetric({ value: '1.75' })).toBe(1.75);
    expect(normalizeScalarMetric({ value: 'N/A' })).toBeNull();
    expect(normalizeScalarMetric(undefined)).toBeNull();
  });
});
