/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from 'vitest';
import {
  VOLATILE_FILTER_ALLOWLISTS,
  DEFERRED_FILTER_KEYS,
  normalizeVolatileFilters,
  buildVolatileIdentity,
} from './volatileFilters';

describe('VOLATILE_FILTER_ALLOWLISTS', () => {
  it('defines allowlists for all four volatile dashboards', () => {
    expect(VOLATILE_FILTER_ALLOWLISTS).toHaveProperty('qcfa');
    expect(VOLATILE_FILTER_ALLOWLISTS).toHaveProperty('container');
    expect(VOLATILE_FILTER_ALLOWLISTS).toHaveProperty('seconds_a4');
    expect(VOLATILE_FILTER_ALLOWLISTS).toHaveProperty('seconds_general');
  });

  it('container allowlist only has customer', () => {
    expect(VOLATILE_FILTER_ALLOWLISTS.container).toEqual(['customer']);
  });

  it('qcfa allowlist includes all supported filter keys', () => {
    const keys = VOLATILE_FILTER_ALLOWLISTS.qcfa;
    expect(keys).toContain('week');
    expect(keys).toContain('team');
    expect(keys).toContain('style');
    expect(keys).toContain('color');
    expect(keys).toContain('customer');
    expect(keys).toContain('batch');
    expect(keys).toContain('line_code');
    expect(keys).toContain('include_dual_lines');
    // date_range MUST NOT be in the allowlist
    expect(keys).not.toContain('date_range');
  });

  it('seconds_a4 allowlist matches expected keys', () => {
    expect(VOLATILE_FILTER_ALLOWLISTS.seconds_a4).toEqual([
      'year', 'week', 'line', 'cut_num', 'style', 'color',
    ]);
  });

  it('seconds_general allowlist matches expected keys', () => {
    const keys = VOLATILE_FILTER_ALLOWLISTS.seconds_general;
    expect(keys).toContain('week');
    expect(keys).toContain('customer');
    expect(keys).toContain('style');
    expect(keys).toContain('color');
    expect(keys).toContain('size');
    expect(keys).toContain('team');
    expect(keys).toContain('line_code');
    expect(keys).toContain('include_dual_lines');
    expect(keys).not.toContain('date_range');
  });
});

describe('DEFERRED_FILTER_KEYS', () => {
  it('includes date_range for v1 deferral', () => {
    expect(DEFERRED_FILTER_KEYS).toContain('date_range');
    expect(DEFERRED_FILTER_KEYS).toContain('from_date');
    expect(DEFERRED_FILTER_KEYS).toContain('to_date');
  });
});

describe('normalizeVolatileFilters', () => {
  it('returns only allowlisted filters for qcfa dashboard', () => {
    const result = normalizeVolatileFilters('qcfa', {
      week: '5',
      team: '3',
      date_range: '2025-01-01,2025-01-31', // should be stripped
      from_date: '2025-01-01', // should be stripped
    });
    expect(result).toEqual({ week: '5', team: '3' });
    expect(result).not.toHaveProperty('date_range');
    expect(result).not.toHaveProperty('from_date');
  });

  it('returns only customer filter for container dashboard', () => {
    const result = normalizeVolatileFilters('container', {
      customer: 'AlphaCorp',
      style: 'N3165', // not in container allowlist
      date_range: '2025-01-01,2025-02-01', // deferred
    });
    expect(result).toEqual({ customer: 'AlphaCorp' });
  });

  it('returns empty object when no filters match the allowlist', () => {
    const result = normalizeVolatileFilters('container', {
      style: 'N3165',
      week: '5',
      date_range: '2025-01-01,2025-02-01',
    });
    expect(result).toEqual({});
  });

  it('strips empty/null/undefined values from normalized filters', () => {
    const result = normalizeVolatileFilters('qcfa', {
      week: '',
      team: null,
      style: undefined,
      customer: 'RealCustomer',
    });
    expect(result).toEqual({ customer: 'RealCustomer' });
  });

  it('returns empty object for unknown dashboard', () => {
    const result = normalizeVolatileFilters('nonexistent', { week: '5' });
    expect(result).toEqual({});
  });

  it('does NOT filter out explicitly allowed falsy values like 0 or false', () => {
    const result = normalizeVolatileFilters('qcfa', {
      week: 0, // valid numeric value
      team: false, // not typical but should pass through
    });
    // Both pass through because they're not null/undefined/empty string
    expect(result.week).toBe(0);
  });

  it('seconds_a4 filters work correctly', () => {
    const result = normalizeVolatileFilters('seconds_a4', {
      year: '2025',
      week: '3',
      line: 'L1',
      cut_num: '101',
      style: 'STYLE-A',
      color: 'Red',
      date_range: 'deferred',
    });
    expect(result).toEqual({
      year: '2025',
      week: '3',
      line: 'L1',
      cut_num: '101',
      style: 'STYLE-A',
      color: 'Red',
    });
  });

  it('seconds_general filters include dual-line keys', () => {
    const result = normalizeVolatileFilters('seconds_general', {
      week: '5',
      customer: 'CUST_A',
      line_code: '35-36',
      include_dual_lines: 'true',
    });
    expect(result).toEqual({
      week: '5',
      customer: 'CUST_A',
      line_code: '35-36',
      include_dual_lines: 'true',
    });
  });
});

describe('buildVolatileIdentity', () => {
  const file = new File(['content'], 'test.xlsx', { lastModified: 1000 });

  it('returns deterministic identity with file, dashboard, context, and filters', () => {
    const id = buildVolatileIdentity(file, 'qcfa', 'plant', { week: '5' });
    expect(id).toBe('test.xlsx:7:1000:qcfa:plant:{"week":"5"}');
  });

  it('same file+dashboard+context+filters produces same identity', () => {
    const id1 = buildVolatileIdentity(file, 'qcfa', 'plant', { week: '5', team: '3' });
    const id2 = buildVolatileIdentity(file, 'qcfa', 'plant', { week: '5', team: '3' });
    expect(id1).toBe(id2);
  });

  it('different filters produce different identities', () => {
    const id1 = buildVolatileIdentity(file, 'qcfa', 'plant', { week: '5' });
    const id2 = buildVolatileIdentity(file, 'qcfa', 'plant', { week: '6' });
    expect(id1).not.toBe(id2);
  });

  it('filters are normalized (only allowlisted keys) before identity build', () => {
    // date_range should be stripped, so identity equals no-filters identity
    const withFilters = buildVolatileIdentity(file, 'container', 'plant', {
      customer: 'Alpha',
      date_range: '2025-01-01,2025-02-01', // stripped
    });
    const withoutFilters = buildVolatileIdentity(file, 'container', 'plant', {
      customer: 'Alpha',
    });
    expect(withFilters).toBe(withoutFilters);
  });

  it('identity changes when context changes even with same filters', () => {
    const id1 = buildVolatileIdentity(file, 'qcfa', 'plant', { week: '5' });
    const id2 = buildVolatileIdentity(file, 'qcfa', 'customer', { week: '5' });
    expect(id1).not.toBe(id2);
  });

  it('identity changes when dashboard changes', () => {
    const id1 = buildVolatileIdentity(file, 'qcfa', 'plant', { week: '5' });
    const id2 = buildVolatileIdentity(file, 'container', 'plant', { week: '5' });
    expect(id1).not.toBe(id2);
  });

  it('identity string is deterministic (same input = same output across calls)', () => {
    const id1 = buildVolatileIdentity(file, 'seconds_a4', null, {
      year: '2025', line: 'L1',
    });
    const id2 = buildVolatileIdentity(file, 'seconds_a4', null, {
      year: '2025', line: 'L1',
    });
    expect(id1).toBe(id2);
  });
});
