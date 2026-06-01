/**
 * Volatile Filters — Dashboard allowlists, filter normalization, and identity serialization.
 *
 * This module provides the contract for how volatile (Fast Mode) dashboards
 * communicate filter intent to the backend. It is the single source of truth
 * for which filters each dashboard supports and how to build deterministic
 * cache/request identity strings.
 *
 * Dashboard allowlists (from design):
 *   - qcfa:        week, team, style, color, customer, batch, line_code, include_dual_lines
 *   - container:   customer
 *   - seconds_a4:  year, week, line, cut_num, style, color
 *   - seconds_general: week, customer, style, color, size, team, line_code, include_dual_lines
 *
 * date_range is explicitly deferred in v1 for ALL dashboards.
 */

/**
 * Dashboard allowlists — maps each dashboard to the set of filter keys
 * it supports in the volatile contract.
 * @type {Object<string, string[]>}
 */
export const VOLATILE_FILTER_ALLOWLISTS = {
  qcfa: [
    'week', 'team', 'style', 'color', 'customer', 'batch',
    'line_code', 'include_dual_lines',
  ],
  container: ['customer'],
  seconds_a4: ['year', 'week', 'line', 'cut_num', 'style', 'color'],
  seconds_general: [
    'week', 'customer', 'style', 'color', 'size', 'team',
    'line_code', 'include_dual_lines',
  ],
};

/**
 * Filter keys explicitly deferred for v1 delivery.
 * These MUST be stripped from volatile filter normalization.
 * @type {string[]}
 */
export const DEFERRED_FILTER_KEYS = ['date_range', 'from_date', 'to_date'];

/**
 * Normalize raw dashboard filter state to only include allowlisted keys
 * for the given volatile dashboard.
 *
 * Deferred keys (date_range, from_date, to_date) are always stripped.
 * Empty/null/undefined values are excluded.
 *
 * @param {string} dashboard - Dashboard key ('qcfa', 'container', 'seconds_a4', 'seconds_general')
 * @param {object} [filters={}] - Raw filter state from the dashboard
 * @returns {object} Normalized filter object with only supported, non-empty values
 */
export function normalizeVolatileFilters(dashboard, filters = {}) {
  const allowlist = VOLATILE_FILTER_ALLOWLISTS[dashboard];
  if (!allowlist) return {};

  const normalized = {};
  for (const key of allowlist) {
    const value = filters[key];
    if (value !== undefined && value !== null && value !== '') {
      normalized[key] = value;
    }
  }
  return normalized;
}

/**
 * Build a deterministic identity string for volatile cache/dedupe keys.
 *
 * Includes file identity (name, size, lastModified), dashboard, context,
 * and a JSON-serialized representation of normalized filters.
 *
 * Same inputs produce identical strings across calls. Different filter
 * combinations produce different strings. Deferred keys are automatically
 * stripped via normalizeVolatileFilters.
 *
 * @param {File} file - The volatile Excel file
 * @param {string} dashboard - Dashboard key
 * @param {string|null} [context] - Optional context ('plant' or 'customer')
 * @param {object} [filters={}] - Raw dashboard filter state
 * @returns {string} Stable identity string
 */
export function buildVolatileIdentity(file, dashboard, context, filters = {}) {
  const normalized = normalizeVolatileFilters(dashboard, filters);
  const sortedKeys = Object.keys(normalized).sort();
  const filterStr = sortedKeys.length > 0
    ? JSON.stringify(normalized, sortedKeys)
    : '';
  return `${file.name}:${file.size}:${file.lastModified}:${dashboard}:${context || ''}:${filterStr}`;
}
