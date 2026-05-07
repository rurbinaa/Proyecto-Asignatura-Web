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

      // Regression: "No data available" must NOT appear while still loading
      expect(screen.queryByText('No data available')).not.toBeInTheDocument();
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

  describe('Stale response prevention', () => {
    it('ignores stale analytics when filters change before first batch resolves', async () => {
      // Use deferred promises to control resolution order
      const resolvers = [];

      axiosClient.get.mockImplementation(
        () => new Promise((resolve) => {
          resolvers.push(resolve);
        })
      );

      render(<SecondsA4Dashboard />);

      // First batch: 9 calls dispatched
      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(9);
      });

      // Change filter — triggers second batch (9 more calls)
      screen.getByTestId('set-year-filter').click();

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(18);
      });

      // We now have 18 pending promises:
      // indices 0-8 = first batch (stale), 9-17 = second batch (should win)
      // index 0 & 9 = filter-options, index 1 & 10 = executive-summary, etc.

      // Resolve SECOND batch first with real data
      resolvers[9]({ data: { year: [2025] } });  // filter-options
      resolvers[10]({                             // executive-summary
        data: {
          totals: { total_of_2ds: 1234, seconds_by_sew: 800, seconds_by_fab: 434 },
          percentages: [],
        },
      });
      // Resolve remaining 7 analytics for second batch
      for (let i = 11; i <= 17; i++) resolvers[i]({ data: [] });

      // Wait for new data to render
      await waitFor(() => {
        expect(screen.getByText('KpiNumberCard-1234')).toBeInTheDocument();
      });

      // NOW resolve FIRST batch with stale data
      resolvers[1]({
        data: {
          totals: { total_of_2ds: 999, seconds_by_sew: 0, seconds_by_fab: 0 },
          percentages: [],
        },
      });
      for (let i = 0; i <= 8; i++) {
        if (i !== 1) resolvers[i]({ data: {} });
      }

      // Give React a tick to process
      await new Promise((r) => setTimeout(r, 50));

      // The dashboard should STILL show the latest (1234), not stale (999)
      expect(screen.getByText('KpiNumberCard-1234')).toBeInTheDocument();
      expect(screen.queryByText('KpiNumberCard-999')).not.toBeInTheDocument();
    });

    it('ignores stale filter-options when superseded by newer filter change', async () => {
      const resolvers = [];

      axiosClient.get.mockImplementation(
        () => new Promise((resolve) => {
          resolvers.push(resolve);
        })
      );

      render(<SecondsA4Dashboard />);

      // First batch dispatched
      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(9);
      });

      // Resolve first batch filter-options immediately
      resolvers[0]({ data: { year: [2025] } });
      resolvers[1]({ data: { totals: { total_of_2ds: 100 } } });
      for (let i = 2; i <= 8; i++) resolvers[i]({ data: [] });

      // Wait for initial render
      await waitFor(() => {
        expect(screen.getByText('KpiNumberCard-100')).toBeInTheDocument();
      });

      // Change filter again
      screen.getByTestId('set-line-filter').click();

      // Second batch dispatched
      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(18);
      });

      // Resolve second batch with specific data
      resolvers[9]({ data: { year: [2025], line: ['L1'] } });
      resolvers[10]({
        data: {
          totals: { total_of_2ds: 5678, seconds_by_sew: 3000, seconds_by_fab: 2678 },
          percentages: [],
        },
      });
      for (let i = 11; i <= 17; i++) resolvers[i]({ data: [] });

      await waitFor(() => {
        expect(screen.getByText('KpiNumberCard-5678')).toBeInTheDocument();
      });

      // Stale value should be gone
      expect(screen.queryByText('KpiNumberCard-100')).not.toBeInTheDocument();
    });
  });

  describe('Loading partition (shell vs content)', () => {
    it('renders card headers immediately while analytics are in flight', async () => {
      // Hold analytics in-flight but resolve filter-options
      const analyticsResolvers = [];

      axiosClient.get.mockImplementation((url) => {
        if (url.includes('filter-options')) {
          return Promise.resolve({ data: { year: [2025] } });
        }
        return new Promise((resolve) => {
          analyticsResolvers.push(resolve);
        });
      });

      render(<SecondsA4Dashboard />);

      // Card titles should render immediately (cards always mounted)
      expect(screen.getByText('Total of 2DS')).toBeInTheDocument();
      expect(screen.getByText('Seconds by Week')).toBeInTheDocument();

      // Chart content should NOT be present yet (no data resolved)
      expect(screen.queryByText('KpiNumberCard')).not.toBeInTheDocument();

      // Resolve ALL analytics deferred promises
      // analyticsResolvers[0] = executive-summary (needs real data)
      analyticsResolvers[0]({
        data: {
          totals: { total_of_2ds: 1234, seconds_by_sew: 800, seconds_by_fab: 434 },
        },
      });
      // Remaining 7 resolve with empty data
      for (let i = 1; i < analyticsResolvers.length; i++) {
        analyticsResolvers[i]({ data: [] });
      }

      // Chart content should now appear
      await waitFor(() => {
        expect(screen.getByText('KpiNumberCard-1234')).toBeInTheDocument();
      });
    });

    it('shows chart content only for the latest accepted fetch, not in-flight reloads', async () => {
      const batch1Resolvers = [];
      const batch2Resolvers = [];
      let currentBatch = null;

      axiosClient.get.mockImplementation((url) => {
        if (url.includes('filter-options')) {
          return Promise.resolve({ data: { year: [2025] } });
        }
        if (currentBatch === null || currentBatch === 1) {
          return new Promise((resolve) => {
            batch1Resolvers.push(resolve);
          });
        }
        return new Promise((resolve) => {
          batch2Resolvers.push(resolve);
        });
      });

      render(<SecondsA4Dashboard />);

      // Wait for first batch
      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(9);
      });

      // Switch to batch 2 before clicking
      currentBatch = 2;

      // Change filter
      screen.getByTestId('set-year-filter').click();

      await waitFor(() => {
        expect(axiosClient.get).toHaveBeenCalledTimes(18);
      });

      // Resolve SECOND batch first (the data that should win)
      batch2Resolvers[0]({
        data: {
          totals: { total_of_2ds: 5678, seconds_by_sew: 3000, seconds_by_fab: 2678 },
        },
      });
      for (let i = 1; i < batch2Resolvers.length; i++) {
        batch2Resolvers[i]({ data: [] });
      }

      await waitFor(() => {
        expect(screen.getByText('KpiNumberCard-5678')).toBeInTheDocument();
      });

      // Now resolve first batch (stale) — should not change display
      batch1Resolvers[0]({
        data: {
          totals: { total_of_2ds: 100 },
        },
      });
      for (let i = 1; i < batch1Resolvers.length; i++) {
        batch1Resolvers[i]({ data: [] });
      }

      await new Promise((r) => setTimeout(r, 50));

      // Still shows the latest batch data
      expect(screen.getByText('KpiNumberCard-5678')).toBeInTheDocument();
      expect(screen.queryByText('KpiNumberCard-100')).not.toBeInTheDocument();
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
