import { useState, useEffect, useCallback } from 'react';
import axiosClient from '../../api/axiosClient';
import KpiCard from '../../Components/kpi/KpiCard';
import BarChartKpi from '../../Components/kpi/BarChartKpi';
import LineChartKpi from '../../Components/kpi/LineChartKpi';
import DonutChartKpi from '../../Components/kpi/DonutChartKpi';
import KpiNumberCard from '../../Components/kpi/KpiNumberCard';
import FilterBar from '../../Components/kpi/FilterBar';
import useVolatileDashboardCache from '../useVolatileDashboardCache';
import Masonry from 'react-masonry-css';
import '../DashboardView.css';

const SECONDS_GEN_BASE = '/quality/kpis/seconds-general';

const INITIAL_FILTERS = {
  date_range: ['', ''],
  week: '',
  customer: '',
  style: '',
  color: '',
  team: '',
  batch: '',
  includeDualLines: false,
  lineCode: '',
};

/**
 * Build query params for the SecondsGeneral API from the FilterBar state.
 * Converts camelCase FilterBar fields to snake_case API params.
 * Omits empty/undefined values and joins arrays as comma-separated strings.
 */
function buildFilterParams(filters) {
  const params = {};

  if (filters.date_range?.[0] && filters.date_range?.[1]) {
    params.date_range = filters.date_range.join(',');
  }
  if (filters.week) params.week = filters.week;
  if (filters.customer) params.customer = filters.customer;
  if (filters.style) params.style = filters.style;
  if (filters.color) params.color = filters.color;
  if (filters.team) params.team = filters.team;
  params.include_dual_lines = filters.includeDualLines === true;
  if (filters.lineCode) params.line_code = filters.lineCode;

  return params;
}

/**
 * SecondsGeneralDashboard — Seconds General analytics view with global filters.
 *
 * Fetches 11 analytics + filter-options from the SecondsGeneral backend:
 *   - Defects by Customer (bar chart)
 *   - Defects by Style (bar chart)
 *   - Weekly Trend (line chart)
 *   - Sewing vs Fabric Mix (donut chart)
 *   - Production Totals (KPI number cards)
 *   - Top Sewing Defects Pareto (bar chart)
 *   - Top Fabric Defects Pareto (bar chart)
 *   - Fix vs Definitive Efficacy (line chart)
 *   - Defects by Color (bar chart) — V2
 *   - Defects by Size (bar chart) — V2
 *   - Defects by Line (bar chart) — V2
 *
 * All data is sourced exclusively from SecondsGeneral data (spec isolation requirement).
 * Global filters are applied to all endpoints via SecondsGeneralFilterMixin on the backend.
 */
export default function SecondsGeneralDashboard({ volatileFile }) {
  // ── Volatile (fast) mode ─────────────────────────────────────────────
  const { data: volatileData, loading: volatileLoading, error: volatileError } =
    useVolatileDashboardCache(volatileFile, 'seconds_general');

  // ── Live mode state ──────────────────────────────────────────────────
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [filterOptions, setFilterOptions] = useState(null);

  const [defectsByCustomer, setDefectsByCustomer] = useState(null);
  const [defectsByStyle, setDefectsByStyle] = useState(null);
  const [weeklyTrend, setWeeklyTrend] = useState(null);
  const [sewingVsFabric, setSewingVsFabric] = useState(null);
  const [productionTotals, setProductionTotals] = useState(null);
  const [topSewingDefects, setTopSewingDefects] = useState(null);
  const [topFabricDefects, setTopFabricDefects] = useState(null);
  const [fixVsDefinitive, setFixVsDefinitive] = useState(null);
  const [defectsByColor, setDefectsByColor] = useState(null);
  const [defectsBySize, setDefectsBySize] = useState(null);
  const [defectsByLine, setDefectsByLine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // If in volatile mode, use volatile data
  const isVolatile = Boolean(volatileFile);

  // Derive state from volatile data when applicable
  const activeDefectsByCustomer = isVolatile ? volatileData?.defectsByCustomer : defectsByCustomer;
  const activeDefectsByStyle = isVolatile ? volatileData?.defectsByStyle : defectsByStyle;

  // Weekly trend: volatile uses camelCase, live uses name/data series
  let activeWeeklyTrend;
  if (isVolatile) {
    activeWeeklyTrend = volatileData?.weeklyTrend || [];
  } else {
    activeWeeklyTrend = weeklyTrend && weeklyTrend.length > 0
      ? weeklyTrend.map((s) => ({ name: s.name || 'Defects', data: s.data || [] }))
      : [];
  }

  // Sewing vs Fabric: volatile uses camelCase with label/value, live uses name/value
  let activeSewingVsFabric;
  if (isVolatile) {
    activeSewingVsFabric = volatileData?.sewingVsFabric
      ? volatileData.sewingVsFabric.map((item) => ({ name: item.label, value: item.value }))
      : [];
  } else {
    activeSewingVsFabric = sewingVsFabric || [];
  }

  const activeProductionTotals = isVolatile ? volatileData?.productionTotals : productionTotals;
  const activeTopSewingDefects = isVolatile ? volatileData?.topSewingDefects : topSewingDefects;
  const activeTopFabricDefects = isVolatile ? volatileData?.topFabricDefects : topFabricDefects;
  const activeFixVsDefinitive = isVolatile ? volatileData?.fixVsDefinitive : fixVsDefinitive;
  const activeDefectsByColor = isVolatile ? volatileData?.defectsByColor : defectsByColor;
  const activeDefectsBySize = isVolatile ? volatileData?.defectsBySize : defectsBySize;
  const activeDefectsByLine = isVolatile ? volatileData?.defectsByLine : defectsByLine;

  const activeLoading = isVolatile ? volatileLoading : loading;
  const activeError = isVolatile ? volatileError : error;

  // ── Live mode: fetch filter options on mount ─────────────────────────
  useEffect(() => {
    if (isVolatile) return; // No filter options needed in volatile mode

    let cancelled = false;

    axiosClient.get(`${SECONDS_GEN_BASE}/filter-options/`, {
      params: {
        include_dual_lines: filters.includeDualLines === true,
      },
    })
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
  }, [filters.includeDualLines, isVolatile]);


  const loadData = useCallback(async (filtersOverride) => {
    if (isVolatile) return; // No live fetch in volatile mode
    setLoading(true);
    setError(null);

    const params = buildFilterParams(filtersOverride);

    try {
      const [
        custRes,
        styleRes,
        trendRes,
        mixRes,
        prodRes,
        sewDefRes,
        fabDefRes,
        fixDefRes,
        colorRes,
        sizeRes,
        lineRes,
      ] = await Promise.all([
        axiosClient.get(`${SECONDS_GEN_BASE}/defects-by-customer/`, { params }),
        axiosClient.get(`${SECONDS_GEN_BASE}/defects-by-style/`, { params }),
        axiosClient.get(`${SECONDS_GEN_BASE}/weekly-trend/`, { params }),
        axiosClient.get(`${SECONDS_GEN_BASE}/sewing-vs-fabric/`, { params }),
        axiosClient.get(`${SECONDS_GEN_BASE}/production-totals/`, { params }),
        axiosClient.get(`${SECONDS_GEN_BASE}/top-defects/`, { params: { ...params, type: 'sewing' } }),
        axiosClient.get(`${SECONDS_GEN_BASE}/top-defects/`, { params: { ...params, type: 'fabric' } }),
        axiosClient.get(`${SECONDS_GEN_BASE}/fix-vs-definitive/`, { params }),
        axiosClient.get(`${SECONDS_GEN_BASE}/defects-by-color/`, { params }),
        axiosClient.get(`${SECONDS_GEN_BASE}/defects-by-size/`, { params }),
        axiosClient.get(`${SECONDS_GEN_BASE}/defects-by-line/`, { params }),
      ]);

      setDefectsByCustomer(custRes.data);
      setDefectsByStyle(styleRes.data);
      setWeeklyTrend(trendRes.data);
      setSewingVsFabric(mixRes.data.map((item) => ({ name: item.label, value: item.value })));
      setProductionTotals(prodRes.data);
      setTopSewingDefects(sewDefRes.data);
      setTopFabricDefects(fabDefRes.data);
      setFixVsDefinitive(fixDefRes.data);
      setDefectsByColor(colorRes.data);
      setDefectsBySize(sizeRes.data);
      setDefectsByLine(lineRes.data);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load analytics');
      setLoading(false);
    }
  }, [isVolatile]);

  // Mirror QC FA Customer behavior: filters apply immediately on change.
  useEffect(() => {
    if (!isVolatile) {
      loadData(filters); // eslint-disable-line react-hooks/set-state-in-effect
    }
  }, [filters, loadData, isVolatile]);


  const handleFilterChange = useCallback((newFilters) => {
    setFilters({
      ...newFilters,
      lineCode: newFilters.includeDualLines ? newFilters.lineCode : '',
    });
  }, []);

  const handleReset = useCallback(() => {
    setFilters(INITIAL_FILTERS);
  }, []);

  const handleRefresh = useCallback(() => {
    if (!isVolatile) {
      loadData(filters);
    }
  }, [loadData, filters, isVolatile]);

  const seriesForWeeklyTrend = Array.isArray(activeWeeklyTrend)
    ? (activeWeeklyTrend.length > 0 && activeWeeklyTrend[0].data
        ? activeWeeklyTrend  // Already in [{name, data}] format
        : [{ name: 'Defects', data: [] }])
    : [];

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Seconds General Analytics</h1>
        <button className="refresh-btn" onClick={handleRefresh} disabled={activeLoading}>
          {activeLoading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {!isVolatile && (
        <FilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
          onReset={handleReset}
          filterOptions={filterOptions}
          context="customer"
        />
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '16px',
          marginBottom: '16px',
        }}
      >
        <KpiCard title="Total Produced" loading={activeLoading} error={activeError}>
          {activeProductionTotals ? (
            <KpiNumberCard
              title=""
              value={activeProductionTotals.total_produced}
              decimals={0}
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        <KpiCard title="Total Fixed" loading={activeLoading} error={activeError}>
          {activeProductionTotals ? (
            <KpiNumberCard
              title=""
              value={activeProductionTotals.total_fixed}
              decimals={0}
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        <KpiCard title="Total Definitive" loading={activeLoading} error={activeError}>
          {activeProductionTotals ? (
            <KpiNumberCard
              title=""
              value={activeProductionTotals.total_definitive}
              decimals={0}
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>
      </div>

      <Masonry
        breakpointCols={{ default: 3, 768: 1 }}
        className="dashboard-masonry"
        columnClassName="dashboard-masonry-column"
      >
        {/* Defects by Customer */}
        <KpiCard title="Defects by Customer" loading={activeLoading} error={activeError}>
          {activeDefectsByCustomer && activeDefectsByCustomer.length > 0 ? (
            <BarChartKpi
              data={activeDefectsByCustomer}
              color="#3b82f6"
              xAxisLabel="Customer"
              yAxisLabel="Total Defects"
              tooltipFormatter={(value) => [value.toString(), 'Defectos']}
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Defects by Style */}
        <KpiCard title="Defects by Style" loading={activeLoading} error={activeError}>
          {activeDefectsByStyle && activeDefectsByStyle.length > 0 ? (
            <BarChartKpi
              data={activeDefectsByStyle}
              color="#8b5cf6"
              horizontal
              xAxisLabel="Total Defects"
              yAxisLabel="Style"
              tooltipFormatter={(value) => [value.toString(), 'Defectos']}
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Weekly Trend */}
        <KpiCard title="Weekly Trend" loading={activeLoading} error={activeError}>
          {seriesForWeeklyTrend.length > 0 && seriesForWeeklyTrend[0].data?.length > 0 ? (
            <LineChartKpi
              series={seriesForWeeklyTrend}
              xAxisLabel="Week"
              yAxisLabel="Defects"
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Sewing vs Fabric Mix */}
        <KpiCard title="Sewing vs Fabric" loading={activeLoading} error={activeError}>
          {activeSewingVsFabric && activeSewingVsFabric.length > 0 ? (
            <DonutChartKpi
              data={[...activeSewingVsFabric].sort((a, b) => {
                if (a.name === 'Sewing') return -1;
                if (b.name === 'Sewing') return 1;
                return 0;
              })}
              showSliceLabels
              minLabelPercent={0}
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Top Sewing Defects */}
        <KpiCard title="Top Sewing Defects" loading={activeLoading} error={activeError}>
          {activeTopSewingDefects && activeTopSewingDefects.length > 0 ? (
            <BarChartKpi
              data={activeTopSewingDefects}
              horizontal
              color="#ef4444"
              xAxisLabel="Total Defects"
              yAxisLabel="Defect Type"
              tooltipFormatter={(value) => [value.toString(), 'Defects']}
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Top Fabric Defects */}
        <KpiCard title="Top Fabric Defects" loading={activeLoading} error={activeError}>
          {activeTopFabricDefects && activeTopFabricDefects.length > 0 ? (
            <BarChartKpi
              data={activeTopFabricDefects}
              horizontal
              color="#f59e0b"
              xAxisLabel="Total Defects"
              yAxisLabel="Defect Type"
              tooltipFormatter={(value) => [value.toString(), 'Defects']}
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Fix vs Definitive */}
        <KpiCard title="Fix vs Definitive" loading={activeLoading} error={activeError}>
          {activeFixVsDefinitive && activeFixVsDefinitive.length > 0 ? (
            <LineChartKpi
              series={activeFixVsDefinitive}
              xAxisLabel="Week"
              yAxisLabel="Quantity"
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Defects by Color */}
        <KpiCard title="Defects by Color" loading={activeLoading} error={activeError}>
          {activeDefectsByColor && activeDefectsByColor.length > 0 ? (
            <BarChartKpi
              data={activeDefectsByColor}
              color="#06b6d4"
              xAxisLabel="Color"
              yAxisLabel="Total Defects"
              tooltipFormatter={(value) => [value.toString(), 'Defectos']}
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Defects by Size */}
        <KpiCard title="Defects by Size" loading={activeLoading} error={activeError}>
          {activeDefectsBySize && activeDefectsBySize.length > 0 ? (
            <BarChartKpi
              data={activeDefectsBySize}
              color="#84cc16"
              xAxisLabel="Size"
              yAxisLabel="Total Defects"
              tooltipFormatter={(value) => [value.toString(), 'Defectos']}
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Defects by Line */}
        <KpiCard title="Defects by Line" loading={activeLoading} error={activeError}>
          {activeDefectsByLine && activeDefectsByLine.length > 0 ? (
            <BarChartKpi
              data={activeDefectsByLine}
              horizontal
              color="#f97316"
              xAxisLabel="Total Defects"
              yAxisLabel="Lines"
              tooltipFormatter={(value) => [value.toString(), 'Defectos']}
            />
          ) : (
            <div className="null-message">
              {activeLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>
      </Masonry>
    </div>
  );
}
