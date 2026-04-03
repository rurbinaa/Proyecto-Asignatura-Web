const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
      if (Array.isArray(value)) {
        params.append(key, value.join(','));
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
  const url = `${API_BASE}/quality/kpis/${endpoint}${queryString}`;

  const response = await fetch(url);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `KPI fetch failed: ${response.status}`);
  }

  return response.json();
}

// ─── Individual KPI helpers ──────────────────────────────────────────────────

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
 * Fetch KPIs from an uploaded Excel file via the volatile endpoint.
 * The response has the same format as live KPI endpoints.
 * @param {File} file - The Excel file to process
 * @returns {Promise<object>} KPI results object (same shape as fetchAllKpis)
 */
export async function fetchVolatileKpis(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/quality/kpis/volatile/`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Upload failed' }));
    throw new Error(error.error || 'Failed to process Excel');
  }

  return response.json();
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
