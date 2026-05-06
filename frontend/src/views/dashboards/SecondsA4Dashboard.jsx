import { useState, useEffect, useCallback } from 'react';
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
  cut_num: '',
};

/**
 * Build query params from SecondsA4 filter state.
 * Omits empty values and maps to snake_case API params.
 */
function buildFilterParams(filters) {
  const params = {};
  if (filters.year) params.year = filters.year;
  if (filters.line) params.line = filters.line;
  if (filters.cut_num) params.cut_num = filters.cut_num;
  return params;
}

/**
 * SecondsA4Dashboard — Seconds A4 analytics view with year/line/cut filters.
 *
 * Fetches 8 analytics + filter-options from the Seconds A4 backend:
 *   - Executive Summary (KPI number cards for totals)
 *   - Weekly Trend (line chart)
 *   - Sew vs Fabric (donut chart)
 *   - Seconds by Style (bar chart)
 *   - Seconds by Color (bar chart)
 *   - Seconds by Line (bar chart)
 *   - Seconds by Cut # (bar chart)
 *   - Pass vs Fail by Week (line chart)
 *
 * Applies year, line, and cut_num filters to all endpoints.
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
  const [prevFetchKey, setPrevFetchKey] = useState('');

  // Build a stable key for fetch deduplication
  const buildFetchKey = (f) => `${f.year}|${f.line}|${f.cut_num}`;

  // ── Fetch filter options (refetches when year/line/cut_num change) ──
  useEffect(() => {
    let cancelled = false;
    const params = buildFilterParams(filters);

    axiosClient.get(`${SECONDS_A4_BASE}/filter-options/`, { params })
      .then((res) => {
        if (!cancelled) {
          setFilterOptions(res.data);
        }
      })
      .catch(() => {
        // Silently fail — FilterBar falls back to text inputs
      });

    return () => {
      cancelled = true;
    };
  }, [filters.year, filters.line, filters.cut_num]);

  // ── Data loading ────────────────────────────────────────────

  const loadData = useCallback(async (filtersOverride) => {
    setLoading(true);
    setError(null);

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
        axiosClient.get(`${SECONDS_A4_BASE}/executive-summary/`, { params }),
        axiosClient.get(`${SECONDS_A4_BASE}/weekly-trend/`, { params }),
        axiosClient.get(`${SECONDS_A4_BASE}/sew-vs-fab/`, { params }),
        axiosClient.get(`${SECONDS_A4_BASE}/by-style/`, { params }),
        axiosClient.get(`${SECONDS_A4_BASE}/by-color/`, { params }),
        axiosClient.get(`${SECONDS_A4_BASE}/by-line/`, { params }),
        axiosClient.get(`${SECONDS_A4_BASE}/by-cut/`, { params }),
        axiosClient.get(`${SECONDS_A4_BASE}/pass-fail-weekly/`, { params }),
      ]);

      setExecutiveSummary(execRes.data);
      setWeeklyTrend(trendRes.data);
      setSewVsFab(mixRes.data);
      setByStyle(styleRes.data);
      setByColor(colorRes.data);
      setByLine(lineRes.data);
      setByCut(cutRes.data);
      setPassFailWeekly(passFailRes.data);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load analytics');
      setLoading(false);
    }
  }, []);

  // Trigger data load when filters change (debounced by fetch key)
  useEffect(() => {
    const key = buildFetchKey(filters);
    if (key !== prevFetchKey) {
      setPrevFetchKey(key);
      loadData(filters);
    }
  }, [filters, loadData, prevFetchKey]);

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

  // ── Derived data ─────────────────────────────────────────────

  const totals = executiveSummary?.totals;

  const seriesForWeeklyTrend = weeklyTrend && weeklyTrend.length > 0
    ? weeklyTrend.map((s) => ({
        name: s.name || 'Total of 2DS',
        data: s.data || [],
      }))
    : [];

  const sewVsFabForDonut = sewVsFab && sewVsFab.length > 0
    ? sewVsFab.map((item) => ({ name: item.label, value: item.value }))
    : [];

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
        <KpiCard title="Total of 2DS" loading={loading} error={error}>
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

        <KpiCard title="Sew vs Fabric" loading={loading} error={error}>
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
        <KpiCard title="Seconds by Week" loading={loading} error={error}>
          {seriesForWeeklyTrend.length > 0 ? (
            <LineChartKpi
              series={seriesForWeeklyTrend}
              xAxisLabel="Week"
              yAxisLabel="Total of 2DS"
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Sew vs Fabric Mix */}
        <KpiCard title="Sew vs Fabric Mix" loading={loading} error={error}>
          {sewVsFabForDonut.length > 0 ? (
            <DonutChartKpi
              data={sewVsFabForDonut}
              showSliceLabels
              minLabelPercent={0}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Seconds by Style */}
        <KpiCard title="Seconds by Style" loading={loading} error={error}>
          {byStyle && byStyle.length > 0 ? (
            <BarChartKpi
              data={byStyle}
              horizontal
              color="#8b5cf6"
              xAxisLabel="Total of 2DS"
              yAxisLabel="Style"
              tooltipFormatter={(value) => [value.toString(), 'Total of 2DS']}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Seconds by Color */}
        <KpiCard title="Seconds by Color" loading={loading} error={error}>
          {byColor && byColor.length > 0 ? (
            <BarChartKpi
              data={byColor}
              color="#06b6d4"
              xAxisLabel="Color"
              yAxisLabel="Total of 2DS"
              tooltipFormatter={(value) => [value.toString(), 'Total of 2DS']}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Seconds by Line */}
        <KpiCard title="Seconds by Line" loading={loading} error={error}>
          {byLine && byLine.length > 0 ? (
            <BarChartKpi
              data={byLine}
              horizontal
              color="#f97316"
              xAxisLabel="Total of 2DS"
              yAxisLabel="Lines"
              tooltipFormatter={(value) => [value.toString(), 'Total of 2DS']}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Seconds by Cut # */}
        <KpiCard title="Seconds by Cut #" loading={loading} error={error}>
          {byCut && byCut.length > 0 ? (
            <BarChartKpi
              data={byCut}
              horizontal
              color="#14b8a6"
              xAxisLabel="Total of 2DS"
              yAxisLabel="Cut #"
              tooltipFormatter={(value) => [value.toString(), 'Total of 2DS']}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Pass vs Fail by Week */}
        <KpiCard title="Pass vs Fail by Week" loading={loading} error={error}>
          {passFailWeekly && passFailWeekly.length > 0 ? (
            <LineChartKpi
              series={passFailWeekly}
              yAxisLabel="Units"
            />
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
