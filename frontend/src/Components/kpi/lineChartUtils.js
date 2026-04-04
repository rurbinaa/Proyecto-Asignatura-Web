const isNumericLike = (value) => {
  if (typeof value === 'number') return Number.isFinite(value);
  if (typeof value === 'string' && value.trim() !== '') return Number.isFinite(Number(value));
  return false;
};

export function buildMergedLineData(series = []) {
  const rawXValues = series.flatMap((s) => s.data?.map((p) => p.x) || []);
  const useNumericXAxis = rawXValues.length > 0 && rawXValues.every(isNumericLike);

  const normalizedX = (value) => (useNumericXAxis ? Number(value) : value);

  const allXValues = [...new Set(rawXValues.map(normalizedX))].sort(
    useNumericXAxis ? (a, b) => a - b : undefined
  );

  const seriesValueMaps = series.map((s) => {
    const map = new Map();
    (s.data || []).forEach((point) => {
      map.set(normalizedX(point.x), point.y);
    });
    return map;
  });

  const mergedData = allXValues.map((x) => {
    const point = { x };
    series.forEach((s, index) => {
      point[s.name] = seriesValueMaps[index].has(x) ? seriesValueMaps[index].get(x) : null;
    });
    return point;
  });

  return { mergedData, allXValues, useNumericXAxis };
}
