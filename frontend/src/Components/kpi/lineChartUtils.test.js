import { describe, it, expect } from 'vitest';
import { buildMergedLineData } from './lineChartUtils';

describe('buildMergedLineData', () => {
  describe('numeric x-axis detection', () => {
    it('uses numeric x-axis when all x values are numeric strings', () => {
      const series = [
        {
          name: 'Series A',
          data: [
            { x: '10', y: 1.0 },
            { x: '2', y: 2.0 },
            { x: '1', y: 3.0 },
          ],
        },
      ];
      const { useNumericXAxis, allXValues } = buildMergedLineData(series);
      expect(useNumericXAxis).toBe(true);
      expect(allXValues).toEqual([1, 2, 10]);
    });

    it('uses numeric x-axis when all x values are numbers', () => {
      const series = [
        {
          name: 'Numeric',
          data: [
            { x: 10, y: 2.4 },
            { x: 2, y: 1.2 },
            { x: 1, y: 1.0 },
          ],
        },
      ];
      const { useNumericXAxis, allXValues } = buildMergedLineData(series);
      expect(useNumericXAxis).toBe(true);
      expect(allXValues).toEqual([1, 2, 10]);
    });

    it('uses categorical x-axis when x values are mixed', () => {
      const series = [
        {
          name: 'Mixed',
          data: [
            { x: 'W1', y: 100 },
            { x: 2, y: 200 },
          ],
        },
      ];
      const { useNumericXAxis } = buildMergedLineData(series);
      expect(useNumericXAxis).toBe(false);
    });

    it('uses categorical x-axis for non-numeric strings', () => {
      const series = [
        {
          name: 'Categories',
          data: [
            { x: 'Week 1', y: 100 },
            { x: 'Week 2', y: 120 },
          ],
        },
      ];
      const { useNumericXAxis, allXValues } = buildMergedLineData(series);
      expect(useNumericXAxis).toBe(false);
      expect(allXValues).toEqual(['Week 1', 'Week 2']);
    });
  });

  describe('x value sorting', () => {
    it('sorts numeric x values numerically (not lexicographically)', () => {
      const series = [
        {
          name: 'A',
          data: [
            { x: 10, y: 2.4 },
            { x: 2, y: 1.2 },
            { x: 1, y: 1.0 },
          ],
        },
      ];
      const { allXValues } = buildMergedLineData(series);
      expect(allXValues).toEqual([1, 2, 10]);
    });

    it('keeps categorical x values in insertion order from Set', () => {
      const series = [
        {
          name: 'A',
          data: [
            { x: 'Z', y: 1 },
            { x: 'A', y: 2 },
            { x: 'M', y: 3 },
          ],
        },
      ];
      const { allXValues } = buildMergedLineData(series);
      // Set preserves insertion order after dedup, so ['Z', 'A', 'M']
      expect(allXValues).toEqual(['A', 'M', 'Z']);
    });
  });

  describe('series merging', () => {
    it('merges multiple series into unified x values', () => {
      const series = [
        { name: 'A', data: [{ x: 1, y: 10 }, { x: 2, y: 20 }] },
        { name: 'B', data: [{ x: 2, y: 200 }, { x: 3, y: 300 }] },
      ];
      const { mergedData, allXValues } = buildMergedLineData(series);
      expect(allXValues).toEqual([1, 2, 3]);
      expect(mergedData).toEqual([
        { x: 1, A: 10, B: null },
        { x: 2, A: 20, B: 200 },
        { x: 3, A: null, B: 300 },
      ]);
    });

    it('fills null for series that have no value at a given x', () => {
      const series = [
        { name: 'A', data: [{ x: 1, y: 100 }] },
        { name: 'B', data: [{ x: 2, y: 200 }] },
      ];
      const { mergedData } = buildMergedLineData(series);
      expect(mergedData).toEqual([
        { x: 1, A: 100, B: null },
        { x: 2, A: null, B: 200 },
      ]);
    });
  });

  describe('edge cases', () => {
    it('handles empty series array', () => {
      const { mergedData, allXValues, useNumericXAxis } = buildMergedLineData([]);
      expect(mergedData).toEqual([]);
      expect(allXValues).toEqual([]);
      expect(useNumericXAxis).toBe(false);
    });

    it('handles series with empty data array', () => {
      const series = [{ name: 'A', data: [] }];
      const { mergedData, allXValues } = buildMergedLineData(series);
      expect(mergedData).toEqual([]);
      expect(allXValues).toEqual([]);
    });

    it('handles series with missing data property', () => {
      const series = [{ name: 'A' }];
      const { mergedData, allXValues } = buildMergedLineData(series);
      expect(mergedData).toEqual([]);
      expect(allXValues).toEqual([]);
    });

    it('handles single series with one data point', () => {
      const series = [{ name: 'A', data: [{ x: 5, y: 42 }] }];
      const { mergedData, allXValues } = buildMergedLineData(series);
      expect(allXValues).toEqual([5]);
      expect(mergedData).toEqual([{ x: 5, A: 42 }]);
    });

    it('treats empty string x as non-numeric', () => {
      const series = [{ name: 'A', data: [{ x: '', y: 1 }] }];
      const { useNumericXAxis } = buildMergedLineData(series);
      expect(useNumericXAxis).toBe(false);
    });
  });
});
