import { useState, useEffect, useCallback } from 'react';
import { fetchAllContainerKpis, getContainerFilterOptions } from '../../api/kpi';
import {
  transformContainerExecutiveSummary,
  transformContainersByState,
  transformTopDefects,
  formatPercent,
  formatPieces,
} from '../../utils/chartTransforms';
import KpiCard from '../../Components/kpi/KpiCard';
import KpiNumberCard from '../../Components/kpi/KpiNumberCard';
import BarChartKpi from '../../Components/kpi/BarChartKpi';
import LineChartKpi from '../../Components/kpi/LineChartKpi';
import DonutChartKpi from '../../Components/kpi/DonutChartKpi';
import ContainerFilterBar from '../../Components/kpi/ContainerFilterBar';
import '../DashboardView.css';
import { withRoleProtection } from '../../hooks/withRoleProtection';

/**
 * ContainerDashboard — Manager-facing Container quality dashboard.
 *
 * Layout (3-column grid rhythm):
 * ┌─────────────────────────────────────────────────────────┐
 * │  Executive Summary — 4 metric cards (full width)        │
 * ├──────────┬──────────────────────────────────────────────┤
 * │  State   │  Inspected Trend (span 2)                    │
 * │  Dist.   │                                               │
 * ├──────────┼──────────────────────────────┬───────────────┤
 * │  Rejected Trend (span 2)                │  Top Defects  │
 * ├─────────────────────────────────────────────────────────┤
 * │  Pass Rate Trend (span 3)                                │
 * └─────────────────────────────────────────────────────────┘
 *
 * Section headers removed — card titles carry the hierarchy.
 * Defect Composition removed (duplicated Top Defects insight).
 * Worst Containers removed (not useful at this stage).
 * Top Defects tooltip shows count + percentage.
 * Donut uses legend-driven labels (no floating slice labels).
 *
 * Volatile (fast) mode: containersByState is available; all other
 * Container-specific KPIs show explicit unavailable messaging.
 */
function ContainerDashboard({ volatileData, volatileFile, context }) {
  const isLiveMode = !volatileData && !volatileFile;
  const isVolatileFileMode = !!volatileFile;

  const [filters, setFilters] = useState({
    date_range: ['', ''],
    from_date: '',
    to_date: '',
    customer: '',
  });

  const [kpiData, setKpiData] = useState(null);
  const [customerOptions, setCustomerOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadData = useCallback(async (activeFilters = filters) => {
    setLoading(true);
    setError(null);

    try {
      const result = await fetchAllContainerKpis(activeFilters, volatileFile, context);
      setKpiData(result);
    } catch (err) {
      setError(err.message || 'Error loading data');
    } finally {
      setLoading(false);
    }
  }, [volatileFile, filters, context]);

  useEffect(() => {
    if (!isVolatileFileMode) {
      loadData();
    }
  }, [isVolatileFileMode, loadData]);

  useEffect(() => {
    if (!isLiveMode) return;

    let active = true;
    getContainerFilterOptions()
      .then((options) => {
        if (!active) return;
        setCustomerOptions(Array.isArray(options?.customer) ? options.customer : []);
      })
      .catch(() => {
        if (!active) return;
        setCustomerOptions([]);
      });

    return () => {
      active = false;
    };
  }, [isLiveMode]);

  // Fetch KPIs from volatile file (server-side calculation)
  useEffect(() => {
    if (!volatileFile) return;

    const fetchVolatile = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchAllContainerKpis(filters, volatileFile, context);
        setKpiData(result);
      } catch (err) {
        setError(err.message || 'Error processing Excel file');
      } finally {
        setLoading(false);
      }
    };

    fetchVolatile();
  }, [volatileFile]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  const handleReset = useCallback(() => {
    const resetFilters = {
      date_range: ['', ''],
      from_date: '',
      to_date: '',
      customer: '',
    };
    setFilters(resetFilters);
    if (isLiveMode) {
      loadData(resetFilters);
    }
  }, [isLiveMode, loadData]);

  const handleRefresh = useCallback(() => {
    loadData(filters);
  }, [loadData, filters]);

  // ── Transform data for charts ─────────────────────────────────

  const execSummary = transformContainerExecutiveSummary(kpiData?.executiveSummary);
  const containersByStateData = transformContainersByState(kpiData?.containersByState);
  const passRateTrendData = kpiData?.passRateTrend;
  const inspectedTrendData = kpiData?.inspectedTrend;
  const rejectedTrendData = kpiData?.rejectedTrend;
  const topDefectsData = transformTopDefects(kpiData?.topDefects);

  // Extract executive summary values
  const execData = execSummary.status === 'ready' && execSummary.data.length > 0
    ? execSummary.data[0]
    : null;

  // ── State helper functions ────────────────────────────────────

  const isNullOrError = (data) => data == null || (data && (data.error || data.status === 'unavailable'));

  const resolveChartData = (data) => {
    if (data && data.status === 'ready') return data.data;
    if (data && (data.status === 'empty' || data.status === 'unavailable')) return null;
    return data;
  };

  const shouldShowMessage = (data) => {
    if (!data) return true;
    if (data.error) return true;
    if (data.status === 'empty' || data.status === 'unavailable') return true;
    return false;
  };

  const getChartMessage = (data) => {
    if (data && data.message) return data.message;
    if (data && data.error) return data.error;
    return nullMessage;
  };

  const getStateClass = (data) => {
    if (!data) return 'state-null';
    if (data.status === 'empty') return 'state-empty';
    if (data.status === 'unavailable') return 'state-unavailable';
    if (data.error) return 'state-error';
    return 'state-null';
  };

  const nullMessage = 'No disponible en modo rápido';

  // ── Trend helpers ─────────────────────────────────────────────

  const renderTrendChart = (title, data, yAxisLabel, valueFormatter, lineColors) => (
    <KpiCard title={title} loading={loading} error={error}>
      {isNullOrError(data) ? (
        <div className="null-message">{nullMessage}</div>
      ) : (
        <LineChartKpi
          series={Array.isArray(data) ? data : []}
          xAxisLabel="Date"
          yAxisLabel={yAxisLabel}
          valueFormatter={valueFormatter}
          lineColors={lineColors}
        />
      )}
    </KpiCard>
  );

  const renderDefectStateCard = (title, data, chartRenderer) => (
    <KpiCard title={title} loading={loading} error={error}>
      {shouldShowMessage(data) ? (
        <div className={`state-message ${getStateClass(data)}`}>
          {getChartMessage(data)}
        </div>
      ) : (
        chartRenderer(resolveChartData(data))
      )}
    </KpiCard>
  );

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Container Dashboard</h1>
        <button className="refresh-btn" onClick={handleRefresh} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {isLiveMode && (
        <ContainerFilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
          onReset={handleReset}
          customerOptions={customerOptions}
        />
      )}

      {!isLiveMode && (
        <div className="volatile-helper" role="status" aria-live="polite">
          <strong>Fast mode:</strong> only Containers by State is available.
          Other Container KPIs require live database connection.
        </div>
      )}

      <div className="container-dashboard-layout">

        {/* ── Executive Summary — full width 4-col sub-grid ── */}
        <div className="layout-full">
          <div className="container-summary-grid">
            <KpiCard title="Total Containers" loading={loading} error={error}>
              {isNullOrError(execData?.totalContainers) ? (
                <div className="null-message">{nullMessage}</div>
              ) : (
                <KpiNumberCard
                  title="Containers"
                  value={execData.totalContainers}
                  decimals={0}
                  label="total containers inspected"
                />
              )}
            </KpiCard>
            <KpiCard title="Average Pass Rate" loading={loading} error={error}>
              {isNullOrError(execData?.averagePassRate) ? (
                <div className="null-message">{nullMessage}</div>
              ) : (
                <KpiNumberCard
                  title="Pass Rate"
                  value={execData.averagePassRate}
                  unit="%"
                  label="average pass rate across containers"
                />
              )}
            </KpiCard>
            <KpiCard title="Total Inspected Palettes" loading={loading} error={error}>
              {isNullOrError(execData?.totalInspected) ? (
                <div className="null-message">{nullMessage}</div>
              ) : (
                <KpiNumberCard
                  title="Inspected"
                  value={execData.totalInspected}
                  decimals={0}
                  label="total palettes inspected"
                />
              )}
            </KpiCard>
            <KpiCard title="Total Rejected Palettes" loading={loading} error={error}>
              {isNullOrError(execData?.totalRejected) ? (
                <div className="null-message">{nullMessage}</div>
              ) : (
                <KpiNumberCard
                  title="Rejected"
                  value={execData.totalRejected}
                  decimals={0}
                  label="total palettes rejected"
                />
              )}
            </KpiCard>
          </div>
        </div>

        {/* ── Left column / Row 1 ── */}
        <div className="layout-left">
          <KpiCard title="Container State Distribution" loading={loading} error={error}>
            {isNullOrError(containersByStateData) ? (
              <div className="null-message">{nullMessage}</div>
            ) : (
              <DonutChartKpi
                data={containersByStateData}
                showSliceLabels
                minLabelPercent={0}
                valueFormatter={(value) => `${Math.round(Number(value))} contenedores`}
                tooltipLabelFormatter={(label) => `Pass rate: ${label}`}
              />
            )}
          </KpiCard>
        </div>

        {/* ── Right block / Row 1 ── */}
        <div className="layout-right-wide">
          {renderTrendChart('Inspected Trend', inspectedTrendData, 'Inspected Palettes', formatPieces, ['#10b981'])}
        </div>

        {/* ── Left column / Rows 2-3 ── */}
        <div className="layout-left layout-tall">
          {renderDefectStateCard('Top Defects', topDefectsData, (data) => (
            <BarChartKpi
              data={data}
              horizontal
              color="#ef4444"
              chartHeight={520}
              xAxisLabel="Cantidad de defectos"
              yAxisLabel="Tipo de defecto"
              valueFormatter={(value) => `${Math.round(Number(value))} defectos`}
              tooltipLabelFormatter={(label) => `Defecto: ${label}`}
              tooltipFormatter={(value, name, props) => {
                const pct = props?.payload?.percentage;
                const count = Math.round(Number(value));
                const base = `${count} defectos`;
                return pct != null ? [`${base} (${pct}%)`, 'Defecto'] : [base, 'Defecto'];
              }}
            />
          ))}
        </div>

        {/* ── Right block / Row 2 ── */}
        <div className="layout-right-wide">
          {renderTrendChart('Rejected Trend', rejectedTrendData, 'Rejected Palettes', formatPieces, ['#ef4444'])}
        </div>

        {/* ── Right block / Row 3 ── */}
        <div className="layout-right-wide layout-right-start">
          {renderTrendChart('Pass Rate Trend', passRateTrendData, 'Pass Rate (%)', formatPercent, ['#8b5cf6'])}
        </div>

      </div>

    </div>
  );
}

export default withRoleProtection(ContainerDashboard, ['manager']);
