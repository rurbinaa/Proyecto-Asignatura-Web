import axiosClient from './axiosClient';
import { normalizeVolatileFilters, buildVolatileIdentity } from '../utils/volatileFilters';

function unavailableKpi(reason) {
  return {
    status: 'unavailable',
    reason: reason || 'KPI unavailable',
    data: null,
  };
}

/**
 * Unwrap a nested KPI value object to a scalar.
 * Handles { label: string, value: number } -> number, or returns the value as-is if already scalar.
 * Returns null for invalid/unparseable values.
 * @param {any} value - The value to unwrap
 * @returns {number|null} Scalar value or null
 */
function unwrapScalarKpiValue(value) {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'object' && value !== null) {
    const innerValue = value.value;
    if (typeof innerValue === 'number' && Number.isFinite(innerValue)) {
      return innerValue;
    }
    // Try to parse as number if it's a string
    if (typeof innerValue === 'string') {
      const parsed = Number(innerValue);
      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }
  }
  // Handle numeric strings
  if (typeof value === 'string') {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return null;
}

/**
 * Build query string from filters object.
 * @param {object} filters - Key-value pairs for query params
 * @returns {string} Query string including leading '?'
 */
function buildQueryString(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      // Arrays (like date_range) should be joined with comma
      // Skip arrays that are empty or contain only empty strings
      if (Array.isArray(value)) {
        const filtered = value.filter(v => v !== '' && v !== null && v !== undefined);
        if (filtered.length > 0) {
          params.append(key, filtered.join(','));
        }
      } else {
        params.append(key, value);
      }
    }
  });
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

function resolveKpiUrl(endpoint, filters = {}, context) {
  const allParams = { ...filters };
  if (context) {
    allParams.context = context;
  }
  const queryString = buildQueryString(allParams);

  const aqlEndpoints = new Set(['aql-by-style/', 'aql-weekly/', 'audited-pieces/', 'aql-by-team/']);
  const rendimientoEndpoints = new Set([
    'ac-re-rate-by-line/',
    'seconds-rework/',
    'performance-by-customer/',
    'performance-by-line/',
  ]);

  if (aqlEndpoints.has(endpoint)) {
    return `/quality/kpis/aql/${endpoint}${queryString}`;
  }

  if (rendimientoEndpoints.has(endpoint)) {
    return `/quality/kpis/rendimiento/${endpoint}${queryString}`;
  }

  return `/quality/kpis/${endpoint}${queryString}`;
}

/**
 * Fetch KPI data from a specific endpoint.
 * @param {string} endpoint - KPI endpoint name (e.g. 'aql-by-style/')
 * @param {object} filters - Optional filters to apply
 * @returns {Promise<any>} JSON response data
 */
export async function fetchKpi(endpoint, filters = {}, context) {
  const url = resolveKpiUrl(endpoint, filters, context);
  try {
    const res = await axiosClient.get(url);
    return mapLiveKpiDto(endpoint, res.data);
  } catch (error) {
    throw new Error(error.response?.data?.error || `KPI fetch failed: ${error.response?.status}`);
  }
}

export function mapLiveKpiDto(endpoint, data) {
  if (endpoint === 'defect-rate/') {
    return unwrapScalarKpiValue(data);
  }
  return data;
}

// ─── Individual KPI helpers ──────────────────────────────────────────────────

/**
 * Fetch filter options for dashboard filters.
 * Returns distinct values for week, team, style, color, customer, batch,
 * plus line_code and include_dual_lines_default metadata.
 * @param {string} [context] - Context value (e.g. 'plant', 'customer')
 * @param {boolean} [includeDualLines] - Whether to request dual-line metadata
 * @returns {Promise<object>} Filter options object
 */
export async function getFilterOptions(context, includeDualLines) {
  const params = {};
  if (context !== undefined && context !== null && context !== '') {
    params.context = context;
  }
  if (includeDualLines !== undefined && includeDualLines !== null) {
    params.include_dual_lines = includeDualLines;
  }
  const queryString = buildQueryString(params);
  const url = `/quality/kpis/filter-options/${queryString}`;
  try {
    const res = await axiosClient.get(url);
    return res.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || `Filter options fetch failed: ${error.response?.status}`);
  }
}

/** AQL grouped by style (defects/sample % per style). */
export async function getAqlByStyle(filters, context) {
  return fetchKpi('aql-by-style/', filters, context);
}

/** AQL grouped by team/line (defects/sample % per team). */
export async function getAqlByTeam(filters, context) {
  return fetchKpi('aql-by-team/', filters, context);
}

/** AQL trend by week — useful for control charts. */
export async function getAqlWeekly(filters, context) {
  return fetchKpi('aql-weekly/', filters, context);
}

/** Total audited pieces per week. */
export async function getAuditedPieces(filters, context) {
  return fetchKpi('audited-pieces/', filters, context);
}

/** Acceptance / Rejection rate per production line (team). */
export async function getAcReRateByLine(filters, context) {
  return fetchKpi('ac-re-rate-by-line/', filters, context);
}

/** Seconds spent on rework per inspection — requires capture data. */
export async function getSecondsRework(filters, context) {
  return fetchKpi('seconds-rework/', filters, context);
}

/** Performance (% accepted) grouped by customer. */
export async function getPerformanceByCustomer(filters, context) {
  return fetchKpi('performance-by-customer/', filters, context);
}

/** Performance (% accepted) grouped by production line (team). */
export async function getPerformanceByLine(filters, context) {
  return fetchKpi('performance-by-line/', filters, context);
}

/** Top defect types by frequency — requires capture defect types. */
export async function getTopDefects(filters, context) {
  return fetchKpi('top-defects/', filters, context);
}

/** Fabric defect distribution — requires fabric inspection data. */
export async function getFabricDefects(filters, context) {
  return fetchKpi('fabric-defects/', filters, context);
}

/** Defect breakdown by style type — requires capture defect types. */
export async function getDefectsByStyleType(filters, context) {
  return fetchKpi('defects-by-style-type/', filters, context);
}

/** Defect composition donut — requires InspectionDefect data. */
export async function getDefectComposition(filters, context) {
  return fetchKpi('defect-composition/', filters, context);
}

/** Top 3 defect types weekly trend — requires InspectionDefect data. */
export async function getDefectTrendTop3(filters, context) {
  return fetchKpi('defect-trend-top-3/', filters, context);
}

/** Pass vs. reject count distribution across all inspections. */
export async function getPassRejectDistribution(filters, context) {
  return fetchKpi('pass-reject-distribution/', filters, context);
}

/** Rejected pieces evolution over weeks. */
export async function getRejectedEvolution(filters, context) {
  return fetchKpi('rejected-evolution/', filters, context);
}

/** Container inspection status counts. */
export async function getContainersByState(filters, context) {
  return fetchKpi('containers-by-state/', filters, context);
}

/** Container-specific filter options. */
export async function getContainerFilterOptions() {
  const url = '/quality/kpis/container/filter-options/';
  try {
    const res = await axiosClient.get(url);
    return res.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || `Container filter options fetch failed: ${error.response?.status}`);
  }
}

/** Overall defect rate (defects per 100 units inspected). */
export async function getDefectRate(filters, context) {
  return fetchKpi('defect-rate/', filters, context);
}

// ─── Volatile (Excel upload) KPIs ─────────────────────────────────────────────

/**
 * Map snake_case API response keys to camelCase for DashboardView compatibility.
 * This adapter ensures the volatile KPI response matches the live endpoints contract.
 * @param {object} response - Raw API response with snake_case keys
 * @returns {object} Response with camelCase keys (idempotent - existing camelCase keys preserved)
 */
export function mapVolatileKpisDto(response) {
  if (!response || typeof response !== 'object') {
    return response;
  }

  const snakeToCamel = {
    aql_by_style: 'aqlByStyle',
    aql_by_team: 'aqlByTeam',
    aql_weekly: 'aqlWeekly',
    audited_pieces: 'auditedPieces',
    ac_re_rate_by_line: 'acReRateByLine',
    seconds_rework: 'secondsRework',
    performance_by_customer: 'performanceByCustomer',
    performance_by_line: 'performanceByLine',
    top_defects: 'topDefects',
    fabric_defects: 'fabricDefects',
    defects_by_style_type: 'defectsByStyleType',
    pass_reject_distribution: 'passRejectDistribution',
    rejected_evolution: 'rejectedEvolution',
    containers_by_state: 'containersByState',
    defect_rate: 'defectRate',
    defect_composition: 'defectComposition',
    defect_trend_top_3: 'defectTrendTop3',
    filter_options: 'filterOptions',
    executive_summary: 'executiveSummary',
    pass_rate_trend: 'passRateTrend',
    inspected_trend: 'inspectedTrend',
    rejected_trend: 'rejectedTrend',
    worst_containers: 'worstContainers',
    // Seconds A4 volatile KPIs
    weekly_trend: 'weeklyTrend',
    sew_vs_fab: 'sewVsFab',
    by_style: 'byStyle',
    by_color: 'byColor',
    by_line: 'byLine',
    by_cut: 'byCut',
    pass_fail_weekly: 'passFailWeekly',
    // Seconds General volatile KPIs
    defects_by_customer: 'defectsByCustomer',
    defects_by_style: 'defectsByStyle',
    sewing_vs_fabric: 'sewingVsFabric',
    production_totals: 'productionTotals',
    top_sewing_defects: 'topSewingDefects',
    top_fabric_defects: 'topFabricDefects',
    fix_vs_definitive: 'fixVsDefinitive',
    defects_by_color: 'defectsByColor',
    defects_by_size: 'defectsBySize',
    defects_by_line: 'defectsByLine',
  };

  const normalized = {};

  for (const [key, value] of Object.entries(response)) {
    if (snakeToCamel[key]) {
      const camelKey = snakeToCamel[key];
      if (camelKey === 'defectRate') {
        normalized[camelKey] = unwrapScalarKpiValue(value);
      } else {
        normalized[camelKey] = value;
      }
    } else if (Object.values(snakeToCamel).includes(key)) {
      if (key === 'defectRate') {
        normalized[key] = unwrapScalarKpiValue(value);
      } else {
        normalized[key] = value;
      }
    } else {
      normalized[key] = value;
    }
  }

  return normalized;
}

/**
 * Fetch KPIs from an uploaded Excel file via the volatile endpoint.
 * The response has the same format as live KPI endpoints.
 * @param {File} file - The Excel file to process
 * @returns {Promise<object>} KPI results object (same shape as fetchAllKpis), with camelCase keys
 */
export async function fetchVolatileKpis(file, context) {
  const formData = new FormData();
  formData.append('file', file);
  if (context) {
    formData.append('context', context);
  }
  try {
    const res = await axiosClient.post('/quality/kpis/volatile/', formData);
    return mapVolatileKpisDto(res.data);
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Failed to process Excel');
  }
}

/**
 * Module-level in-flight promise map for volatile dashboard requests.
 * Deduplicates concurrent requests with identical file+dashboard+context.
 * @type {Map<string, Promise<object>>}
 */
const volatileInFlight = new Map();

/**
 * Build a stable deduplication key from volatile request parameters.
 * Includes normalized filter identity so different filter combinations
 * do NOT share in-flight promises or cache entries.
 * @param {File} file
 * @param {string} dashboard
 * @param {string|null} [context]
 * @param {object} [filters={}] - Raw dashboard filter state
 * @returns {string}
 */
function buildVolatileKey(file, dashboard, context, filters = {}) {
  return buildVolatileIdentity(file, dashboard, context, filters);
}

/**
 * Dashboard-aware volatile fetch with in-flight deduplication.
 *
 * Sends the optional ``dashboard`` parameter so the backend can dispatch
 * to the correct sheet and return only the relevant KPIs for that dashboard.
 * Accepts an optional ``filters`` object that is normalized through
 * ``normalizeVolatileFilters`` and appended as ``filter_*`` FormData fields.
 *
 * The response is also camelCase-mapped via ``mapVolatileKpisDto``.
 *
 * Concurrent calls with the same file+dashboard+context+filters share a
 * single in-flight promise. The promise is removed from the dedupe map
 * after settlement so subsequent calls always get a fresh request.
 *
 * @param {File} file - The Excel file to process
 * @param {string} dashboard - Dashboard key ('qcfa', 'container', 'seconds_a4', 'seconds_general')
 * @param {string} [context] - Optional context ('plant', 'customer')
 * @param {object} [filters={}] - Raw dashboard filter state (normalized internally)
 * @returns {Promise<object>} Dashboard-scoped KPI results, camelCase keys
 */
export async function fetchVolatileDashboard(file, dashboard, context, filters = {}) {
  const key = buildVolatileKey(file, dashboard, context, filters);

  // In-flight deduplication: return existing promise if one is still pending
  if (volatileInFlight.has(key)) {
    return volatileInFlight.get(key);
  }

  const promise = (async () => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('dashboard', dashboard);
    if (context) {
      formData.append('context', context);
    }
    // Normalize and append filter_* fields from the filter state
    const normalized = normalizeVolatileFilters(dashboard, filters);
    for (const [key, value] of Object.entries(normalized)) {
      formData.append(`filter_${key}`, String(value));
    }
    let res;
    try {
      res = await axiosClient.post('/quality/kpis/volatile/', formData);
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to process Excel');
    }
    return mapVolatileKpisDto(res.data);
  })();

  volatileInFlight.set(key, promise);

  // Clean up the dedupe entry after settlement so subsequent calls are fresh.
  // .catch(() => {}) suppresses the forwarded rejection on the finally()-returned promise.
  // The actual rejection is handled by the caller's try/catch.
  promise.finally(() => {
    if (volatileInFlight.get(key) === promise) {
      volatileInFlight.delete(key);
    }
  }).catch(() => {});

  return promise;
}

// ─── Bulk fetch ───────────────────────────────────────────────────────────────

/**
 * Fetch all 14 KPIs in parallel, gracefully handling partial failures.
 * Returns an object keyed by KPI name.
 *
 * @param {object} filters - Optional shared filters for all KPIs
 * @returns {Promise<object>} { aqlByStyle, aqlWeekly, auditedPieces, ... }
 */
export async function fetchAllKpis(filters = {}, context) {
  const kpiMap = {
    aqlByStyle: getAqlByStyle,
    aqlByTeam: getAqlByTeam,
    aqlWeekly: getAqlWeekly,
    auditedPieces: getAuditedPieces,
    acReRateByLine: getAcReRateByLine,
    secondsRework: getSecondsRework,
    performanceByCustomer: getPerformanceByCustomer,
    performanceByLine: getPerformanceByLine,
    topDefects: getTopDefects,
    fabricDefects: getFabricDefects,
    defectsByStyleType: getDefectsByStyleType,
    passRejectDistribution: getPassRejectDistribution,
    rejectedEvolution: getRejectedEvolution,
    containersByState: getContainersByState,
    defectRate: getDefectRate,
    defectComposition: getDefectComposition,
    defectTrendTop3: getDefectTrendTop3,
  };

  const entries = Object.entries(kpiMap).map(([key, fn]) => [
    key,
    fn(filters, context).catch((err) => unavailableKpi(err.message)),
  ]);

  const results = await Promise.allSettled(entries.map(([, p]) => p));

  /** @type {object} */
  const kpis = {};
  entries.forEach(([key], i) => {
    const result = results[i];
    if (result.status === 'fulfilled') {
      kpis[key] = result.value;
    } else {
      kpis[key] = unavailableKpi(result.reason?.message ?? 'Unknown error');
    }
  });

  return kpis;
}

// ─── Container-specific KPI helpers ──────────────────────────────────────────

/** Container executive summary (total containers, pass rate, inspected, rejected). */
export async function getContainerExecutiveSummary(filters, context) {
  return fetchKpi('container/executive-summary/', filters, context);
}

/** Container pass rate trend over time. */
export async function getContainerPassRateTrend(filters, context) {
  return fetchKpi('container/pass-rate-trend/', filters, context);
}

/** Container inspected palettes trend. */
export async function getContainerInspectedTrend(filters, context) {
  return fetchKpi('container/inspected-trend/', filters, context);
}

/** Container rejected palettes trend. */
export async function getContainerRejectedTrend(filters, context) {
  return fetchKpi('container/rejected-trend/', filters, context);
}

/** Container top defect types. */
export async function getContainerTopDefects(filters, context) {
  return fetchKpi('container/top-defects/', filters, context);
}

/** Container defect composition donut data. */
export async function getContainerDefectComposition(filters, context) {
  return fetchKpi('container/defect-composition/', filters, context);
}

/** Container worst containers (lowest pass rate first, bounded ranking). */
export async function getContainerWorstContainers(filters, context) {
  return fetchKpi('container/worst-containers/', { ...filters, top: 5 }, context);
}

/**
 * Fetch all Container KPIs in parallel, with live/volatile orchestration.
 *
 * In live mode (no volatileFile), fetches all 7 container-specific KPIs
 * plus the shared containers-by-state endpoint in parallel.
 *
 * In volatile mode, only containersByState is available from the volatile
 * data; all Container-specific KPIs return explicit unavailable states.
 *
 * @param {object} filters - Container filters (customer, date_range, from_date, to_date)
 * @param {File|null} volatileFile - Excel file for volatile mode, or null for live
 * @param {string} [context] - Context (e.g. 'plant', 'customer')
 * @returns {Promise<object>} Container KPI results
 */
export async function fetchAllContainerKpis(filters = {}, volatileFile = null, context) {
  if (volatileFile) {
    // Volatile mode: all Container KPIs computed server-side from the uploaded file
    const volatileData = await fetchVolatileDashboard(volatileFile, 'container', context);
    return {
      executiveSummary: volatileData.executiveSummary || unavailableKpi('Executive Summary not available'),
      containersByState: volatileData.containersByState || unavailableKpi('Containers by State not available'),
      passRateTrend: volatileData.passRateTrend || unavailableKpi('Pass Rate Trend not available'),
      inspectedTrend: volatileData.inspectedTrend || unavailableKpi('Inspected Trend not available'),
      rejectedTrend: volatileData.rejectedTrend || unavailableKpi('Rejected Trend not available'),
      topDefects: volatileData.topDefects || unavailableKpi('Top Defects not available'),
      defectComposition: volatileData.defectComposition || unavailableKpi('Defect Composition not available'),
      worstContainers: volatileData.worstContainers || unavailableKpi('Worst Containers not available'),
    };
  }

  // Live mode: fetch all container KPIs in parallel
  const kpiMap = {
    executiveSummary: getContainerExecutiveSummary,
    containersByState: getContainersByState,
    passRateTrend: getContainerPassRateTrend,
    inspectedTrend: getContainerInspectedTrend,
    rejectedTrend: getContainerRejectedTrend,
    topDefects: getContainerTopDefects,
    defectComposition: getContainerDefectComposition,
    worstContainers: getContainerWorstContainers,
  };

  const entries = Object.entries(kpiMap).map(([key, fn]) => [
    key,
    fn(filters, context).catch((err) => unavailableKpi(err.message)),
  ]);

  const results = await Promise.allSettled(entries.map(([, p]) => p));

  /** @type {object} */
  const kpis = {};
  entries.forEach(([key], i) => {
    const result = results[i];
    if (result.status === 'fulfilled') {
      kpis[key] = result.value;
    } else {
      kpis[key] = unavailableKpi(result.reason?.message ?? 'Unknown error');
    }
  });

  return kpis;
}

// ─── Seconds A4 KPI helpers ───────────────────────────────────────────────

/**
 * Build filter params object for Seconds A4 API from dashboard filter state.
 * Strips empty/null/undefined values so they are not sent as query params.
 * @param {object} [filters={}] - Dashboard filter state (year, style, color, line, cut_num)
 * @returns {object} Params object with only active filter values
 */
export function buildSecondsA4Params(filters = {}) {
  const params = {};
  if (filters.year) params.year = filters.year;
  if (filters.style) params.style = filters.style;
  if (filters.color) params.color = filters.color;
  if (filters.line) params.line = filters.line;
  if (filters.cut_num) params.cut_num = filters.cut_num;
  return params;
}

/** Fetch filter options for Seconds A4 (year, line, cut_num lists). */
export async function getSecondsA4FilterOptions(filters = {}) {
  return fetchKpi('seconds-a4/filter-options/', filters);
}

/** Fetch Seconds A4 executive summary (totals + validated percentages). */
export async function getSecondsA4ExecutiveSummary(filters = {}) {
  return fetchKpi('seconds-a4/executive-summary/', filters);
}

/** Fetch Seconds A4 weekly trend series. */
export async function getSecondsA4WeeklyTrend(filters = {}) {
  return fetchKpi('seconds-a4/weekly-trend/', filters);
}

/** Fetch Seconds A4 sew vs fab split data. */
export async function getSecondsA4SewVsFab(filters = {}) {
  return fetchKpi('seconds-a4/sew-vs-fab/', filters);
}

/** Fetch Seconds A4 breakdown by style. */
export async function getSecondsA4ByStyle(filters = {}) {
  return fetchKpi('seconds-a4/by-style/', filters);
}

/** Fetch Seconds A4 breakdown by color. */
export async function getSecondsA4ByColor(filters = {}) {
  return fetchKpi('seconds-a4/by-color/', filters);
}

// ─── Seconds General volatile helper ──────────────────────────────────────

/**
 * Fetch all Seconds General KPIs in volatile (fast) mode.
 *
 * When volatileFile is provided, fetches all 12 Seconds General KPIs from
 * the volatile endpoint with ``dashboard=seconds_general``.
 * When volatileFile is null, fetches the live Seconds General analytics.
 *
 * @param {object} filters - Seconds General filters (customer, style, week, etc.)
 * @param {File|null} volatileFile - Excel file for volatile mode, or null for live
 * @returns {Promise<object>} Seconds General KPI results
 */
export async function fetchAllSecondsGeneralKpis(filters = {}, volatileFile = null) {
  if (volatileFile) {
    const volatileData = await fetchVolatileDashboard(volatileFile, 'seconds_general');
    return {
      defectsByCustomer: volatileData.defectsByCustomer || unavailableKpi('Defects by Customer unavailable'),
      defectsByStyle: volatileData.defectsByStyle || unavailableKpi('Defects by Style unavailable'),
      weeklyTrend: volatileData.weeklyTrend || unavailableKpi('Weekly Trend unavailable'),
      sewingVsFabric: volatileData.sewingVsFabric || unavailableKpi('Sewing vs Fabric unavailable'),
      productionTotals: volatileData.productionTotals || unavailableKpi('Production Totals unavailable'),
      topSewingDefects: volatileData.topSewingDefects || unavailableKpi('Top Sewing Defects unavailable'),
      topFabricDefects: volatileData.topFabricDefects || unavailableKpi('Top Fabric Defects unavailable'),
      fixVsDefinitive: volatileData.fixVsDefinitive || unavailableKpi('Fix vs Definitive unavailable'),
      defectsByColor: volatileData.defectsByColor || unavailableKpi('Defects by Color unavailable'),
      defectsBySize: volatileData.defectsBySize || unavailableKpi('Defects by Size unavailable'),
      defectsByLine: volatileData.defectsByLine || unavailableKpi('Defects by Line unavailable'),
    };
  }

  // Live mode: fetch from Seconds General analytics endpoints
  const kpiMap = {
    defectsByCustomer: () => fetchKpi('seconds-general/defects-by-customer/', filters),
    defectsByStyle: () => fetchKpi('seconds-general/defects-by-style/', filters),
    weeklyTrend: () => fetchKpi('seconds-general/weekly-trend/', filters),
    sewingVsFabric: () => fetchKpi('seconds-general/sewing-vs-fabric/', filters),
    productionTotals: () => fetchKpi('seconds-general/production-totals/', filters),
    topSewingDefects: () => fetchKpi('seconds-general/top-defects/', { ...filters, type: 'sewing' }),
    topFabricDefects: () => fetchKpi('seconds-general/top-defects/', { ...filters, type: 'fabric' }),
    fixVsDefinitive: () => fetchKpi('seconds-general/fix-vs-definitive/', filters),
    defectsByColor: () => fetchKpi('seconds-general/defects-by-color/', filters),
    defectsBySize: () => fetchKpi('seconds-general/defects-by-size/', filters),
    defectsByLine: () => fetchKpi('seconds-general/defects-by-line/', filters),
  };

  const entries = Object.entries(kpiMap).map(([key, fn]) => [
    key,
    fn().catch((err) => unavailableKpi(err.message)),
  ]);

  const results = await Promise.allSettled(entries.map(([, p]) => p));

  const kpis = {};
  entries.forEach(([key], i) => {
    const result = results[i];
    if (result.status === 'fulfilled') {
      kpis[key] = result.value;
    } else {
      kpis[key] = unavailableKpi(result.reason?.message ?? 'Unknown error');
    }
  });

  return kpis;
}
