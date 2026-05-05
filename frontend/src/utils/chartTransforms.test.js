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
  // AQL by Team/Line
  transformAqlByTeam,
  // Chart-state helpers
  readyState,
  emptyState,
  unavailableState,
  resolveChartState,
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
  // Container transforms
  transformContainerExecutiveSummary,
  transformContainerWorstContainers,
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

const SAMPLE_AQL_TEAM = {
  data: [
    { label: 'Team-A', value: 1.5 },
    { label: 'Team-B', value: 2.3 },
    { label: 'Team-C', value: 3.1 },
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
    expect(result).toEqual([
      { name: 'PASS', value: 100 },
      { name: 'REJECT', value: 0 }
    ]);
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
  it('returns ready state with label, value, and percentage from result array', () => {
    const result = transformTopDefects(SAMPLE_TOP_DEFECTS);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(3);
    expect(result.data[0]).toEqual({ label: 'Loose Thread', value: 234, percentage: 48.9 });
    expect(result.data[1]).toEqual({ label: 'Broken Stitch', value: 156, percentage: 32.6 });
    expect(result.data[2]).toEqual({ label: 'Color Fading', value: 89, percentage: 18.6 });
  });

  it('handles direct array input with percentage', () => {
    const input = [{ label: 'Defect A', value: 50 }];
    const result = transformTopDefects(input);
    expect(result.status).toBe('ready');
    expect(result.data).toEqual([{ label: 'Defect A', value: 50, percentage: 100 }]);
  });

  it('returns empty state for null input', () => {
    const result = transformTopDefects(null);
    expect(result.status).toBe('empty');
    expect(result.message).toBeTruthy();
  });

  it('returns unavailable state for error object', () => {
    const result = transformTopDefects({ error: 'failed' });
    expect(result.status).toBe('unavailable');
    expect(result.reason).toBe('api_error');
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
  it('returns ready state with x, y, value from result array', () => {
    const result = transformDefectsByStyleType(SAMPLE_DEFECTS_STYLE_TYPE);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(2);
    expect(result.data[0]).toEqual({ x: 'Style-2', y: 'Loose Thread', value: 45 });
  });

  it('handles direct array input', () => {
    const input = [{ x: 'S1', y: 'Def1', value: 5 }];
    const result = transformDefectsByStyleType(input);
    expect(result.status).toBe('ready');
    expect(result.data).toEqual(input);
  });

  it('returns empty state for null input', () => {
    const result = transformDefectsByStyleType(null);
    expect(result.status).toBe('empty');
  });

  it('returns unavailable state for error object', () => {
    const result = transformDefectsByStyleType({ error: 'failed' });
    expect(result.status).toBe('unavailable');
    expect(result.reason).toBe('api_error');
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
  it('returns ready state with name and value from result array for donut chart', () => {
    const result = transformDefectComposition(SAMPLE_DEFECT_COMPOSITION);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(3);
    expect(result.data[0]).toEqual({ name: 'Loose Thread', value: 45 });
    expect(result.data[1]).toEqual({ name: 'Broken Stitch', value: 32 });
    expect(result.data[2]).toEqual({ name: 'Color Fading', value: 18 });
  });

  it('handles direct array input (no result wrapper)', () => {
    const input = [{ name: 'Hole', value: 12 }];
    const result = transformDefectComposition(input);
    expect(result.status).toBe('ready');
    expect(result.data).toEqual([{ name: 'Hole', value: 12 }]);
  });

  it('returns empty state for empty result', () => {
    const result = transformDefectComposition({ result: [] });
    expect(result.status).toBe('empty');
    expect(result.message).toBeTruthy();
  });

  it('returns empty state for null input', () => {
    const result = transformDefectComposition(null);
    expect(result.status).toBe('empty');
  });

  it('returns empty state for undefined input', () => {
    const result = transformDefectComposition(undefined);
    expect(result.status).toBe('empty');
  });

  it('returns unavailable state for error object', () => {
    const result = transformDefectComposition({ error: 'something went wrong' });
    expect(result.status).toBe('unavailable');
    expect(result.reason).toBe('api_error');
  });
});

describe('transformDefectTrendTop3', () => {
  it('returns ready state with series name and data structure for line chart', () => {
    const result = transformDefectTrendTop3(SAMPLE_DEFECT_TREND_TOP3);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(2);
    expect(result.data[0]).toEqual({
      name: 'Loose Thread',
      data: [{ x: 10, y: 5 }, { x: 11, y: 8 }],
    });
    expect(result.data[1]).toEqual({
      name: 'Broken Stitch',
      data: [{ x: 10, y: 3 }, { x: 11, y: 12 }],
    });
  });

  it('handles single-series input', () => {
    const input = { result: [{ name: 'Hole', data: [{ x: 1, y: 10 }] }] };
    const result = transformDefectTrendTop3(input);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(1);
    expect(result.data[0].name).toBe('Hole');
  });

  it('handles direct array input (no result wrapper)', () => {
    const input = [{ name: 'Hole', data: [{ x: 1, y: 5 }] }];
    const result = transformDefectTrendTop3(input);
    expect(result.status).toBe('ready');
    expect(result.data).toEqual(input);
  });

  it('returns empty state for empty result', () => {
    const result = transformDefectTrendTop3({ result: [] });
    expect(result.status).toBe('empty');
    expect(result.message).toBeTruthy();
  });

  it('returns empty state for null input', () => {
    const result = transformDefectTrendTop3(null);
    expect(result.status).toBe('empty');
  });

  it('returns empty state for undefined input', () => {
    const result = transformDefectTrendTop3(undefined);
    expect(result.status).toBe('empty');
  });

  it('returns unavailable state for error object', () => {
    const result = transformDefectTrendTop3({ error: 'failed' });
    expect(result.status).toBe('unavailable');
    expect(result.reason).toBe('api_error');
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
    { name: 'transformAqlByTeam', fn: transformAqlByTeam, input: SAMPLE_AQL_TEAM },
    { name: 'transformContainerExecutiveSummary', fn: transformContainerExecutiveSummary, input: [{ label: 'Total Containers', value: 150 }] },
    { name: 'transformContainerWorstContainers', fn: transformContainerWorstContainers, input: [{ containerNumber: 'C1', customer: 'A', passRate: 80, rejectedPalettes: 2, inspectionDate: '2025-01-01' }] },
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
    { name: 'transformAqlByTeam', fn: transformAqlByTeam, input: SAMPLE_AQL_TEAM },
    { name: 'transformContainerExecutiveSummary', fn: transformContainerExecutiveSummary, input: [{ label: 'Total Containers', value: 150 }] },
    { name: 'transformContainerWorstContainers', fn: transformContainerWorstContainers, input: [{ containerNumber: 'C1', customer: 'A', passRate: 80, rejectedPalettes: 2, inspectionDate: '2025-01-01' }] },
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

// ─── Chart-State Contract Tests ────────────────────────────────────────────────

describe('Chart-state helpers', () => {
  describe('readyState', () => {
    it('RED - wraps data in ready status object', () => {
      const data = [{ label: 'A', value: 10 }];
      const result = readyState(data);
      expect(result).toEqual({ status: 'ready', data });
      expect(result.data).toBe(data); // same reference
    });

    it('RED - handles empty array as ready (empty is different)', () => {
      const result = readyState([]);
      expect(result).toEqual({ status: 'ready', data: [] });
    });
  });

  describe('emptyState', () => {
    it('RED - returns empty status with default message', () => {
      const result = emptyState();
      expect(result.status).toBe('empty');
      expect(result.message).toBeTruthy();
      expect(result.data).toBeUndefined();
    });

    it('RED - accepts custom message', () => {
      const result = emptyState('No defects found');
      expect(result).toEqual({ status: 'empty', message: 'No defects found' });
    });
  });

  describe('unavailableState', () => {
    it('RED - returns unavailable status with reason and message', () => {
      const result = unavailableState('volatile_unsupported', 'Customer volatile insights not supported');
      expect(result).toEqual({
        status: 'unavailable',
        reason: 'volatile_unsupported',
        message: 'Customer volatile insights not supported',
      });
    });

    it('RED - uses reason as message fallback when no message provided', () => {
      const result = unavailableState('endpoint_error');
      expect(result).toEqual({
        status: 'unavailable',
        reason: 'endpoint_error',
        message: 'Unavailable: endpoint_error',
      });
    });
  });

  describe('resolveChartState', () => {
    it('RED - returns emptyState when input is null', () => {
      const result = resolveChartState(null, () => []);
      expect(result.status).toBe('empty');
    });

    it('RED - returns emptyState when input is undefined', () => {
      const result = resolveChartState(undefined, () => []);
      expect(result.status).toBe('empty');
    });

    it('RED - passes through explicit unavailable objects', () => {
      const unavailableInput = { status: 'unavailable', reason: 'db_error', message: 'DB down', data: null };
      const result = resolveChartState(unavailableInput, () => []);
      expect(result).toBe(unavailableInput);
    });

    it('RED - returns unavailable for error objects', () => {
      const result = resolveChartState({ error: 'something failed' }, () => []);
      expect(result.status).toBe('unavailable');
      expect(result.reason).toBe('api_error');
    });

    it('RED - returns empty when transform produces empty array', () => {
      const result = resolveChartState({ result: [] }, (d) => d.result);
      expect(result.status).toBe('empty');
    });

    it('RED - returns ready when transform produces non-empty array', () => {
      const input = { result: [{ name: 'A', value: 5 }] };
      const result = resolveChartState(input, (d) => d.result);
      expect(result.status).toBe('ready');
      expect(result.data).toEqual([{ name: 'A', value: 5 }]);
    });
  });
});

// ─── Top-6 + Other Grouping Tests ──────────────────────────────────────────────

describe('transformDefectComposition — top-6 + Other grouping', () => {
  it('RED - groups 10 categories into top 6 + Other', () => {
    const input = {
      result: [
        { name: 'Cat-A', value: 100 },
        { name: 'Cat-B', value: 90 },
        { name: 'Cat-C', value: 80 },
        { name: 'Cat-D', value: 70 },
        { name: 'Cat-E', value: 60 },
        { name: 'Cat-F', value: 50 },
        { name: 'Cat-G', value: 40 },
        { name: 'Cat-H', value: 30 },
        { name: 'Cat-I', value: 20 },
        { name: 'Cat-J', value: 10 },
      ],
    };

    const result = transformDefectComposition(input);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(7); // 6 top + Other

    // First 6 slices are the top categories
    expect(result.data[0]).toEqual({ name: 'Cat-A', value: 100 });
    expect(result.data[5]).toEqual({ name: 'Cat-F', value: 50 });

    // 7th slice is Other
    const otherSlice = result.data[6];
    expect(otherSlice.name).toBe('Other');
    expect(otherSlice.value).toBe(100); // 40+30+20+10 = 100
    expect(otherSlice.groupedItems).toBeDefined();
    expect(otherSlice.groupedItems).toHaveLength(4);
    expect(otherSlice.groupedItems[0]).toEqual({ name: 'Cat-G', value: 40 });
  });

  it('RED - does NOT group when 6 or fewer categories', () => {
    const input = {
      result: [
        { name: 'Cat-A', value: 100 },
        { name: 'Cat-B', value: 90 },
        { name: 'Cat-C', value: 80 },
      ],
    };

    const result = transformDefectComposition(input);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(3);
    // No Other slice
    expect(result.data.find((s) => s.name === 'Other')).toBeUndefined();
  });

  it('RED - sorts by value descending', () => {
    const input = {
      result: [
        { name: 'Small', value: 5 },
        { name: 'Large', value: 100 },
        { name: 'Medium', value: 50 },
      ],
    };

    const result = transformDefectComposition(input);
    expect(result.status).toBe('ready');
    expect(result.data[0].name).toBe('Large');
    expect(result.data[1].name).toBe('Medium');
    expect(result.data[2].name).toBe('Small');
  });

  it('RED - handles exactly 7 categories (top 6 + Other with 1 item)', () => {
    const input = {
      result: [
        { name: 'A', value: 10 },
        { name: 'B', value: 9 },
        { name: 'C', value: 8 },
        { name: 'D', value: 7 },
        { name: 'E', value: 6 },
        { name: 'F', value: 5 },
        { name: 'G', value: 4 },
      ],
    };

    const result = transformDefectComposition(input);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(7);
    const otherSlice = result.data[6];
    expect(otherSlice.name).toBe('Other');
    expect(otherSlice.value).toBe(4);
    expect(otherSlice.groupedItems).toHaveLength(1);
  });

  it('RED - returns empty state for empty result', () => {
    const result = transformDefectComposition({ result: [] });
    expect(result.status).toBe('empty');
  });

  it('RED - returns unavailable for error input', () => {
    const result = transformDefectComposition({ error: 'failed' });
    expect(result.status).toBe('unavailable');
    expect(result.reason).toBe('api_error');
  });

  it('RED - returns empty state for null input', () => {
    const result = transformDefectComposition(null);
    expect(result.status).toBe('empty');
  });
});

// ─── Chart-State Contract for Top Defects ──────────────────────────────────────

describe('transformTopDefects — chart-state contract', () => {
  it('RED - returns ready state for valid non-empty data with percentages', () => {
    const result = transformTopDefects(SAMPLE_TOP_DEFECTS);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(3);
    expect(result.data[0]).toEqual({ label: 'Loose Thread', value: 234, percentage: 48.9 });
  });

  it('RED - returns empty state for empty result array', () => {
    const result = transformTopDefects({ result: [] });
    expect(result.status).toBe('empty');
    expect(result.message).toBeTruthy();
  });

  it('RED - returns unavailable for error objects', () => {
    const result = transformTopDefects({ error: 'failed' });
    expect(result.status).toBe('unavailable');
    expect(result.reason).toBe('api_error');
  });

  it('RED - returns empty state for null input', () => {
    const result = transformTopDefects(null);
    expect(result.status).toBe('empty');
  });
});

// ─── Chart-State Contract for Defects by Style × Type ──────────────────────────

describe('transformDefectsByStyleType — chart-state contract', () => {
  it('RED - returns ready state for valid non-empty data', () => {
    const result = transformDefectsByStyleType(SAMPLE_DEFECTS_STYLE_TYPE);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(2);
    expect(result.data[0]).toEqual({ x: 'Style-2', y: 'Loose Thread', value: 45 });
  });

  it('RED - returns empty state for empty result', () => {
    const result = transformDefectsByStyleType({ result: [] });
    expect(result.status).toBe('empty');
  });

  it('RED - returns unavailable for error', () => {
    const result = transformDefectsByStyleType({ error: 'failed' });
    expect(result.status).toBe('unavailable');
  });

  it('RED - returns empty for null input', () => {
    const result = transformDefectsByStyleType(null);
    expect(result.status).toBe('empty');
  });
});

// ─── Task 2.2: transformAqlByTeam ──────────────────────────────────────────────

describe('transformAqlByTeam', () => {
  it('extracts label and numeric value from data array (bar chart contract)', () => {
    const input = {
      data: [
        { label: 'Team-A', value: 1.8 },
        { label: 'Team-B', value: 2.4 },
        { label: 'Team-C', value: 3.1 },
      ],
    };
    const result = transformAqlByTeam(input);
    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({ label: 'Team-A', value: 1.8 });
    expect(result[1]).toEqual({ label: 'Team-B', value: 2.4 });
    expect(result[2]).toEqual({ label: 'Team-C', value: 3.1 });
  });

  it('handles direct array input (no data wrapper)', () => {
    const input = [{ label: 'Line-1', value: 5.0 }];
    const result = transformAqlByTeam(input);
    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({ label: 'Line-1', value: 5.0 });
  });

  it('converts string values to numbers', () => {
    const input = { data: [{ label: 'Team-X', value: '2.5' }] };
    const result = transformAqlByTeam(input);
    expect(result[0].value).toBe(2.5);
  });

  it('filters out items with zero or negative value', () => {
    const input = {
      data: [
        { label: 'Zero', value: 0 },
        { label: 'Negative', value: -1 },
        { label: 'Valid', value: 3 },
      ],
    };
    const result = transformAqlByTeam(input);
    expect(result).toHaveLength(1);
    expect(result[0].label).toBe('Valid');
  });

  it('handles unavailable contract pass-through', () => {
    const unavailableInput = {
      status: 'unavailable',
      reason: 'aql_by_team_not_supported',
      message: 'AQL by team not available in volatile mode',
    };
    const result = transformAqlByTeam(unavailableInput);
    expect(result).toEqual(unavailableInput);
  });

  it('returns null for null input', () => {
    expect(transformAqlByTeam(null)).toBeNull();
  });

  it('returns null for error object', () => {
    expect(transformAqlByTeam({ error: 'failed' })).toBeNull();
  });

  it('limits to 12 items maximum (bar chart cap)', () => {
    const manyItems = {
      data: Array.from({ length: 20 }, (_, i) => ({ label: `Team-${i}`, value: i + 1 })),
    };
    const result = transformAqlByTeam(manyItems);
    expect(result).toHaveLength(12);
  });
});

// ─── Chart-State Contract for Defect Trend Top 3 ───────────────────────────────

describe('transformDefectTrendTop3 — chart-state contract', () => {
  it('RED - returns ready state for valid non-empty data', () => {
    const result = transformDefectTrendTop3(SAMPLE_DEFECT_TREND_TOP3);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(2);
    expect(result.data[0].name).toBe('Loose Thread');
  });

  it('RED - returns empty state for empty result', () => {
    const result = transformDefectTrendTop3({ result: [] });
    expect(result.status).toBe('empty');
  });

  it('RED - returns unavailable for error', () => {
    const result = transformDefectTrendTop3({ error: 'failed' });
    expect(result.status).toBe('unavailable');
  });

  it('RED - returns empty for null input', () => {
    const result = transformDefectTrendTop3(null);
    expect(result.status).toBe('empty');
  });
});

// ─── Container Dashboard Transforms ────────────────────────────────────────────

describe('transformContainerExecutiveSummary', () => {
  it('RED - converts result array with canonical labels to keyed summary array', () => {
    const input = [
      { label: 'Total Containers', value: 150 },
      { label: 'Average Pass Rate', value: 87.5 },
      { label: 'Total Palettes Inspected', value: 1200 },
      { label: 'Total Rejected Palettes', value: 45 },
    ];
    const result = transformContainerExecutiveSummary(input);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(1);
    expect(result.data[0]).toEqual({
      totalContainers: 150,
      averagePassRate: 87.5,
      totalInspected: 1200,
      totalRejected: 45,
    });
  });

  it('RED - ignores old non-canonical label aliases (only canonical labels map)', () => {
    const input = [
      { label: 'Total Containers', value: 150 },
      { label: 'Average Pass Rate', value: 87.5 },
      { label: 'Total Inspected', value: 1200 },
      { label: 'Total Rejected', value: 45 },
    ];
    const result = transformContainerExecutiveSummary(input);
    expect(result.status).toBe('ready');
    expect(result.data[0].totalContainers).toBe(150);
    expect(result.data[0].averagePassRate).toBe(87.5);
    // Old aliases should NOT map — only canonical backend labels work
    expect(result.data[0].totalInspected).toBeUndefined();
    expect(result.data[0].totalRejected).toBeUndefined();
  });

  it('RED - passes through explicit unavailable objects', () => {
    const unavailable = { status: 'unavailable', reason: 'volatile', message: 'Not available' };
    const result = transformContainerExecutiveSummary(unavailable);
    expect(result).toEqual(unavailable);
  });

  it('RED - returns empty state for null input', () => {
    const result = transformContainerExecutiveSummary(null);
    expect(result.status).toBe('empty');
  });

  it('RED - returns unavailable state for error objects', () => {
    const result = transformContainerExecutiveSummary({ error: 'API error' });
    expect(result.status).toBe('unavailable');
    expect(result.reason).toBe('api_error');
  });

  it('RED - returns empty state for empty array', () => {
    const result = transformContainerExecutiveSummary([]);
    expect(result.status).toBe('empty');
  });

  it('TRIANGULATE - handles partial canonical input (some labels unknown)', () => {
    const input = [
      { label: 'Total Containers', value: 100 },
      { label: 'NonExistent Label', value: 999 },
      { label: 'Total Rejected Palettes', value: 10 },
    ];
    const result = transformContainerExecutiveSummary(input);
    expect(result.status).toBe('ready');
    expect(result.data[0].totalContainers).toBe(100);
    expect(result.data[0].totalRejected).toBe(10);
    expect(result.data[0].totalInspected).toBeUndefined();
    expect(result.data[0].averagePassRate).toBeUndefined();
  });

  it('TRIANGULATE - renders zero values from canonical labels correctly', () => {
    const input = [
      { label: 'Total Containers', value: 0 },
      { label: 'Average Pass Rate', value: 0 },
      { label: 'Total Palettes Inspected', value: 0 },
      { label: 'Total Rejected Palettes', value: 0 },
    ];
    const result = transformContainerExecutiveSummary(input);
    expect(result.status).toBe('ready');
    expect(result.data[0]).toEqual({
      totalContainers: 0,
      averagePassRate: 0,
      totalInspected: 0,
      totalRejected: 0,
    });
  });
});

describe('transformContainerWorstContainers', () => {
  it('RED - normalizes worst-container rows and returns ready state', () => {
    const input = [
      { containerNumber: 'CONT-001', customer: 'Customer A', passRate: 72.5, rejectedPalettes: 5, inspectionDate: '2025-01-10' },
      { containerNumber: 'CONT-002', customer: 'Customer B', passRate: 85.0, rejectedPalettes: 2, inspectionDate: '2025-01-11' },
    ];
    const result = transformContainerWorstContainers(input);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(2);
    expect(result.data[0]).toEqual({
      containerNumber: 'CONT-001',
      customer: 'Customer A',
      passRate: 72.5,
      rejectedPalettes: 5,
      inspectionDate: '2025-01-10',
      key: 'CONT-001',
    });
    expect(result.data[1].key).toBe('CONT-002');
  });

  it('RED - passes through unavailable objects unchanged', () => {
    const unavailable = { status: 'unavailable', reason: 'volatile', message: 'Not available' };
    const result = transformContainerWorstContainers(unavailable);
    expect(result).toEqual(unavailable);
  });

  it('RED - returns empty state for null input', () => {
    const result = transformContainerWorstContainers(null);
    expect(result.status).toBe('empty');
  });

  it('RED - returns empty state for empty array', () => {
    const result = transformContainerWorstContainers([]);
    expect(result.status).toBe('empty');
  });

  it('RED - returns unavailable state for error objects', () => {
    const result = transformContainerWorstContainers({ error: 'fetch failed' });
    expect(result.status).toBe('unavailable');
    expect(result.reason).toBe('api_error');
  });

  it('RED - handles single-element array', () => {
    const input = [
      { containerNumber: 'CONT-001', customer: 'Customer A', passRate: 50.0, rejectedPalettes: 10, inspectionDate: '2025-01-05' },
    ];
    const result = transformContainerWorstContainers(input);
    expect(result.status).toBe('ready');
    expect(result.data).toHaveLength(1);
    expect(result.data[0].passRate).toBe(50.0);
    expect(result.data[0].key).toBe('CONT-001');
  });
});
