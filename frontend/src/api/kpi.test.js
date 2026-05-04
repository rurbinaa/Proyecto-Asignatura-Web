/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchKpi, fetchVolatileKpis, getFilterOptions, fetchAllKpis, getDefectComposition, getDefectTrendTop3 } from './kpi.js';
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
      .mockResolvedValueOnce({ data: { label: 'Defect Rate', value: 2.5 } })
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: [] });

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

// ─── Task 4.1: context parameter support ───────────────────────────────────
describe('kpi.js - context parameter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('includes context=plant in the URL query string for fetchKpi', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });

    await fetchKpi('aql-by-style/', {}, 'plant');

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('context=plant');
    // Verify it's a proper query string parameter, not part of the path
    expect(url).toMatch(/[?&]context=plant/);
  });

  it('includes context=customer in the URL query string for fetchKpi', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });

    await fetchKpi('aql-by-style/', {}, 'customer');

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('context=customer');
  });

  it('does NOT include context param when not provided (backward compatibility)', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });

    await fetchKpi('aql-by-style/');

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).not.toContain('context=');
    expect(url).not.toMatch(/context/);
  });

  it('fetchAllKpis passes context to all 16 sub-calls via fetchKpi', async () => {
    // Each individual KPI function calls fetchKpi, which calls axiosClient.get
    // We mock axiosClient.get to resolve for all 16 calls
    for (let i = 0; i < 16; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis({}, 'plant');

    // All 16 calls should include context=plant
    const calls = axiosClient.get.mock.calls;
    expect(calls).toHaveLength(16);
    calls.forEach(([url]) => {
      expect(url).toContain('context=plant');
    });
  });

  it('fetchAllKpis with context=customer passes it to all sub-calls', async () => {
    for (let i = 0; i < 16; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis({}, 'customer');

    const calls = axiosClient.get.mock.calls;
    expect(calls).toHaveLength(16);
    calls.forEach(([url]) => {
      expect(url).toContain('context=customer');
    });
  });

  it('fetchAllKpis without context does NOT inject context param', async () => {
    for (let i = 0; i < 16; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis();

    const calls = axiosClient.get.mock.calls;
    expect(calls).toHaveLength(16);
    calls.forEach(([url]) => {
      expect(url).not.toContain('context=');
    });
  });

  it('context coexists with other filter params in the URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });

    await fetchKpi('aql-by-style/', { week: '5', team: '1' }, 'plant');

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('week=5');
    expect(url).toContain('team=1');
    expect(url).toContain('context=plant');
  });
});

// ─── Task 3.1: New defect insight API helpers ───────────────────────────────
describe('kpi.js - getDefectComposition', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches correct endpoint and returns raw DTO', async () => {
    const mockDto = [
      { name: 'Loose Thread', value: 45 },
      { name: 'Broken Stitch', value: 32 },
    ];
    axiosClient.get.mockResolvedValueOnce({ data: mockDto });

    const result = await getDefectComposition();
    expect(axiosClient.get).toHaveBeenCalledOnce();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/defect-composition/');
    expect(result).toEqual(mockDto);
  });

  it('passes context param in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    await getDefectComposition({}, 'plant');
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('context=plant');
  });

  it('returns empty array when no defects match', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    const result = await getDefectComposition();
    expect(result).toEqual([]);
  });

  it('throws on HTTP error', async () => {
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'Server error' }, status: 500 } });
    await expect(getDefectComposition()).rejects.toThrow('Server error');
  });
});

describe('kpi.js - getDefectTrendTop3', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches correct endpoint and returns series DTO', async () => {
    const mockDto = [
      { name: 'Loose Thread', data: [{ x: 10, y: 5 }, { x: 11, y: 8 }] },
      { name: 'Broken Stitch', data: [{ x: 10, y: 3 }, { x: 11, y: 2 }] },
    ];
    axiosClient.get.mockResolvedValueOnce({ data: mockDto });

    const result = await getDefectTrendTop3();
    expect(axiosClient.get).toHaveBeenCalledOnce();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/defect-trend-top-3/');
    expect(result).toEqual(mockDto);
  });

  it('passes context param in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    await getDefectTrendTop3({}, 'customer');
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('context=customer');
  });

  it('returns empty array when no defects found', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    const result = await getDefectTrendTop3();
    expect(result).toEqual([]);
  });

  it('throws on HTTP error', async () => {
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'Not found' }, status: 404 } });
    await expect(getDefectTrendTop3()).rejects.toThrow('Not found');
  });
});

// ─── Task 3.1: Volatile DTO mapping for defect insights ────────────────────
describe('kpi.js - fetchVolatileKpis_defect_insights', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maps defect_composition snake_case to defectComposition camelCase', async () => {
    const mockResponse = {
      aql_by_style: [],
      aql_weekly: [],
      defect_composition: [
        { name: 'Loose Thread', value: 45 },
        { name: 'Broken Stitch', value: 32 },
      ],
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));
    expect(result.defectComposition).toBeDefined();
    expect(result.defectComposition).toEqual([
      { name: 'Loose Thread', value: 45 },
      { name: 'Broken Stitch', value: 32 },
    ]);
    // Snake_case key must not leak
    expect(result.defect_composition).toBeUndefined();
  });

  it('maps defect_trend_top_3 snake_case to defectTrendTop3 camelCase', async () => {
    const mockResponse = {
      aql_by_style: [],
      aql_weekly: [],
      defect_trend_top_3: [
        { name: 'Loose Thread', data: [{ x: 10, y: 5 }, { x: 11, y: 8 }] },
      ],
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));
    expect(result.defectTrendTop3).toBeDefined();
    expect(result.defectTrendTop3).toEqual([
      { name: 'Loose Thread', data: [{ x: 10, y: 5 }, { x: 11, y: 8 }] },
    ]);
    expect(result.defect_trend_top_3).toBeUndefined();
  });

  it('handles empty arrays for both new volatile keys', async () => {
    const mockResponse = {
      aql_by_style: [],
      aql_weekly: [],
      defect_composition: [],
      defect_trend_top_3: [],
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));
    expect(result.defectComposition).toEqual([]);
    expect(result.defectTrendTop3).toEqual([]);
  });

  it('handles absent new keys gracefully (backward compat for old volatile responses)', async () => {
    const mockResponse = {
      aql_by_style: [],
      aql_weekly: [],
      // No defect_composition or defect_trend_top_3 at all
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));
    // Should not crash — keys just won't be present
    expect(result.defectComposition).toBeUndefined();
    expect(result.defectTrendTop3).toBeUndefined();
  });

  it('full volatile contract regression now includes both new insight keys', async () => {
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
      defect_composition: [{ name: 'Loose Thread', value: 45 }],
      defect_trend_top_3: [{ name: 'Loose Thread', data: [{ x: 10, y: 5 }] }],
    };

    axiosClient.post.mockResolvedValueOnce({ data: snakeCaseApiResponse });
    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    // All camelCase keys expected (existing + new)
    const expectedKeys = [
      'aqlByStyle', 'aqlWeekly', 'auditedPieces', 'acReRateByLine',
      'secondsRework', 'performanceByCustomer', 'performanceByLine',
      'topDefects', 'fabricDefects', 'defectsByStyleType',
      'passRejectDistribution', 'rejectedEvolution', 'containersByState',
      'defectRate', 'defectComposition', 'defectTrendTop3',
    ];

    expectedKeys.forEach((key) => {
      expect(result).toHaveProperty(key);
    });

    // No snake_case keys leaked
    const snakeCaseKeys = Object.keys(snakeCaseApiResponse);
    snakeCaseKeys.forEach((key) => {
      expect(result).not.toHaveProperty(key);
    });
  });
});

// ─── Task 3.1: fetchAllKpis includes defect insight KPIs ───────────────────
describe('kpi.js - fetchAllKpis_includes_defect_insights', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchAllKpis result includes defectComposition and defectTrendTop3 keys', async () => {
    const mockComposition = [{ name: 'Loose Thread', value: 45 }];
    const mockTrend = [{ name: 'Loose Thread', data: [{ x: 10, y: 5 }] }];

    // 16 calls: 14 original + 2 new
    for (let i = 0; i < 14; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }
    // 15th call = defectComposition
    axiosClient.get.mockResolvedValueOnce({ data: mockComposition });
    // 16th call = defectTrendTop3
    axiosClient.get.mockResolvedValueOnce({ data: mockTrend });

    const result = await fetchAllKpis();

    expect(result).toHaveProperty('defectComposition');
    expect(result).toHaveProperty('defectTrendTop3');
    expect(result.defectComposition).toEqual(mockComposition);
    expect(result.defectTrendTop3).toEqual(mockTrend);
  });

  it('fetchAllKpis calls the defect composition endpoint with correct URL', async () => {
    for (let i = 0; i < 16; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis({}, 'plant');

    const urls = axiosClient.get.mock.calls.map(([url]) => url);
    expect(urls.some((u) => u.includes('/quality/kpis/defect-composition/'))).toBe(true);
    expect(urls.some((u) => u.includes('/quality/kpis/defect-trend-top-3/'))).toBe(true);
  });

  it('fetchAllKpis gracefully handles defect insight failures via unavailableKpi', async () => {
    for (let i = 0; i < 14; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }
    // defectComposition fails
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'DB error' }, status: 500 } });
    // defectTrendTop3 succeeds
    axiosClient.get.mockResolvedValueOnce({ data: [{ name: 'A', data: [{ x: 1, y: 1 }] }] });

    const result = await fetchAllKpis();

    expect(result.defectComposition).toEqual({
      status: 'unavailable',
      reason: 'DB error',
      data: null,
    });
    expect(result.defectTrendTop3).toEqual([{ name: 'A', data: [{ x: 1, y: 1 }] }]);
  });
});
