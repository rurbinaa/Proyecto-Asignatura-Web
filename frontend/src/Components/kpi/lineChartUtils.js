const isNumericLike = (value) => {
  if (typeof value === 'number') return Number.isFinite(value);
  if (typeof value === 'string' && value.trim() !== '') return Number.isFinite(Number(value));
  return false;
};

const WEEK_LABEL_REGEX = /^(\d{1,4})-W(\d{1,2})$/;

const parseWeekLabel = (value) => {
  if (typeof value !== 'string') return null;
  const match = value.trim().match(WEEK_LABEL_REGEX);
  if (!match) return null;

  return {
    year: Number(match[1]),
    week: Number(match[2]),
  };
};

const compareCategoricalX = (a, b) => {
  const parsedA = parseWeekLabel(a);
  const parsedB = parseWeekLabel(b);

  if (parsedA && parsedB) {
    if (parsedA.year !== parsedB.year) return parsedA.year - parsedB.year;
    return parsedA.week - parsedB.week;
  }

  return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: 'base' });
};

export function buildMergedLineData(series = []) {
  const rawXValues = series.flatMap((s) => s.data?.map((p) => p.x) || []);
  const useNumericXAxis = rawXValues.length > 0 && rawXValues.every(isNumericLike);

  const normalizedX = (value) => (useNumericXAxis ? Number(value) : value);

  const allXValues = [...new Set(rawXValues.map(normalizedX))].sort(
    useNumericXAxis ? (a, b) => a - b : compareCategoricalX
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
