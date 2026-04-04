export function normalizeScalarMetric(value) {
  if (typeof value === 'number' && Number.isFinite(value)) return value;

  if (value && typeof value === 'object') {
    const nested = value.value;
    if (typeof nested === 'number' && Number.isFinite(nested)) return nested;
    if (typeof nested === 'string' && nested.trim() !== '' && Number.isFinite(Number(nested))) {
      return Number(nested);
    }
  }

  if (typeof value === 'string' && value.trim() !== '' && Number.isFinite(Number(value))) {
    return Number(value);
  }

  return null;
}
