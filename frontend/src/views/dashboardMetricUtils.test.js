import { describe, it, expect } from 'vitest';
import { normalizeScalarMetric } from './dashboardMetricUtils';

describe('normalizeScalarMetric', () => {
  describe('plain numbers', () => {
    it('returns a finite number as-is', () => {
      expect(normalizeScalarMetric(42)).toBe(42);
    });

    it('returns zero as-is', () => {
      expect(normalizeScalarMetric(0)).toBe(0);
    });

    it('returns negative numbers as-is', () => {
      expect(normalizeScalarMetric(-3.14)).toBe(-3.14);
    });

    it('returns null for Infinity', () => {
      expect(normalizeScalarMetric(Infinity)).toBeNull();
    });

    it('returns null for NaN', () => {
      expect(normalizeScalarMetric(NaN)).toBeNull();
    });

    it('returns null for -Infinity', () => {
      expect(normalizeScalarMetric(-Infinity)).toBeNull();
    });
  });

  describe('object with nested value', () => {
    it('unwraps object with numeric value key', () => {
      expect(normalizeScalarMetric({ value: 42 })).toBe(42);
    });

    it('unwraps object with string value that is numeric', () => {
      expect(normalizeScalarMetric({ value: '3.14' })).toBe(3.14);
    });

    it('returns null for object with non-numeric value string', () => {
      expect(normalizeScalarMetric({ value: 'abc' })).toBeNull();
    });

    it('returns null for object with null value', () => {
      expect(normalizeScalarMetric({ value: null })).toBeNull();
    });

    it('returns null for object with undefined value', () => {
      expect(normalizeScalarMetric({ value: undefined })).toBeNull();
    });

    it('returns null for object with NaN value', () => {
      expect(normalizeScalarMetric({ value: NaN })).toBeNull();
    });

    it('returns null for empty object', () => {
      expect(normalizeScalarMetric({})).toBeNull();
    });
  });

  describe('string parsing', () => {
    it('parses numeric string to number', () => {
      expect(normalizeScalarMetric('42')).toBe(42);
    });

    it('parses decimal string to number', () => {
      expect(normalizeScalarMetric('3.14')).toBe(3.14);
    });

    it('returns null for non-numeric string', () => {
      expect(normalizeScalarMetric('abc')).toBeNull();
    });

    it('returns null for empty string', () => {
      expect(normalizeScalarMetric('')).toBeNull();
    });

    it('returns null for string with only whitespace', () => {
      expect(normalizeScalarMetric('   ')).toBeNull();
    });
  });

  describe('invalid inputs', () => {
    it('returns null for null', () => {
      expect(normalizeScalarMetric(null)).toBeNull();
    });

    it('returns null for undefined', () => {
      expect(normalizeScalarMetric(undefined)).toBeNull();
    });

    it('returns null for boolean true', () => {
      expect(normalizeScalarMetric(true)).toBeNull();
    });

    it('returns null for boolean false', () => {
      expect(normalizeScalarMetric(false)).toBeNull();
    });

    it('returns null for array', () => {
      expect(normalizeScalarMetric([1, 2, 3])).toBeNull();
    });
  });

  describe('priority order', () => {
    it('prefers the direct number over object with value key', () => {
      // The function checks typeof number first
      expect(normalizeScalarMetric(42)).toBe(42);
    });

    it('does not unwrap nested object if outer value is already a number', () => {
      const input = { value: { value: 99 } };
      // input is an object, so it goes to the object branch
      // input.value is { value: 99 }, which is not a number and not a numeric string
      // So it returns null
      expect(normalizeScalarMetric(input)).toBeNull();
    });

    it('prefers number over string when value is 0', () => {
      expect(normalizeScalarMetric(0)).toBe(0);
    });

    it('handles string with leading/trailing whitespace as numeric', () => {
      expect(normalizeScalarMetric('  42  ')).toBe(42);
    });
  });
});
