/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import PlantDashboard from './PlantDashboard';
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

describe('PlantDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchAllKpis.mockResolvedValue({});
  });

  it('renders the QC FA Plant dashboard with context=plant', () => {
    render(<PlantDashboard />);
    expect(fetchAllKpis).toHaveBeenCalled();
    const [, context] = fetchAllKpis.mock.calls[0];
    expect(context).toBe('plant');
  });

  it('renders all 15 KPI card titles for plant context', () => {
    render(<PlantDashboard />);
    expect(screen.getByText('Defect Rate (AQL %)')).toBeInTheDocument();
    expect(screen.getByText('Weekly AQL (%)')).toBeInTheDocument();
    expect(screen.getByText('Containers by Status')).toBeInTheDocument();
  });

  it('forwards volatileData prop to QcfaKpiDashboard', () => {
    const testData = [{ id: 1, value: 'test' }];
    render(<PlantDashboard volatileData={testData} />);
    // volatileData triggers the "Fast mode" banner
    const banner = screen.getByRole('status');
    expect(banner).toBeInTheDocument();
    expect(banner.textContent).toMatch(/fast mode/i);
  });

  it('renders without volatileData (live mode)', () => {
    render(<PlantDashboard />);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});
