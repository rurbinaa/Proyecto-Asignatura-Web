/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchKpi, fetchVolatileKpis, getFilterOptions, fetchAllKpis, getDefectComposition, getDefectTrendTop3, getAqlByTeam, getAcReRateByLine, getPerformanceByLine, fetchAllContainerKpis, getContainerExecutiveSummary, getContainerWorstContainers, getContainerPassRateTrend, getContainerTopDefects } from './kpi.js';
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
      .mockResolvedValueOnce({ data: { data: [] } })   // aqlByStyle
      .mockResolvedValueOnce({ data: { data: [] } })   // aqlByTeam
      .mockResolvedValueOnce({ data: { data: [] } })   // aqlWeekly
      .mockResolvedValueOnce({ data: { data: [] } })   // auditedPieces
      .mockResolvedValueOnce({ data: { data: [] } })   // acReRateByLine
      .mockRejectedValueOnce({ response: { data: { error: 'not available' }, status: 503 } }) // secondsRework
      .mockResolvedValueOnce({ data: { data: [] } })   // performanceByCustomer
      .mockResolvedValueOnce({ data: { data: [] } })   // performanceByLine
      .mockResolvedValueOnce({ data: { data: [] } })   // topDefects
      .mockResolvedValueOnce({ data: { data: [] } })   // fabricDefects
      .mockResolvedValueOnce({ data: { data: [] } })   // defectsByStyleType
      .mockResolvedValueOnce({ data: { data: [] } })   // passRejectDistribution
      .mockResolvedValueOnce({ data: { data: [] } })   // rejectedEvolution
      .mockResolvedValueOnce({ data: { data: [] } })   // containersByState
      .mockResolvedValueOnce({ data: { label: 'Defect Rate', value: 2.5 } }) // defectRate
      .mockResolvedValueOnce({ data: [] })             // defectComposition
      .mockResolvedValueOnce({ data: [] });            // defectTrendTop3

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

  it('fetchAllKpis passes context to all 17 sub-calls via fetchKpi', async () => {
    // Each individual KPI function calls fetchKpi, which calls axiosClient.get
    // We mock axiosClient.get to resolve for all 17 calls
    for (let i = 0; i < 17; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis({}, 'plant');

    // All 17 calls should include context=plant
    const calls = axiosClient.get.mock.calls;
    expect(calls).toHaveLength(17);
    calls.forEach(([url]) => {
      expect(url).toContain('context=plant');
    });
  });

  it('fetchAllKpis with context=customer passes it to all sub-calls', async () => {
    for (let i = 0; i < 17; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis({}, 'customer');

    const calls = axiosClient.get.mock.calls;
    expect(calls).toHaveLength(17);
    calls.forEach(([url]) => {
      expect(url).toContain('context=customer');
    });
  });

  it('fetchAllKpis without context does NOT inject context param', async () => {
    for (let i = 0; i < 17; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis();

    const calls = axiosClient.get.mock.calls;
    expect(calls).toHaveLength(17);
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

// ─── Task 4.1 / Slice 3: Dual-line filter-options and KPI params ───────────
describe('kpi.js - getFilterOptions dual-line', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('RED - passes context=plant and include_dual_lines=true in query string', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { team: [1] } });

    await getFilterOptions('plant', true);

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/filter-options/');
    expect(url).toContain('context=plant');
    expect(url).toContain('include_dual_lines=true');
  });

  it('RED - passes context=customer and include_dual_lines=false in query string', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { team: [1] } });

    await getFilterOptions('customer', false);

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('context=customer');
    expect(url).toContain('include_dual_lines=false');
  });

  it('RED - backward compat: no params when called without arguments', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { team: [1] } });

    await getFilterOptions();

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).not.toContain('context=');
    expect(url).not.toContain('include_dual_lines');
  });

  it('RED - backward compat: only context passed, no include_dual_lines', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { team: [1] } });

    await getFilterOptions('plant');

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('context=plant');
    expect(url).not.toContain('include_dual_lines');
  });
});

describe('kpi.js - line-grouped KPI dual-line params', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('RED - getAqlByTeam passes include_dual_lines=true in URL via filters', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });

    await getAqlByTeam({ include_dual_lines: true }, 'customer');

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('include_dual_lines=true');
    expect(url).toContain('context=customer');
  });

  it('RED - getAcReRateByLine passes include_dual_lines=false and line_code via filters', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });

    await getAcReRateByLine({ include_dual_lines: false, line_code: '35-36' }, 'plant');

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('include_dual_lines=false');
    expect(url).toContain('line_code=35-36');
  });

  it('RED - getPerformanceByLine passes include_dual_lines=true via filters', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });

    await getPerformanceByLine({ include_dual_lines: true }, 'plant');

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('include_dual_lines=true');
  });

  it('RED - backward compat: no dual params when filters do not contain them', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });

    await getPerformanceByLine({ week: '5' }, 'plant');

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('week=5');
    expect(url).not.toContain('include_dual_lines');
    expect(url).not.toContain('line_code');
  });
});

describe('kpi.js - fetchAllKpis dual-line params', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('RED - fetchAllKpis passes include_dual_lines=false to all sub-calls (default hidden)', async () => {
    for (let i = 0; i < 17; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis({ include_dual_lines: false }, 'customer');

    const calls = axiosClient.get.mock.calls;
    expect(calls).toHaveLength(17);
    calls.forEach(([url]) => {
      expect(url).toContain('include_dual_lines=false');
    });
  });

  it('RED - fetchAllKpis passes include_dual_lines=true and line_code to all sub-calls', async () => {
    for (let i = 0; i < 17; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis({ include_dual_lines: true, line_code: '35-36' }, 'customer');

    const calls = axiosClient.get.mock.calls;
    expect(calls).toHaveLength(17);
    calls.forEach(([url]) => {
      expect(url).toContain('include_dual_lines=true');
      expect(url).toContain('line_code=35-36');
    });
  });

  it('RED - backward compat: fetchAllKpis without dual params does not inject them', async () => {
    for (let i = 0; i < 17; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis({ week: '5' }, 'plant');

    const calls = axiosClient.get.mock.calls;
    expect(calls).toHaveLength(17);
    calls.forEach(([url]) => {
      expect(url).not.toContain('include_dual_lines');
      expect(url).not.toContain('line_code');
    });
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
      aql_by_team: { data: [{ label: 'Team-1', value: 2.5 }] },
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
      'aqlByStyle', 'aqlByTeam', 'aqlWeekly', 'auditedPieces', 'acReRateByLine',
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

    // 17 calls: 15 original + 2 defect insight
    for (let i = 0; i < 15; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }
    // 16th call = defectComposition
    axiosClient.get.mockResolvedValueOnce({ data: mockComposition });
    // 17th call = defectTrendTop3
    axiosClient.get.mockResolvedValueOnce({ data: mockTrend });

    const result = await fetchAllKpis();

    expect(result).toHaveProperty('defectComposition');
    expect(result).toHaveProperty('defectTrendTop3');
    expect(result.defectComposition).toEqual(mockComposition);
    expect(result.defectTrendTop3).toEqual(mockTrend);
  });

  it('fetchAllKpis calls the defect composition endpoint with correct URL', async () => {
    for (let i = 0; i < 17; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis({}, 'plant');

    const urls = axiosClient.get.mock.calls.map(([url]) => url);
    expect(urls.some((u) => u.includes('/quality/kpis/defect-composition/'))).toBe(true);
    expect(urls.some((u) => u.includes('/quality/kpis/defect-trend-top-3/'))).toBe(true);
  });

  it('fetchAllKpis gracefully handles defect insight failures via unavailableKpi', async () => {
    for (let i = 0; i < 15; i++) {
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

// ─── Task 2.1: AQL by Team/Line endpoint wiring ───────────────────────────────
describe('kpi.js - getAqlByTeam', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches correct AQL by team endpoint and returns DTO', async () => {
    const mockDto = { data: [{ label: 'Team-1', value: 2.5 }] };
    axiosClient.get.mockResolvedValueOnce({ data: mockDto });

    const result = await getAqlByTeam();
    expect(axiosClient.get).toHaveBeenCalledOnce();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/aql/aql-by-team/');
    expect(result).toEqual(mockDto);
  });

  it('passes context param in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });

    await getAqlByTeam({}, 'plant');
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('context=plant');
  });

  it('returns empty data when no teams match', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });

    const result = await getAqlByTeam();
    expect(result).toEqual({ data: [] });
  });

  it('throws on HTTP error', async () => {
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'Server error' }, status: 500 } });
    await expect(getAqlByTeam()).rejects.toThrow('Server error');
  });
});

describe('kpi.js - fetchAllKpis_includes_aqlByTeam', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchAllKpis result includes aqlByTeam key', async () => {
    // 17 calls (16 previous + 1 new aqlByTeam)
    for (let i = 0; i < 17; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    const result = await fetchAllKpis();

    expect(result).toHaveProperty('aqlByTeam');
  });

  it('fetchAllKpis calls aql-by-team endpoint with correct URL', async () => {
    for (let i = 0; i < 17; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    await fetchAllKpis({}, 'plant');

    const urls = axiosClient.get.mock.calls.map(([url]) => url);
    expect(urls.some((u) => u.includes('/quality/kpis/aql/aql-by-team/'))).toBe(true);
  });

  it('fetchAllKpis gracefully handles aqlByTeam failure via unavailableKpi', async () => {
    // aqlByStyle passes (1st)
    axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    // aqlByTeam fails (2nd) ← inserted at position 2 in kpiMap
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'DB error' }, status: 500 } });
    // remaining 15 calls pass
    for (let i = 0; i < 15; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: { data: [] } });
    }

    const result = await fetchAllKpis();

    expect(result.aqlByTeam).toEqual({
      status: 'unavailable',
      reason: 'DB error',
      data: null,
    });
  });
});

describe('kpi.js - fetchVolatileKpis_includes_aqlByTeam', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maps aql_by_team snake_case to aqlByTeam camelCase', async () => {
    const mockResponse = {
      aql_by_team: { data: [{ label: 'Team-1', value: 2.5 }] },
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));
    expect(result.aqlByTeam).toBeDefined();
    expect(result.aqlByTeam).toEqual({ data: [{ label: 'Team-1', value: 2.5 }] });
    // Snake_case key must NOT leak
    expect(result.aql_by_team).toBeUndefined();
  });

  it('handles absent aqlByTeam key gracefully (backward compat)', async () => {
    const mockResponse = {
      aql_by_style: [],
      aql_weekly: [],
      // No aql_by_team
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'));
    expect(result.aqlByTeam).toBeUndefined();
  });
});

// ─── Task 1.1/1.2: Volatile context forwarding ────────────────────────────
describe('kpi.js - fetchVolatileKpis_context_forwarding', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('RED - sends context parameter in FormData when provided', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: {} });

    await fetchVolatileKpis(new File(['test'], 'test.xlsx'), 'plant');

    const [url, formData] = axiosClient.post.mock.calls[0];
    expect(url).toContain('/quality/kpis/volatile/');
    expect(formData).toBeInstanceOf(FormData);
    expect(formData.get('context')).toBe('plant');
  });

  it('RED - sends context=customer in FormData', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: {} });

    await fetchVolatileKpis(new File(['test'], 'test.xlsx'), 'customer');

    const [, formData] = axiosClient.post.mock.calls[0];
    expect(formData.get('context')).toBe('customer');
  });

  it('RED - does NOT include context in FormData when not provided (backward compat)', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: {} });

    await fetchVolatileKpis(new File(['test'], 'test.xlsx'));

    const [, formData] = axiosClient.post.mock.calls[0];
    expect(formData.get('context')).toBeNull();
  });

  it('RED - volatile context forwarding with full payload still maps defect insights', async () => {
    const mockResponse = {
      aql_by_style: [],
      aql_weekly: [],
      defect_composition: [{ name: 'Hole', value: 12 }],
      defect_trend_top_3: [{ name: 'Hole', data: [{ x: 1, y: 3 }] }],
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileKpis(new File(['test'], 'test.xlsx'), 'customer');

    expect(result.defectComposition).toEqual([{ name: 'Hole', value: 12 }]);
    expect(result.defectTrendTop3).toEqual([{ name: 'Hole', data: [{ x: 1, y: 3 }] }]);
    // Verify context was sent
    const [, formData] = axiosClient.post.mock.calls[0];
    expect(formData.get('context')).toBe('customer');
  });
});

// ─── Container-Specific KPI Helpers ───────────────────────────────────────────

describe('kpi.js - container helpers - endpoint wiring', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('RED - getContainerExecutiveSummary fetches from container/executive-summary/', async () => {
    const mockDto = [
      { label: 'Total Containers', value: 150 },
    ];
    axiosClient.get.mockResolvedValueOnce({ data: mockDto });

    const result = await getContainerExecutiveSummary();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/container/executive-summary/');
    expect(result).toEqual(mockDto);
  });

  it('RED - getContainerWorstContainers fetches from container/worst-containers/', async () => {
    const mockDto = [
      { containerNumber: 'C1', customer: 'A', passRate: 72.5, rejectedPalettes: 5, inspectionDate: '2025-01-10' },
    ];
    axiosClient.get.mockResolvedValueOnce({ data: mockDto });

    const result = await getContainerWorstContainers();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/container/worst-containers/');
    expect(result).toEqual(mockDto);
  });

  it('RED - getContainerPassRateTrend fetches from container/pass-rate-trend/', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });
    await getContainerPassRateTrend();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/container/pass-rate-trend/');
  });

  it('RED - getContainerTopDefects fetches from container/top-defects/', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });
    await getContainerTopDefects();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/container/top-defects/');
  });

  it('RED - context parameter is forwarded in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });
    await getContainerExecutiveSummary({ customer: 'Test' }, 'plant');
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('context=plant');
    expect(url).toContain('customer=Test');
  });
});

describe('kpi.js - fetchAllContainerKpis - live mode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('RED - returns all container KPI keys in live mode', async () => {
    // Mock all 7 container KPI calls + containersByState (shared)
    for (let i = 0; i < 8; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: [] });
    }

    const result = await fetchAllContainerKpis({}, null);

    expect(result).toHaveProperty('executiveSummary');
    expect(result).toHaveProperty('containersByState');
    expect(result).toHaveProperty('passRateTrend');
    expect(result).toHaveProperty('inspectedTrend');
    expect(result).toHaveProperty('rejectedTrend');
    expect(result).toHaveProperty('topDefects');
    expect(result).toHaveProperty('defectComposition');
    expect(result).toHaveProperty('worstContainers');
    // 8 calls: 7 container + 1 containers-by-state
    expect(axiosClient.get).toHaveBeenCalledTimes(8);
  });

  it('RED - context parameter is forwarded to all sub-calls', async () => {
    for (let i = 0; i < 8; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: [] });
    }

    await fetchAllContainerKpis({}, null, 'plant');

    const urls = axiosClient.get.mock.calls.map(([url]) => url);
    urls.forEach((url) => {
      expect(url).toContain('context=plant');
    });
  });

  it('RED - individual KPI failures become unavailable states', async () => {
    // Mock for 8 calls: positions 0-3 resolve, positions 4-7 reject
    for (let i = 0; i < 4; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: [] });
    }
    for (let i = 0; i < 4; i++) {
      axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'DB error' }, status: 503 } });
    }

    const result = await fetchAllContainerKpis({}, null);

    // Positions 0-3 resolve successfully (execSummary, containersByState, passRateTrend, inspectedTrend)
    expect(result.executiveSummary).toEqual([]);
    expect(result.containersByState).toEqual([]);
    expect(result.passRateTrend).toEqual([]);
    expect(result.inspectedTrend).toEqual([]);
    // Positions 4-7 reject (rejectedTrend, topDefects, defectComposition, worstContainers)
    expect(result.rejectedTrend).toEqual(expect.objectContaining({ status: 'unavailable' }));
    expect(result.topDefects).toEqual(expect.objectContaining({ status: 'unavailable' }));
    expect(result.defectComposition).toEqual(expect.objectContaining({ status: 'unavailable' }));
    expect(result.worstContainers).toEqual(expect.objectContaining({ status: 'unavailable' }));
  });
});

describe('kpi.js - fetchAllContainerKpis - volatile mode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('RED - returns containersByState from volatile data and unavailable for others', async () => {
    const mockVolatileResponse = {
      aql_by_style: [],
      containers_by_state: [{ name: '< 80%', value: 3 }, { name: '80-90%', value: 5 }],
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockVolatileResponse });

    const result = await fetchAllContainerKpis({}, new File(['test'], 'test.xlsx'));

    expect(result.containersByState).toEqual([
      { name: '< 80%', value: 3 },
      { name: '80-90%', value: 5 },
    ]);
    // Container-specific KPIs are unavailable in volatile mode
    const containerKeys = ['executiveSummary', 'passRateTrend', 'inspectedTrend', 'rejectedTrend', 'topDefects', 'defectComposition', 'worstContainers'];
    containerKeys.forEach((key) => {
      expect(result[key]).toEqual(expect.objectContaining({ status: 'unavailable' }));
    });
  });

  it('RED - does NOT fetch live KPIs when volatileFile is provided', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: { aql_by_style: [] } });

    await fetchAllContainerKpis({}, new File(['test'], 'test.xlsx'));

    // Only the volatile POST should have been made; no GET calls
    expect(axiosClient.post).toHaveBeenCalledTimes(1);
    expect(axiosClient.get).not.toHaveBeenCalled();
  });
});
