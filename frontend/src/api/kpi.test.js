/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchKpi, fetchVolatileKpis, getFilterOptions, fetchAllKpis } from './kpi.js';
import axiosClient from './axiosClient';

vi.mock('./axiosClient');

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

    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });
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

    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });
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

    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });
    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    expect(result.aqlByStyle).toBeNull();
    expect(result.auditedPieces).toBeUndefined();
    expect(result.defectRate).toBe(0);
  });

  it('throws error on HTTP failure', async () => {
    axiosClient.post.mockRejectedValueOnce({ response: { data: { error: 'Server error' }, status: 500 } });
    await expect(fetchVolatileKpis(new File(['test'], 'test.xlsx')))
      .rejects.toThrow('Server error');
  });

  it('passes file in FormData correctly', async () => {
    const mockFile = new File(['test'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    axiosClient.post.mockResolvedValueOnce({ data: {} });
    await fetchVolatileKpis(mockFile);
    expect(axiosClient.post).toHaveBeenCalledOnce();
    const [url, formData] = axiosClient.post.mock.calls[0];
    expect(url).toContain('/quality/kpis/volatile/');
    expect(formData).toBeInstanceOf(FormData);
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

    axiosClient.post.mockResolvedValueOnce({ data: snakeCaseApiResponse });
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

    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });
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

    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });
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

    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });
    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));
    // Should return null without throwing
    expect(result.defectRate).toBeNull();
  });

  it('RED - handles non-numeric nested value with null fallback', async () => {
    const mockResponse = {
      aql_by_style: [],
      defect_rate: { label: 'Invalid', value: 'not-a-number' },
    };

    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });
    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));
    // Should handle non-numeric gracefully
    expect(result.defectRate).toBeNull();
  });

  it('normalizes filter_options snake_case to camelCase', async () => {
    const mockResponse = {
      aql_by_style: [],
      aql_weekly: [],
      filter_options: {
        week: [1, 2, 3],
        team: [1, 2],
        style: ['N6165', 'N1234'],
        color: ['red', 'blue'],
        customer: ['CustomerA'],
        batch: [100, 200],
      },
    };

    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });
    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));
    expect(result.filterOptions).toBeDefined();
    expect(result.filterOptions).toEqual(mockResponse.filter_options);
  });

  it('preserves explicit unavailable contract objects in volatile DTO mapping', async () => {
    const mockResponse = {
      seconds_rework: {
        status: 'unavailable',
        reason: 'excel_volatile_not_computable',
        data: null,
      },
    };

    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });
    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    expect(result.secondsRework).toEqual({
      status: 'unavailable',
      reason: 'excel_volatile_not_computable',
      data: null,
    });
  });
});

describe('kpi.js - fetchAllKpis unavailable contract', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maps endpoint failures to explicit unavailable status objects', async () => {
    axiosClient.get
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockRejectedValueOnce({ response: { data: { error: 'not available' }, status: 503 } })
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { label: 'Defect Rate', value: 2.5 } });

    const result = await fetchAllKpis();

    expect(result.secondsRework).toEqual({
      status: 'unavailable',
      reason: 'not available',
      data: null,
    });
  });
});

describe('kpi.js - getFilterOptions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches filter options from correct endpoint', async () => {
    const mockOptions = {
      week: [1, 2, 3],
      team: [1, 2],
      style: ['N6165', 'N1234'],
      color: ['red', 'blue'],
      customer: ['CustomerA'],
      batch: [100, 200],
    };

    axiosClient.get.mockResolvedValueOnce({ data: mockOptions });
    const result = await getFilterOptions();
    expect(axiosClient.get).toHaveBeenCalledOnce();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/filter-options/');
    expect(result).toEqual(mockOptions);
  });

  it('throws error on HTTP failure', async () => {
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'Not found' }, status: 404 } });
    await expect(getFilterOptions()).rejects.toThrow('Not found');
  });
});

describe('kpi.js - live DTO mapping boundary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maps live defect-rate DTO object to scalar number', async () => {
    axiosClient.get.mockResolvedValueOnce({
      data: { label: 'Defect Rate', value: 4.25 },
    });

    const result = await fetchKpi('defect-rate/');
    expect(result).toBe(4.25);
  });

  it('preserves wrapped live payload for chart endpoints', async () => {
    const dto = { data: [{ label: 'Style-1', value: 2.1 }] };
    axiosClient.get.mockResolvedValueOnce({ data: dto });

    const result = await fetchKpi('aql-by-style/');
    expect(result).toEqual(dto);
  });
});
