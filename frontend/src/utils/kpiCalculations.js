/**
 * KPI calculation utilities — pure functions for in-memory Excel data.
 *
 * All functions receive the raw parsed Excel row array and return a
 * processed result suitable for charting / display.
 *
 * KPIs unavailable in volatile (Excel-only) mode return null so the UI
 * can render a graceful "No disponible en modo rápido" message.
 */

// ─── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Sum a numeric field, ignoring null / undefined / non-numeric values.
 * @param {object[]} rows
 * @param {string} field
 * @returns {number}
 */
function sumField(rows, field) {
  return rows.reduce((acc, row) => {
    const val = Number(row[field]);
    return acc + (isNaN(val) ? 0 : val);
  }, 0);
}

/**
 * Group by field and return count of rows.
 * @param {object[]} rows
 * @param {string} groupKey
 * @returns {{ name: string, value: number }[]}
 */
function groupByCount(rows, groupKey) {
  const map = {};
  for (const row of rows) {
    const key = String(row[groupKey] ?? 'Desconocido');
    map[key] = (map[key] ?? 0) + 1;
  }
  return Object.entries(map)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);
}

// ─── KPI calculations ────────────────────────────────────────────────────────

/**
 * AQL by style: total defects / total sample * 100 per style.
 *
 * @param {object[]} rows - Parsed Excel rows
 * @returns {{ style: string, aql: number }[]}
 */
export function calculateAqlByStyle(rows) {
  const map = {};
  for (const row of rows) {
    const style = String(row.style ?? 'Desconocido');
    const defects = Number(row.defects_total) || 0;
    const sample = Number(row.sample) || 0;
    if (!map[style]) map[style] = { defects: 0, sample: 0 };
    map[style].defects += defects;
    map[style].sample += sample;
  }
  return Object.entries(map).map(([style, { defects, sample }]) => ({
    style,
    aql: sample > 0 ? (defects / sample) * 100 : 0,
  }));
}

/**
 * AQL weekly: total defects / total sample * 100 per week.
 *
 * @param {object[]} rows
 * @returns {{ week: string, aql: number }[]}
 */
export function calculateAqlWeekly(rows) {
  const map = {};
  for (const row of rows) {
    const week = String(row.week ?? 'N/A');
    const defects = Number(row.defects_total) || 0;
    const sample = Number(row.sample) || 0;
    if (!map[week]) map[week] = { defects: 0, sample: 0 };
    map[week].defects += defects;
    map[week].sample += sample;
  }
  return Object.entries(map)
    .map(([week, { defects, sample }]) => ({
      week,
      aql: sample > 0 ? (defects / sample) * 100 : 0,
    }))
    .sort((a, b) => a.week.localeCompare(b.week, undefined, { numeric: true }));
}

/**
 * Total audited pieces per week (sum of the `sample` field).
 *
 * @param {object[]} rows
 * @returns {{ week: string, pieces: number }[]}
 */
export function calculateAuditedPieces(rows) {
  const map = {};
  for (const row of rows) {
    const week = String(row.week ?? 'N/A');
    const sample = Number(row.sample) || 0;
    map[week] = (map[week] ?? 0) + sample;
  }
  return Object.entries(map)
    .map(([week, pieces]) => ({ week, pieces }))
    .sort((a, b) => a.week.localeCompare(b.week, undefined, { numeric: true }));
}

/**
 * Acceptance / Rejection rate per production line (team field).
 * Returns pass rate = accepted / (accepted + rejected) * 100.
 *
 * @param {object[]} rows
 * @returns {{ line: string, passRate: number, accepted: number, rejected: number }[]}
 */
export function calculateAcReRateByLine(rows) {
  const map = {};
  for (const row of rows) {
    const line = String(row.team ?? 'Desconocida');
    const accepted = Number(row.accepted) || 0;
    const rejected = Number(row.rejected) || 0;
    if (!map[line]) map[line] = { accepted: 0, rejected: 0 };
    map[line].accepted += accepted;
    map[line].rejected += rejected;
  }
  return Object.entries(map).map(([line, { accepted, rejected }]) => {
    const total = accepted + rejected;
    return {
      line,
      passRate: total > 0 ? (accepted / total) * 100 : 0,
      accepted,
      rejected,
    };
  });
}

/**
 * Seconds rework — NOT available in Excel volatile mode.
 *
 * @param {object[]} _
 * @returns {null}
 */
// eslint-disable-next-line no-unused-vars
export function calculateSecondsRework(_) {
  return null;
}

/**
 * Performance by customer: accepted / sample * 100 per customer.
 *
 * @param {object[]} rows
 * @returns {{ customer: string, performance: number }[]}
 */
export function calculatePerformanceByCustomer(rows) {
  const map = {};
  for (const row of rows) {
    const customer = String(row.customer ?? 'Desconocido');
    const accepted = Number(row.accepted) || 0;
    const sample = Number(row.sample) || 0;
    if (!map[customer]) map[customer] = { accepted: 0, sample: 0 };
    map[customer].accepted += accepted;
    map[customer].sample += sample;
  }
  return Object.entries(map).map(([customer, { accepted, sample }]) => ({
    customer,
    performance: sample > 0 ? (accepted / sample) * 100 : 0,
  }));
}

/**
 * Performance by production line (team): accepted / sample * 100 per line.
 *
 * @param {object[]} rows
 * @returns {{ line: string, performance: number }[]}
 */
export function calculatePerformanceByLine(rows) {
  const map = {};
  for (const row of rows) {
    const line = String(row.team ?? 'Desconocida');
    const accepted = Number(row.accepted) || 0;
    const sample = Number(row.sample) || 0;
    if (!map[line]) map[line] = { accepted: 0, sample: 0 };
    map[line].accepted += accepted;
    map[line].sample += sample;
  }
  return Object.entries(map).map(([line, { accepted, sample }]) => ({
    line,
    performance: sample > 0 ? (accepted / sample) * 100 : 0,
  }));
}

/**
 * Top defects: uses defects_total as a single metric since Excel
 * does not contain individual defect type breakdowns.
 *
 * @param {object[]} rows
 * @returns {{ defectType: string, count: number }[]}
 */
export function calculateTopDefects(rows) {
  // Single aggregated "Total Defects" bucket
  const total = sumField(rows, 'defects_total');
  return [{ defectType: 'Total Defectos', count: total }];
}

/**
 * Fabric defects — NOT available in Excel volatile mode.
 *
 * @param {object[]} _
 * @returns {null}
 */
// eslint-disable-next-line no-unused-vars
export function calculateFabricDefects(_) {
  return null;
}

/**
 * Defects by style type — NOT available in Excel volatile mode.
 *
 * @param {object[]} _
 * @returns {null}
 */
// eslint-disable-next-line no-unused-vars
export function calculateDefectsByStyleType(_) {
  return null;
}

/**
 * Pass / reject distribution: count of rows with pass_or_fail = 'PASS' vs 'REJECT'.
 *
 * @param {object[]} rows
 * @returns {{ result: string, count: number }[]}
 */
export function calculatePassRejectDistribution(rows) {
  return groupByCount(rows, 'pass_or_fail');
}

/**
 * Rejected pieces evolution per week.
 *
 * @param {object[]} rows
 * @returns {{ week: string, rejected: number }[]}
 */
export function calculateRejectedEvolution(rows) {
  const map = {};
  for (const row of rows) {
    const week = String(row.week ?? 'N/A');
    const rejected = Number(row.rejected) || 0;
    map[week] = (map[week] ?? 0) + rejected;
  }
  return Object.entries(map)
    .map(([week, rejected]) => ({ week, rejected }))
    .sort((a, b) => a.week.localeCompare(b.week, undefined, { numeric: true }));
}

/**
 * Containers by state — NOT available in Excel volatile mode.
 *
 * @param {object[]} _
 * @returns {null}
 */
// eslint-disable-next-line no-unused-vars
export function calculateContainersByState(_) {
  return null;
}

/**
 * Overall defect rate: SUM(defects_total) / SUM(sample) * 100 across all rows.
 * Rows with zero sample are excluded from the sum to avoid Infinity.
 *
 * @param {object[]} rows
 * @returns {number}
 */
export function calculateDefectRate(rows) {
  let totalDefects = 0;
  let totalSample = 0;
  for (const row of rows) {
    const defects = Number(row.defects_total) || 0;
    const sample = Number(row.sample) || 0;
    if (sample > 0) {
      totalDefects += defects;
      totalSample += sample;
    }
  }
  return totalSample > 0 ? (totalDefects / totalSample) * 100 : 0;
}
