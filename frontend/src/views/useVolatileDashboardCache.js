import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchVolatileDashboard } from '../api/kpi';
import { buildVolatileIdentity } from '../utils/volatileFilters';

/**
 * Module-level cache shared across all hook instances.
 * Key format: ``filename:fileSize:lastModified:dashboard:context``
 * @type {Map<string, { data: object, error: string|null }>}
 */
const volatileCache = new Map();

/**
 * Module-level pending-promises map for in-flight deduplication.
 * When two hook instances mount simultaneously with the same key,
 * they share a single in-flight promise instead of firing two requests.
 * @type {Map<string, Promise<object>>}
 */
const volatilePending = new Map();

/**
 * Build a stable cache key from file identity + dashboard + context + filters.
 * Uses the same identity function as kpi.js for alignment.
 * @param {File|null} file
 * @param {string} dashboard
 * @param {string|null} [context]
 * @param {object} [filters={}]
 * @returns {string|null} Cache key or null if file is null.
 */
function buildCacheKey(file, dashboard, context, filters = {}) {
  if (!file) return null;
  return buildVolatileIdentity(file, dashboard, context, filters);
}

/**
 * useVolatileDashboardCache — In-memory cache for volatile (fast mode) KPI payloads.
 *
 * Prevents re-uploading the same Excel file when switching dashboard tabs.
 * The cache is keyed by ``file.name:file.size:file.lastModified + dashboard + context + filters``
 * so different filter combinations never share a cache entry.
 *
 * Usage in a dashboard component:
 * ```js
 * const { data, loading, error } = useVolatileDashboardCache(volatileFile, 'qcfa', 'plant', { week: '5' });
 * ```
 *
 * @param {File|null} file — The volatile Excel file, or null for live mode.
 * @param {string} dashboard — Dashboard key (``'qcfa'``, ``'container'``, etc.).
 * @param {string|null} [context] — Optional context (``'plant'`` or ``'customer'``).
 * @param {object} [filters={}] — Raw dashboard filter state (normalized internally).
 * @returns {{ data: object|null, loading: boolean, error: string|null }}
 */
export default function useVolatileDashboardCache(file, dashboard, context, filters = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const keyRef = useRef(null);
  const activeRequestRef = useRef(0);

  const cacheKey = buildCacheKey(file, dashboard, context, filters);

  const fetchData = useCallback(async (key) => {
    const requestId = ++activeRequestRef.current;
    setLoading(true);
    setError(null);

    try {
      // In-flight deduplication: reuse existing promise if another hook
      // instance is already fetching the same key
      let promise;
      if (volatilePending.has(key)) {
        promise = volatilePending.get(key);
      } else {
        promise = fetchVolatileDashboard(file, dashboard, context, filters);
        volatilePending.set(key, promise);
        // .catch(() => {}) suppresses the forwarded rejection on the finally()-returned promise.
        // The actual rejection is caught by the try/catch below.
        promise.finally(() => {
          if (volatilePending.get(key) === promise) {
            volatilePending.delete(key);
          }
        }).catch(() => {});
      }

      const result = await promise;
      // Only commit if this request is still the active one
      if (requestId === activeRequestRef.current) {
        volatileCache.set(key, { data: result, error: null });
        setData(result);
      }
    } catch (err) {
      if (requestId === activeRequestRef.current) {
        const msg = err.message || 'Failed to process Excel';
        volatileCache.set(key, { data: null, error: msg });
        setError(msg);
      }
    } finally {
      if (requestId === activeRequestRef.current) {
        setLoading(false);
      }
    }
  }, [file, dashboard, context, filters]);

  useEffect(() => {
    // No file → live mode, clear state
    if (!file || !cacheKey) {
      /* eslint-disable react-hooks/set-state-in-effect */
      setData(null);
      setLoading(false);
      setError(null);
      /* eslint-enable react-hooks/set-state-in-effect */
      return;
    }

    // Check cache
    if (volatileCache.has(cacheKey)) {
      const cached = volatileCache.get(cacheKey);
      setData(cached.data);
      setError(cached.error);
      setLoading(false);
      keyRef.current = cacheKey;
      return;
    }

    // Avoid re-fetching if the key hasn't changed
    if (keyRef.current === cacheKey && data !== null) {
      return;
    }

    keyRef.current = cacheKey;
    fetchData(cacheKey);
  }, [cacheKey, file, fetchData, data]);

  return { data, loading, error };
}

/**
 * Clear the volatile cache and pending-promises map.
 * Useful for tests or when the user explicitly requests a fresh upload.
 */
export function clearVolatileCache() {
  volatileCache.clear();
  volatilePending.clear();
}
