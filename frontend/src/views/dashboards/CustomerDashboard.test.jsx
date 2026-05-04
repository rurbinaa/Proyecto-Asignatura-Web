/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import CustomerDashboard from './CustomerDashboard';
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

describe('CustomerDashboard — thin wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchAllKpis.mockResolvedValue({});
  });

  it('passes context=customer to QcfaKpiDashboard', () => {
    render(<CustomerDashboard />);
    expect(fetchAllKpis).toHaveBeenCalled();
    const [, context] = fetchAllKpis.mock.calls[0];
    expect(context).toBe('customer');
  });

  it('renders 14 KPI card titles for customer context (exclusive layout)', () => {
    render(<CustomerDashboard />);
    const kpiCards = document.querySelectorAll('.kpi-card h2');
    expect(kpiCards).toHaveLength(14);
  });

  it('includes Defect Rate (AQL %) and Weekly AQL (%) from Excel section', () => {
    render(<CustomerDashboard />);
    expect(screen.getByText('Defect Rate (AQL %)')).toBeInTheDocument();
    expect(screen.getByText('Weekly AQL (%)')).toBeInTheDocument();
  });

  it('includes Defect Composition from Rift section', () => {
    render(<CustomerDashboard />);
    expect(screen.getByText('Defect Composition')).toBeInTheDocument();
  });

  it('does NOT render removed cross-sheet cards', () => {
    render(<CustomerDashboard />);
    expect(screen.queryByText('Containers by Status')).not.toBeInTheDocument();
    expect(screen.queryByText('Fabric Defects')).not.toBeInTheDocument();
    expect(screen.queryByText('Weekly Rework (seconds)')).not.toBeInTheDocument();
  });

  it('forwards volatileData prop to QcfaKpiDashboard', () => {
    const testData = [{ id: 1, value: 'test' }];
    render(<CustomerDashboard volatileData={testData} />);
    const banner = screen.getByRole('status');
    expect(banner).toBeInTheDocument();
    expect(banner.textContent).toMatch(/fast mode/i);
  });

  it('renders without volatileData (live mode)', () => {
    render(<CustomerDashboard />);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});
