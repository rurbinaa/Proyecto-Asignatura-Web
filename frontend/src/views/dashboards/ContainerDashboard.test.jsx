/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ContainerDashboard from './ContainerDashboard';
import { fetchAllContainerKpis, getContainerFilterOptions } from '../../api/kpi';

vi.mock('../../api/kpi', () => ({
  fetchAllContainerKpis: vi.fn(),
  getContainerFilterOptions: vi.fn().mockResolvedValue({ customer: ['Customer A', 'Customer B'] }),
  fetchVolatileKpis: vi.fn(),
  getContainersByState: vi.fn(),
  fetchKpi: vi.fn(),
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

vi.mock('../../Components/kpi/KpiNumberCard', () => ({
  default: ({ value, unit }) => <div className="kpi-number">{value}{unit}</div>,
}));

vi.mock('../../Components/kpi/ContainerFilterBar', () => ({
  default: () => <div data-testid="container-filter-bar">ContainerFilterBar</div>,
}));

vi.mock('../../Components/DateRangePicker', () => ({
  default: () => <div>DateRangePicker</div>,
}));

describe('ContainerDashboard — live mode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getContainerFilterOptions.mockResolvedValue({ customer: ['Customer A', 'Customer B'] });
    fetchAllContainerKpis.mockResolvedValue({
      executiveSummary: [
        { label: 'Total Containers', value: 150 },
        { label: 'Average Pass Rate', value: 87.5 },
        { label: 'Total Palettes Inspected', value: 1200 },
        { label: 'Total Rejected Palettes', value: 45 },
      ],
      containersByState: [
        { name: '< 80%', value: 3 },
        { name: '80-90%', value: 12 },
        { name: '90-95%', value: 20 },
        { name: '> 95%', value: 65 },
      ],
      passRateTrend: [{ name: 'Pass Rate', data: [{ x: '2025-01-10', y: 87.5 }] }],
      inspectedTrend: [{ name: 'Inspected', data: [{ x: '2025-01-10', y: 100 }] }],
      rejectedTrend: [{ name: 'Rejected', data: [{ x: '2025-01-10', y: 5 }] }],
      topDefects: { result: [{ label: 'Loose Thread', value: 45 }] },
      defectComposition: { result: [{ name: 'Loose Thread', value: 45 }] },
      worstContainers: [
        { containerNumber: 'CONT-001', customer: 'Customer A', passRate: 72.5, rejectedPalettes: 5, inspectionDate: '2025-01-10' },
      ],
    });
  });

  // ── Dashboard title ───────────────────────────────────────────

  it('renders dashboard title', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.getByText('Container Dashboard')).toBeInTheDocument();
  });

  it('renders refresh button', async () => {
    render(<ContainerDashboard context="plant" />);
    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });

  // ── Section headers removed ───────────────────────────────────

  it('does NOT render redundant section headers (card titles carry hierarchy)', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.queryByText('Executive Summary')).not.toBeInTheDocument();
    expect(screen.queryByText('Containers by State')).not.toBeInTheDocument();
    expect(screen.queryByText('Trends')).not.toBeInTheDocument();
    expect(screen.queryByText('Defect Insights')).not.toBeInTheDocument();
  });

  // ── Executive Summary cards ───────────────────────────────────

  it('renders 4 executive summary metric cards', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.getByText('Total Containers')).toBeInTheDocument();
    expect(screen.getByText('Average Pass Rate')).toBeInTheDocument();
    expect(screen.getByText('Total Inspected Palettes')).toBeInTheDocument();
    expect(screen.getByText('Total Rejected Palettes')).toBeInTheDocument();
  });

  // ── Containers by State ───────────────────────────────────────

  it('renders Container State Distribution donut chart', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.getByText('Container State Distribution')).toBeInTheDocument();
  });



  // ── Trend cards ───────────────────────────────────────────────

  it('renders all 3 trend chart titles', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.getByText('Pass Rate Trend')).toBeInTheDocument();
    expect(screen.getByText('Inspected Trend')).toBeInTheDocument();
    expect(screen.getByText('Rejected Trend')).toBeInTheDocument();
  });

  // ── Defect Insights cards ─────────────────────────────────────

  it('renders Top Defects and does NOT render Defect Composition (duplicate removed)', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.getByText('Top Defects')).toBeInTheDocument();
    expect(screen.queryByText('Defect Composition')).not.toBeInTheDocument();
  });

  it('does NOT render worst containers section', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.queryByText('Worst Containers')).not.toBeInTheDocument();
    expect(screen.queryByText('Lowest Pass Rate Containers')).not.toBeInTheDocument();
  });

  // ── ContainerFilterBar ────────────────────────────────────────

  it('renders ContainerFilterBar in live mode', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.getByTestId('container-filter-bar')).toBeInTheDocument();
  });

  // ── Absence of QFA-only filters ───────────────────────────────

  it('does NOT render QFA-only Week filter', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.queryByText('Week')).not.toBeInTheDocument();
  });

  it('does NOT render QFA-only Team filter', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.queryByText('Team')).not.toBeInTheDocument();
  });

  it('does NOT render QFA-only Style filter', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.queryByText('Style')).not.toBeInTheDocument();
  });

  it('does NOT render QFA-only Color filter', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.queryByText('Color')).not.toBeInTheDocument();
  });

  it('does NOT render QFA-only Batch filter', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.queryByText('Batch')).not.toBeInTheDocument();
  });

  // ── fetchAllContainerKpis wiring ──────────────────────────────

  it('calls fetchAllContainerKpis with context on initial load', () => {
    render(<ContainerDashboard context="plant" />);
    expect(fetchAllContainerKpis).toHaveBeenCalled();
    const [filters, volatileFile, context] = fetchAllContainerKpis.mock.calls[0];
    expect(context).toBe('plant');
    expect(volatileFile).toBeUndefined();
  });

  it('calls fetchAllContainerKpis with context=customer', () => {
    render(<ContainerDashboard context="customer" />);
    expect(fetchAllContainerKpis).toHaveBeenCalled();
    const [filters, volatileFile, context] = fetchAllContainerKpis.mock.calls[0];
    expect(context).toBe('customer');
  });

  // ── Total KPI card count ──────────────────────────────────────

  it('renders 9 KPI card titles (Defect Composition removed)', () => {
    render(<ContainerDashboard context="plant" />);
    const kpiCards = document.querySelectorAll('.kpi-card h2');
    // 4 exec summary + 1 state donut + 3 trends + 1 top defects = 9
    expect(kpiCards.length).toBeGreaterThanOrEqual(9);
  });

  // ── Not "coming soon" ─────────────────────────────────────────

  it('does NOT render the stub "coming soon" message', () => {
    render(<ContainerDashboard context="plant" />);
    expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument();
  });
});

describe('ContainerDashboard — volatile mode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Realistic container KPI data that the backend now returns for volatile mode
  const volatileKpiData = {
    executiveSummary: [
      { label: 'Total Containers', value: 3 },
      { label: 'Average Pass Rate', value: 70.0 },
      { label: 'Total Palettes Inspected', value: 60 },
      { label: 'Total Rejected Palettes', value: 20 },
    ],
    containersByState: [
      { name: '< 80%', value: 2 },
      { name: '80-90%', value: 0 },
      { name: '90-95%', value: 1 },
      { name: '> 95%', value: 0 },
    ],
    passRateTrend: [{ name: 'Pass Rate', data: [{ x: '2025-01-10', y: 70.0 }] }],
    inspectedTrend: [{ name: 'Inspected', data: [{ x: '2025-01-10', y: 60 }] }],
    rejectedTrend: [{ name: 'Rejected', data: [{ x: '2025-01-10', y: 20 }] }],
    topDefects: { result: [{ label: 'Dirt Label', value: 12 }] },
    defectComposition: { result: [{ name: 'Dirt Label', value: 12 }] },
    worstContainers: [],
  };

  it('renders all KPI cards from volatile data (no fast-mode banner)', async () => {
    fetchAllContainerKpis.mockResolvedValue(volatileKpiData);

    render(<ContainerDashboard context="plant" volatileFile={new File(['test'], 'test.xlsx')} />);

    await waitFor(() => {
      // Should NOT render old fast-mode banner
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
      expect(screen.queryByText(/only containers by state/i)).not.toBeInTheDocument();

      // All KPI cards should render
      expect(screen.getByText('Container Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Total Containers')).toBeInTheDocument();
      expect(screen.getByText('Pass Rate Trend')).toBeInTheDocument();
      expect(screen.getByText('Top Defects')).toBeInTheDocument();
    });
  });

  it('does not show ContainerFilterBar in volatile mode', () => {
    fetchAllContainerKpis.mockResolvedValue(volatileKpiData);

    render(<ContainerDashboard context="plant" volatileFile={new File(['test'], 'test.xlsx')} />);

    expect(screen.queryByTestId('container-filter-bar')).not.toBeInTheDocument();
  });

  it('renders executive summary cards in volatile mode', async () => {
    fetchAllContainerKpis.mockResolvedValue(volatileKpiData);

    render(<ContainerDashboard context="plant" volatileFile={new File(['test'], 'test.xlsx')} />);

    await waitFor(() => {
      expect(screen.getByText('Total Containers')).toBeInTheDocument();
      expect(screen.getByText('Average Pass Rate')).toBeInTheDocument();
      expect(screen.getByText('Total Inspected Palettes')).toBeInTheDocument();
      expect(screen.getByText('Total Rejected Palettes')).toBeInTheDocument();
    });
  });

  it('renders trend charts in volatile mode', async () => {
    fetchAllContainerKpis.mockResolvedValue(volatileKpiData);

    render(<ContainerDashboard context="plant" volatileFile={new File(['test'], 'test.xlsx')} />);

    await waitFor(() => {
      expect(screen.getByText('Pass Rate Trend')).toBeInTheDocument();
      expect(screen.getByText('Inspected Trend')).toBeInTheDocument();
      expect(screen.getByText('Rejected Trend')).toBeInTheDocument();
    });
  });

  it('shows non-available messaging when volatile data is empty', async () => {
    fetchAllContainerKpis.mockResolvedValue({
      executiveSummary: { status: 'unavailable', reason: 'volatile', message: 'Not available' },
      containersByState: [],
      passRateTrend: { status: 'unavailable', reason: 'volatile', message: 'Not available' },
      inspectedTrend: { status: 'unavailable', reason: 'volatile', message: 'Not available' },
      rejectedTrend: { status: 'unavailable', reason: 'volatile', message: 'Not available' },
      topDefects: { status: 'unavailable', reason: 'volatile', message: 'Not available' },
      defectComposition: { status: 'unavailable', reason: 'volatile', message: 'Not available' },
      worstContainers: { status: 'unavailable', reason: 'volatile', message: 'Not available' },
    });

    render(<ContainerDashboard context="plant" volatileFile={new File(['test'], 'test.xlsx')} />);

    await waitFor(() => {
      // Dashboard should not crash — card titles still render
      expect(screen.getByText('Container Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Container State Distribution')).toBeInTheDocument();
    });
  });
});

describe('ContainerDashboard — render stability', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not crash when kpiData is empty (initial loading state)', () => {
    fetchAllContainerKpis.mockResolvedValue({});
    render(<ContainerDashboard context="plant" />);
    expect(screen.getByText('Container Dashboard')).toBeInTheDocument();
  });

  it('does not crash when fetchAllContainerKpis rejects with error', async () => {
    fetchAllContainerKpis.mockRejectedValue(new Error('Network error'));
    render(<ContainerDashboard context="plant" />);
    await waitFor(() => {
      expect(screen.getByText('Container Dashboard')).toBeInTheDocument();
    });
  });

  it('does not crash when KPI data has null values', () => {
    fetchAllContainerKpis.mockResolvedValue({
      executiveSummary: null,
      containersByState: null,
      passRateTrend: null,
      inspectedTrend: null,
      rejectedTrend: null,
      topDefects: null,
      defectComposition: null,
      worstContainers: null,
    });
    // Should render without crashing
    const { container } = render(<ContainerDashboard context="plant" />);
    expect(container.querySelector('.dashboard-view')).toBeInTheDocument();
  });
});


