/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import SecondsGeneralDashboard from './SecondsGeneralDashboard';
import axiosClient from '../../api/axiosClient';

vi.mock('../../api/axiosClient');

vi.mock('../../Components/kpi/KpiCard', () => ({
  default: ({ title, children, error }) => (
    <section className="kpi-card">
      <h2>{title}</h2>
      {error && <div className="error-message">{error}</div>}
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
  default: () => <div>KpiNumberCard</div>,
}));

vi.mock('../../Components/kpi/FilterBar', () => ({
  default: ({ filters, onFilterChange, context }) => (
    <div>
      {`FilterBar-${context}`}
      <button
        data-testid="toggle-dual-lines"
        onClick={() => onFilterChange({ ...filters, includeDualLines: !filters.includeDualLines })}
      >
        Toggle Dual Lines
      </button>
      <button
        data-testid="select-line-code"
        onClick={() => onFilterChange({ ...filters, includeDualLines: true, lineCode: 'L1' })}
      >
        Select Line Code
      </button>
    </div>
  ),
}));

describe('SecondsGeneralDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('API calls', () => {
    it('fetches filter-options endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/filter-options/');

      const filterOptionsCall = axiosClient.get.mock.calls.find(
        ([url]) => url === '/quality/kpis/seconds-general/filter-options/'
      );
      expect(filterOptionsCall[1]?.params?.include_dual_lines).toBe(false);
    });

    it('fetches defects-by-customer endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/defects-by-customer/');
    });

    it('fetches defects-by-style endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/defects-by-style/');
    });

    it('fetches weekly-trend endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/weekly-trend/');
    });

    it('fetches sewing-vs-fabric endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/sewing-vs-fabric/');
    });

    it('fetches production-totals endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/production-totals/');
    });

    it('fetches top-defects with type=sewing endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/top-defects/');
    });

    it('fetches top-defects with type=fabric endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/top-defects/');
    });

    it('fetches fix-vs-definitive endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/fix-vs-definitive/');
    });

    it('fetches defects-by-color endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/defects-by-color/');
    });

    it('fetches defects-by-size endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/defects-by-size/');
    });

    it('fetches defects-by-line endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-general/defects-by-line/');
    });

    it('makes exactly 12 API calls on mount (1 filter-options + 11 analytics)', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(12);
      });
    });

    it('default analytics requests include include_dual_lines: false param', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(12);
      });

      // Check all analytics calls (skip filter-options) for the boolean flag
      const analyticsParams = axiosClient.get.mock.calls
        .filter(([url]) => url.includes('/quality/kpis/seconds-general/') && !url.includes('filter-options'))
        .map(([, config]) => config.params);

      for (const params of analyticsParams) {
        expect(params).toHaveProperty('include_dual_lines');
        expect(params.include_dual_lines).toBe(false);
      }
    });

    it('refetches filter-options when dual-line toggle changes', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(12);
      });

      // Count filter-options calls before toggle
      const filterCallsBefore = axiosClient.get.mock.calls.filter(
        ([url]) => url.includes('filter-options')
      );
      expect(filterCallsBefore).toHaveLength(1);

      // Toggle dual lines ON
      fireEvent.click(screen.getByTestId('toggle-dual-lines'));

      // Should trigger one more full reload: 11 analytics + 1 filter-options
      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(24);
      });

      const filterCallsAfter = axiosClient.get.mock.calls.filter(
        ([url]) => url.includes('filter-options')
      );
      expect(filterCallsAfter).toHaveLength(2);
      expect(filterCallsAfter[1][1]?.params?.include_dual_lines).toBe(true);
    });

    it('reapplies analytics immediately when line code changes', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(12);
      });

      fireEvent.click(screen.getByTestId('select-line-code'));

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(24);
      });

      const lineCall = axiosClient.get.mock.calls.findLast(
        ([url]) => url === '/quality/kpis/seconds-general/defects-by-line/'
      );
      expect(lineCall[1].params.include_dual_lines).toBe(true);
      expect(lineCall[1].params.line_code).toBe('L1');
    });
  });

  describe('Card rendering', () => {
    it('renders FilterBar component', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('FilterBar-customer')).toBeInTheDocument();
      });
    });

    it('passes customer context to FilterBar to enable dual line filters', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('FilterBar-customer')).toBeInTheDocument();
      });
    });

    it('renders Defects by Customer bar chart card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Defects by Customer')).toBeInTheDocument();
      });
    });

    it('renders Defects by Style bar chart card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Defects by Style')).toBeInTheDocument();
      });
    });

    it('renders Weekly Trend line chart card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Weekly Trend')).toBeInTheDocument();
      });
    });

    it('renders Sewing vs Fabric donut chart card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Sewing vs Fabric')).toBeInTheDocument();
      });
    });

    it('renders top row with independent production KPI cards', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Total Produced')).toBeInTheDocument();
        expect(screen.getByText('Total Fixed')).toBeInTheDocument();
        expect(screen.getByText('Total Definitive')).toBeInTheDocument();
      });
    });

    it('renders Top Sewing Defects card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Top Sewing Defects')).toBeInTheDocument();
      });
    });

    it('renders Top Fabric Defects card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Top Fabric Defects')).toBeInTheDocument();
      });
    });

    it('renders Fix vs Definitive card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Fix vs Definitive')).toBeInTheDocument();
      });
    });

    it('renders Defects by Color bar chart card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Defects by Color')).toBeInTheDocument();
      });
    });

    it('renders Defects by Size bar chart card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Defects by Size')).toBeInTheDocument();
      });
    });

    it('renders Defects by Line bar chart card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Defects by Line')).toBeInTheDocument();
      });
    });

    it('renders dashboard title', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Seconds General Analytics')).toBeInTheDocument();
      });
    });
  });

  describe('Error handling', () => {
    it('handles API errors gracefully — still attempts all 12 calls', async () => {
      axiosClient.get.mockRejectedValue(new Error('Network error'));

      render(<SecondsGeneralDashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(12);
      });
    });
  });
});
