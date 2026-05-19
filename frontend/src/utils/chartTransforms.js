/**
 * Chart Transforms Utility
 * Pure data transformation functions that normalize API responses into chart-ready formats.
 * All functions are side-effect free, deterministic, and return null for error/null inputs.
 */

// ─── Chart-State Contract Helpers ──────────────────────────────────────────────

/**
 * Create a ready chart-state with data payload.
 * @template T
 * @param {T} data - The chart-ready data
 * @returns {{ status: 'ready', data: T }}
 */
export function readyState(data) {
  return { status: 'ready', data };
}

/**
 * Create an empty chart-state with a descriptive message.
 * @param {string} [message] - Custom message
 * @returns {{ status: 'empty', message: string }}
 */
export function emptyState(message) {
  return { status: 'empty', message: message || 'No data available for the selected filters' };
}

/**
 * Create an unavailable chart-state with reason and message.
 * @param {string} reason - Machine-readable reason code
 * @param {string} [message] - Human-readable message (falls back to reason)
 * @returns {{ status: 'unavailable', message: string, reason: string }}
 */
export function unavailableState(reason, message) {
  return {
    status: 'unavailable',
    reason,
    message: message || `Unavailable: ${reason}`,
  };
}

/**
 * Resolve raw API input into a chart-state object.
 * - Explicit unavailable objects pass through unchanged.
 * - null/undefined → empty
 * - Error objects → unavailable
 * - Transform result is empty → empty
 * - Transform result is non-empty → ready
 *
 * @template T
 * @param {any} input - Raw API response or DTO
 * @param {(input: any) => T[]} transformFn - Function that extracts chart-ready array
 * @returns {import('./chartTransforms').ChartState<T>}
 */
export function resolveChartState(input, transformFn) {
  // Pass through explicit unavailable objects
  if (input && typeof input === 'object' && input.status === 'unavailable') {
    return input;
  }
  // Null/undefined → empty
  if (input == null) {
    return emptyState();
  }
  // Error objects → unavailable
  if (input.error) {
    return unavailableState('api_error', input.error);
  }
  // Transform and check result
  const data = transformFn(input);
  if (!data || (Array.isArray(data) && data.length === 0)) {
    return emptyState();
  }
  return readyState(data);
}

/**
 * Transform pass/reject distribution for DonutChart.
 * API returns: [{name: "PASS", value: 85}, {name: "REJECT", value: 15}]
 */
export function transformPassReject(data) {
  if (!data || data.error) return null;
  const arr = data.result || data;
  if (!Array.isArray(arr)) return null;

  const passItem = arr.find((item) => item.name === 'PASS') || { name: 'PASS', value: 0 };
  const rejectItem = arr.find((item) => item.name === 'REJECT') || { name: 'REJECT', value: 0 };

  return [passItem, rejectItem];
}

/**
 * Transform AQL by team/line for BarChart horizontal.
 * API returns: {data: [{label: "Team-1", value: 1.5}, ...]}
 * Handles explicit unavailable pass-through for non-live modes.
 */
export function transformAqlByTeam(data) {
  // Pass through explicit unavailable objects
  if (data && typeof data === 'object' && data.status === 'unavailable') {
    return data;
  }
  if (!data || data.error) return null;
  const arr = data.data || data;
  return arr
    .map((item) => ({
      label: item.label,
      value: Number(item.value) || 0,
    }))
    .filter((item) => item.value > 0)
    .slice(0, 12);
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

function getLineSortParts(label) {
  const text = String(label ?? '').trim();
  const dualMatch = text.match(/^(\d+)-(\d+)$/);
  if (dualMatch) {
    return {
      start: Number(dualMatch[1]),
      end: Number(dualMatch[2]),
      isDual: 1,
      raw: text,
    };
  }

  const simpleMatch = text.match(/^(\d+)$/);
  if (simpleMatch) {
    return {
      start: Number(simpleMatch[1]),
      end: Number(simpleMatch[1]),
      isDual: 0,
      raw: text,
    };
  }

  return {
    start: Number.MAX_SAFE_INTEGER,
    end: Number.MAX_SAFE_INTEGER,
    isDual: 1,
    raw: text,
  };
}

function compareLineLabels(a, b) {
  const left = getLineSortParts(a);
  const right = getLineSortParts(b);

  if (left.start !== right.start) return left.start - right.start;
  if (left.isDual !== right.isDual) return left.isDual - right.isDual;
  if (left.end !== right.end) return left.end - right.end;
  return left.raw.localeCompare(right.raw, undefined, { numeric: true });
}

/**
 * Transform performance by line for horizontal BarChart.
 * API returns: [{label: "Line 1", value: 95.2}, ...]
 */
export function transformPerformanceByLine(data) {
  if (!data || data.error) return null;
  return (data.result || data)
    .map(item => ({
      label: item.label,
      value: item.value,
    }))
    .sort((a, b) => compareLineLabels(a.label, b.label));
}

/**
 * Transform top defects for horizontal BarChart.
 * API returns: [{label: "Loose Thread", value: 234}, ...]
 * Returns chart-state: ready | empty | unavailable
 */
export function transformTopDefects(data) {
  return resolveChartState(data, (d) => {
    const items = (d.result || d).map((item) => ({
      label: item.label,
      value: item.value,
    }));
    const total = items.reduce((sum, item) => sum + item.value, 0);
    return items.map((item) => ({
      ...item,
      percentage: total > 0 ? Number(((item.value / total) * 100).toFixed(1)) : 0,
    }));
  });
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
 * Returns chart-state: ready | empty | unavailable
 */
export function transformDefectsByStyleType(data) {
  return resolveChartState(data, (d) =>
    (d.result || d).map((item) => ({
      x: item.x,
      y: item.y,
      value: item.value,
    })),
  );
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
 * Transform defect composition for DonutChart.
 * Groups minor categories (beyond top 6) into "Other" slice with metadata.
 * API returns: [{name: "Loose Thread", value: 45}, {name: "Broken Stitch", value: 32}, ...]
 * Returns chart-state: ready | empty | unavailable
 */
export function transformDefectComposition(data) {
  return resolveChartState(data, (d) => {
    const raw = d.result || d;
    // Sort descending by value
    const sorted = [...raw].sort((a, b) => (b.value || 0) - (a.value || 0));
    const TOP_N = 6;

    if (sorted.length <= TOP_N) {
      return sorted.map((item) => ({ name: item.name, value: item.value }));
    }

    const top = sorted.slice(0, TOP_N);
    const rest = sorted.slice(TOP_N);

    const otherValue = rest.reduce((sum, item) => sum + (item.value || 0), 0);
    const otherSlice = {
      name: 'Other',
      value: otherValue,
      groupedItems: rest.map((item) => ({ name: item.name, value: item.value })),
    };

    return [
      ...top.map((item) => ({ name: item.name, value: item.value })),
      otherSlice,
    ];
  });
}

/**
 * Transform defect trend top 3 for LineChart.
 * API returns: [{name: "Loose Thread", data: [{x: 10, y: 5}, ...]}, ...]
 * Returns chart-state: ready | empty | unavailable
 */
export function transformDefectTrendTop3(data) {
  return resolveChartState(data, (d) =>
    (d.result || d).map((series) => ({
      name: series.name,
      data: series.data,
    })),
  );
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

/**
 * Transform Container executive summary for metric display.
 * API returns: [{label: "Total Containers", value: 150}, ...]
 * Converts to keyed object: {totalContainers: 150, averagePassRate: 87.5, ...}
 * Returns chart-state: ready | empty | unavailable
 */
export function transformContainerExecutiveSummary(data) {
  return resolveChartState(data, (d) => {
    const arr = Array.isArray(d) ? d : d.result || d;
    if (!Array.isArray(arr) || arr.length === 0) return [];

    const keyMap = {
      'Total Containers': 'totalContainers',
      'Average Pass Rate': 'averagePassRate',
      'Total Palettes Inspected': 'totalInspected',
      'Total Rejected Palettes': 'totalRejected',
    };

    const result = {};
    arr.forEach((item) => {
      const key = keyMap[item.label];
      if (key) {
        result[key] = typeof item.value === 'number' ? item.value : Number(item.value) || 0;
      }
    });

    return Object.keys(result).length > 0 ? [result] : [];
  });
}

/**
 * Transform worst containers for table/card display.
 * API returns: [{containerNumber, customer, passRate, rejectedPalettes, inspectionDate}]
 * Adds a unique `key` for React list rendering.
 * Returns chart-state: ready | empty | unavailable
 */
export function transformContainerWorstContainers(data) {
  return resolveChartState(data, (d) => {
    const arr = Array.isArray(d) ? d : d.result || d;
    if (!Array.isArray(arr) || arr.length === 0) return [];

    return arr.map((row, index) => ({
      containerNumber: row.containerNumber,
      customer: row.customer,
      passRate: typeof row.passRate === 'number' ? row.passRate : Number(row.passRate) || 0,
      rejectedPalettes: typeof row.rejectedPalettes === 'number' ? row.rejectedPalettes : Number(row.rejectedPalettes) || 0,
      inspectionDate: row.inspectionDate || '',
      key: `${row.containerNumber || `row-${index}`}`,
    }));
  });
}
