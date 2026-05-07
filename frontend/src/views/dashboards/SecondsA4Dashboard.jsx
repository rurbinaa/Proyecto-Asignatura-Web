import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import axiosClient from '../../api/axiosClient';
import KpiCard from '../../Components/kpi/KpiCard';
import BarChartKpi from '../../Components/kpi/BarChartKpi';
import LineChartKpi from '../../Components/kpi/LineChartKpi';
import DonutChartKpi from '../../Components/kpi/DonutChartKpi';
import KpiNumberCard from '../../Components/kpi/KpiNumberCard';
import SecondsA4FilterBar from '../../Components/kpi/SecondsA4FilterBar';
import Masonry from 'react-masonry-css';
import '../DashboardView.css';

const SECONDS_A4_BASE = '/quality/kpis/seconds-a4';

const INITIAL_FILTERS = {
  year: '',
  line: '',
};

/**
 * Reserved body heights for KpiCard stability — chart cards get a taller
 * reserved height to match their chart body, while summary cards get a
 * compact height. This prevents Masonry reflow across state transitions.
 */
const CARD_BODY_HEIGHTS = {
  chart: 360,
  summary: 180,
};

/**
 * Build query params from SecondsA4 filter state.
 * Frontend scope intentionally exposes only year + line.
 */
function buildFilterParams(filters) {
  const params = {};
  if (filters.year) params.year = filters.year;
  if (filters.line) params.line = filters.line;
  return params;
}

/**
 * SecondsA4Dashboard — Seconds A4 analytics view with year/line filters.
 *
 * Cards stay mounted at all times with a stable reserved body height so
 * Masonry never reflows. An AbortController + monotonic request-id guard
 * ensures only the latest fetch batch commits its data to state; any stale
 * completions from superseded filter changes are silently ignored.
 *
 * Card rendering follows the same pattern as other dashboard sheets:
 * while loading, KpiCard shows a spinner; when data arrives, the chart or
 * "No data available" content is rendered. No intermediate readiness gate.
 */
export default function SecondsA4Dashboard() {
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [filterOptions, setFilterOptions] = useState(null);

  const [executiveSummary, setExecutiveSummary] = useState(null);
  const [weeklyTrend, setWeeklyTrend] = useState(null);
  const [sewVsFab, setSewVsFab] = useState(null);
  const [byStyle, setByStyle] = useState(null);
  const [byColor, setByColor] = useState(null);
  const [byLine, setByLine] = useState(null);
  const [byCut, setByCut] = useState(null);
  const [passFailWeekly, setPassFailWeekly] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Minimum loading time so the spinner is visible even on cache hits
  const LOADING_MIN_MS = 300;
  const loadingStartRef = useRef(0);

  // ── Stale-response guards ──────────────────────────────────
  // Monotonic request id — incremented each loadData call so late
  // completions from superseded filter batches are ignored.
  const requestIdRef = useRef(0);

  // AbortController ref for the analytics batch — aborted on every
  // new loadData call so in-flight requests are cancelled early.
  const analyticsAbortRef = useRef(null);

  // AbortController ref for the filter-options fetch.
  const filterOptsAbortRef = useRef(null);

  // ── Fetch filter options (refetches when year/line change) ──
  useEffect(() => {
    // Abort any previous filter-options request
    if (filterOptsAbortRef.current) {
      filterOptsAbortRef.current.abort();
    }
    const controller = new AbortController();
    filterOptsAbortRef.current = controller;

    const params = buildFilterParams(filters);

    axiosClient.get(`${SECONDS_A4_BASE}/filter-options/`, {
      params,
      signal: controller.signal,
    })
      .then((res) => {
        // Only accept if this controller is still the active one
        if (filterOptsAbortRef.current === controller) {
          setFilterOptions(res.data);
        }
      })
      .catch(() => {
        // Silently fail — FilterBar falls back to text inputs
      });

    return () => {
      controller.abort();
    };
  }, [filters.year, filters.line]);

  // ── Data loading ────────────────────────────────────────────

  const loadData = useCallback(async (filtersOverride) => {
    // Abort any previous analytics batch
    if (analyticsAbortRef.current) {
      analyticsAbortRef.current.abort();
    }

    // Increment request id — this batch is now the active one
    const requestId = ++requestIdRef.current;
    const controller = new AbortController();
    analyticsAbortRef.current = controller;

    setLoading(true);
    setError(null);
    loadingStartRef.current = performance.now();

    const params = buildFilterParams(filtersOverride);

    try {
      const [
        execRes,
        trendRes,
        mixRes,
        styleRes,
        colorRes,
        lineRes,
        cutRes,
        passFailRes,
      ] = await Promise.all([
        axiosClient.get(`${SECONDS_A4_BASE}/executive-summary/`, { params, signal: controller.signal }),
        axiosClient.get(`${SECONDS_A4_BASE}/weekly-trend/`, { params, signal: controller.signal }),
        axiosClient.get(`${SECONDS_A4_BASE}/sew-vs-fab/`, { params, signal: controller.signal }),
        axiosClient.get(`${SECONDS_A4_BASE}/by-style/`, { params, signal: controller.signal }),
        axiosClient.get(`${SECONDS_A4_BASE}/by-color/`, { params, signal: controller.signal }),
        axiosClient.get(`${SECONDS_A4_BASE}/by-line/`, { params, signal: controller.signal }),
        axiosClient.get(`${SECONDS_A4_BASE}/by-cut/`, { params, signal: controller.signal }),
        axiosClient.get(`${SECONDS_A4_BASE}/pass-fail-weekly/`, { params, signal: controller.signal }),
      ]);

      // Only commit state if THIS batch is still the active one
      if (requestIdRef.current === requestId) {
        setExecutiveSummary(execRes.data);
        setWeeklyTrend(trendRes.data);
        setSewVsFab(mixRes.data);
        setByStyle(styleRes.data);
        setByColor(colorRes.data);
        setByLine(lineRes.data);
        setByCut(cutRes.data);
        setPassFailWeekly(passFailRes.data);

        // Ensure spinner is visible at least LOADING_MIN_MS
        const elapsed = performance.now() - loadingStartRef.current;
        if (elapsed < LOADING_MIN_MS) {
          await new Promise((r) => setTimeout(r, LOADING_MIN_MS - elapsed));
        }
        setLoading(false);
      }
    } catch (err) {
      // Ignore aborted requests — they are expected
      if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') return;
      // Only surface errors for the active request
      if (requestIdRef.current === requestId) {
        setError(err.response?.data?.detail || err.message || 'Failed to load analytics');

        // Ensure spinner is visible at least LOADING_MIN_MS
        const elapsed = performance.now() - loadingStartRef.current;
        if (elapsed < LOADING_MIN_MS) {
          await new Promise((r) => setTimeout(r, LOADING_MIN_MS - elapsed));
        }
        setLoading(false);
      }
    }
  }, []);

  // Trigger data load when filters change
  useEffect(() => {
    loadData(filters);
  }, [filters, loadData]);

  // ── Filter handlers ─────────────────────────────────────────

  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  const handleReset = useCallback(() => {
    setFilters(INITIAL_FILTERS);
  }, []);

  const handleRefresh = useCallback(() => {
    loadData(filters);
  }, [loadData, filters]);

  // ── Derived data (memoized) ────────────────────────────────

  const totals = useMemo(
    () => executiveSummary?.totals ?? null,
    [executiveSummary],
  );

  const seriesForWeeklyTrend = useMemo(
    () => (weeklyTrend && weeklyTrend.length > 0
      ? weeklyTrend.map((s) => ({
          name: s.name || 'Total of 2DS',
          data: s.data || [],
        }))
      : []),
    [weeklyTrend],
  );

  const sewVsFabForDonut = useMemo(
    () => (sewVsFab && sewVsFab.length > 0
      ? sewVsFab.map((item) => ({ name: item.label, value: item.value }))
      : []),
    [sewVsFab],
  );

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Seconds A4 Analytics</h1>
        <button className="refresh-btn" onClick={handleRefresh} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      <SecondsA4FilterBar
        filters={filters}
        onFilterChange={handleFilterChange}
        onReset={handleReset}
        filterOptions={filterOptions}
      />

      {/* ── Top row: KPI number cards ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '16px',
        }}
      >
        <KpiCard title="Total of 2DS" loading={loading} error={error} bodyMinHeight={CARD_BODY_HEIGHTS.summary}>
          {totals ? (
            <KpiNumberCard
              title=""
              value={totals.total_of_2ds}
              decimals={0}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        <KpiCard title="Sew vs Fabric" loading={loading} error={error} bodyMinHeight={CARD_BODY_HEIGHTS.summary}>
          {totals ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', padding: '16px' }}>
              <KpiNumberCard
                title="Sew"
                value={totals.seconds_by_sew}
                decimals={0}
              />
              <KpiNumberCard
                title="Fabric"
                value={totals.seconds_by_fab}
                decimals={0}
              />
            </div>
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>
      </div>

      <Masonry
        breakpointCols={{ default: 3, 768: 1 }}
        className="dashboard-masonry"
        columnClassName="dashboard-masonry-column"
      >
        {/* Seconds by Week */}
        <KpiCard title="Seconds by Week" loading={loading} bodyMinHeight={CARD_BODY_HEIGHTS.chart} error={error}>
          {seriesForWeeklyTrend.length > 0 ? (
            <LineChartKpi series={seriesForWeeklyTrend} xAxisLabel="Week" yAxisLabel="Total of 2DS" />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Sew vs Fabric Mix */}
        <KpiCard title="Sew vs Fabric Mix" loading={loading} bodyMinHeight={CARD_BODY_HEIGHTS.chart} error={error}>
          {sewVsFabForDonut.length > 0 ? (
            <DonutChartKpi data={sewVsFabForDonut} showSliceLabels minLabelPercent={0} />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Seconds by Style */}
        <KpiCard title="Seconds by Style" loading={loading} bodyMinHeight={CARD_BODY_HEIGHTS.chart} error={error}>
          {byStyle && byStyle.length > 0 ? (
            <BarChartKpi data={byStyle} horizontal color="#8b5cf6" xAxisLabel="Total of 2DS" yAxisLabel="Style" tooltipFormatter={(value) => [value.toString(), 'Total of 2DS']} />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Seconds by Color */}
        <KpiCard title="Seconds by Color" loading={loading} bodyMinHeight={CARD_BODY_HEIGHTS.chart} error={error}>
          {byColor && byColor.length > 0 ? (
            <BarChartKpi data={byColor} color="#06b6d4" xAxisLabel="Color" yAxisLabel="Total of 2DS" tooltipFormatter={(value) => [value.toString(), 'Total of 2DS']} />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Seconds by Line */}
        <KpiCard title="Seconds by Line" loading={loading} bodyMinHeight={CARD_BODY_HEIGHTS.chart} error={error}>
          {byLine && byLine.length > 0 ? (
            <BarChartKpi data={byLine} horizontal color="#f97316" xAxisLabel="Total of 2DS" yAxisLabel="Lines" tooltipFormatter={(value) => [value.toString(), 'Total of 2DS']} />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Seconds by Cut # */}
        <KpiCard title="Seconds by Cut #" loading={loading} bodyMinHeight={CARD_BODY_HEIGHTS.chart} error={error}>
          {byCut && byCut.length > 0 ? (
            <BarChartKpi data={byCut} horizontal color="#14b8a6" xAxisLabel="Total of 2DS" yAxisLabel="Cut #" tooltipFormatter={(value) => [value.toString(), 'Total of 2DS']} />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Pass vs Fail by Week */}
        <KpiCard title="Pass vs Fail by Week" loading={loading} bodyMinHeight={CARD_BODY_HEIGHTS.chart} error={error}>
          {passFailWeekly && passFailWeekly.length > 0 ? (
            <LineChartKpi series={passFailWeekly} yAxisLabel="Units" forceCategoricalXAxis />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>
      </Masonry>
    </div>
  );
}
