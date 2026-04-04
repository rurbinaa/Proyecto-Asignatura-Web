import { useState, useEffect, useCallback } from 'react';
import { fetchAllKpis, fetchVolatileKpis } from '../api/kpi';
import * as calc from '../utils/kpiCalculations';
import KpiCard from '../Components/kpi/KpiCard';
import BarChartKpi from '../Components/kpi/BarChartKpi';
import LineChartKpi from '../Components/kpi/LineChartKpi';
import DonutChartKpi from '../Components/kpi/DonutChartKpi';
import HeatmapKpi from '../Components/kpi/HeatmapKpi';
import KpiNumberCard from '../Components/kpi/KpiNumberCard';
import FilterBar from '../Components/kpi/FilterBar';
import { normalizeScalarMetric } from './dashboardMetricUtils';
import Masonry from 'react-masonry-css';
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

const formatPercent = (value) => `${Number(value).toFixed(2)}%`;
const formatPieces = (value) => `${Math.round(Number(value))} piezas`;
const formatCount = (value) => `${Math.round(Number(value))} conteo`;
const formatSeconds = (value) => `${Number(value).toFixed(1)} seg`;
const formatWeekLabel = (value) => `Semana ${value}`;
const formatAcceptanceIndex = (value) => `${Number(value).toFixed(2)} idx`;
const trimCategoryLabel = (value) => {
  const text = String(value ?? '');
  return text.length > 18 ? `${text.slice(0, 18)}…` : text;
};

const parseLineStateLabel = (label) => {
  const raw = String(label ?? '');
  const parts = raw.split(' - ');
  if (parts.length < 2) {
    return { line: raw, state: '' };
  }

  return {
    line: parts.slice(0, -1).join(' - ').trim(),
    state: parts[parts.length - 1].trim().toUpperCase(),
  };
};

const buildLineCountDataByState = (data, targetState) => {
  if (!Array.isArray(data)) return [];

  return data
    .map((item) => {
      const { line, state } = parseLineStateLabel(item.label);
      return {
        line,
        state,
        value: Number(item.value) || 0,
      };
    })
    .filter((item) => item.state === targetState)
    .map((item) => ({ label: item.line, value: item.value }));
};

export default function DashboardView({ volatileData, volatileFile }) {
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
    if (!isVolatileFileMode) {
      loadData();
    }
  }, [isVolatileFileMode, loadData]);

  // Fetch KPIs from volatile file (server-side calculation)
  useEffect(() => {
    if (!volatileFile) return;

    const fetchVolatile = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchVolatileKpis(volatileFile);
        setKpiData(result);
      } catch (err) {
        setError(err.message || 'Error al procesar archivo Excel');
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

      {!isLiveMode && (
        <div className="volatile-helper" role="status" aria-live="polite">
          <strong>Modo rápido:</strong> no aplica filtros live y algunos KPIs pueden no estar
          disponibles por depender de tablas de base de datos.
        </div>
      )}

      <Masonry
        breakpointCols={{ default: 3, 1100: 2, 768: 1 }}
        className="dashboard-masonry"
        columnClassName="dashboard-masonry-column"
      >
        {/* Row 1: Defect Rate, Pass/Reject, AQL Weekly */}
        <KpiCard title="Tasa de Defectos (AQL %)" loading={loading} error={error}>
          <KpiNumberCard
            title="AQL"
            value={defectRate !== null && !isNullOrError(defectRate) ? defectRate : null}
            unit="%"
            label="defectos / muestra × 100"
          />
        </KpiCard>

        <KpiCard title="Distribución Pass / Reject" loading={loading} error={error}>
          {isNullOrError(passRejectData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <DonutChartKpi
              data={passRejectData}
              valueFormatter={formatPieces}
              tooltipLabelFormatter={(label) => `Estado: ${label}`}
            />
          )}
        </KpiCard>

        <KpiCard title="AQL semanal (%)" loading={loading} error={error}>
          {isNullOrError(aqlWeeklySeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi
              series={aqlWeeklySeries}
              xAxisLabel="Semana"
              yAxisLabel="AQL (%)"
              xTickFormatter={formatWeekLabel}
              yTickFormatter={(value) => `${value}%`}
              valueFormatter={formatPercent}
              tooltipLabelFormatter={formatWeekLabel}
            />
          )}
        </KpiCard>

        {/* Row 2: AQL by Style, Top Defects */}
        <KpiCard title="AQL por Estilo" loading={loading} error={error}>
          {isNullOrError(aqlByStyleData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={aqlByStyleData}
              horizontal
              color="#3b82f6"
              xAxisLabel="AQL (%)"
              yAxisLabel="Estilo"
              xTickFormatter={(value) => `${value}%`}
              valueFormatter={formatPercent}
              tooltipLabelFormatter={(label) => `Estilo: ${label}`}
              yAxisWidth={110}
            />
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
        <KpiCard title="Piezas auditadas por semana" loading={loading} error={error}>
          {isNullOrError(auditedPiecesSeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi
              series={auditedPiecesSeries}
              xAxisLabel="Semana"
              yAxisLabel="Piezas"
              xTickFormatter={formatWeekLabel}
              valueFormatter={formatPieces}
              tooltipLabelFormatter={formatWeekLabel}
            />
          )}
        </KpiCard>

        <KpiCard title="Piezas rechazadas por semana" loading={loading} error={error}>
          {isNullOrError(rejectedEvolutionSeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi
              series={rejectedEvolutionSeries}
              xAxisLabel="Semana"
              yAxisLabel="Piezas rechazadas"
              xTickFormatter={formatWeekLabel}
              valueFormatter={formatPieces}
              tooltipLabelFormatter={formatWeekLabel}
            />
          )}
        </KpiCard>

        {/* Row 4: Acceptance/Reject counts by line, Perf by Customer */}
        <KpiCard title="Aceptadas por línea (conteo)" loading={loading} error={error}>
          {isNullOrError(acReRateByLineData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={acceptedByLineData}
              color="#10b981"
              horizontal
              xAxisLabel="Conteo (piezas)"
              yAxisLabel="Línea"
              xTickFormatter={formatPieces}
              yTickFormatter={trimCategoryLabel}
              valueFormatter={formatCount}
              tooltipLabelFormatter={(label) => `Línea (aceptadas): ${label}`}
            />
          )}
        </KpiCard>

        <KpiCard title="Rechazadas por línea (conteo)" loading={loading} error={error}>
          {isNullOrError(acReRateByLineData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={rejectedByLineData}
              color="#ef4444"
              horizontal
              xAxisLabel="Conteo (piezas)"
              yAxisLabel="Línea"
              xTickFormatter={formatPieces}
              yTickFormatter={trimCategoryLabel}
              valueFormatter={formatCount}
              tooltipLabelFormatter={(label) => `Línea (rechazadas): ${label}`}
            />
          )}
        </KpiCard>

        {/* Row 5: Perf by Customer, Perf by Line */}
        <KpiCard title="Índice de aceptación por cliente (accepted/sample × 100)" loading={loading} error={error}>
          {isNullOrError(perfByCustomerData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={perfByCustomerData}
              color="#8b5cf6"
              xAxisLabel="Cliente"
              yAxisLabel="Índice de aceptación (accepted/sample × 100)"
              xTickFormatter={trimCategoryLabel}
              yTickFormatter={(value) => Number(value).toFixed(0)}
              valueFormatter={formatAcceptanceIndex}
              tooltipLabelFormatter={(label) => `Cliente: ${label}`}
            />
          )}
        </KpiCard>

        <KpiCard title="Índice de aceptación por línea (accepted/sample × 100)" loading={loading} error={error}>
          {isNullOrError(perfByLineData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={perfByLineData}
              horizontal
              color="#f59e0b"
              xAxisLabel="Índice de aceptación (accepted/sample × 100)"
              yAxisLabel="Línea"
              xTickFormatter={(value) => Number(value).toFixed(0)}
              valueFormatter={formatAcceptanceIndex}
              tooltipLabelFormatter={(label) => `Línea: ${label}`}
            />
          )}
        </KpiCard>

        {/* Row 6: Seconds Rework, Fabric Defects */}
        <KpiCard title="Rework en segundos por semana" loading={loading} error={error}>
          {isNullOrError(secondsReworkSeries) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <LineChartKpi
              series={secondsReworkSeries}
              xAxisLabel="Semana"
              yAxisLabel="Segundos"
              xTickFormatter={formatWeekLabel}
              valueFormatter={formatSeconds}
              tooltipLabelFormatter={formatWeekLabel}
            />
          )}
        </KpiCard>

        <KpiCard title="Defectos de Tela" loading={loading} error={error}>
          {isNullOrError(fabricDefectsData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <BarChartKpi
              data={fabricDefectsData}
              color="#ec4899"
              showAllCategoryTicks
              chartHeight={340}
              xAxisLabel="Tipo de defecto"
              yAxisLabel="Conteo"
            />
          )}
        </KpiCard>

        {/* Row 7: Containers by State, Defects Heatmap */}
        <KpiCard title="Contenedores por Estado" loading={loading} error={error}>
          {isNullOrError(containersByStateData) ? (
            <div className="null-message">{nullMessage}</div>
          ) : (
            <DonutChartKpi
              data={containersByStateData}
              valueFormatter={formatCount}
              tooltipLabelFormatter={(label) => `Rango: ${label}`}
              showSliceLabels
            />
          )}
        </KpiCard>

        <KpiCard title="Defectos por Estilo × Tipo" loading={loading} error={error}>
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
