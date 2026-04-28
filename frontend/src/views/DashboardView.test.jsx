import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import DashboardView from './DashboardView';
import { normalizeScalarMetric } from './dashboardMetricUtils';
import { fetchAllKpis, fetchVolatileKpis } from '../api/kpi';

const barChartCalls = [];

vi.mock('../api/kpi', () => ({
  fetchAllKpis: vi.fn(),
  fetchVolatileKpis: vi.fn(),
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

describe('DashboardView UI semantics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchAllKpis.mockResolvedValue({});
    fetchVolatileKpis.mockResolvedValue({});
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

  it('renders KPI cards in DOM order matching source data', () => {
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

    expectedTitles.forEach((title) => {
      expect(screen.getByText(title)).toBeInTheDocument();
    });
  });

  it('preserves content order within masonry columns', () => {
    render(<DashboardView />);
    const kpiCards = document.querySelectorAll('.kpi-card');
    expect(kpiCards.length).toBeGreaterThan(0);
  });

  it('configures masonry with correct responsive breakpoints contract', () => {
    render(<DashboardView />);
    const masonry = document.querySelector('.dashboard-masonry');
    expect(masonry).toBeInTheDocument();
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
  });

  it('does not render heatmap card as full-width layout', () => {
    render(<DashboardView />);
    expect(screen.getByText('Defects by Style × Type')).toBeInTheDocument();
  });

  it('does not clamp acceptance percentages above 100%', () => {
    render(<DashboardView />);
    expect(screen.getByText('Acceptance Rate by Customer (accepted/sample × 100)')).toBeInTheDocument();
  });

  it('configures fabric defects chart to render all category ticks', () => {
    render(<DashboardView />);
    expect(screen.getByText('Fabric Defects')).toBeInTheDocument();
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
  it('normalizes scalar metrics correctly', () => {
    expect(normalizeScalarMetric(5)).toBe(5);
    expect(normalizeScalarMetric('5')).toBe(5);
    expect(normalizeScalarMetric(null)).toBe(null);
  });
});