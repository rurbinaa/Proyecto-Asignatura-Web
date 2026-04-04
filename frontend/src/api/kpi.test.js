/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchVolatileKpis } from './kpi.js';

// Mock fetch globally
global.fetch = vi.fn();

describe('kpi.js - fetchVolatileKpis', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('normalizes snake_case response to camelCase', async () => {
    const mockResponse = {
      aql_by_style: [{ style: 'A', aql: 1.5 }],
      aql_weekly: [{ week: 1, aql: 2.0 }],
      audited_pieces: 1000,
      ac_re_rate_by_line: [{ line: '1', accept: 95, reject: 5 }],
      seconds_rework: 150,
      performance_by_customer: [{ customer: 'X', rate: 0.9 }],
      performance_by_line: [{ line: '1', rate: 0.85 }],
      top_defects: [{ defect: 'seam', count: 50 }],
      fabric_defects: [{ type: 'hole', count: 20 }],
      defects_by_style_type: [{ style: 'A', type: 'seam', count: 10 }],
      pass_reject_distribution: { pass: 800, reject: 200 },
      rejected_evolution: [{ week: 1, rejected: 50 }],
      containers_by_state: { open: 10, closed: 20 },
      defect_rate: 2.5,
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    // Verify camelCase keys
    expect(result).toHaveProperty('aqlByStyle');
    expect(result).toHaveProperty('aqlWeekly');
    expect(result).toHaveProperty('auditedPieces');
    expect(result).toHaveProperty('acReRateByLine');
    expect(result).toHaveProperty('secondsRework');
    expect(result).toHaveProperty('performanceByCustomer');
    expect(result).toHaveProperty('performanceByLine');
    expect(result).toHaveProperty('topDefects');
    expect(result).toHaveProperty('fabricDefects');
    expect(result).toHaveProperty('defectsByStyleType');
    expect(result).toHaveProperty('passRejectDistribution');
    expect(result).toHaveProperty('rejectedEvolution');
    expect(result).toHaveProperty('containersByState');
    expect(result).toHaveProperty('defectRate');

    // Verify values preserved
    expect(result.aqlByStyle).toEqual([{ style: 'A', aql: 1.5 }]);
    expect(result.auditedPieces).toBe(1000);
    expect(result.defectRate).toBe(2.5);
  });

  it('preserves existing camelCase keys (idempotent)', async () => {
    // Already camelCase - should not be transformed again
    const mockResponse = {
      aqlByStyle: [{ style: 'B', aql: 1.2 }],
      auditedPieces: 500,
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    expect(result.aqlByStyle).toEqual([{ style: 'B', aql: 1.2 }]);
    expect(result.auditedPieces).toBe(500);
  });

  it('handles null/missing values gracefully', async () => {
    const mockResponse = {
      aql_by_style: null,
      audited_pieces: undefined,
      defect_rate: 0,
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    expect(result.aqlByStyle).toBeNull();
    expect(result.auditedPieces).toBeUndefined();
    expect(result.defectRate).toBe(0);
  });

  it('throws error on HTTP failure', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ error: 'Server error' }),
    });

    await expect(fetchVolatileKpis(new File(['test'], 'test.xlsx')))
      .rejects.toThrow('Server error');
  });

  it('passes file in FormData correctly', async () => {
    const mockFile = new File(['test'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
    });

    await fetchVolatileKpis(mockFile);

    expect(global.fetch).toHaveBeenCalledOnce();
    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toContain('/quality/kpis/volatile/');
    expect(options.method).toBe('POST');
    expect(options.body).toBeInstanceOf(FormData);
  });

  it('contract regression: adapter output matches DashboardView consumer shape', async () => {
    // This test verifies that the adapter normalizes the API response
    // to exactly match what DashboardView expects (camelCase keys)
    const snakeCaseApiResponse = {
      aql_by_style: [{ style: 'A', aql: 1.5 }],
      aql_weekly: [{ week: 1, aql: 2.0 }],
      audited_pieces: 1000,
      ac_re_rate_by_line: [{ line: '1', accept: 95, reject: 5 }],
      seconds_rework: 150,
      performance_by_customer: [{ customer: 'X', rate: 0.9 }],
      performance_by_line: [{ line: '1', rate: 0.85 }],
      top_defects: [{ defect: 'seam', count: 50 }],
      fabric_defects: [{ type: 'hole', count: 20 }],
      defects_by_style_type: [{ style: 'A', type: 'seam', count: 10 }],
      pass_reject_distribution: { pass: 800, reject: 200 },
      rejected_evolution: [{ week: 1, rejected: 50 }],
      containers_by_state: { open: 10, closed: 20 },
      defect_rate: 2.5,
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(snakeCaseApiResponse),
    });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    // DashboardView expects these exact camelCase keys
    const expectedKeys = [
      'aqlByStyle',
      'aqlWeekly',
      'auditedPieces',
      'acReRateByLine',
      'secondsRework',
      'performanceByCustomer',
      'performanceByLine',
      'topDefects',
      'fabricDefects',
      'defectsByStyleType',
      'passRejectDistribution',
      'rejectedEvolution',
      'containersByState',
      'defectRate',
    ];

    // Verify all expected keys are present
    expectedKeys.forEach((key) => {
      expect(result).toHaveProperty(key);
    });

    // Verify no snake_case keys leaked through (would break DashboardView)
    const snakeCaseKeys = Object.keys(snakeCaseApiResponse);
    snakeCaseKeys.forEach((key) => {
      expect(result).not.toHaveProperty(key);
    });

    // Verify values are correctly mapped
    expect(result.aqlByStyle).toEqual(snakeCaseApiResponse.aql_by_style);
    expect(result.auditedPieces).toBe(snakeCaseApiResponse.audited_pieces);
    expect(result.defectRate).toBe(snakeCaseApiResponse.defect_rate);
  });

  // RED tests for defect_rate object normalization
  it('RED - normalizes defect_rate object {label, value} to scalar defectRate', async () => {
    const mockResponse = {
      aql_by_style: [],
      aql_weekly: [],
      audited_pieces: 1000,
      defect_rate: { label: 'Defect Rate', value: 2.5 },
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    // Should unwrap object to scalar
    expect(result.defectRate).toBe(2.5);
    expect(typeof result.defectRate).toBe('number');
  });

  it('RED - normalizes defectRate object (camelCase) to scalar', async () => {
    const mockResponse = {
      aql_by_style: [],
      aql_weekly: [],
      audited_pieces: 500,
      defectRate: { label: 'Defect Rate', value: 3.2 },
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    // Should unwrap object to scalar
    expect(result.defectRate).toBe(3.2);
    expect(typeof result.defectRate).toBe('number');
  });

  it('RED - handles missing/null defect rate gracefully with null fallback', async () => {
    const mockResponse = {
      aql_by_style: null,
      audited_pieces: undefined,
      defect_rate: null,
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    // Should return null without throwing
    expect(result.defectRate).toBeNull();
  });

  it('RED - handles non-numeric nested value with null fallback', async () => {
    const mockResponse = {
      aql_by_style: [],
      defect_rate: { label: 'Invalid', value: 'not-a-number' },
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    // Should handle non-numeric gracefully
    expect(result.defectRate).toBeNull();
  });
});