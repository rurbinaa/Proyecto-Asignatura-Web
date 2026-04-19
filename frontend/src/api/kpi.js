import axiosClient from './axiosClient';
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

/**
 * Fetch KPI data from a specific endpoint.
 * @param {string} endpoint - KPI endpoint name (e.g. 'aql-by-style/')
 * @param {object} filters - Optional filters to apply
 * @returns {Promise<any>} JSON response data
 */
export async function fetchKpi(endpoint, filters = {}) {
  const queryString = buildQueryString(filters);
  const url = `/quality/kpis/${endpoint}${queryString}`;
  try {
    const res = await axiosClient.get(url);
    return res.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || `KPI fetch failed: ${error.response?.status}`);
  }
}

// ─── Individual KPI helpers ──────────────────────────────────────────────────

/**
 * Fetch filter options for dashboard filters.
 * Returns distinct values for week, team, style, color, customer, batch.
 * @returns {Promise<object>} Filter options object
 */
export async function getFilterOptions() {
  const url = `/quality/kpis/filter-options/`;
  try {
    const res = await axiosClient.get(url);
    return res.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || `Filter options fetch failed: ${error.response?.status}`);
  }
}

/** AQL grouped by style (defects/sample % per style). */
export async function getAqlByStyle(filters) {
  return fetchKpi('aql-by-style/', filters);
}

/** AQL trend by week — useful for control charts. */
export async function getAqlWeekly(filters) {
  return fetchKpi('aql-weekly/', filters);
}

/** Total audited pieces per week. */
export async function getAuditedPieces(filters) {
  return fetchKpi('audited-pieces/', filters);
}

/** Acceptance / Rejection rate per production line (team). */
export async function getAcReRateByLine(filters) {
  return fetchKpi('ac-re-rate-by-line/', filters);
}

/** Seconds spent on rework per inspection — requires capture data. */
export async function getSecondsRework(filters) {
  return fetchKpi('seconds-rework/', filters);
}

/** Performance (% accepted) grouped by customer. */
export async function getPerformanceByCustomer(filters) {
  return fetchKpi('performance-by-customer/', filters);
}

/** Performance (% accepted) grouped by production line (team). */
export async function getPerformanceByLine(filters) {
  return fetchKpi('performance-by-line/', filters);
}

/** Top defect types by frequency — requires capture defect types. */
export async function getTopDefects(filters) {
  return fetchKpi('top-defects/', filters);
}

/** Fabric defect distribution — requires fabric inspection data. */
export async function getFabricDefects(filters) {
  return fetchKpi('fabric-defects/', filters);
}

/** Defect breakdown by style type — requires capture defect types. */
export async function getDefectsByStyleType(filters) {
  return fetchKpi('defects-by-style-type/', filters);
}

/** Pass vs. reject count distribution across all inspections. */
export async function getPassRejectDistribution(filters) {
  return fetchKpi('pass-reject-distribution/', filters);
}

/** Rejected pieces evolution over weeks. */
export async function getRejectedEvolution(filters) {
  return fetchKpi('rejected-evolution/', filters);
}

/** Container inspection status counts. */
export async function getContainersByState(filters) {
  return fetchKpi('containers-by-state/', filters);
}

/** Overall defect rate (defects per 100 units inspected). */
export async function getDefectRate(filters) {
  return fetchKpi('defect-rate/', filters);
}

// ─── Volatile (Excel upload) KPIs ─────────────────────────────────────────────

/**
 * Map snake_case API response keys to camelCase for DashboardView compatibility.
 * This adapter ensures the volatile KPI response matches the live endpoints contract.
 * @param {object} response - Raw API response with snake_case keys
 * @returns {object} Response with camelCase keys (idempotent - existing camelCase keys preserved)
 */
function normalizeVolatileResponse(response) {
  if (!response || typeof response !== 'object') {
    return response;
  }

  const snakeToCamel = {
    aql_by_style: 'aqlByStyle',
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
    filter_options: 'filterOptions',
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
export async function fetchVolatileKpis(file) {
  const formData = new FormData();
  formData.append('file', file);
  try {
    const res = await axiosClient.post('/quality/kpis/volatile/', formData);
    return normalizeVolatileResponse(res.data);
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Failed to process Excel');
  }
}

// ─── Bulk fetch ───────────────────────────────────────────────────────────────

/**
 * Fetch all 14 KPIs in parallel, gracefully handling partial failures.
 * Returns an object keyed by KPI name.
 *
 * @param {object} filters - Optional shared filters for all KPIs
 * @returns {Promise<object>} { aqlByStyle, aqlWeekly, auditedPieces, ... }
 */
export async function fetchAllKpis(filters = {}) {
  const kpiMap = {
    aqlByStyle: getAqlByStyle,
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
  };

  const entries = Object.entries(kpiMap).map(([key, fn]) => [
    key,
    fn(filters).catch((err) => ({ error: err.message })),
  ]);

  const results = await Promise.allSettled(entries.map(([, p]) => p));

  /** @type {object} */
  const kpis = {};
  entries.forEach(([key], i) => {
    const result = results[i];
    if (result.status === 'fulfilled') {
      kpis[key] = result.value;
    } else {
      kpis[key] = { error: result.reason?.message ?? 'Unknown error' };
    }
  });

  return kpis;
}
