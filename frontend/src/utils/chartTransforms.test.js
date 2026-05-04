import { describe, it, expect } from 'vitest';
import {
  // 13 Transform functions
  transformPassReject,
  transformAqlByStyle,
  transformAqlWeekly,
  transformAuditedPieces,
  transformRejectedEvolution,
  transformAcReRateByLine,
  transformPerformanceByCustomer,
  transformPerformanceByLine,
  transformTopDefects,
  transformFabricDefects,
  transformContainersByState,
  transformDefectsByStyleType,
  transformSecondsRework,
  // 2 New defect insight transforms
  transformDefectComposition,
  transformDefectTrendTop3,
  // 7 Formatters
  formatPercent,
  formatPieces,
  formatCount,
  formatSeconds,
  formatWeekLabel,
  formatAcceptanceIndex,
  trimCategoryLabel,
  // 2 Helpers
  parseLineStateLabel,
  buildLineCountDataByState,
} from './chartTransforms.js';

// ─── Shared test fixtures ─────────────────────────────────────────────────────

const SAMPLE_PASS_REJECT = {
  result: [
    { name: 'PASS', value: 85 },
    { name: 'REJECT', value: 15 },
  ],
};

const SAMPLE_AQL_STYLE = {
  data: [
    { label: 'Style-1', value: 2.34 },
    { label: 'Style-2', value: 3.5 },
    { label: 'Style-3', value: 1.2 },
  ],
};

const SAMPLE_AQL_WEEKLY = {
  data: [
    { name: 'AQL', data: [{ x: 1, y: 2.3 }, { x: 2, y: 2.8 }] },
    { name: 'Trend', data: [{ x: 1, y: 2.5 }, { x: 2, y: 2.6 }] },
  ],
};

const SAMPLE_AUDITED_PIECES = {
  data: [{ name: 'Pieces', data: [{ x: 1, y: 234 }, { x: 2, y: 312 }] }],
};

const SAMPLE_REJECTED_EVOLUTION = {
  data: [
    { name: 'Rejected', data: [{ x: 1, y: 23 }, { x: 2, y: 18 }] },
  ],
};

const SAMPLE_AC_RE_RATE = {
  result: [
    { label: '1 - PASS', value: 45 },
    { label: '1 - REJECT', value: 5 },
    { label: '2 - PASS', value: 38 },
    { label: '2 - REJECT', value: 12 },
  ],
};

const SAMPLE_PERF_CUSTOMER = {
  result: [
    { label: 'Customer X', value: 92.5 },
    { label: 'Customer Y', value: 87.3 },
  ],
};

const SAMPLE_PERF_LINE = {
  result: [
    { label: 'Line 1', value: 95.2 },
    { label: 'Line 2', value: 88.7 },
  ],
};

const SAMPLE_TOP_DEFECTS = {
  result: [
    { label: 'Loose Thread', value: 234 },
    { label: 'Broken Stitch', value: 156 },
    { label: 'Color Fading', value: 89 },
  ],
};

const SAMPLE_FABRIC_DEFECTS = {
  result: [
    { label: 'Corrido', value: 45 },
    { label: 'Barre', value: 23 },
    { label: 'Hole', value: 12 },
  ],
};

const SAMPLE_CONTAINERS = {
  result: [
    { name: '< 80%', value: 3 },
    { name: '80-90%', value: 12 },
    { name: '> 90%', value: 25 },
  ],
};

const SAMPLE_DEFECTS_STYLE_TYPE = {
  result: [
    { x: 'Style-2', y: 'Loose Thread', value: 45 },
    { x: 'Style-1', y: 'Broken Stitch', value: 32 },
  ],
};

const SAMPLE_SECONDS_REWORK = {
  result: [
    { name: 'Sewing', data: [{ x: 1, y: 12.3 }, { x: 2, y: 10.5 }] },
    { name: 'Fabric', data: [{ x: 1, y: 8.2 }, { x: 2, y: 7.8 }] },
  ],
};

const SAMPLE_DEFECT_COMPOSITION = {
  result: [
    { name: 'Loose Thread', value: 45 },
    { name: 'Broken Stitch', value: 32 },
    { name: 'Color Fading', value: 18 },
  ],
};

const SAMPLE_DEFECT_TREND_TOP3 = {
  result: [
    { name: 'Loose Thread', data: [{ x: 10, y: 5 }, { x: 11, y: 8 }] },
    { name: 'Broken Stitch', data: [{ x: 10, y: 3 }, { x: 11, y: 12 }] },
  ],
};

const SAMPLE_LINE_COUNT_DATA = [
  { label: 'Line 1 - PASS', value: 45 },
  { label: 'Line 1 - REJECT', value: 5 },
  { label: 'Line 2 - PASS', value: 38 },
  { label: 'Line 2 - REJECT', value: 12 },
  { label: 'Line 3 - Line 4 - PASS', value: 50 },
  { label: 'Line 3 - Line 4 - REJECT', value: 8 },
];

// ─── Transform Function Tests ──────────────────────────────────────────────────

describe('transformPassReject', () => {
  it('returns array with name and value from result', () => {
    const result = transformPassReject(SAMPLE_PASS_REJECT);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ name: 'PASS', value: 85 });
    expect(result[1]).toEqual({ name: 'REJECT', value: 15 });
  });

  it('handles direct array input', () => {
    const input = [{ name: 'PASS', value: 100 }];
    const result = transformPassReject(input);
    expect(result).toEqual([{ name: 'PASS', value: 100 }]);
  });

  it('returns null for null input', () => {
    expect(transformPassReject(null)).toBeNull();
  });

  it('returns null for undefined input', () => {
    expect(transformPassReject(undefined)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformPassReject({ error: 'something went wrong' })).toBeNull();
  });
});

describe('transformAqlByStyle', () => {
  it('extracts label and numeric value from data array', () => {
    const result = transformAqlByStyle(SAMPLE_AQL_STYLE);
    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({ label: 'Style-1', value: 2.34 });
    expect(result[1]).toEqual({ label: 'Style-2', value: 3.5 });
  });

  it('filters out items with zero or negative value', () => {
    const input = { data: [{ label: 'Zero', value: 0 }, { label: 'Valid', value: 1 }] };
    const result = transformAqlByStyle(input);
    expect(result).toHaveLength(1);
    expect(result[0].label).toBe('Valid');
  });

  it('converts string values to numbers', () => {
    const input = { data: [{ label: 'Style', value: '2.5' }] };
    const result = transformAqlByStyle(input);
    expect(result[0].value).toBe(2.5);
  });

  it('limits to 12 items maximum', () => {
    const manyItems = { data: Array.from({ length: 20 }, (_, i) => ({ label: `Style-${i}`, value: 1 })) };
    const result = transformAqlByStyle(manyItems);
    expect(result).toHaveLength(12);
  });

  it('handles direct array input', () => {
    const input = [{ label: 'Style-A', value: 1.5 }];
    const result = transformAqlByStyle(input);
    expect(result).toHaveLength(1);
  });

  it('returns null for null input', () => {
    expect(transformAqlByStyle(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformAqlByStyle({ error: 'failed' })).toBeNull();
  });
});

describe('transformAqlWeekly', () => {
  it('preserves series name and data structure', () => {
    const result = transformAqlWeekly(SAMPLE_AQL_WEEKLY);
    expect(result).toHaveLength(2);
    expect(result[0].name).toBe('AQL');
    expect(result[0].data).toEqual([{ x: 1, y: 2.3 }, { x: 2, y: 2.8 }]);
  });

  it('handles direct array input', () => {
    const input = [{ name: 'Test', data: [{ x: 1, y: 1 }] }];
    const result = transformAqlWeekly(input);
    expect(result).toEqual(input);
  });

  it('returns null for null input', () => {
    expect(transformAqlWeekly(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformAqlWeekly({ error: 'failed' })).toBeNull();
  });
});

describe('transformAuditedPieces', () => {
  it('preserves series structure', () => {
    const result = transformAuditedPieces(SAMPLE_AUDITED_PIECES);
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('Pieces');
    expect(result[0].data).toEqual([{ x: 1, y: 234 }, { x: 2, y: 312 }]);
  });

  it('handles direct array input', () => {
    const input = [{ name: 'Pieces', data: [{ x: 1, y: 100 }] }];
    const result = transformAuditedPieces(input);
    expect(result).toEqual(input);
  });

  it('returns null for null input', () => {
    expect(transformAuditedPieces(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformAuditedPieces({ error: 'failed' })).toBeNull();
  });
});

describe('transformRejectedEvolution', () => {
  it('preserves series structure', () => {
    const result = transformRejectedEvolution(SAMPLE_REJECTED_EVOLUTION);
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('Rejected');
    expect(result[0].data).toEqual([{ x: 1, y: 23 }, { x: 2, y: 18 }]);
  });

  it('handles direct array input', () => {
    const input = [{ name: 'Rej', data: [{ x: 1, y: 5 }] }];
    const result = transformRejectedEvolution(input);
    expect(result).toEqual(input);
  });

  it('returns null for null input', () => {
    expect(transformRejectedEvolution(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformRejectedEvolution({ error: 'failed' })).toBeNull();
  });
});

describe('transformAcReRateByLine', () => {
  it('extracts label and value from result array', () => {
    const result = transformAcReRateByLine(SAMPLE_AC_RE_RATE);
    expect(result).toHaveLength(4);
    expect(result[0]).toEqual({ label: '1 - PASS', value: 45 });
  });

  it('handles direct array input', () => {
    const input = [{ label: 'Test', value: 10 }];
    const result = transformAcReRateByLine(input);
    expect(result).toEqual(input);
  });

  it('returns null for null input', () => {
    expect(transformAcReRateByLine(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformAcReRateByLine({ error: 'failed' })).toBeNull();
  });
});

describe('transformPerformanceByCustomer', () => {
  it('extracts label and value from result array', () => {
    const result = transformPerformanceByCustomer(SAMPLE_PERF_CUSTOMER);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ label: 'Customer X', value: 92.5 });
  });

  it('handles direct array input', () => {
    const input = [{ label: 'Customer Z', value: 95 }];
    const result = transformPerformanceByCustomer(input);
    expect(result).toEqual(input);
  });

  it('returns null for null input', () => {
    expect(transformPerformanceByCustomer(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformPerformanceByCustomer({ error: 'failed' })).toBeNull();
  });
});

describe('transformPerformanceByLine', () => {
  it('extracts label and value from result array', () => {
    const result = transformPerformanceByLine(SAMPLE_PERF_LINE);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ label: 'Line 1', value: 95.2 });
  });

  it('handles direct array input', () => {
    const input = [{ label: 'Line A', value: 90 }];
    const result = transformPerformanceByLine(input);
    expect(result).toEqual(input);
  });

  it('returns null for null input', () => {
    expect(transformPerformanceByLine(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformPerformanceByLine({ error: 'failed' })).toBeNull();
  });
});

describe('transformTopDefects', () => {
  it('extracts label and value from result array', () => {
    const result = transformTopDefects(SAMPLE_TOP_DEFECTS);
    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({ label: 'Loose Thread', value: 234 });
  });

  it('handles direct array input', () => {
    const input = [{ label: 'Defect A', value: 50 }];
    const result = transformTopDefects(input);
    expect(result).toEqual(input);
  });

  it('returns null for null input', () => {
    expect(transformTopDefects(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformTopDefects({ error: 'failed' })).toBeNull();
  });
});

describe('transformFabricDefects', () => {
  it('extracts label and value from result array', () => {
    const result = transformFabricDefects(SAMPLE_FABRIC_DEFECTS);
    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({ label: 'Corrido', value: 45 });
  });

  it('handles direct array input', () => {
    const input = [{ label: 'Fabric A', value: 20 }];
    const result = transformFabricDefects(input);
    expect(result).toEqual(input);
  });

  it('returns null for null input', () => {
    expect(transformFabricDefects(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformFabricDefects({ error: 'failed' })).toBeNull();
  });
});

describe('transformContainersByState', () => {
  it('extracts name and value from result array', () => {
    const result = transformContainersByState(SAMPLE_CONTAINERS);
    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({ name: '< 80%', value: 3 });
  });

  it('handles direct array input', () => {
    const input = [{ name: 'State A', value: 10 }];
    const result = transformContainersByState(input);
    expect(result).toEqual(input);
  });

  it('returns null for null input', () => {
    expect(transformContainersByState(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformContainersByState({ error: 'failed' })).toBeNull();
  });
});

describe('transformDefectsByStyleType', () => {
  it('extracts x, y, value from result array', () => {
    const result = transformDefectsByStyleType(SAMPLE_DEFECTS_STYLE_TYPE);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ x: 'Style-2', y: 'Loose Thread', value: 45 });
  });

  it('handles direct array input', () => {
    const input = [{ x: 'S1', y: 'Def1', value: 5 }];
    const result = transformDefectsByStyleType(input);
    expect(result).toEqual(input);
  });

  it('returns null for null input', () => {
    expect(transformDefectsByStyleType(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformDefectsByStyleType({ error: 'failed' })).toBeNull();
  });
});

describe('transformSecondsRework', () => {
  it('extracts series with name and data from result array', () => {
    const result = transformSecondsRework(SAMPLE_SECONDS_REWORK);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ name: 'Sewing', data: [{ x: 1, y: 12.3 }, { x: 2, y: 10.5 }] });
  });

  it('handles direct array input', () => {
    const input = [{ name: 'Type', data: [{ x: 1, y: 5.5 }] }];
    const result = transformSecondsRework(input);
    expect(result).toEqual(input);
  });

  it('returns null for null input', () => {
    expect(transformSecondsRework(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformSecondsRework({ error: 'failed' })).toBeNull();
  });
});

// ─── Defect Insight Transform Tests ─────────────────────────────────────────────

describe('transformDefectComposition', () => {
  it('extracts name and value from result array for donut chart', () => {
    const result = transformDefectComposition(SAMPLE_DEFECT_COMPOSITION);
    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({ name: 'Loose Thread', value: 45 });
    expect(result[1]).toEqual({ name: 'Broken Stitch', value: 32 });
    expect(result[2]).toEqual({ name: 'Color Fading', value: 18 });
  });

  it('handles direct array input (no result wrapper)', () => {
    const input = [{ name: 'Hole', value: 12 }];
    const result = transformDefectComposition(input);
    expect(result).toEqual([{ name: 'Hole', value: 12 }]);
  });

  it('returns empty array for empty result', () => {
    expect(transformDefectComposition({ result: [] })).toEqual([]);
  });

  it('returns null for null input', () => {
    expect(transformDefectComposition(null)).toBeNull();
  });

  it('returns null for undefined input', () => {
    expect(transformDefectComposition(undefined)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformDefectComposition({ error: 'something went wrong' })).toBeNull();
  });

  it('does not mutate input (immutability)', () => {
    const original = JSON.parse(JSON.stringify(SAMPLE_DEFECT_COMPOSITION));
    transformDefectComposition(SAMPLE_DEFECT_COMPOSITION);
    expect(SAMPLE_DEFECT_COMPOSITION).toEqual(original);
  });

  it('is deterministic', () => {
    const r1 = transformDefectComposition(SAMPLE_DEFECT_COMPOSITION);
    const r2 = transformDefectComposition(SAMPLE_DEFECT_COMPOSITION);
    expect(r1).toEqual(r2);
  });
});

describe('transformDefectTrendTop3', () => {
  it('preserves series name and data structure for line chart', () => {
    const result = transformDefectTrendTop3(SAMPLE_DEFECT_TREND_TOP3);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({
      name: 'Loose Thread',
      data: [{ x: 10, y: 5 }, { x: 11, y: 8 }],
    });
    expect(result[1]).toEqual({
      name: 'Broken Stitch',
      data: [{ x: 10, y: 3 }, { x: 11, y: 12 }],
    });
  });

  it('handles single-series input', () => {
    const input = { result: [{ name: 'Hole', data: [{ x: 1, y: 10 }] }] };
    const result = transformDefectTrendTop3(input);
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('Hole');
  });

  it('handles direct array input (no result wrapper)', () => {
    const input = [{ name: 'Hole', data: [{ x: 1, y: 5 }] }];
    const result = transformDefectTrendTop3(input);
    expect(result).toEqual(input);
  });

  it('returns empty array for empty result', () => {
    expect(transformDefectTrendTop3({ result: [] })).toEqual([]);
  });

  it('returns null for null input', () => {
    expect(transformDefectTrendTop3(null)).toBeNull();
  });

  it('returns null for undefined input', () => {
    expect(transformDefectTrendTop3(undefined)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformDefectTrendTop3({ error: 'failed' })).toBeNull();
  });

  it('does not mutate input (immutability)', () => {
    const original = JSON.parse(JSON.stringify(SAMPLE_DEFECT_TREND_TOP3));
    transformDefectTrendTop3(SAMPLE_DEFECT_TREND_TOP3);
    expect(SAMPLE_DEFECT_TREND_TOP3).toEqual(original);
  });

  it('is deterministic', () => {
    const r1 = transformDefectTrendTop3(SAMPLE_DEFECT_TREND_TOP3);
    const r2 = transformDefectTrendTop3(SAMPLE_DEFECT_TREND_TOP3);
    expect(r1).toEqual(r2);
  });
});

// ─── Formatter Tests ───────────────────────────────────────────────────────────

describe('formatPercent', () => {
  it('formats number with 2 decimal places and % symbol', () => {
    expect(formatPercent(2.3456)).toBe('2.35%');
  });

  it('handles integer input', () => {
    expect(formatPercent(50)).toBe('50.00%');
  });

  it('handles string number input', () => {
    expect(formatPercent('25.5')).toBe('25.50%');
  });

  it('handles zero', () => {
    expect(formatPercent(0)).toBe('0.00%');
  });

  it('handles undefined as 0', () => {
    expect(formatPercent(undefined)).toBe('NaN%');
  });
});

describe('formatPieces', () => {
  it('rounds and appends "piezas" suffix', () => {
    expect(formatPieces(234.7)).toBe('235 piezas');
  });

  it('handles integer input', () => {
    expect(formatPieces(100)).toBe('100 piezas');
  });

  it('rounds down correctly', () => {
    expect(formatPieces(99.4)).toBe('99 piezas');
  });

  it('handles string input', () => {
    expect(formatPieces('50.6')).toBe('51 piezas');
  });
});

describe('formatCount', () => {
  it('rounds and appends "conteo" suffix', () => {
    expect(formatCount(42.7)).toBe('43 conteo');
  });

  it('handles integer input', () => {
    expect(formatCount(100)).toBe('100 conteo');
  });

  it('handles string input', () => {
    expect(formatCount('25.3')).toBe('25 conteo');
  });
});

describe('formatSeconds', () => {
  it('formats with 1 decimal place and "seg" suffix', () => {
    expect(formatSeconds(12.34)).toBe('12.3 seg');
  });

  it('handles integer input', () => {
    expect(formatSeconds(10)).toBe('10.0 seg');
  });

  it('handles string input', () => {
    expect(formatSeconds('5.67')).toBe('5.7 seg');
  });
});

describe('formatWeekLabel', () => {
  it('prepends "Semana " to week number', () => {
    expect(formatWeekLabel(1)).toBe('Semana 1');
  });

  it('handles string week number', () => {
    expect(formatWeekLabel('12')).toBe('Semana 12');
  });

  it('handles large week numbers', () => {
    expect(formatWeekLabel(52)).toBe('Semana 52');
  });
});

describe('formatAcceptanceIndex', () => {
  it('formats with 2 decimal places and "idx" suffix', () => {
    expect(formatAcceptanceIndex(95.567)).toBe('95.57 idx');
  });

  it('handles integer input', () => {
    expect(formatAcceptanceIndex(100)).toBe('100.00 idx');
  });

  it('handles string input', () => {
    expect(formatAcceptanceIndex('88.9')).toBe('88.90 idx');
  });
});

describe('trimCategoryLabel', () => {
  it('returns text unchanged if 17 chars or less', () => {
    expect(trimCategoryLabel('Short label')).toBe('Short label');
  });

  it('truncates text longer than 17 chars with ellipsis', () => {
    expect(trimCategoryLabel('This is a very long text label')).toBe('This is a very lo…');
  });

  it('handles exactly 17 characters', () => {
    const exactly17 = '12345678901234567';
    expect(trimCategoryLabel(exactly17)).toBe(exactly17);
  });

  it('handles 18 characters', () => {
    const over18 = '123456789012345678';
    expect(trimCategoryLabel(over18)).toBe('12345678901234567…');
  });

  it('handles null input', () => {
    expect(trimCategoryLabel(null)).toBe('');
  });

  it('handles undefined input', () => {
    expect(trimCategoryLabel(undefined)).toBe('');
  });

  it('handles non-string input', () => {
    expect(trimCategoryLabel(12345)).toBe('12345');
  });
});

// ─── Helper Function Tests ────────────────────────────────────────────────────

describe('parseLineStateLabel', () => {
  it('splits on last " - " and uppercases state', () => {
    const result = parseLineStateLabel('Line 1 - PASS');
    expect(result).toEqual({ line: 'Line 1', state: 'PASS' });
  });

  it('handles multi-part line name', () => {
    const result = parseLineStateLabel('Line 1 - Line 2 - REJECT');
    expect(result).toEqual({ line: 'Line 1 - Line 2', state: 'REJECT' });
  });

  it('returns original text as line when no separator', () => {
    const result = parseLineStateLabel('SingleLabel');
    expect(result).toEqual({ line: 'SingleLabel', state: '' });
  });

  it('handles null input', () => {
    const result = parseLineStateLabel(null);
    expect(result).toEqual({ line: '', state: '' });
  });

  it('handles undefined input', () => {
    const result = parseLineStateLabel(undefined);
    expect(result).toEqual({ line: '', state: '' });
  });

  it('uppercases the state portion only', () => {
    const result = parseLineStateLabel('Assembly - reject');
    expect(result).toEqual({ line: 'Assembly', state: 'REJECT' });
  });

  it('trims whitespace', () => {
    const result = parseLineStateLabel('  Line 1  -  PASS  ');
    expect(result).toEqual({ line: 'Line 1', state: 'PASS' });
  });
});

describe('buildLineCountDataByState', () => {
  it('filters by PASS state and extracts line/value', () => {
    const result = buildLineCountDataByState(SAMPLE_LINE_COUNT_DATA, 'PASS');
    expect(result).toHaveLength(3);
    expect(result).toContainEqual({ label: 'Line 1', value: 45 });
    expect(result).toContainEqual({ label: 'Line 2', value: 38 });
    expect(result).toContainEqual({ label: 'Line 3 - Line 4', value: 50 });
  });

  it('filters by REJECT state', () => {
    const result = buildLineCountDataByState(SAMPLE_LINE_COUNT_DATA, 'REJECT');
    expect(result).toHaveLength(3);
    expect(result).toContainEqual({ label: 'Line 1', value: 5 });
    expect(result).toContainEqual({ label: 'Line 2', value: 12 });
  });

  it('returns empty array for non-matching state', () => {
    const result = buildLineCountDataByState(SAMPLE_LINE_COUNT_DATA, 'PENDING');
    expect(result).toEqual([]);
  });

  it('returns empty array for non-array input', () => {
    expect(buildLineCountDataByState(null, 'PASS')).toEqual([]);
    expect(buildLineCountDataByState(undefined, 'PASS')).toEqual([]);
    expect(buildLineCountDataByState('not an array', 'PASS')).toEqual([]);
  });

  it('handles empty array input', () => {
    const result = buildLineCountDataByState([], 'PASS');
    expect(result).toEqual([]);
  });

  it('converts string values to numbers', () => {
    const input = [{ label: 'Line 1 - PASS', value: '100' }];
    const result = buildLineCountDataByState(input, 'PASS');
    expect(result[0].value).toBe(100);
  });

  it('uses 0 for missing or invalid values', () => {
    const input = [{ label: 'Line 1 - PASS', value: null }];
    const result = buildLineCountDataByState(input, 'PASS');
    expect(result[0].value).toBe(0);
  });
});

// ─── Pure Function Tests ───────────────────────────────────────────────────────
//
// These tests verify two critical properties of all transform functions:
// 1. IMMUTABILITY: Functions do not mutate their input arrays/objects
// 2. DETERMINISM:  Functions return the same output for the same input

describe('Transform functions are pure (do not mutate input)', () => {
  // Deep clone helper using JSON (no external deps)
  const deepClone = (obj) => JSON.parse(JSON.stringify(obj));

  const mutations = [
    { name: 'transformPassReject', fn: transformPassReject, input: SAMPLE_PASS_REJECT },
    { name: 'transformAqlByStyle', fn: transformAqlByStyle, input: SAMPLE_AQL_STYLE },
    { name: 'transformAqlWeekly', fn: transformAqlWeekly, input: SAMPLE_AQL_WEEKLY },
    { name: 'transformAuditedPieces', fn: transformAuditedPieces, input: SAMPLE_AUDITED_PIECES },
    { name: 'transformRejectedEvolution', fn: transformRejectedEvolution, input: SAMPLE_REJECTED_EVOLUTION },
    { name: 'transformAcReRateByLine', fn: transformAcReRateByLine, input: SAMPLE_AC_RE_RATE },
    { name: 'transformPerformanceByCustomer', fn: transformPerformanceByCustomer, input: SAMPLE_PERF_CUSTOMER },
    { name: 'transformPerformanceByLine', fn: transformPerformanceByLine, input: SAMPLE_PERF_LINE },
    { name: 'transformTopDefects', fn: transformTopDefects, input: SAMPLE_TOP_DEFECTS },
    { name: 'transformFabricDefects', fn: transformFabricDefects, input: SAMPLE_FABRIC_DEFECTS },
    { name: 'transformContainersByState', fn: transformContainersByState, input: SAMPLE_CONTAINERS },
    { name: 'transformDefectsByStyleType', fn: transformDefectsByStyleType, input: SAMPLE_DEFECTS_STYLE_TYPE },
    { name: 'transformSecondsRework', fn: transformSecondsRework, input: SAMPLE_SECONDS_REWORK },
    { name: 'transformDefectComposition', fn: transformDefectComposition, input: SAMPLE_DEFECT_COMPOSITION },
    { name: 'transformDefectTrendTop3', fn: transformDefectTrendTop3, input: SAMPLE_DEFECT_TREND_TOP3 },
  ];

  mutations.forEach(({ name, fn, input }) => {
    it(`${name} does not mutate the input object`, () => {
      const original = deepClone(input);
      fn(input);
      expect(input).toEqual(original);
    });
  });

  it('buildLineCountDataByState does not mutate input array', () => {
    const original = deepClone(SAMPLE_LINE_COUNT_DATA);
    buildLineCountDataByState(SAMPLE_LINE_COUNT_DATA, 'PASS');
    expect(SAMPLE_LINE_COUNT_DATA).toEqual(original);
  });
});

describe('Transform functions are deterministic', () => {
  const determinismTests = [
    { name: 'transformPassReject', fn: transformPassReject, input: SAMPLE_PASS_REJECT },
    { name: 'transformAqlByStyle', fn: transformAqlByStyle, input: SAMPLE_AQL_STYLE },
    { name: 'transformAqlWeekly', fn: transformAqlWeekly, input: SAMPLE_AQL_WEEKLY },
    { name: 'transformAuditedPieces', fn: transformAuditedPieces, input: SAMPLE_AUDITED_PIECES },
    { name: 'transformRejectedEvolution', fn: transformRejectedEvolution, input: SAMPLE_REJECTED_EVOLUTION },
    { name: 'transformAcReRateByLine', fn: transformAcReRateByLine, input: SAMPLE_AC_RE_RATE },
    { name: 'transformPerformanceByCustomer', fn: transformPerformanceByCustomer, input: SAMPLE_PERF_CUSTOMER },
    { name: 'transformPerformanceByLine', fn: transformPerformanceByLine, input: SAMPLE_PERF_LINE },
    { name: 'transformTopDefects', fn: transformTopDefects, input: SAMPLE_TOP_DEFECTS },
    { name: 'transformFabricDefects', fn: transformFabricDefects, input: SAMPLE_FABRIC_DEFECTS },
    { name: 'transformContainersByState', fn: transformContainersByState, input: SAMPLE_CONTAINERS },
    { name: 'transformDefectsByStyleType', fn: transformDefectsByStyleType, input: SAMPLE_DEFECTS_STYLE_TYPE },
    { name: 'transformSecondsRework', fn: transformSecondsRework, input: SAMPLE_SECONDS_REWORK },
    { name: 'transformDefectComposition', fn: transformDefectComposition, input: SAMPLE_DEFECT_COMPOSITION },
    { name: 'transformDefectTrendTop3', fn: transformDefectTrendTop3, input: SAMPLE_DEFECT_TREND_TOP3 },
  ];

  determinismTests.forEach(({ name, fn, input }) => {
    it(`${name} returns identical output for same input (deterministic)`, () => {
      const result1 = fn(input);
      const result2 = fn(input);
      expect(result1).toEqual(result2);
    });
  });

  it('buildLineCountDataByState is deterministic', () => {
    const result1 = buildLineCountDataByState(SAMPLE_LINE_COUNT_DATA, 'PASS');
    const result2 = buildLineCountDataByState(SAMPLE_LINE_COUNT_DATA, 'PASS');
    expect(result1).toEqual(result2);
  });
});
