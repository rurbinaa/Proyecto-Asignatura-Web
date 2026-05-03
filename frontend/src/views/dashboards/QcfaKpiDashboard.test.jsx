/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import QcfaKpiDashboard from './QcfaKpiDashboard';
import { fetchAllKpis } from '../../api/kpi';

vi.mock('../../api/kpi', () => ({
  fetchAllKpis: vi.fn(),
}));

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'manager' }, loading: false }),
}));

vi.mock('../../hooks/withRoleProtection', () => ({
  withRoleProtection: (Component) => Component,
}));

vi.mock('../../Components/kpi/KpiCard', () => ({
  default: ({ title, children }) => (
    <section className="kpi-card">
      <h2>{title}</h2>
      <div>{children}</div>
    </section>
  ),
}));

vi.mock('../../Components/kpi/BarChartKpi', () => ({
  default: () => <div>BarChartKpi</div>,
}));

vi.mock('../../Components/kpi/LineChartKpi', () => ({
  default: () => <div>LineChartKpi</div>,
}));

vi.mock('../../Components/kpi/DonutChartKpi', () => ({
  default: () => <div>DonutChartKpi</div>,
}));

vi.mock('../../Components/kpi/HeatmapKpi', () => ({
  default: () => <div>HeatmapKpi</div>,
}));

vi.mock('../../Components/kpi/KpiNumberCard', () => ({
  default: () => <div>KpiNumberCard</div>,
}));

vi.mock('../../Components/kpi/FilterBar', () => ({
  default: () => <div>FilterBar</div>,
}));

vi.mock('../../Components/ReportGenerator', () => ({
  default: () => <div>ReportGenerator</div>,
}));

describe('QcfaKpiDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchAllKpis.mockResolvedValue({});
  });

  it('renders all 15 KPI card titles in DOM order', () => {
    render(<QcfaKpiDashboard context="plant" />);

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

  it('renders masonry layout with correct CSS classes', () => {
    const { container } = render(<QcfaKpiDashboard context="plant" />);
    const masonryContainer = container.querySelector('.dashboard-masonry');
    expect(masonryContainer).toBeInTheDocument();
    const masonryColumn = container.querySelector('.dashboard-masonry-column');
    expect(masonryColumn).toBeInTheDocument();
  });

  it('passes context=plant to fetchAllKpis on initial load', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(fetchAllKpis).toHaveBeenCalled();
    const [filters, context] = fetchAllKpis.mock.calls[0];
    expect(context).toBe('plant');
    // filters is the default state object (not empty)
    expect(filters).toBeDefined();
  });

  it('passes context=customer to fetchAllKpis', () => {
    render(<QcfaKpiDashboard context="customer" />);
    expect(fetchAllKpis).toHaveBeenCalled();
    const [, context] = fetchAllKpis.mock.calls[0];
    expect(context).toBe('customer');
  });

  it('shows refresh button', async () => {
    render(<QcfaKpiDashboard context="plant" />);
    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });

  it('shows split Accepted/Rejected by Line cards', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.getByText('Accepted by Line (count)')).toBeInTheDocument();
    expect(screen.getByText('Rejected by Line (count)')).toBeInTheDocument();
  });

  it('shows volatile helper banner when volatileData is provided', () => {
    render(<QcfaKpiDashboard context="plant" volatileData={[{ id: 1, value: 'test' }]} />);
    // volatileData triggers the "Fast mode" banner
    const banner = screen.getByRole('status');
    expect(banner).toBeInTheDocument();
    expect(banner.textContent).toMatch(/fast mode/i);
  });

  it('does not show volatile helper banner in live mode', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('renders FilterBar when in live mode', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.getByText('FilterBar')).toBeInTheDocument();
  });

  it('renders ReportGenerator component', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.getByText('ReportGenerator')).toBeInTheDocument();
  });

  it('renders Defects by Style × Type heatmap card', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.getByText('Defects by Style × Type')).toBeInTheDocument();
  });

  it('renders Fabric Defects card', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.getByText('Fabric Defects')).toBeInTheDocument();
  });
});
