import { useState, useEffect, useCallback } from 'react';
import { fetchAllKpis, getFilterOptions } from '../../api/kpi';
import useVolatileDashboardCache from '../useVolatileDashboardCache';
import {
  transformPassReject,
  transformAqlByStyle,
  transformAqlByTeam,
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
  unavailableState,
  formatPercent,
  formatPieces,
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
import { normalizeScalarMetric } from '../dashboardMetricUtils';
import '../DashboardView.css';
import { withRoleProtection } from '../../hooks/withRoleProtection';

/**
 * Section descriptor for the exclusive QFA/QFC layout.
 * @typedef {{ title: string, chart: string, data: any, chartProps?: object }} CardDescriptor
 */

/**
 * Original Excel Reports — 8 cards, ordered per spec.
 * @param {object} opts
 * @returns {CardDescriptor[]}
 */
function buildExcelSection(opts) {
  const {
    context, defectRate, passRejectData, aqlWeeklySeries, aqlByStyleData,
    aqlByTeamData, topDefectsData, rejectedEvolutionSeries,
    acReRateByLineData, acceptedByLineData, rejectedByLineData,
    loading, error, nullMessage, isNullOrError,
    shouldShowMessage, getChartMessage, getStateClass, resolveChartData,
  } = opts;

  return [
    {
      title: 'Defect Rate (AQL %)',
      chart: 'number',
      data: defectRate,
      layoutRole: 'metric',
      render: () => (
        <KpiCard title="Defect Rate (AQL %)" loading={loading} error={error}>
          <KpiNumberCard
            title="AQL"
            value={defectRate !== null && !isNullOrError(defectRate) ? defectRate : null}
            unit="%"
            label="defects / (pass + fail) × 100"
          />
        </KpiCard>
      ),
    },
    {
      title: 'Pass / Reject Distribution',
      chart: 'donut',
      data: passRejectData,
      layoutRole: 'standard',
      render: () => (
        <KpiCard title="Pass / Reject Distribution" loading={loading} error={error}>
          {isNullOrError(passRejectData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <DonutChartKpi
              data={passRejectData}
              valueFormatter={formatPieces}
              tooltipLabelFormatter={(label) => `Status: ${label}`}
              minLabelPercent={0}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Weekly AQL (%)',
      chart: 'line',
      data: aqlWeeklySeries,
      layoutRole: 'standard',
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
      layoutRole: 'standard',
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
              tooltipFormatter={(value) => [formatPercent(value), 'AQL']}
              tooltipLabelFormatter={(label) => `Style: ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'AQL by Team/Line',
      chart: 'bar',
      data: aqlByTeamData,
      layoutRole: 'standard',
      render: () => (
        <KpiCard title="AQL by Team/Line" loading={loading} error={error}>
          {isNullOrError(aqlByTeamData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={aqlByTeamData}
              horizontal
              color="#3b82f6"
              xAxisLabel="AQL (%)"
              yAxisLabel="Team / Line"
              xTickFormatter={(value) => `${value}%`}
              valueFormatter={formatPercent}
              tooltipFormatter={(value) => [formatPercent(value), 'AQL']}
              tooltipLabelFormatter={(label) => `Team / Line: ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Top Defects',
      chart: 'bar',
      data: topDefectsData,
      layoutRole: 'standard',
      render: () => (
        <KpiCard title="Top Defects" loading={loading} error={error}>
          {shouldShowMessage(topDefectsData) ? (
            <div className={`state-message ${getStateClass(topDefectsData)}`}>
              {getChartMessage(topDefectsData)}
            </div>
          ) : (
            <BarChartKpi
              data={resolveChartData(topDefectsData)}
              horizontal
              color="#ef4444"
              xAxisLabel="Cantidad de defectos"
              yAxisLabel="Tipo de defecto"
              xTickFormatter={formatPieces}
              tooltipFormatter={(value) => [Math.round(Number(value)).toString(), 'defectos']}
              tooltipLabelFormatter={(label) => `Defecto: ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Weekly Rejected Pieces',
      chart: 'line',
      data: rejectedEvolutionSeries,
      layoutRole: 'standard',
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
      title: 'Accepted / Rejected Absolute Volume',
      chart: 'bar',
      data: { accepted: acceptedByLineData, rejected: rejectedByLineData },
      layoutRole: 'composed',
      render: () => (
        <KpiCard title="Accepted / Rejected Absolute Volume" loading={loading} error={error}>
          {isNullOrError(acReRateByLineData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <div className="volume-card-body">
              <div className="volume-subcard">
                <strong>Accepted</strong>
                <BarChartKpi
                  data={acceptedByLineData}
                  color="#10b981"
                  horizontal
                  xAxisLabel="Piezas aceptadas"
                  yAxisLabel="Line"
                  xTickFormatter={formatPieces}
                  yTickFormatter={trimCategoryLabel}
                  valueFormatter={formatPieces}
                  tooltipFormatter={(value) => [formatPieces(value), 'Piezas aceptadas']}
                  tooltipLabelFormatter={(label) => `Line (accepted): ${label}`}
                />
              </div>
              <div className="volume-subcard">
                <strong>Rejected</strong>
                <BarChartKpi
                  data={rejectedByLineData}
                  color="#ef4444"
                  horizontal
                  xAxisLabel="Piezas rechazadas"
                  xTickFormatter={formatPieces}
                  yTickFormatter={trimCategoryLabel}
                  valueFormatter={formatPieces}
                  tooltipFormatter={(value) => [formatPieces(value), 'Piezas rechazadas']}
                  tooltipLabelFormatter={(label) => `Line (rejected): ${label}`}
                />
              </div>
            </div>
          )}
        </KpiCard>
      ),
    },
  ];
}

/**
 * Rift Analytics Insights — 6 cards, ordered per spec.
 * @param {object} opts
 * @returns {CardDescriptor[]}
 */
function buildRiftSection(opts) {
  const {
    auditedPiecesSeries, perfByCustomerData, perfByLineData,
    defectsByStyleTypeData, defectTrendTop3Data, defectCompositionData,
    loading, error, nullMessage, isNullOrError,
    shouldShowMessage, getChartMessage, getStateClass, resolveChartData,
    formatSparseLineTick,
  } = opts;

  return [
    {
      title: 'Weekly Audited Pieces',
      chart: 'line',
      data: auditedPiecesSeries,
      layoutRole: 'standard',
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
      title: 'Acceptance Rate by Customer (accepted / (accepted + rejected) × 100)',
      chart: 'bar',
      data: perfByCustomerData,
      layoutRole: 'standard',
      render: () => (
        <KpiCard title="Acceptance Rate by Customer (accepted / (accepted + rejected) × 100)" loading={loading} error={error}>
          {isNullOrError(perfByCustomerData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={perfByCustomerData}
              color="#8b5cf6"
              xAxisLabel="Customer"
              yAxisLabel="Acceptance Rate (accepted / (accepted + rejected) × 100)"
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
      title: 'Defects by Style × Type',
      chart: 'heatmap',
      data: defectsByStyleTypeData,
      layoutRole: 'standard',
      render: () => (
        <KpiCard title="Defects by Style × Type" loading={loading} error={error}>
          {shouldShowMessage(defectsByStyleTypeData) ? (
            <div className={`state-message ${getStateClass(defectsByStyleTypeData)}`}>
              {getChartMessage(defectsByStyleTypeData)}
            </div>
          ) : (
            <HeatmapKpi data={resolveChartData(defectsByStyleTypeData)} />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Defect Trend Top 3',
      chart: 'line',
      data: defectTrendTop3Data,
      layoutRole: 'full',
      render: () => (
        <KpiCard title="Defect Trend Top 3" loading={loading} error={error}>
          {shouldShowMessage(defectTrendTop3Data) ? (
            <div className={`state-message ${getStateClass(defectTrendTop3Data)}`}>
              {getChartMessage(defectTrendTop3Data)}
            </div>
          ) : (
            <LineChartKpi
              series={resolveChartData(defectTrendTop3Data)}
              xAxisLabel="Week"
              yAxisLabel="Defects"
              xTickFormatter={formatWeekLabel}
              valueFormatter={(value) => `${Math.round(Number(value))} defectos`}
              tooltipFormatter={(value, name) => [`${Math.round(Number(value))} defectos`, name]}
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
      layoutRole: 'wide',
      render: () => (
        <KpiCard title="Defect Composition" loading={loading} error={error}>
          {shouldShowMessage(defectCompositionData) ? (
            <div className={`state-message ${getStateClass(defectCompositionData)}`}>
              {getChartMessage(defectCompositionData)}
            </div>
          ) : (
            <DonutChartKpi
              data={resolveChartData(defectCompositionData)}
              valueFormatter={(value) => `${Math.round(Number(value))} defectos`}
              tooltipLabelFormatter={(label) => `Defect: ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
    {
      title: 'Acceptance Rate by Line (accepted / (accepted + rejected) × 100)',
      chart: 'bar',
      data: perfByLineData,
      layoutRole: 'standard',
      render: () => (
        <KpiCard title="Acceptance Rate by Line (accepted / (accepted + rejected) × 100)" loading={loading} error={error}>
          {isNullOrError(perfByLineData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={perfByLineData}
              horizontal
              color="#f59e0b"
              xAxisLabel="Acceptance Rate (accepted / (accepted + rejected) × 100)"
              yAxisLabel="Line"
              showAllCategoryTicks
              xTickFormatter={(value) => Number(value).toFixed(0)}
              yTickFormatter={formatSparseLineTick}
              valueFormatter={formatAcceptanceIndex}
              tooltipLabelFormatter={(label) => `Line: ${label}`}
            />
          )}
        </KpiCard>
      ),
    },
  ];
}

/**
 * Render a semantic grid section shell.
 * @param {string} sectionTitle
 * @param {CardDescriptor[]} cards
 */
function renderSection(sectionTitle, cards) {
  return (
    <div className="dashboard-section dashboard-section--qfa-qfc">
      <h2 className="dashboard-section__title">{sectionTitle}</h2>
      <div className="dashboard-section__grid">
        {cards.map((card) => (
          <div
            className="dashboard-section__item"
            data-layout-role={card.layoutRole || 'standard'}
            key={card.title}
          >
            {card.render()}
          </div>
        ))}
      </div>
    </div>
  );
}

function QcfaKpiDashboard({ volatileFile, context }) {
  const isLiveMode = !volatileFile;

  const [filters, setFilters] = useState({
    date_range: ['', ''],
    week: '',
    team: '',
    style: '',
    color: '',
    customer: '',
    batch: '',
    includeDualLines: false,
    lineCode: '',
  });

  const [kpiData, setKpiData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterOptions, setFilterOptions] = useState(null);

  const mapFiltersForApi = useCallback((activeFilters) => {
    const { includeDualLines, lineCode, ...rest } = activeFilters;
    return {
      ...rest,
      include_dual_lines: includeDualLines,
      line_code: lineCode,
    };
  }, []);

  const loadData = useCallback(async (activeFilters = filters) => {
    setLoading(true);
    setError(null);

    try {
      const result = await fetchAllKpis(mapFiltersForApi(activeFilters), context);
      setKpiData(result);
    } catch (err) {
      setError(err.message || 'Error loading data');
    } finally {
      setLoading(false);
    }
  }, [filters, context, mapFiltersForApi]);

  useEffect(() => {
    if (!volatileFile) {
      loadData();
    }
  }, [volatileFile, loadData]);

  // Fetch filter options for live mode
  useEffect(() => {
    if (volatileFile) return;

    const fetchOptions = async () => {
      try {
        const includeDualLines = context === 'customer' ? filters.includeDualLines : undefined;
        const options = await getFilterOptions(context, includeDualLines);
        setFilterOptions(options);
      } catch (err) {
        console.warn('Failed to fetch filter options:', err.message);
      }
    };

    fetchOptions();
  }, [volatileFile, context, filters.includeDualLines]);

  // Volatile dashboard cache hook — prevents re-upload on tab switch.
  // Uses module-level cache keyed by file identity + dashboard + context.
  const {
    data: volatileData,
    loading: volatileLoading,
    error: volatileError,
  } = useVolatileDashboardCache(volatileFile || null, 'qcfa', context);

  // Sync volatile cache result into shared component state
  useEffect(() => {
    if (!volatileFile) return;

    setLoading(volatileLoading);
    if (volatileError) {
      setError(volatileError);
    }
    if (volatileData) {
      setKpiData(volatileData);
      if (volatileData.filterOptions) {
        setFilterOptions(volatileData.filterOptions);
      }
    }
  }, [volatileFile, volatileData, volatileLoading, volatileError]);

  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  const handleReset = useCallback(() => {
    const resetFilters = {
      date_range: ['', ''],
      week: '',
      team: '',
      style: '',
      color: '',
      customer: '',
      batch: '',
      includeDualLines: false,
      lineCode: '',
    };
    setFilters(resetFilters);
    if (!volatileFile) {
      loadData(resetFilters);
    }
  }, [volatileFile, loadData]);

  const handleRefresh = useCallback(() => {
    loadData(filters);
  }, [loadData, filters]);

  // Transform data for charts
  const defectRate = normalizeScalarMetric(kpiData?.defectRate);
  const passRejectData = transformPassReject(kpiData?.passRejectDistribution);
  const aqlWeeklySeries = transformAqlWeekly(kpiData?.aqlWeekly);
  const aqlByStyleData = transformAqlByStyle(kpiData?.aqlByStyle);
  const aqlByTeamData = transformAqlByTeam(kpiData?.aqlByTeam);
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

  const isNullOrError = (data) => data == null || (data && (data.error || data.status === 'unavailable'));

  /**
   * Resolve chart-ready data from either chart-state object (new contract) or legacy raw data.
   * - chart-state { status: 'ready', data: [...] } → returns data array
   * - legacy raw array → returns as-is
   * - null/unavailable/empty → returns null
   */
  const resolveChartData = (data) => {
    if (data && data.status === 'ready') return data.data;
    if (data && (data.status === 'empty' || data.status === 'unavailable')) return null;
    return data; // legacy (raw array, null, etc.)
  };

  /**
   * Get the display message for a chart state, falling back to legacy nullMessage.
   */
  const getChartMessage = (data) => {
    if (data && data.message) return data.message;
    if (data && data.error) return data.error;
    return nullMessage;
  };

  /**
   * Determine if a chart should show a state message instead of rendering.
   */
  const shouldShowMessage = (data) => {
    if (!data) return true; // null/undefined → show message
    if (data.error) return true;
    if (data.status === 'empty' || data.status === 'unavailable') return true;
    return false;
  };

  /**
   * Get CSS class modifier for the state message.
   */
  const getStateClass = (data) => {
    if (!data) return 'state-null';
    if (data.status === 'empty') return 'state-empty';
    if (data.status === 'unavailable') return 'state-unavailable';
    if (data.error) return 'state-error';
    return 'state-null';
  };

  const nullMessage = "No disponible en modo rápido";

  const formatSparseLineTick = (value, index) => {
    if (!Array.isArray(perfByLineData) || perfByLineData.length === 0) return value;
    const lastIndex = perfByLineData.length - 1;
    if (index === 0 || index === lastIndex || index % 3 === 0) return value;
    return '';
  };

  const excelSectionOpts = {
    context, defectRate, passRejectData, aqlWeeklySeries, aqlByStyleData,
    aqlByTeamData, topDefectsData, rejectedEvolutionSeries,
    acReRateByLineData, acceptedByLineData, rejectedByLineData,
    loading, error, nullMessage, isNullOrError,
    shouldShowMessage, getChartMessage, getStateClass, resolveChartData,
  };

  const riftSectionOpts = {
    auditedPiecesSeries, perfByCustomerData, perfByLineData,
    defectsByStyleTypeData, defectTrendTop3Data, defectCompositionData,
    loading, error, nullMessage, isNullOrError,
    shouldShowMessage, getChartMessage, getStateClass, resolveChartData,
    formatSparseLineTick,
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
          onReset={handleReset}
          filterOptions={filterOptions}
          context={context}
        />
      )}

      {!isLiveMode && (
        <div className="volatile-helper" role="status" aria-live="polite">
          <strong>Fast mode:</strong> does not apply live filters and some KPIs may not be
          available as they depend on database tables.
        </div>
      )}

      {renderSection('Original Excel Reports', excelCards)}

      {renderSection('Rift Analytics Insights', riftCards)}
    </div>
  );
}

export default withRoleProtection(QcfaKpiDashboard, ['manager']);
