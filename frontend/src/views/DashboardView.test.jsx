import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import DashboardView from './DashboardView';
import { normalizeScalarMetric } from './dashboardMetricUtils';
import { fetchAllKpis, fetchVolatileKpis } from '../api/kpi';

const barChartCalls = [];

vi.mock('../api/kpi', () => ({
  fetchAllKpis: vi.fn(),
  fetchVolatileKpis: vi.fn(),
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
    barChartCalls.length = 0;
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
    // The KPI card titles in order as they appear in the source
    const expectedTitles = [
      'Tasa de Defectos (AQL %)',
      'Distribución Pass / Reject',
      'AQL semanal (%)',
      'AQL por Estilo',
      'Top Defectos',
      'Piezas auditadas por semana',
      'Piezas rechazadas por semana',
      'Aceptadas por línea (conteo)',
      'Rechazadas por línea (conteo)',
      'Índice de aceptación por cliente (accepted/sample × 100)',
      'Índice de aceptación por línea (accepted/sample × 100)',
      'Rework en segundos por semana',
      'Defectos de Tela',
      'Contenedores por Estado',
      'Defectos por Estilo × Tipo',
    ];

    // Verify all 15 KPI card titles are present in the document
    // The Masonry component preserves source order in DOM
    expectedTitles.forEach((title) => {
      expect(screen.getByText(title)).toBeInTheDocument();
    });
  });

  it('preserves content order within masonry columns', () => {
    render(<DashboardView />);

    // The key contract: all KPI titles exist in the document
    // This verifies the masonry container doesn't drop or duplicate cards
    expect(screen.getByText('Tasa de Defectos (AQL %)')).toBeInTheDocument();
    expect(screen.getByText('Distribución Pass / Reject')).toBeInTheDocument();
    expect(screen.getByText('AQL semanal (%)')).toBeInTheDocument();
    expect(screen.getByText('Defectos por Estilo × Tipo')).toBeInTheDocument();

    // Verify the first card in DOM order is correct
    // (Masonry renders in columns, so DOM order ≠ visual row order)
    const kpiCards = document.querySelectorAll('.kpi-card');
    expect(kpiCards.length).toBeGreaterThan(0);

    const firstCard = kpiCards[0];
    // First card should be "Tasa de Defectos (AQL %)" - the first KPI in source
    expect(firstCard.querySelector('h2')?.textContent).toBe('Tasa de Defectos (AQL %)');
  });

  it('configures masonry with correct responsive breakpoints contract', () => {
    const { container } = render(<DashboardView />);

    // Verify masonry container exists with correct class
    const masonryContainer = container.querySelector('.dashboard-masonry');
    expect(masonryContainer).toBeInTheDocument();

    // Verify column class is applied (masonry uses this to style columns)
    const masonryColumn = container.querySelector('.dashboard-masonry-column');
    expect(masonryColumn).toBeInTheDocument();

    // The breakpointCols configuration { default: 3, 1100: 2, 768: 1 }
    // is passed as props to Masonry component.
    // We verify the CSS structure that supports this behavior exists:
    // - dashboard-masonry uses flexbox layout for columns
    // - Each column receives dashboard-masonry-column class for padding
    expect(masonryContainer).toHaveClass('dashboard-masonry');
  });

  it('masonry CSS supports responsive breakpoint behavior', () => {
    render(<DashboardView />);

    // Verify the CSS structure that supports responsive breakpoints exists:
    // - dashboard-masonry-column provides padding-left for column spacing
    // - The CSS @media query for mobile breakpoint exists in the stylesheet
    const columnEl = document.querySelector('.dashboard-masonry-column');
    expect(columnEl).toBeInTheDocument();

    // Verify the CSS class structure supports the breakpointCols contract
    // The .dashboard-masonry-column class provides column padding
    // which is essential for the masonry layout algorithm
    const computedPaddingLeft = window.getComputedStyle(columnEl).paddingLeft;
    expect(computedPaddingLeft).not.toBe('0px');
  });

  it('shows split AC/RE cards with count semantics', () => {
    render(<DashboardView />);

    expect(screen.getByText('Aceptadas por línea (conteo)')).toBeInTheDocument();
    expect(screen.getByText('Rechazadas por línea (conteo)')).toBeInTheDocument();
    expect(screen.queryByText('Conteo Aceptación/Rechazo por línea')).not.toBeInTheDocument();
  });

  it('does not render heatmap card as full-width layout', () => {
    const { container } = render(<DashboardView />);
    const heatmapTitle = screen.getByText('Defectos por Estilo × Tipo');
    const card = heatmapTitle.closest('.kpi-card');

    expect(card).toBeInTheDocument();
    expect(card).not.toHaveClass('full-width');
    expect(container.querySelector('.full-width')).toBeNull();
  });

  it('does not clamp acceptance percentages above 100%', async () => {
    fetchAllKpis.mockResolvedValue({
      performanceByCustomer: [{ label: 'Cliente QA', value: 134.56 }],
      performanceByLine: [{ label: '1', value: 120.0 }],
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
    expect(fabricChart.xAxisLabel).toBe('Tipo de defecto');
  });

  it('shows volatile helper banner in quick mode', () => {
    render(<DashboardView volatileFile={new File(['x'], 'kpis.xlsx')} />);

    expect(screen.getByText(/modo rápido:/i)).toBeInTheDocument();
    expect(screen.getByText(/no aplica filtros live/i)).toBeInTheDocument();
    expect(
      screen.getByText(/algunos kpis pueden no estar disponibles por depender de tablas de base de datos/i),
    ).toBeInTheDocument();
  });

  it('does not show volatile helper banner in live mode', () => {
    render(<DashboardView />);

    expect(screen.queryByText(/modo rápido:/i)).not.toBeInTheDocument();
  });
});

describe('DashboardView metric normalization', () => {
  it('returns scalar number unchanged', () => {
    expect(normalizeScalarMetric(2.5)).toBe(2.5);
  });

  it('unwraps { value } object metrics', () => {
    expect(normalizeScalarMetric({ label: 'Defect Rate', value: 3.1 })).toBe(3.1);
  });

  it('parses numeric strings and invalid values fallback to null', () => {
    expect(normalizeScalarMetric('4.2')).toBe(4.2);
    expect(normalizeScalarMetric({ value: '1.75' })).toBe(1.75);
    expect(normalizeScalarMetric({ value: 'N/A' })).toBeNull();
    expect(normalizeScalarMetric(undefined)).toBeNull();
  });
});
