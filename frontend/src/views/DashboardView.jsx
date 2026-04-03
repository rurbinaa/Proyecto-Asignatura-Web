import { useState, useEffect, useCallback } from 'react';
import { fetchAllKpis } from '../api/kpi';
import * as calc from '../utils/kpiCalculations';
import KpiCard from '../Components/kpi/KpiCard';
import BarChartKpi from '../Components/kpi/BarChartKpi';
import LineChartKpi from '../Components/kpi/LineChartKpi';
import DonutChartKpi from '../Components/kpi/DonutChartKpi';
import HeatmapKpi from '../Components/kpi/HeatmapKpi';
import KpiNumberCard from '../Components/kpi/KpiNumberCard';
import FilterBar from '../Components/kpi/FilterBar';
import './DashboardView.css';

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

/**
 * Transform API response to chart-friendly format.
 * Handles both direct data and wrapped response formats.
 */
function normalizeApiData(kpiName, data) {
  if (!data || data.error) return null;
  return data;
}

/**
 * Transform pass/reject distribution for DonutChart.
 * API returns: [{name: "PASS", value: 85}, {name: "REJECT", value: 15}]
 */
function transformPassReject(data) {
  if (!data || data.error) return null;
  return (data.result || data).map(item => ({
    name: item.name,
    value: item.value,
  }));
}

/**
 * Transform AQL by style for BarChart horizontal.
 * API returns: {data: [{label: "Style-1", value: 2.34}, ...]}
 */
function transformAqlByStyle(data) {
  if (!data || data.error) return null;
  const arr = data.data || data;
  return arr.map(item => ({
    label: item.label,
    value: item.value,
  }));
}

/**
 * Transform AQL weekly for LineChart.
 * API returns: [{name: "AQL", data: [{x: 1, y: 2.3}, ...]}, {name: "Trend", data: [...]}]
 */
function transformAqlWeekly(data) {
  if (!data || data.error) return null;
  const arr = data.data || data;
  return arr.map(series => ({
    name: series.name,
    data: series.data,
  }));
}

/**
 * Transform audited pieces for LineChart.
 * API returns: [{name: "Pieces", data: [{x: 1, y: 234}, ...]}]
 */
function transformAuditedPieces(data) {
  if (!data || data.error) return null;
  const arr = data.data || data;
  return arr.map(series => ({
    name: series.name,
    data: series.data,
  }));
}

/**
 * Transform rejected evolution for LineChart.
 * API returns: [{name: "Rejected", data: [{x: 1, y: 23}, ...]}]
 */
function transformRejectedEvolution(data) {
  if (!data || data.error) return null;
  const arr = data.data || data;
  return arr.map(series => ({
    name: series.name,
    data: series.data,
  }));
}

/**
 * Transform AC/RE rate by line for BarChart.
 * API returns: [{label: "1 - PASS", value: 45}, {label: "1 - REJECT", value: 5}, ...]
 */
function transformAcReRateByLine(data) {
  if (!data || data.error) return null;
  return (data.result || data).map(item => ({
    label: item.label,
    value: item.value,
  }));
}

/**
 * Transform performance by customer for BarChart.
 * API returns: [{label: "Customer X", value: 92.5}, ...]
 */
function transformPerformanceByCustomer(data) {
  if (!data || data.error) return null;
  return (data.result || data).map(item => ({
    label: item.label,
    value: item.value,
  }));
}

/**
 * Transform performance by line for horizontal BarChart.
 * API returns: [{label: "Line 1", value: 95.2}, ...]
 */
function transformPerformanceByLine(data) {
  if (!data || data.error) return null;
  return (data.result || data).map(item => ({
    label: item.label,
    value: item.value,
  }));
}

/**
 * Transform top defects for horizontal BarChart.
 * API returns: [{label: "Loose Thread", value: 234}, ...]
 */
function transformTopDefects(data) {
  if (!data || data.error) return null;
  return (data.result || data).map(item => ({
    label: item.label,
    value: item.value,
  }));
}

/**
 * Transform fabric defects for BarChart.
 * API returns: [{label: "Corrido", value: 45}, {label: "Barre", value: 23}, ...]
 */
function transformFabricDefects(data) {
  if (!data || data.error) return null;
  return (data.result || data).map(item => ({
    label: item.label,
    value: item.value,
  }));
}

/**
 * Transform containers by state for DonutChart.
 * API returns: [{name: "< 80%", value: 3}, {name: "80-90%", value: 12}, ...]
 */
function transformContainersByState(data) {
  if (!data || data.error) return null;
  return (data.result || data).map(item => ({
    name: item.name,
    value: item.value,
  }));
}

/**
 * Transform defects by style × type for Heatmap.
 * API returns: [{x: "Style-2", y: "Loose Thread", value: 45}, ...]
 */
function transformDefectsByStyleType(data) {
  if (!data || data.error) return null;
  return (data.result || data).map(item => ({
    x: item.x,
    y: item.y,
    value: item.value,
  }));
}

/**
 * Transform seconds rework for double LineChart.
 * API returns: [{name: "Sewing", data: [{x: 1, y: 12.3}, ...]}, {name: "Fabric", data: [...]}]
 */
function transformSecondsRework(data) {
  if (!data || data.error) return null;
  return (data.result || data).map(series => ({
    name: series.name,
    data: series.data,
  }));
}

export default function DashboardView({ volatileData }) {
  const isLiveMode = !volatileData;

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

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      if (isLiveMode) {
        const result = await fetchAllKpis(filters);
        setKpiData(result);
      } else {
        const result = calculateAllKpis(volatileData);
        setKpiData(result);
      }
    } catch (err) {
      setError(err.message || 'Error al cargar datos');
    } finally {
      setLoading(false);
    }
  }, [isLiveMode, filters, volatileData]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  const handleApply = useCallback(() => {
    loadData();
  }, [loadData]);

  const handleReset = useCallback(() => {
    setFilters({
      date_range: ['', ''],
      week: '',
      team: '',
      style: '',
      color: '',
      customer: '',
      batch: '',
    });
  }, []);

  const handleRefresh = useCallback(() => {
    loadData();
  }, [loadData]);

  // Transform data for charts
  const defectRate = kpiData?.defectRate;
  const passRejectData = transformPassReject(kpiData?.passRejectDistribution);
  const aqlWeeklySeries = transformAqlWeekly(kpiData?.aqlWeekly);
  const aqlByStyleData = transformAqlByStyle(kpiData?.aqlByStyle);
  const topDefectsData = transformTopDefects(kpiData?.topDefects);
  const auditedPiecesSeries = transformAuditedPieces(kpiData?.auditedPieces);
  const rejectedEvolutionSeries = transformRejectedEvolution(kpiData?.rejectedEvolution);
  const acReRateByLineData = transformAcReRateByLine(kpiData?.acReRateByLine);
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
        <h1 className="dashboard-title">Dashboard de KPIs</h1>
        <button className="refresh-btn" onClick={handleRefresh} disabled={loading}>
          {loading ? 'Cargando...' : 'Actualizar'}
        </button>
      </div>

      {isLiveMode && (
        <FilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
          onApply={handleApply}
          onReset={handleReset}
        />
      )}

      <div className="dashboard-grid">
        {/* Row 1: Defect Rate, Pass/Reject, AQL Weekly */}
        <KpiCard title="Tasa de Defectos" loading={loading} error={error}>
          <KpiNumberCard
            title="Defect Rate"
            value={defectRate !== null && !isNullOrError(defectRate) ? defectRate : null}
            unit="%"
            label="defectos / muestra × 100"
          />
        </KpiCard>

        <KpiCard title="Distribución Pass / Reject" loading={loading} error={error}>
          {isNullOrError(passRejectData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <DonutChartKpi data={passRejectData} />
          )}
        </KpiCard>

        <KpiCard title="AQL Semanal" loading={loading} error={error}>
          {isNullOrError(aqlWeeklySeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi series={aqlWeeklySeries} />
          )}
        </KpiCard>

        {/* Row 2: AQL by Style, Top Defects */}
        <KpiCard title="AQL por Estilo" loading={loading} error={error}>
          {isNullOrError(aqlByStyleData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi data={aqlByStyleData} horizontal color="#3b82f6" />
          )}
        </KpiCard>

        <KpiCard title="Top Defectos" loading={loading} error={error}>
          {isNullOrError(topDefectsData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi data={topDefectsData} horizontal color="#ef4444" />
          )}
        </KpiCard>

        {/* Row 3: Audited Pieces, Rejected Evolution */}
        <KpiCard title="Piezas Auditadas" loading={loading} error={error}>
          {isNullOrError(auditedPiecesSeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi series={auditedPiecesSeries} />
          )}
        </KpiCard>

        <KpiCard title="Evolución Rechazadas" loading={loading} error={error}>
          {isNullOrError(rejectedEvolutionSeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi series={rejectedEvolutionSeries} />
          )}
        </KpiCard>

        {/* Row 4: Ac/Re Rate by Line, Perf by Customer */}
        <KpiCard title="Tasa Aceptación/Rechazo por Línea" loading={loading} error={error}>
          {isNullOrError(acReRateByLineData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi data={acReRateByLineData} color="#10b981" />
          )}
        </KpiCard>

        <KpiCard title="Performance por Cliente" loading={loading} error={error}>
          {isNullOrError(perfByCustomerData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi data={perfByCustomerData} color="#8b5cf6" />
          )}
        </KpiCard>

        {/* Row 5: Perf by Line, Seconds Rework */}
        <KpiCard title="Performance por Línea" loading={loading} error={error}>
          {isNullOrError(perfByLineData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi data={perfByLineData} horizontal color="#f59e0b" />
          )}
        </KpiCard>

        <KpiCard title="Tiempo de Rework (segundos)" loading={loading} error={error}>
          {isNullOrError(secondsReworkSeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi series={secondsReworkSeries} />
          )}
        </KpiCard>

        {/* Row 6: Fabric Defects, Containers by State */}
        <KpiCard title="Defectos de Tela" loading={loading} error={error}>
          {isNullOrError(fabricDefectsData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi data={fabricDefectsData} color="#ec4899" />
          )}
        </KpiCard>

        <KpiCard title="Contenedores por Estado" loading={loading} error={error}>
          {isNullOrError(containersByStateData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <DonutChartKpi data={containersByStateData} />
          )}
        </KpiCard>

        {/* Row 7: Defects by Style × Type (full width) */}
        <KpiCard title="Defectos por Estilo × Tipo" loading={loading} error={error} className="full-width">
          {isNullOrError(defectsByStyleTypeData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <HeatmapKpi data={defectsByStyleTypeData} />
          )}
        </KpiCard>
      </div>
    </div>
  );
}
