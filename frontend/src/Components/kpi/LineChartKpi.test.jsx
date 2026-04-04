import { describe, it, expect } from 'vitest';
import { buildMergedLineData } from './lineChartUtils';

describe('LineChartKpi data normalization', () => {
  it('sorts numeric x values numerically (not lexicographically)', () => {
    const series = [
      {
        name: 'AQL',
        data: [
          { x: 10, y: 2.4 },
          { x: 2, y: 1.2 },
          { x: 1, y: 1.0 },
        ],
      },
    ];

    const { allXValues, useNumericXAxis } = buildMergedLineData(series);

    expect(useNumericXAxis).toBe(true);
    expect(allXValues).toEqual([1, 2, 10]);
  });

  it('keeps categorical x values and does not force numeric mode', () => {
    const series = [
      {
        name: 'Categorical',
        data: [
          { x: 'W1', y: 100 },
          { x: 'W2', y: 120 },
        ],
      },
    ];

    const { allXValues, useNumericXAxis } = buildMergedLineData(series);

    expect(useNumericXAxis).toBe(false);
    expect(allXValues).toEqual(['W1', 'W2']);
  });
});
