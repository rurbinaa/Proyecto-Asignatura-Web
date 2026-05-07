import { useState, useEffect, useCallback } from 'react';
import axiosClient from '../../api/axiosClient';
import KpiCard from '../../Components/kpi/KpiCard';
import BarChartKpi from '../../Components/kpi/BarChartKpi';
import LineChartKpi from '../../Components/kpi/LineChartKpi';
import DonutChartKpi from '../../Components/kpi/DonutChartKpi';
import KpiNumberCard from '../../Components/kpi/KpiNumberCard';
import FilterBar from '../../Components/kpi/FilterBar';
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
export default function SecondsGeneralDashboard() {
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

  // Fetch filter options on mount and whenever dual-line toggle changes.
  useEffect(() => {
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
  }, [filters.includeDualLines]);


  const loadData = useCallback(async (filtersOverride) => {
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
  }, []);

  // Mirror QC FA Customer behavior: filters apply immediately on change.
  useEffect(() => {
    loadData(filters);
  }, [filters, loadData]);


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
    loadData(filters);
  }, [loadData, filters]);

  const seriesForWeeklyTrend = weeklyTrend && weeklyTrend.length > 0
    ? weeklyTrend.map((s) => ({
        name: s.name || 'Defects',
        data: s.data || [],
      }))
    : [];

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Seconds General Analytics</h1>
        <button className="refresh-btn" onClick={handleRefresh} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      <FilterBar
        filters={filters}
        onFilterChange={handleFilterChange}
        onReset={handleReset}
        filterOptions={filterOptions}
        context="customer"
      />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '16px',
          marginBottom: '16px',
        }}
      >
        <KpiCard title="Total Produced" loading={loading} error={error}>
          {productionTotals ? (
            <KpiNumberCard
              title=""
              value={productionTotals.total_produced}
              decimals={0}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        <KpiCard title="Total Fixed" loading={loading} error={error}>
          {productionTotals ? (
            <KpiNumberCard
              title=""
              value={productionTotals.total_fixed}
              decimals={0}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        <KpiCard title="Total Definitive" loading={loading} error={error}>
          {productionTotals ? (
            <KpiNumberCard
              title=""
              value={productionTotals.total_definitive}
              decimals={0}
            />
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
        {/* Defects by Customer */}
        <KpiCard title="Defects by Customer" loading={loading} error={error}>
          {defectsByCustomer && defectsByCustomer.length > 0 ? (
            <BarChartKpi
              data={defectsByCustomer}
              color="#3b82f6"
              xAxisLabel="Customer"
              yAxisLabel="Total Defects"
              tooltipFormatter={(value) => [value.toString(), 'Defectos']}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Defects by Style */}
        <KpiCard title="Defects by Style" loading={loading} error={error}>
          {defectsByStyle && defectsByStyle.length > 0 ? (
            <BarChartKpi
              data={defectsByStyle}
              color="#8b5cf6"
              horizontal
              xAxisLabel="Total Defects"
              yAxisLabel="Style"
              tooltipFormatter={(value) => [value.toString(), 'Defectos']}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Weekly Trend */}
        <KpiCard title="Weekly Trend" loading={loading} error={error}>
          {seriesForWeeklyTrend.length > 0 ? (
            <LineChartKpi
              series={seriesForWeeklyTrend}
              xAxisLabel="Week"
              yAxisLabel="Defects"
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Sewing vs Fabric Mix */}
        <KpiCard title="Sewing vs Fabric" loading={loading} error={error}>
          {sewingVsFabric && sewingVsFabric.length > 0 ? (
            <DonutChartKpi
              data={[...sewingVsFabric].sort((a, b) => {
                if (a.name === 'Sewing') return -1;
                if (b.name === 'Sewing') return 1;
                return 0;
              })}
              showSliceLabels
              minLabelPercent={0}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Top Sewing Defects */}
        <KpiCard title="Top Sewing Defects" loading={loading} error={error}>
          {topSewingDefects && topSewingDefects.length > 0 ? (
            <BarChartKpi
              data={topSewingDefects}
              horizontal
              color="#ef4444"
              xAxisLabel="Total Defects"
              yAxisLabel="Defect Type"
              tooltipFormatter={(value) => [value.toString(), 'Defects']}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Top Fabric Defects */}
        <KpiCard title="Top Fabric Defects" loading={loading} error={error}>
          {topFabricDefects && topFabricDefects.length > 0 ? (
            <BarChartKpi
              data={topFabricDefects}
              horizontal
              color="#f59e0b"
              xAxisLabel="Total Defects"
              yAxisLabel="Defect Type"
              tooltipFormatter={(value) => [value.toString(), 'Defects']}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Fix vs Definitive */}
        <KpiCard title="Fix vs Definitive" loading={loading} error={error}>
          {fixVsDefinitive && fixVsDefinitive.length > 0 ? (
            <LineChartKpi
              series={fixVsDefinitive}
              xAxisLabel="Week"
              yAxisLabel="Quantity"
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Defects by Color */}
        <KpiCard title="Defects by Color" loading={loading} error={error}>
          {defectsByColor && defectsByColor.length > 0 ? (
            <BarChartKpi
              data={defectsByColor}
              color="#06b6d4"
              xAxisLabel="Color"
              yAxisLabel="Total Defects"
              tooltipFormatter={(value) => [value.toString(), 'Defectos']}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Defects by Size */}
        <KpiCard title="Defects by Size" loading={loading} error={error}>
          {defectsBySize && defectsBySize.length > 0 ? (
            <BarChartKpi
              data={defectsBySize}
              color="#84cc16"
              xAxisLabel="Size"
              yAxisLabel="Total Defects"
              tooltipFormatter={(value) => [value.toString(), 'Defectos']}
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Defects by Line */}
        <KpiCard title="Defects by Line" loading={loading} error={error}>
          {defectsByLine && defectsByLine.length > 0 ? (
            <BarChartKpi
              data={defectsByLine}
              horizontal
              color="#f97316"
              xAxisLabel="Total Defects"
              yAxisLabel="Lines"
              tooltipFormatter={(value) => [value.toString(), 'Defectos']}
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
