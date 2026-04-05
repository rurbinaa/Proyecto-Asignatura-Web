/**
 * Chart Transforms Utility
 * Pure data transformation functions that normalize API responses into chart-ready formats.
 * All functions are side-effect free, deterministic, and return null for error/null inputs.
 */

/**
 * Transform pass/reject distribution for DonutChart.
 * API returns: [{name: "PASS", value: 85}, {name: "REJECT", value: 15}]
 */
export function transformPassReject(data) {
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
export function transformAqlByStyle(data) {
  if (!data || data.error) return null;
  const arr = data.data || data;
  return arr
    .map(item => ({
      label: item.label,
      value: Number(item.value) || 0,
    }))
    .filter((item) => item.value > 0)
    .slice(0, 12);
}

/**
 * Transform AQL weekly for LineChart.
 * API returns: [{name: "AQL", data: [{x: 1, y: 2.3}, ...]}, {name: "Trend", data: [...]}]
 */
export function transformAqlWeekly(data) {
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
export function transformAuditedPieces(data) {
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
export function transformRejectedEvolution(data) {
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
export function transformAcReRateByLine(data) {
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
export function transformPerformanceByCustomer(data) {
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
export function transformPerformanceByLine(data) {
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
export function transformTopDefects(data) {
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
export function transformFabricDefects(data) {
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
export function transformContainersByState(data) {
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
export function transformDefectsByStyleType(data) {
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
export function transformSecondsRework(data) {
  if (!data || data.error) return null;
  return (data.result || data).map(series => ({
    name: series.name,
    data: series.data,
  }));
}

/**
 * Format a numeric value as a percentage with 2 decimal places.
 * @param {number} value - The numeric value to format
 * @returns {string} Formatted percentage string (e.g., "2.35%")
 */
export const formatPercent = (value) => `${Number(value).toFixed(2)}%`;

/**
 * Format a numeric value as piece count with rounding.
 * @param {number} value - The numeric value to format
 * @returns {string} Formatted string (e.g., "235 piezas")
 */
export const formatPieces = (value) => `${Math.round(Number(value))} piezas`;

/**
 * Format a numeric value as a count.
 * @param {number} value - The numeric value to format
 * @returns {string} Formatted string (e.g., "42 conteo")
 */
export const formatCount = (value) => `${Math.round(Number(value))} conteo`;

/**
 * Format seconds with 1 decimal place.
 * @param {number} value - The numeric value to format
 * @returns {string} Formatted string (e.g., "12.3 seg")
 */
export const formatSeconds = (value) => `${Number(value).toFixed(1)} seg`;

/**
 * Format week label with "Semana" prefix.
 * @param {number} value - The week number
 * @returns {string} Formatted string (e.g., "Semana 1")
 */
export const formatWeekLabel = (value) => `Semana ${value}`;

/**
 * Format acceptance index with 2 decimal places.
 * @param {number} value - The numeric value to format
 * @returns {string} Formatted string (e.g., "95.00 idx")
 */
export const formatAcceptanceIndex = (value) => `${Number(value).toFixed(2)} idx`;

/**
 * Truncate category labels longer than 18 characters.
 * @param {string} value - The label to potentially truncate
 * @returns {string} Truncated label with ellipsis if needed
 */
export const trimCategoryLabel = (value) => {
  const text = String(value ?? '');
  return text.length > 17 ? `${text.slice(0, 17)}…` : text;
};

/**
 * Parse a combined line-state label into its components.
 * Splits on the last " - " and uppercases the state portion.
 * @param {string} label - Combined label (e.g., "Line 1 - Line 2 - PASS")
 * @returns {{line: string, state: string}} Parsed components
 */
export const parseLineStateLabel = (label) => {
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

/**
 * Build line count data filtered by target state.
 * @param {Array} data - Array of items with labels
 * @param {string} targetState - State to filter by (e.g., "PASS", "REJECT")
 * @returns {Array} Filtered and transformed data with {label, value}
 */
export const buildLineCountDataByState = (data, targetState) => {
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
