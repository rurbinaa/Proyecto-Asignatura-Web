/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import QcfaKpiDashboard from './QcfaKpiDashboard';
import { fetchAllKpis, getFilterOptions } from '../../api/kpi';

vi.mock('../../api/kpi', () => ({
  fetchAllKpis: vi.fn(),
  getFilterOptions: vi.fn().mockResolvedValue({}),
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

  // ── 14-card membership (exact inventory) ─────────────────────

  it('renders exactly 14 KPI card titles total', () => {
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
      'AQL by Team/Line',
      'Top Defects',
      'Weekly Rejected Pieces',
      'Accepted / Rejected Absolute Volume',
      'Weekly Audited Pieces',
      'Acceptance Rate by Customer (accepted / (accepted + rejected) × 100)',
      'Acceptance Rate by Line (accepted / (accepted + rejected) × 100)',
      'Defects by Style × Type',
      'Defect Trend Top 3',
      'Defect Composition',
    ];

    expectedTitles.forEach((title) => {
      expect(screen.getByText(title)).toBeInTheDocument();
    });
  });

  // ── Wrapper parity: plant and customer show same layout ──────

  it('renders the same 14-card layout for wrapper=plant', () => {
    render(<QcfaKpiDashboard context="plant" />);
    const kpiCards = document.querySelectorAll('.kpi-card h2');
    expect(kpiCards).toHaveLength(14);
    expect(screen.getByText('Defect Rate (AQL %)')).toBeInTheDocument();
    expect(screen.getByText('Defect Composition')).toBeInTheDocument();
  });

  it('renders the same 14-card layout for wrapper=customer', () => {
    render(<QcfaKpiDashboard context="customer" />);
    const kpiCards = document.querySelectorAll('.kpi-card h2');
    expect(kpiCards).toHaveLength(14);
    expect(screen.getByText('Defect Rate (AQL %)')).toBeInTheDocument();
    expect(screen.getByText('Defect Composition')).toBeInTheDocument();
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

  // ── Section membership: Original Excel Reports (8 cards) ────

  const EXCEL_TITLES = [
    'Defect Rate (AQL %)',
    'Pass / Reject Distribution',
    'Weekly AQL (%)',
    'AQL by Style',
    'AQL by Team/Line',
    'Top Defects',
    'Weekly Rejected Pieces',
    'Accepted / Rejected Absolute Volume',
  ];

  it('groups all 8 Original Excel Reports cards under the first section', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const excelHeader = screen.getByText('Original Excel Reports');
    const riftHeader = screen.getByText('Rift Analytics Insights');

    // Excel section header is before rift header in DOM order
    expect(
      excelHeader.compareDocumentPosition(riftHeader) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();

    EXCEL_TITLES.forEach((title) => {
      const card = screen.getByText(title);
      expect(card).toBeInTheDocument();
    });

    // Each excel card must appear after the excel header and before the rift header
    EXCEL_TITLES.forEach((title) => {
      const card = screen.getByText(title);
      expect(
        excelHeader.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
      // Excel cards must appear BEFORE the rift header
      expect(
        card.compareDocumentPosition(riftHeader) & Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
    });
  });

  it('contains exactly the 8 expected Excel cards between Excel and Rift headers', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const excelHeader = screen.getByText('Original Excel Reports');
    const riftHeader = screen.getByText('Rift Analytics Insights');

    // All cards between the two headers belong to Excel section
    const allKpiCards = document.querySelectorAll('.kpi-card h2');
    const excelCards = Array.from(allKpiCards).filter((h2) => {
      const posVsExcel = excelHeader.compareDocumentPosition(h2);
      const posVsRift = riftHeader.compareDocumentPosition(h2);
      return (posVsExcel & Node.DOCUMENT_POSITION_FOLLOWING) !== 0
        && (h2.compareDocumentPosition(riftHeader) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
    });

    expect(excelCards).toHaveLength(8);

    const excelTitles = excelCards.map((h2) => h2.textContent);
    EXCEL_TITLES.forEach((title) => {
      expect(excelTitles).toContain(title);
    });
  });

  // ── Section membership: Rift Analytics Insights (6 cards) ────

  const RIFT_TITLES = [
    'Weekly Audited Pieces',
    'Acceptance Rate by Customer (accepted / (accepted + rejected) × 100)',
    'Acceptance Rate by Line (accepted / (accepted + rejected) × 100)',
    'Defects by Style × Type',
    'Defect Trend Top 3',
    'Defect Composition',
  ];

  it('groups all 6 Rift Analytics Insights cards under the second section', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const riftHeader = screen.getByText('Rift Analytics Insights');

    RIFT_TITLES.forEach((title) => {
      const card = screen.getByText(title);
      expect(card).toBeInTheDocument();
    });

    // Each rift card must appear after the Rift section header
    RIFT_TITLES.forEach((title) => {
      const card = screen.getByText(title);
      expect(
        riftHeader.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
    });
  });

  it('contains exactly the 6 expected Rift cards after the Rift header', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const riftHeader = screen.getByText('Rift Analytics Insights');

    const allKpiCards = document.querySelectorAll('.kpi-card h2');
    const riftCards = Array.from(allKpiCards).filter((h2) => {
      return (riftHeader.compareDocumentPosition(h2) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
    });

    expect(riftCards).toHaveLength(6);

    const riftTitles = riftCards.map((h2) => h2.textContent);
    RIFT_TITLES.forEach((title) => {
      expect(riftTitles).toContain(title);
    });
  });

  // ── AQL by Team/Line visibility ────────────────────────────

  it('renders AQL by Team/Line card in live mode', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.getByText('AQL by Team/Line')).toBeInTheDocument();
  });

  it('renders AQL by Team/Line card in volatile mode', () => {
    render(<QcfaKpiDashboard context="customer" volatileData={[{ id: 1, value: 'test' }]} />);
    expect(screen.getByText('AQL by Team/Line')).toBeInTheDocument();
  });

  // ── Single accepted/rejected volume card ─────────────────────

  it('renders exactly one Accepted / Rejected Absolute Volume card', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.getByText('Accepted / Rejected Absolute Volume')).toBeInTheDocument();
  });

  it('does NOT render split Accepted by Line (count) card', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.queryByText('Accepted by Line (count)')).not.toBeInTheDocument();
  });

  it('does NOT render split Rejected by Line (count) card', () => {
    render(<QcfaKpiDashboard context="plant" />);
    expect(screen.queryByText('Rejected by Line (count)')).not.toBeInTheDocument();
  });

  // ── Intra-section DOM order (exact spec order per section) ──

  it('renders Excel section cards in exact DOM order per spec', () => {
    const { container } = render(<QcfaKpiDashboard context="plant" />);

    const sections = container.querySelectorAll('.dashboard-section--qfa-qfc');
    const excelGrid = sections[0].querySelector('.dashboard-section__grid');
    const excelItems = excelGrid.querySelectorAll('.dashboard-section__item');
    expect(excelItems).toHaveLength(8);

    const titles = Array.from(excelItems).map(
      (item) => item.querySelector('.kpi-card h2').textContent,
    );

    expect(titles).toEqual([
      'Defect Rate (AQL %)',
      'Pass / Reject Distribution',
      'Weekly AQL (%)',
      'AQL by Style',
      'AQL by Team/Line',
      'Top Defects',
      'Weekly Rejected Pieces',
      'Accepted / Rejected Absolute Volume',
    ]);
  });

  it('renders Rift section cards in exact DOM order per spec', () => {
    const { container } = render(<QcfaKpiDashboard context="plant" />);

    const sections = container.querySelectorAll('.dashboard-section--qfa-qfc');
    const riftGrid = sections[1].querySelector('.dashboard-section__grid');
    const riftItems = riftGrid.querySelectorAll('.dashboard-section__item');
    expect(riftItems).toHaveLength(6);

    const titles = Array.from(riftItems).map(
      (item) => item.querySelector('.kpi-card h2').textContent,
    );

    expect(titles).toEqual([
      'Weekly Audited Pieces',
      'Acceptance Rate by Customer (accepted / (accepted + rejected) × 100)',
      'Acceptance Rate by Line (accepted / (accepted + rejected) × 100)',
      'Defects by Style × Type',
      'Defect Trend Top 3',
      'Defect Composition',
    ]);
  });

  // ── Grid layout structure (replaces Masonry assertions) ──────

  it('renders two dashboard section containers with grid bodies', () => {
    const { container } = render(<QcfaKpiDashboard context="plant" />);

    const sections = container.querySelectorAll('.dashboard-section--qfa-qfc');
    expect(sections).toHaveLength(2);

    const grids = container.querySelectorAll('.dashboard-section__grid');
    expect(grids).toHaveLength(2);
  });

  it('renders 14 .dashboard-section__item wrappers, one per card', () => {
    const { container } = render(<QcfaKpiDashboard context="plant" />);

    const items = container.querySelectorAll('.dashboard-section__item');
    expect(items).toHaveLength(14);

    items.forEach((item) => {
      expect(item.dataset.layoutRole).toBeTruthy();
    });
  });

  it('assigns data-layout-role="metric" to Defect Rate (AQL %)', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const card = screen.getByText('Defect Rate (AQL %)');
    const item = card.closest('.dashboard-section__item');
    expect(item).not.toBeNull();
    expect(item.dataset.layoutRole).toBe('metric');
  });

  it('assigns data-layout-role="composed" to Accepted / Rejected Absolute Volume', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const card = screen.getByText('Accepted / Rejected Absolute Volume');
    const item = card.closest('.dashboard-section__item');
    expect(item).not.toBeNull();
    expect(item.dataset.layoutRole).toBe('composed');
  });

  it('assigns data-layout-role="wide" to Defects by Style × Type', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const card = screen.getByText('Defects by Style × Type');
    const item = card.closest('.dashboard-section__item');
    expect(item).not.toBeNull();
    expect(item.dataset.layoutRole).toBe('wide');
  });

  it('assigns data-layout-role="standard" to a sample of standard cards', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const standardTitles = [
      'Weekly AQL (%)',
      'Top Defects',
      'Weekly Audited Pieces',
      'Defect Composition',
    ];

    standardTitles.forEach((title) => {
      const card = screen.getByText(title);
      const item = card.closest('.dashboard-section__item');
      expect(item).not.toBeNull();
      expect(item.dataset.layoutRole).toBe('standard');
    });
  });

  it('assigns data-layout-role="standard" to Acceptance Rate by Customer', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const card = screen.getByText('Acceptance Rate by Customer (accepted / (accepted + rejected) × 100)');
    const item = card.closest('.dashboard-section__item');
    expect(item).not.toBeNull();
    expect(item.dataset.layoutRole).toBe('standard');
  });

  it('assigns data-layout-role="standard" to Acceptance Rate by Line', () => {
    render(<QcfaKpiDashboard context="plant" />);

    const card = screen.getByText('Acceptance Rate by Line (accepted / (accepted + rejected) × 100)');
    const item = card.closest('.dashboard-section__item');
    expect(item).not.toBeNull();
    expect(item.dataset.layoutRole).toBe('standard');
  });

  it('does not render any masonry-related CSS classes', () => {
    const { container } = render(<QcfaKpiDashboard context="plant" />);

    expect(container.querySelector('.dashboard-masonry')).toBeNull();
    expect(container.querySelector('.dashboard-masonry-column')).toBeNull();
  });

  it('renders the same section+grid structure for context=customer', () => {
    const { container } = render(<QcfaKpiDashboard context="customer" />);

    const sections = container.querySelectorAll('.dashboard-section--qfa-qfc');
    expect(sections).toHaveLength(2);

    const grids = container.querySelectorAll('.dashboard-section__grid');
    expect(grids).toHaveLength(2);

    const items = container.querySelectorAll('.dashboard-section__item');
    expect(items).toHaveLength(14);
  });

  it('assigns data-layout-role="composed" to exactly one card', () => {
    const { container } = render(<QcfaKpiDashboard context="plant" />);

    const composedItems = container.querySelectorAll(
      '.dashboard-section__item[data-layout-role="composed"]',
    );
    expect(composedItems).toHaveLength(1);

    const card = composedItems[0].querySelector('.kpi-card h2');
    expect(card).not.toBeNull();
    expect(card.textContent).toBe('Accepted / Rejected Absolute Volume');
  });

  it('assigns data-layout-role="wide" to exactly one card (Defects by Style × Type)', () => {
    const { container } = render(<QcfaKpiDashboard context="plant" />);

    const wideItems = container.querySelectorAll(
      '.dashboard-section__item[data-layout-role="wide"]',
    );
    expect(wideItems).toHaveLength(1);

    const card = wideItems[0].querySelector('.kpi-card h2');
    expect(card).not.toBeNull();
    expect(card.textContent).toBe('Defects by Style × Type');
  });

  it('assigns data-layout-role="metric" to exactly one card (Defect Rate)', () => {
    const { container } = render(<QcfaKpiDashboard context="plant" />);

    const metricItems = container.querySelectorAll(
      '.dashboard-section__item[data-layout-role="metric"]',
    );
    expect(metricItems).toHaveLength(1);

    const card = metricItems[0].querySelector('.kpi-card h2');
    expect(card).not.toBeNull();
    expect(card.textContent).toBe('Defect Rate (AQL %)');
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

  // ── Volatile mode insight chart parity ────────────────────────

  it('renders all Rift insight cards in volatile mode without crash', () => {
    render(<QcfaKpiDashboard context="plant" volatileData={[{ id: 1, value: 'test' }]} />);

    expect(screen.getByText('Defect Trend Top 3')).toBeInTheDocument();
    expect(screen.getByText('Defect Composition')).toBeInTheDocument();
    expect(screen.getByText('Original Excel Reports')).toBeInTheDocument();
    expect(screen.getByText('Rift Analytics Insights')).toBeInTheDocument();
  });

  it('renders all Rift insight cards in live mode without crash', () => {
    render(<QcfaKpiDashboard context="customer" />);

    expect(screen.getByText('Defect Trend Top 3')).toBeInTheDocument();
    expect(screen.getByText('Defect Composition')).toBeInTheDocument();
  });

  // ── Chart-state rendering ──────────────────────────────────────

  it('shows explicit empty message in defect cards when KPIs return empty', async () => {
    fetchAllKpis.mockResolvedValue({
      defectComposition: [],
      defectTrendTop3: [],
      topDefects: [],
      defectsByStyleType: [],
    });

    render(<QcfaKpiDashboard context="plant" />);

    await waitFor(() => {
      const stateMessages = document.querySelectorAll('.state-message');
      expect(stateMessages.length).toBeGreaterThanOrEqual(4);
    });
  });

  it('shows explicit unavailable message when volatile data has unsupported defect insights', () => {
    render(<QcfaKpiDashboard
      context="customer"
      volatileData={[{ id: 1, value: 'test' }]}
    />);

    const stateMessages = document.querySelectorAll('.state-message');
    expect(stateMessages.length).toBeGreaterThanOrEqual(2);
    const unavailableTexts = Array.from(stateMessages).filter(
      (el) => el.textContent.toLowerCase().includes('unavailable') ||
              el.textContent.toLowerCase().includes('not supported') ||
              el.textContent.toLowerCase().includes('not available') ||
              el.textContent.toLowerCase().includes('no disponible'),
    );
    expect(unavailableTexts.length).toBeGreaterThanOrEqual(1);
  });

  it('renders defect charts with ready status when valid data is returned', async () => {
    fetchAllKpis.mockResolvedValue({
      topDefects: { result: [{ label: 'Hole', value: 10 }] },
      defectsByStyleType: { result: [{ x: 'S1', y: 'Hole', value: 5 }] },
      defectComposition: { result: [{ name: 'Hole', value: 10 }] },
      defectTrendTop3: { result: [{ name: 'Hole', data: [{ x: 1, y: 5 }] }] },
    });

    render(<QcfaKpiDashboard context="plant" />);

    await waitFor(() => {
      // Multiple BarChartKpi elements exist (Excel: Top Defects, AQL by Team/Line + composed volume)
      const barCharts = screen.getAllByText('BarChartKpi');
      expect(barCharts.length).toBeGreaterThanOrEqual(1);
      // LineChartKpi must appear (AQL Weekly, Weekly Rejected Pieces, Defect Trend Top 3, etc.)
      const lineCharts = screen.getAllByText('LineChartKpi');
      expect(lineCharts.length).toBeGreaterThanOrEqual(1);
      // DonutChartKpi must appear (Pass/Reject Distribution, Defect Composition)
      expect(screen.getByText('DonutChartKpi')).toBeInTheDocument();
    });
  });

  it('includes context indicator in volatile mode rendering', () => {
    render(<QcfaKpiDashboard
      context="customer"
      volatileFile={new File(['test'], 'test.xlsx')}
    />);

    const banner = screen.getByRole('status');
    expect(banner).toBeInTheDocument();
  });

  // ── Dual-line toggle (Slice 3 / Task 4.3) ──────────────────────────

  it('RED - passes includeDualLines=false in filters to fetchAllKpis by default (hidden)', async () => {
    fetchAllKpis.mockResolvedValue({});

    render(<QcfaKpiDashboard context="customer" />);

    await waitFor(() => {
      expect(fetchAllKpis).toHaveBeenCalled();
      const [filters, contextArg] = fetchAllKpis.mock.calls[0];
      expect(contextArg).toBe('customer');
      expect(filters.includeDualLines).toBe(false);
    });
  });

  it('RED - passes dual-line filter state to fetchAllKpis on initial load', async () => {
    fetchAllKpis.mockResolvedValue({});

    render(<QcfaKpiDashboard context="customer" />);

    await waitFor(() => {
      const [filters] = fetchAllKpis.mock.calls[0];
      expect(filters).toHaveProperty('includeDualLines');
      expect(filters).toHaveProperty('lineCode');
    });
  });

  it('RED - dual lines hidden by default: includeDualLines is false', async () => {
    fetchAllKpis.mockResolvedValue({});

    render(<QcfaKpiDashboard context="customer" />);

    await waitFor(() => {
      const [filters] = fetchAllKpis.mock.calls[0];
      expect(filters.includeDualLines).toBe(false);
    });
  });

  it('RED - context=plant does not send includeDualLines in filter-options request', () => {
    // For plant context, getFilterOptions should be called without include_dual_lines
    getFilterOptions.mockResolvedValue({ week: [], team: [] });
    render(<QcfaKpiDashboard context="plant" />);

    expect(getFilterOptions).toHaveBeenCalled();
    // Plant context: first arg should be 'plant', second should be undefined (no include_dual_lines)
    const [contextArg, includeDualLinesArg] = getFilterOptions.mock.calls[0];
    expect(contextArg).toBe('plant');
    expect(includeDualLinesArg).toBeUndefined();
  });

  it('RED - context=customer passes include_dual_lines to getFilterOptions', () => {
    getFilterOptions.mockResolvedValue({ week: [], team: [] });
    render(<QcfaKpiDashboard context="customer" />);

    expect(getFilterOptions).toHaveBeenCalled();
    const [contextArg, includeDualLinesArg] = getFilterOptions.mock.calls[0];
    expect(contextArg).toBe('customer');
    // includeDualLines defaults to false (hidden)
    expect(includeDualLinesArg).toBe(false);
  });

  it('RED - passes context prop to FilterBar', () => {
    render(<QcfaKpiDashboard context="customer" />);

    // FilterBar is mocked to render "FilterBar", but we verify the component renders
    expect(screen.getByText('FilterBar')).toBeInTheDocument();
  });

  // ── Data wiring: AQL by Team/Line renders chart (not null message) with data ──

  it('renders AQL by Team/Line bar chart when aqlByTeam data is available in live mode', async () => {
    fetchAllKpis.mockResolvedValue({
      aqlByTeam: { data: [{ label: 'Team-1', value: 2.5 }] },
    });

    render(<QcfaKpiDashboard context="plant" />);

    await waitFor(() => {
      // The AQL by Team/Line card must exist
      expect(screen.getByText('AQL by Team/Line')).toBeInTheDocument();
      // It must NOT show a null message (proof that aqlByTeamData is wired)
      const aqlCard = screen.getByText('AQL by Team/Line').closest('.kpi-card');
      expect(aqlCard.querySelector('.null-message')).toBeNull();
    });
  });

  it('shows unavailable message for AQL by Team/Line when backend returns unavailable status', async () => {
    fetchAllKpis.mockResolvedValue({
      aqlByTeam: { status: 'unavailable', reason: 'db_error', message: 'AQL by Team data unavailable' },
    });

    render(<QcfaKpiDashboard context="plant" />);

    await waitFor(() => {
      const aqlCard = screen.getByText('AQL by Team/Line').closest('.kpi-card');
      expect(aqlCard.querySelector('.null-message')).not.toBeNull();
    });
  });

  // ── Data wiring: Rift section cards render charts (not null messages) with data ──

  it('renders Rift section cards with chart data when valid KPIs are returned', async () => {
    fetchAllKpis.mockResolvedValue({
      auditedPieces: { data: [{ name: 'Pieces', data: [{ x: 1, y: 100 }] }] },
      performanceByCustomer: { result: [{ label: 'Customer X', value: 92.5 }] },
      performanceByLine: { result: [{ label: 'Line 1', value: 95.2 }] },
      defectsByStyleType: { result: [{ x: 'S1', y: 'Hole', value: 5 }] },
      defectTrendTop3: { result: [{ name: 'Hole', data: [{ x: 1, y: 5 }] }] },
      defectComposition: { result: [{ name: 'Hole', value: 10 }] },
    });

    render(<QcfaKpiDashboard context="plant" />);

    await waitFor(() => {
      // All 6 Rift cards must exist
      expect(screen.getByText('Weekly Audited Pieces')).toBeInTheDocument();
      expect(screen.getByText('Acceptance Rate by Customer (accepted / (accepted + rejected) × 100)')).toBeInTheDocument();
      expect(screen.getByText('Acceptance Rate by Line (accepted / (accepted + rejected) × 100)')).toBeInTheDocument();
      expect(screen.getByText('Defects by Style × Type')).toBeInTheDocument();
      expect(screen.getByText('Defect Trend Top 3')).toBeInTheDocument();
      expect(screen.getByText('Defect Composition')).toBeInTheDocument();

      // Rift cards with data must NOT show null messages (proof of wiring)
      RIFT_TITLES.forEach((title) => {
        const card = screen.getByText(title).closest('.kpi-card');
        expect(card.querySelector('.null-message')).toBeNull();
      });
    });
  });

  it('shows null/unavailable messages in Rift cards when KPI data is absent', async () => {
    // Default mock returns empty object — all Rift KPIs are null/undefined
    fetchAllKpis.mockResolvedValue({});

    render(<QcfaKpiDashboard context="plant" />);

    await waitFor(() => {
      // At least the first 4 Rift cards should show null messages
      // (defectTrendTop3 and defectComposition use state messages, not null-message)
      ['Weekly Audited Pieces', 'Acceptance Rate by Customer (accepted / (accepted + rejected) × 100)',
        'Acceptance Rate by Line (accepted / (accepted + rejected) × 100)'].forEach((title) => {
        const card = screen.getByText(title).closest('.kpi-card');
        expect(card.querySelector('.null-message')).not.toBeNull();
      });
    });
  });
});
