import { useState, useEffect, useCallback } from 'react';
import { fetchAllKpis, fetchVolatileKpis, getFilterOptions } from '../api/kpi';
import * as calc from '../utils/kpiCalculations';
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
  transformFabricDefects,
  transformContainersByState,
  transformDefectsByStyleType,
  transformSecondsRework,
  formatPercent,
  formatPieces,
  formatCount,
  formatSeconds,
  formatWeekLabel,
  formatAcceptanceIndex,
  trimCategoryLabel,
  buildLineCountDataByState,
} from '../utils/chartTransforms';
import KpiCard from '../Components/kpi/KpiCard';
import BarChartKpi from '../Components/kpi/BarChartKpi';
import LineChartKpi from '../Components/kpi/LineChartKpi';
import DonutChartKpi from '../Components/kpi/DonutChartKpi';
import HeatmapKpi from '../Components/kpi/HeatmapKpi';
import KpiNumberCard from '../Components/kpi/KpiNumberCard';
import FilterBar from '../Components/kpi/FilterBar';
import ReportGenerator from '../Components/ReportGenerator';
import { normalizeScalarMetric } from './dashboardMetricUtils';
import Masonry from 'react-masonry-css';
import './DashboardView.css';
import { withRoleProtection } from '../hooks/withRoleProtection';

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
      secondsRework: null,
      performanceByCustomer: null,
      performanceByLine: null,
      topDefects: null,
      fabricDefects: null,
      defectsByStyleType: null,
      passRejectDistribution: null,
      rejectedEvolution: null,
      containersByState: null,
      defectRate: null,
    };
  }

  return {
    aqlByStyle: calc.calculateAqlByStyle(rows),
    aqlWeekly: calc.calculateAqlWeekly(rows),
    auditedPieces: calc.calculateAuditedPieces(rows),
    acReRateByLine: calc.calculateAcReRateByLine(rows),
    secondsRework: calc.calculateSecondsRework(rows),
    performanceByCustomer: calc.calculatePerformanceByCustomer(rows),
    performanceByLine: calc.calculatePerformanceByLine(rows),
    topDefects: calc.calculateTopDefects(rows),
    fabricDefects: calc.calculateFabricDefects(rows),
    defectsByStyleType: calc.calculateDefectsByStyleType(rows),
    passRejectDistribution: calc.calculatePassRejectDistribution(rows),
    rejectedEvolution: calc.calculateRejectedEvolution(rows),
    containersByState: calc.calculateContainersByState(rows),
    defectRate: calc.calculateDefectRate(rows),
  };
}

function DashboardView({ volatileData, volatileFile }) {
  // Live mode = no volatile data, no volatile file
  // Volatile mode (file) = volatileFile provided (server-side calculation)
  // Volatile mode (data) = volatileData provided (client-side calculation)
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
        const result = await fetchAllKpis(activeFilters);
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
  }, [isLiveMode, volatileData, filters]);

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
  const secondsReworkSeries = transformSecondsRework(kpiData?.secondsRework);
  const fabricDefectsData = transformFabricDefects(kpiData?.fabricDefects);
  const containersByStateData = transformContainersByState(kpiData?.containersByState);
  const defectsByStyleTypeData = transformDefectsByStyleType(kpiData?.defectsByStyleType);

  const isNullOrError = (data) => data === null || (data && data.error);

  const nullMessage = "No disponible en modo rápido";
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

      <Masonry
        breakpointCols={{ default: 3, 1100: 2, 768: 1 }}
        className="dashboard-masonry"
        columnClassName="dashboard-masonry-column"
      >
        {/* Row 1: Defect Rate, Pass/Reject, AQL Weekly */}
        <KpiCard title="Defect Rate (AQL %)" loading={loading} error={error}>
          <KpiNumberCard
            title="AQL"
            value={defectRate !== null && !isNullOrError(defectRate) ? defectRate : null}
            unit="%"
            label="defects / sample × 100"
          />
        </KpiCard>

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

        {/* Row 2: AQL by Style, Top Defects */}
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

        <KpiCard title="Top Defects" loading={loading} error={error}>
          {isNullOrError(topDefectsData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi data={topDefectsData} horizontal color="#ef4444" />
          )}
        </KpiCard>

        {/* Row 3: Audited Pieces, Rejected Evolution */}
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

        {/* Row 4: Acceptance/Reject counts by line, Perf by Customer */}
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

        {/* Row 5: Perf by Customer, Perf by Line */}
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

        {/* Row 6: Seconds Rework, Fabric Defects */}
        <KpiCard title="Weekly Rework (seconds)" loading={loading} error={error}>
          {isNullOrError(secondsReworkSeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi
              series={secondsReworkSeries}
              xAxisLabel="Week"
              yAxisLabel="Seconds"
              xTickFormatter={formatWeekLabel}
              valueFormatter={formatSeconds}
              tooltipLabelFormatter={formatWeekLabel}
            />
          )}
        </KpiCard>

        <KpiCard title="Fabric Defects" loading={loading} error={error}>
          {isNullOrError(fabricDefectsData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={fabricDefectsData}
              color="#ec4899"
              showAllCategoryTicks
              chartHeight={340}
              xAxisLabel="Defect Type"
              yAxisLabel="Count"
            />
          )}
        </KpiCard>

        {/* Row 7: Containers by State, Defects Heatmap */}
        <KpiCard title="Containers by Status" loading={loading} error={error}>
          {isNullOrError(containersByStateData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <DonutChartKpi
              data={containersByStateData}
              valueFormatter={formatCount}
              tooltipLabelFormatter={(label) => `Range: ${label}`}
              showSliceLabels
            />
          )}
        </KpiCard>

        <KpiCard title="Defects by Style × Type" loading={loading} error={error}>
          {isNullOrError(defectsByStyleTypeData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <HeatmapKpi data={defectsByStyleTypeData} />
          )}
        </KpiCard>
      </Masonry>
    </div>
  );
}

export default withRoleProtection(DashboardView, ['manager']);
