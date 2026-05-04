import { useState, useEffect, useCallback } from 'react';
import { fetchAllKpis, fetchVolatileKpis, getFilterOptions } from '../../api/kpi';
import * as calc from '../../utils/kpiCalculations';
import {
  transformPassReject,
  transformAqlByStyle,
  transformAqlWeekly,
  transformAuditedPieces,
  transformRejectedEvolution,
  transformAcReRateByLine,
  transformPerformanceByCustomer,
  transformPerformanceByLine,
  transformTopDefects,
  transformDefectsByStyleType,
  transformDefectComposition,
  transformDefectTrendTop3,
  formatPercent,
  formatPieces,
  formatCount,
  formatWeekLabel,
  formatAcceptanceIndex,
  trimCategoryLabel,
  buildLineCountDataByState,
} from '../../utils/chartTransforms';
import KpiCard from '../../Components/kpi/KpiCard';
import BarChartKpi from '../../Components/kpi/BarChartKpi';
import LineChartKpi from '../../Components/kpi/LineChartKpi';
import DonutChartKpi from '../../Components/kpi/DonutChartKpi';
import HeatmapKpi from '../../Components/kpi/HeatmapKpi';
import KpiNumberCard from '../../Components/kpi/KpiNumberCard';
import FilterBar from '../../Components/kpi/FilterBar';
import ReportGenerator from '../../Components/ReportGenerator';
import { normalizeScalarMetric } from '../dashboardMetricUtils';
import Masonry from 'react-masonry-css';
import '../DashboardView.css';
import { withRoleProtection } from '../../hooks/withRoleProtection';

/**
 * Calculate all KPIs from volatile (Excel) data.
 * Returns null for KPIs not available in volatile mode.
 * @param {object[]} rows - Parsed Excel rows
 * @returns {object} KPI results object
 */
function calculateAllKpis(rows) {
  if (!rows || rows.length === 0) {
    return {
      aqlByStyle: null,
      aqlWeekly: null,
      auditedPieces: null,
      acReRateByLine: null,
      performanceByCustomer: null,
      performanceByLine: null,
      topDefects: null,
      defectsByStyleType: null,
      passRejectDistribution: null,
      rejectedEvolution: null,
      defectRate: null,
      defectComposition: null,
      defectTrendTop3: null,
    };
  }

  return {
    aqlByStyle: calc.calculateAqlByStyle(rows),
    aqlWeekly: calc.calculateAqlWeekly(rows),
    auditedPieces: calc.calculateAuditedPieces(rows),
    acReRateByLine: calc.calculateAcReRateByLine(rows),
    performanceByCustomer: calc.calculatePerformanceByCustomer(rows),
    performanceByLine: calc.calculatePerformanceByLine(rows),
    topDefects: calc.calculateTopDefects(rows),
    defectsByStyleType: calc.calculateDefectsByStyleType(rows),
    passRejectDistribution: calc.calculatePassRejectDistribution(rows),
    rejectedEvolution: calc.calculateRejectedEvolution(rows),
    defectRate: calc.calculateDefectRate(rows),
    defectComposition: null,
    defectTrendTop3: null,
  };
}

/**
 * Section descriptor for the exclusive QFA/QFC layout.
 * @typedef {{ title: string, chart: string, data: any, chartProps?: object }} CardDescriptor
 */

/**
 * Original Excel Reports — 12 cards, ordered per spec.
 * @param {object} opts
 * @returns {CardDescriptor[]}
 */
function buildExcelSection(opts) {
  const {
    defectRate, passRejectData, aqlWeeklySeries, aqlByStyleData,
    topDefectsData, auditedPiecesSeries, rejectedEvolutionSeries,
    acReRateByLineData, acceptedByLineData, rejectedByLineData,
    perfByCustomerData, perfByLineData, defectsByStyleTypeData,
    loading, error, nullMessage, isNullOrError,
  } = opts;

  return [
    {
      title: 'Defect Rate (AQL %)',
      chart: 'number',
      data: defectRate,
      render: () => (
        <KpiCard title="Defect Rate (AQL %)" loading={loading} error={error}>
          <KpiNumberCard
            title="AQL"
            value={defectRate !== null && !isNullOrError(defectRate) ? defectRate : null}
            unit="%"
            label="defects / sample × 100"
          />
        </KpiCard>
      ),
    },
    {
      title: 'Pass / Reject Distribution',
      chart: 'donut',
      data: passRejectData,
      render: () => (
        <KpiCard title="Pass / Reject Distribution" loading={loading} error={error}>
          {isNullOrError(passRejectData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <DonutChartKpi
              data={passRejectData}
              valueFormatter={formatPieces}
              tooltipLabelFormatter={(label) => `Status: ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Weekly AQL (%)',
      chart: 'line',
      data: aqlWeeklySeries,
      render: () => (
        <KpiCard title="Weekly AQL (%)" loading={loading} error={error}>
          {isNullOrError(aqlWeeklySeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi
              series={aqlWeeklySeries}
              xAxisLabel="Week"
              yAxisLabel="AQL (%)"
              xTickFormatter={formatWeekLabel}
              yTickFormatter={(value) => `${value}%`}
              valueFormatter={formatPercent}
              tooltipLabelFormatter={formatWeekLabel}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'AQL by Style',
      chart: 'bar',
      data: aqlByStyleData,
      render: () => (
        <KpiCard title="AQL by Style" loading={loading} error={error}>
          {isNullOrError(aqlByStyleData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={aqlByStyleData}
              horizontal
              color="#3b82f6"
              xAxisLabel="AQL (%)"
              yAxisLabel="Style"
              xTickFormatter={(value) => `${value}%`}
              valueFormatter={formatPercent}
              tooltipLabelFormatter={(label) => `Style: ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Top Defects',
      chart: 'bar',
      data: topDefectsData,
      render: () => (
        <KpiCard title="Top Defects" loading={loading} error={error}>
          {isNullOrError(topDefectsData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi data={topDefectsData} horizontal color="#ef4444" />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Weekly Audited Pieces',
      chart: 'line',
      data: auditedPiecesSeries,
      render: () => (
        <KpiCard title="Weekly Audited Pieces" loading={loading} error={error}>
          {isNullOrError(auditedPiecesSeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi
              series={auditedPiecesSeries}
              xAxisLabel="Week"
              yAxisLabel="Pieces"
              xTickFormatter={formatWeekLabel}
              valueFormatter={formatPieces}
              tooltipLabelFormatter={formatWeekLabel}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Weekly Rejected Pieces',
      chart: 'line',
      data: rejectedEvolutionSeries,
      render: () => (
        <KpiCard title="Weekly Rejected Pieces" loading={loading} error={error}>
          {isNullOrError(rejectedEvolutionSeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi
              series={rejectedEvolutionSeries}
              xAxisLabel="Week"
              yAxisLabel="Rejected Pieces"
              xTickFormatter={formatWeekLabel}
              valueFormatter={formatPieces}
              tooltipLabelFormatter={formatWeekLabel}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Accepted by Line (count)',
      chart: 'bar',
      data: acceptedByLineData,
      render: () => (
        <KpiCard title="Accepted by Line (count)" loading={loading} error={error}>
          {isNullOrError(acReRateByLineData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={acceptedByLineData}
              color="#10b981"
              horizontal
              xAxisLabel="Count (pieces)"
              yAxisLabel="Line"
              xTickFormatter={formatPieces}
              yTickFormatter={trimCategoryLabel}
              valueFormatter={formatCount}
              tooltipLabelFormatter={(label) => `Line (accepted): ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Rejected by Line (count)',
      chart: 'bar',
      data: rejectedByLineData,
      render: () => (
        <KpiCard title="Rejected by Line (count)" loading={loading} error={error}>
          {isNullOrError(acReRateByLineData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={rejectedByLineData}
              color="#ef4444"
              horizontal
              xAxisLabel="Count (pieces)"
              yAxisLabel="Line"
              xTickFormatter={formatPieces}
              yTickFormatter={trimCategoryLabel}
              valueFormatter={formatCount}
              tooltipLabelFormatter={(label) => `Line (rejected): ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Acceptance Rate by Customer (accepted/sample × 100)',
      chart: 'bar',
      data: perfByCustomerData,
      render: () => (
        <KpiCard title="Acceptance Rate by Customer (accepted/sample × 100)" loading={loading} error={error}>
          {isNullOrError(perfByCustomerData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={perfByCustomerData}
              color="#8b5cf6"
              xAxisLabel="Customer"
              yAxisLabel="Acceptance Rate (accepted/sample × 100)"
              xTickFormatter={trimCategoryLabel}
              yTickFormatter={(value) => Number(value).toFixed(0)}
              valueFormatter={formatAcceptanceIndex}
              tooltipLabelFormatter={(label) => `Customer: ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Acceptance Rate by Line (accepted/sample × 100)',
      chart: 'bar',
      data: perfByLineData,
      render: () => (
        <KpiCard title="Acceptance Rate by Line (accepted/sample × 100)" loading={loading} error={error}>
          {isNullOrError(perfByLineData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={perfByLineData}
              horizontal
              color="#f59e0b"
              xAxisLabel="Acceptance Rate (accepted/sample × 100)"
              yAxisLabel="Line"
              xTickFormatter={(value) => Number(value).toFixed(0)}
              valueFormatter={formatAcceptanceIndex}
              tooltipLabelFormatter={(label) => `Line: ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Defects by Style × Type',
      chart: 'heatmap',
      data: defectsByStyleTypeData,
      render: () => (
        <KpiCard title="Defects by Style × Type" loading={loading} error={error}>
          {isNullOrError(defectsByStyleTypeData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <HeatmapKpi data={defectsByStyleTypeData} />
          )}
        </KpiCard>
      ),
    },
  ];
}

/**
 * Rift Analytics Insights — 2 cards, ordered per spec.
 * @param {object} opts
 * @returns {CardDescriptor[]}
 */
function buildRiftSection(opts) {
  const {
    defectTrendTop3Data, defectCompositionData, loading, error,
    nullMessage, isNullOrError,
  } = opts;

  return [
    {
      title: 'Defect Trend Top 3',
      chart: 'line',
      data: defectTrendTop3Data,
      render: () => (
        <KpiCard title="Defect Trend Top 3" loading={loading} error={error}>
          {isNullOrError(defectTrendTop3Data) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi
              series={defectTrendTop3Data}
              xAxisLabel="Week"
              yAxisLabel="Defects"
              xTickFormatter={formatWeekLabel}
              valueFormatter={formatCount}
              tooltipLabelFormatter={formatWeekLabel}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Defect Composition',
      chart: 'donut',
      data: defectCompositionData,
      render: () => (
        <KpiCard title="Defect Composition" loading={loading} error={error}>
          {isNullOrError(defectCompositionData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <DonutChartKpi
              data={defectCompositionData}
              valueFormatter={formatCount}
              tooltipLabelFormatter={(label) => `Defect: ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
  ];
}

function QcfaKpiDashboard({ volatileData, volatileFile, context }) {
  const isLiveMode = !volatileData && !volatileFile;
  const isVolatileFileMode = !!volatileFile;

  const [filters, setFilters] = useState({
    date_range: ['', ''],
    week: '',
    team: '',
    style: '',
    color: '',
    customer: '',
    batch: '',
  });

  const [kpiData, setKpiData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterOptions, setFilterOptions] = useState(null);

  const loadData = useCallback(async (activeFilters = filters) => {
    setLoading(true);
    setError(null);

    try {
      if (isLiveMode) {
        const result = await fetchAllKpis(activeFilters, context);
        setKpiData(result);
      } else {
        const result = calculateAllKpis(volatileData);
        setKpiData(result);
      }
    } catch (err) {
      setError(err.message || 'Error loading data');
    } finally {
      setLoading(false);
    }
  }, [isLiveMode, volatileData, filters, context]);

  useEffect(() => {
    if (!isVolatileFileMode) {
      loadData();
    }
  }, [isVolatileFileMode, loadData]);

  // Fetch filter options for live mode
  useEffect(() => {
    if (!isLiveMode) return;

    const fetchOptions = async () => {
      try {
        const options = await getFilterOptions();
        setFilterOptions(options);
      } catch (err) {
        console.warn('Failed to fetch filter options:', err.message);
      }
    };

    fetchOptions();
  }, [isLiveMode]);

  // Fetch KPIs from volatile file (server-side calculation)
  useEffect(() => {
    if (!volatileFile) return;

    const fetchVolatile = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchVolatileKpis(volatileFile);
        setKpiData(result);
        if (result.filterOptions) {
          setFilterOptions(result.filterOptions);
        }
      } catch (err) {
        setError(err.message || 'Error processing Excel file');
      } finally {
        setLoading(false);
      }
    };

    fetchVolatile();
  }, [volatileFile]);

  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  const handleApply = useCallback(() => {
    loadData(filters);
  }, [loadData, filters]);

  const handleReset = useCallback(() => {
    const resetFilters = {
      date_range: ['', ''],
      week: '',
      team: '',
      style: '',
      color: '',
      customer: '',
      batch: '',
    };
    setFilters(resetFilters);
    if (isLiveMode) {
      loadData(resetFilters);
    }
  }, [isLiveMode, loadData]);

  const handleRefresh = useCallback(() => {
    loadData(filters);
  }, [loadData, filters]);

  // Transform data for charts
  const defectRate = normalizeScalarMetric(kpiData?.defectRate);
  const passRejectData = transformPassReject(kpiData?.passRejectDistribution);
  const aqlWeeklySeries = transformAqlWeekly(kpiData?.aqlWeekly);
  const aqlByStyleData = transformAqlByStyle(kpiData?.aqlByStyle);
  const topDefectsData = transformTopDefects(kpiData?.topDefects);
  const auditedPiecesSeries = transformAuditedPieces(kpiData?.auditedPieces);
  const rejectedEvolutionSeries = transformRejectedEvolution(kpiData?.rejectedEvolution);
  const acReRateByLineData = transformAcReRateByLine(kpiData?.acReRateByLine);
  const acceptedByLineData = buildLineCountDataByState(acReRateByLineData, 'PASS');
  const rejectedByLineData = buildLineCountDataByState(acReRateByLineData, 'REJECT');
  const perfByCustomerData = transformPerformanceByCustomer(kpiData?.performanceByCustomer);
  const perfByLineData = transformPerformanceByLine(kpiData?.performanceByLine);
  const defectsByStyleTypeData = transformDefectsByStyleType(kpiData?.defectsByStyleType);
  const defectCompositionData = transformDefectComposition(kpiData?.defectComposition);
  const defectTrendTop3Data = transformDefectTrendTop3(kpiData?.defectTrendTop3);

  const isNullOrError = (data) => data === null || (data && (data.error || data.status === 'unavailable'));

  const nullMessage = "No disponible en modo rápido";

  const excelSectionOpts = {
    defectRate, passRejectData, aqlWeeklySeries, aqlByStyleData,
    topDefectsData, auditedPiecesSeries, rejectedEvolutionSeries,
    acReRateByLineData, acceptedByLineData, rejectedByLineData,
    perfByCustomerData, perfByLineData, defectsByStyleTypeData,
    loading, error, nullMessage, isNullOrError,
  };

  const riftSectionOpts = {
    defectTrendTop3Data, defectCompositionData,
    loading, error, nullMessage, isNullOrError,
  };

  const excelCards = buildExcelSection(excelSectionOpts);
  const riftCards = buildRiftSection(riftSectionOpts);

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h1 className="dashboard-title">KPIs Dashboard</h1>
        <button className="refresh-btn" onClick={handleRefresh} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {isLiveMode && (
        <FilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
          onApply={handleApply}
          onReset={handleReset}
          filterOptions={filterOptions}
        />
      )}

      <ReportGenerator />

      {!isLiveMode && (
        <div className="volatile-helper" role="status" aria-live="polite">
          <strong>Fast mode:</strong> does not apply live filters and some KPIs may not be
          available as they depend on database tables.
        </div>
      )}

      {/* ── Section 1: Original Excel Reports ── */}
      <h2 className="dashboard-section__title">Original Excel Reports</h2>
      <Masonry
        breakpointCols={{ default: 3, 1100: 2, 768: 1 }}
        className="dashboard-masonry"
        columnClassName="dashboard-masonry-column"
      >
        {excelCards.map((card) => (
          <div key={card.title}>{card.render()}</div>
        ))}
      </Masonry>

      {/* ── Section 2: Rift Analytics Insights ── */}
      <h2 className="dashboard-section__title">Rift Analytics Insights</h2>
      <Masonry
        breakpointCols={{ default: 3, 1100: 2, 768: 1 }}
        className="dashboard-masonry"
        columnClassName="dashboard-masonry-column"
      >
        {riftCards.map((card) => (
          <div key={card.title}>{card.render()}</div>
        ))}
      </Masonry>
    </div>
  );
}

export default withRoleProtection(QcfaKpiDashboard, ['manager']);
