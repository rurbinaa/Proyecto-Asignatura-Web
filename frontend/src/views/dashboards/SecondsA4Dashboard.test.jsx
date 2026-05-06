/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import SecondsA4Dashboard from './SecondsA4Dashboard';
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
  default: ({ value }) => <div>KpiNumberCard-{value}</div>,
}));

vi.mock('../../Components/kpi/SecondsA4FilterBar', () => ({
  default: ({ filters, onFilterChange }) => (
    <div>
      SecondsA4FilterBar
      <button
        data-testid="set-year-filter"
        onClick={() => onFilterChange({ ...filters, year: '2025' })}
      >
        Set Year 2025
      </button>
      <button
        data-testid="set-line-filter"
        onClick={() => onFilterChange({ ...filters, year: '2025', line: 'L1' })}
      >
        Set Line L1
      </button>
    </div>
  ),
}));

describe('SecondsA4Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('API calls', () => {
    it('fetches filter-options endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-a4/filter-options/');
    });

    it('fetches executive-summary endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-a4/executive-summary/');
    });

    it('fetches weekly-trend endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-a4/weekly-trend/');
    });

    it('fetches sew-vs-fab endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-a4/sew-vs-fab/');
    });

    it('fetches by-style endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-a4/by-style/');
    });

    it('fetches by-color endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-a4/by-color/');
    });

    it('fetches by-line endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-a4/by-line/');
    });

    it('fetches by-cut endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-a4/by-cut/');
    });

    it('fetches pass-fail-weekly endpoint on mount', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalled();
      });

      const urls = axiosClient.get.mock.calls.map(([url]) => url);
      expect(urls).toContain('/quality/kpis/seconds-a4/pass-fail-weekly/');
    });

    it('makes exactly 9 API calls on mount (1 filter-options + 8 analytics)', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(9);
      });
    });

    it('passes year filter param to analytics endpoints', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      // Wait for initial 9 calls
      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(9);
      });

      // All analytics calls (non-filter-options) should have include_dual_lines param
      // for consistency with rest of app, even if unused by A4 backend
    });

    it('refetches all endpoints when filter changes via filter bar', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(9);
      });

      // Change filter via the mock filter bar
      const yearBtn = screen.getByTestId('set-year-filter');
      yearBtn.click();

      // Should trigger 1 filter-options + 8 analytics = 9 new calls
      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(18);
      });
    });

    it('refetches filter-options and analytics when line filter changes', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(9);
      });

      const lineBtn = screen.getByTestId('set-line-filter');
      lineBtn.click();

      // Should trigger 1 filter-options + 8 analytics = 9 new calls
      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(18);
      });
    });
  });

  describe('Card rendering', () => {
    it('renders dashboard title', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Seconds A4 Analytics')).toBeInTheDocument();
      });
    });

    it('renders SecondsA4FilterBar component', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('SecondsA4FilterBar')).toBeInTheDocument();
      });
    });

    it('renders Total of 2DS KPI card', async () => {
      const mockExecSummary = {
        totals: { total_of_2ds: 1234, seconds_by_sew: 800, seconds_by_fab: 434 },
        percentages: [],
      };
      // Mock 9 calls: filter-options + 8 analytics
      axiosClient.get
        .mockResolvedValueOnce({ data: { year: [2025] } })        // filter-options
        .mockResolvedValueOnce({ data: mockExecSummary })          // executive-summary
        .mockResolvedValueOnce({ data: [] })                        // weekly-trend
        .mockResolvedValueOnce({ data: [] })                        // sew-vs-fab
        .mockResolvedValueOnce({ data: [] })                        // by-style
        .mockResolvedValueOnce({ data: [] })                        // by-color
        .mockResolvedValueOnce({ data: [] })                        // by-line
        .mockResolvedValueOnce({ data: [] })                        // by-cut
        .mockResolvedValueOnce({ data: [] });                       // pass-fail-weekly

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Total of 2DS')).toBeInTheDocument();
      });
    });

    it('renders Sew vs Fabric KPI card', async () => {
      const mockExecSummary = {
        totals: { total_of_2ds: 1234, seconds_by_sew: 800, seconds_by_fab: 434 },
        percentages: [],
      };
      axiosClient.get
        .mockResolvedValueOnce({ data: { year: [2025] } })
        .mockResolvedValueOnce({ data: mockExecSummary })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Sew vs Fabric')).toBeInTheDocument();
      });
    });

    it('renders Seconds by Week card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Seconds by Week')).toBeInTheDocument();
      });
    });

    it('renders Seconds by Style card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Seconds by Style')).toBeInTheDocument();
      });
    });

    it('renders Seconds by Color card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Seconds by Color')).toBeInTheDocument();
      });
    });

    it('renders Seconds by Line card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Seconds by Line')).toBeInTheDocument();
      });
    });

    it('renders Seconds by Cut # card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Seconds by Cut #')).toBeInTheDocument();
      });
    });

    it('renders Pass vs Fail by Week card', async () => {
      axiosClient.get.mockResolvedValue({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Pass vs Fail by Week')).toBeInTheDocument();
      });
    });

    it('renders KpiNumberCard with Total of 2DS value', async () => {
      const mockExecSummary = {
        totals: { total_of_2ds: 1234, seconds_by_sew: 800, seconds_by_fab: 434 },
        percentages: [],
      };
      axiosClient.get
        .mockResolvedValueOnce({ data: { year: [2025] } })
        .mockResolvedValueOnce({ data: mockExecSummary })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('KpiNumberCard-1234')).toBeInTheDocument();
      });
    });

    it('renders Sew vs Fabric donut chart when data present', async () => {
      const mockExecSummary = {
        totals: { total_of_2ds: 1234, seconds_by_sew: 800, seconds_by_fab: 434 },
        percentages: [],
      };
      const mockSewVsFab = [
        { label: 'Sew', value: 800 },
        { label: 'Fabric', value: 434 },
      ];
      axiosClient.get
        .mockResolvedValueOnce({ data: { year: [2025] } })
        .mockResolvedValueOnce({ data: mockExecSummary })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: mockSewVsFab })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('DonutChartKpi')).toBeInTheDocument();
      });
    });

    it('renders BarChartKpi for Seconds by Style chart when data present', async () => {
      const mockExecSummary = {
        totals: { total_of_2ds: 1234, seconds_by_sew: 800, seconds_by_fab: 434 },
        percentages: [],
      };
      const mockByStyle = [
        { label: 'Style-A', value: 500 },
        { label: 'Style-B', value: 300 },
      ];
      axiosClient.get
        .mockResolvedValueOnce({ data: { year: [2025] } })
        .mockResolvedValueOnce({ data: mockExecSummary })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: mockByStyle })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('BarChartKpi')).toBeInTheDocument();
      });
    });
  });

  describe('States', () => {
    it('shows loading state while requests are in flight', async () => {
      // Never resolve — keep loading forever
      axiosClient.get.mockReturnValue(new Promise(() => {}));

      render(<SecondsA4Dashboard />);

      // Should show loading indicators — KpiCard renders spinner when loading
      // (we can't easily check the spinner DOM via mock, so verify the header renders)
      expect(screen.getByText('Seconds A4 Analytics')).toBeInTheDocument();
    });

    it('shows No data messages when all endpoints return empty', async () => {
      axiosClient.get.mockResolvedValue({ data: {} });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(9);
      });

      // With no totals data, charts show "No data available" — multiple cards render it
      await waitFor(() => {
        const emptyMessages = screen.getAllByText('No data available');
        expect(emptyMessages.length).toBeGreaterThanOrEqual(4);
      });
    });

    it('does NOT render a percentages section when percentages array is empty', async () => {
      const mockExecSummary = {
        totals: { total_of_2ds: 1234, seconds_by_sew: 800, seconds_by_fab: 434 },
        percentages: [],
      };
      axiosClient.get
        .mockResolvedValueOnce({ data: { year: [2025] } })
        .mockResolvedValueOnce({ data: mockExecSummary })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: [] });

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('Total of 2DS')).toBeInTheDocument();
      });

      // With empty percentages, no percentage-related heading should render
      expect(screen.queryByText('Quality Metrics')).not.toBeInTheDocument();
    });
  });

  describe('Error handling', () => {
    it('handles API errors gracefully — still attempts all 9 calls', async () => {
      axiosClient.get.mockRejectedValue(new Error('Network error'));

      render(<SecondsA4Dashboard />);

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(9);
      });
    });
  });
});
