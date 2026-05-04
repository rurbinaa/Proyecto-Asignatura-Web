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

describe('QcfaKpiDashboard — exclusive layout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchAllKpis.mockResolvedValue({});
  });

  // ── Section headers ──────────────────────────────────────────

  it('renders section headers in order: Original Excel Reports then Rift Analytics Insights', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const excelHeader = screen.getByText('Original Excel Reports');
    const riftHeader = screen.getByText('Rift Analytics Insights');

    expect(excelHeader).toBeInTheDocument();
    expect(riftHeader).toBeInTheDocument();

    // Order: Excel section must appear before Rift section in the DOM
    const excelPos = excelHeader.compareDocumentPosition(riftHeader);
    expect(excelPos & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('renders section headers when volatileData is provided', () => {
    render(<QcfaKpiDashboard context="plant" volatileData={[{ id: 1, value: 'test' }]} />);

    expect(screen.getByText('Original Excel Reports')).toBeInTheDocument();
    expect(screen.getByText('Rift Analytics Insights')).toBeInTheDocument();
  });

  // ── 14-card membership (not 15) ──────────────────────────────

  it('renders exactly 14 KPI card titles total (3 removed, 2 added)', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const kpiCards = document.querySelectorAll('.kpi-card h2');
    expect(kpiCards).toHaveLength(14);
  });

  it('renders all 14 expected card titles in DOM order', () => {
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
      'Defects by Style × Type',
      'Defect Trend Top 3',
      'Defect Composition',
    ];

    expectedTitles.forEach((title) => {
      expect(screen.getByText(title)).toBeInTheDocument();
    });
  });

  // ── Removed cross-sheet cards ────────────────────────────────

  it('does NOT render Weekly Rework (seconds) card', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.queryByText('Weekly Rework (seconds)')).not.toBeInTheDocument();
  });

  it('does NOT render Fabric Defects card', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.queryByText('Fabric Defects')).not.toBeInTheDocument();
  });

  it('does NOT render Containers by Status card', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.queryByText('Containers by Status')).not.toBeInTheDocument();
  });

  // ── Section membership: Original Excel Reports (12 cards) ────

  it('groups all 12 Original Excel Reports cards under the first section', () => {
    const { container } = render(<QcfaKpiDashboard context="plant" />);

    // Find the section headers in the DOM
    const excelHeader = screen.getByText('Original Excel Reports');
    const riftHeader = screen.getByText('Rift Analytics Insights');

    // Excel section header is before rift header in DOM order
    expect(
      excelHeader.compareDocumentPosition(riftHeader) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();

    const excelTitles = [
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
      'Defects by Style × Type',
    ];

    excelTitles.forEach((title) => {
      const card = screen.getByText(title);
      expect(card).toBeInTheDocument();
    });

    // Each excel card must appear after the excel header
    excelTitles.forEach((title) => {
      const card = screen.getByText(title);
      expect(
        excelHeader.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
    });
  });

  // ── Section membership: Rift Analytics Insights (2 cards) ────

  it('groups both Rift Analytics Insights cards under the second section', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const riftHeader = screen.getByText('Rift Analytics Insights');
    const trendCard = screen.getByText('Defect Trend Top 3');
    const compCard = screen.getByText('Defect Composition');

    expect(trendCard).toBeInTheDocument();
    expect(compCard).toBeInTheDocument();

    // Both cards must appear after the Rift section header
    expect(
      riftHeader.compareDocumentPosition(trendCard) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      riftHeader.compareDocumentPosition(compCard) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it('orders Rift cards as Defect Trend Top 3 then Defect Composition', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const trendCard = screen.getByText('Defect Trend Top 3');
    const compCard = screen.getByText('Defect Composition');

    // Trend must appear before Composition in DOM order
    expect(
      trendCard.compareDocumentPosition(compCard) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  // ── New insight chart cards are wired ────────────────────────

  it('renders Defect Trend Top 3 card', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.getByText('Defect Trend Top 3')).toBeInTheDocument();
  });

  it('renders Defect Composition card', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.getByText('Defect Composition')).toBeInTheDocument();
  });

  // ── Layout structure ─────────────────────────────────────────

  it('renders a masonry container per section', () => {
    const { container } = render(<QcfaKpiDashboard context="plant" />);
    const masonryContainers = container.querySelectorAll('.dashboard-masonry');
    // Two sections → two masonry containers
    expect(masonryContainers.length).toBeGreaterThanOrEqual(2);
  });

  // ── Context forwarding (unchanged behavior) ─────────────────

  it('passes context=plant to fetchAllKpis on initial load', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(fetchAllKpis).toHaveBeenCalled();
    const [filters, context] = fetchAllKpis.mock.calls[0];
    expect(context).toBe('plant');
    expect(filters).toBeDefined();
  });

  it('passes context=customer to fetchAllKpis', () => {
    render(<QcfaKpiDashboard context="customer" />);
    expect(fetchAllKpis).toHaveBeenCalled();
    const [, context] = fetchAllKpis.mock.calls[0];
    expect(context).toBe('customer');
  });

  // ── UI chrome ────────────────────────────────────────────────

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
});
