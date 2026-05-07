/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchKpi, fetchVolatileKpis, fetchVolatileDashboard, getFilterOptions, fetchAllKpis, getDefectComposition, getDefectTrendTop3, getAqlByTeam, getAcReRateByLine, getPerformanceByLine, fetchAllContainerKpis, fetchAllSecondsGeneralKpis, getContainerExecutiveSummary, getContainerWorstContainers, getContainerPassRateTrend, getContainerTopDefects, getSecondsA4FilterOptions, getSecondsA4ExecutiveSummary, getSecondsA4WeeklyTrend, getSecondsA4SewVsFab, getSecondsA4ByStyle, getSecondsA4ByColor, buildSecondsA4Params } from './kpi.js';
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

  it('returns all container KPIs from volatile response (no more unavailable)', async () => {
    const mockVolatileResponse = {
      executive_summary: [{ label: 'Total Containers', value: 3 }],
      containers_by_state: [{ name: '< 80%', value: 3 }, { name: '80-90%', value: 5 }],
      pass_rate_trend: [{ name: 'Pass Rate', data: [{ x: '2025-01-10', y: 70 }] }],
      inspected_trend: [{ name: 'Inspected', data: [{ x: '2025-01-10', y: 60 }] }],
      rejected_trend: [{ name: 'Rejected', data: [{ x: '2025-01-10', y: 20 }] }],
      top_defects: [{ label: 'Dirt Label', value: 12 }],
      defect_composition: [{ name: 'Dirt Label', value: 12 }],
      worst_containers: [{ containerNumber: 100, customer: 'Alpha', passRate: 50, rejectedPalettes: 15, inspectionDate: '2025-01-11' }],
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockVolatileResponse });

    const result = await fetchAllContainerKpis({}, new File(['test'], 'test.xlsx'));

    expect(result.containersByState).toEqual([{ name: '< 80%', value: 3 }, { name: '80-90%', value: 5 }]);
    expect(result.executiveSummary).toEqual([{ label: 'Total Containers', value: 3 }]);
    expect(result.passRateTrend).toEqual([{ name: 'Pass Rate', data: [{ x: '2025-01-10', y: 70 }] }]);
    expect(result.inspectedTrend).toEqual([{ name: 'Inspected', data: [{ x: '2025-01-10', y: 60 }] }]);
    expect(result.rejectedTrend).toEqual([{ name: 'Rejected', data: [{ x: '2025-01-10', y: 20 }] }]);
    expect(result.topDefects).toEqual([{ label: 'Dirt Label', value: 12 }]);
    expect(result.defectComposition).toEqual([{ name: 'Dirt Label', value: 12 }]);
    expect(result.worstContainers).toEqual([{ containerNumber: 100, customer: 'Alpha', passRate: 50, rejectedPalettes: 15, inspectionDate: '2025-01-11' }]);
  });

  it('falls back to unavailableKpi when volatile key is missing', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: { containers_by_state: [] } });

    const result = await fetchAllContainerKpis({}, new File(['test'], 'test.xlsx'));

    expect(result.containersByState).toEqual([]);
    expect(result.executiveSummary).toEqual(expect.objectContaining({ status: 'unavailable' }));
    expect(result.passRateTrend).toEqual(expect.objectContaining({ status: 'unavailable' }));
  });

  it('does NOT fetch live KPIs when volatileFile is provided', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: { containers_by_state: [] } });

    await fetchAllContainerKpis({}, new File(['test'], 'test.xlsx'));

    // Only the volatile POST should have been made; no GET calls
    expect(axiosClient.post).toHaveBeenCalledTimes(1);
    expect(axiosClient.get).not.toHaveBeenCalled();
  });
});

// ─── Task 3.1: Seconds A4 API helpers ─────────────────────────────────────
describe('kpi.js - buildSecondsA4Params', () => {
  it('builds params object with all active filter fields', () => {
    const result = buildSecondsA4Params({ year: '2025', line: 'L1', cut_num: '2', style: 'A', color: 'red' });
    expect(result).toEqual({ year: '2025', line: 'L1', cut_num: '2', style: 'A', color: 'red' });
  });

  it('omits empty and null filter values', () => {
    const result = buildSecondsA4Params({ year: '', line: 'L1', cut_num: null, style: undefined, color: '' });
    expect(result).toEqual({ line: 'L1' });
  });

  it('returns empty object when no filters provided', () => {
    const result = buildSecondsA4Params({});
    expect(result).toEqual({});
  });

  it('returns empty object when called without arguments', () => {
    const result = buildSecondsA4Params();
    expect(result).toEqual({});
  });
});

describe('kpi.js - getSecondsA4FilterOptions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches from seconds-a4/filter-options/ endpoint', async () => {
    const mockDto = { year: [2025, 2026], line: ['L1', 'L2'], cut_num: [1, 2, 3] };
    axiosClient.get.mockResolvedValueOnce({ data: mockDto });

    const result = await getSecondsA4FilterOptions();

    expect(axiosClient.get).toHaveBeenCalledOnce();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/seconds-a4/filter-options/');
    expect(result).toEqual(mockDto);
  });

  it('passes year filter in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: {} });

    await getSecondsA4FilterOptions({ year: 2025 });

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('year=2025');
  });

  it('passes line and cut_num filters in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: {} });

    await getSecondsA4FilterOptions({ year: 2026, line: 'L1', cut_num: 2 });

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('year=2026');
    expect(url).toContain('line=L1');
    expect(url).toContain('cut_num=2');
  });

  it('passes style and color filters in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: {} });

    await getSecondsA4FilterOptions({ style: 'N6165', color: 'blue' });

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('style=N6165');
    expect(url).toContain('color=blue');
  });

  it('throws on HTTP error', async () => {
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'Server error' }, status: 500 } });

    await expect(getSecondsA4FilterOptions()).rejects.toThrow('Server error');
  });
});

describe('kpi.js - getSecondsA4ExecutiveSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches from seconds-a4/executive-summary/ endpoint', async () => {
    const mockDto = { totals: { total_of_2ds: 1234, seconds_by_sew: 800, seconds_by_fab: 434 }, percentages: [] };
    axiosClient.get.mockResolvedValueOnce({ data: mockDto });

    const result = await getSecondsA4ExecutiveSummary();

    expect(axiosClient.get).toHaveBeenCalledOnce();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/seconds-a4/executive-summary/');
    expect(result).toEqual(mockDto);
  });

  it('passes year filter in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: {} });

    await getSecondsA4ExecutiveSummary({ year: 2025 });

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('year=2025');
  });

  it('throws on HTTP error', async () => {
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'DB error' }, status: 503 } });

    await expect(getSecondsA4ExecutiveSummary()).rejects.toThrow('DB error');
  });
});

describe('kpi.js - getSecondsA4WeeklyTrend', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches from seconds-a4/weekly-trend/ endpoint', async () => {
    const mockDto = [{ name: 'Total of 2DS', data: [{ x: 1, y: 100 }, { x: 2, y: 120 }] }];
    axiosClient.get.mockResolvedValueOnce({ data: mockDto });

    const result = await getSecondsA4WeeklyTrend();

    expect(axiosClient.get).toHaveBeenCalledOnce();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/seconds-a4/weekly-trend/');
    expect(result).toEqual(mockDto);
  });

  it('passes year and line filters in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    await getSecondsA4WeeklyTrend({ year: 2025, line: 'L1' });

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('year=2025');
    expect(url).toContain('line=L1');
  });

  it('returns empty array when no trend data', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    const result = await getSecondsA4WeeklyTrend();
    expect(result).toEqual([]);
  });

  it('throws on HTTP error', async () => {
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'Not found' }, status: 404 } });

    await expect(getSecondsA4WeeklyTrend()).rejects.toThrow('Not found');
  });
});

describe('kpi.js - getSecondsA4SewVsFab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches from seconds-a4/sew-vs-fab/ endpoint', async () => {
    const mockDto = [{ label: 'Sew', value: 800 }, { label: 'Fab', value: 434 }];
    axiosClient.get.mockResolvedValueOnce({ data: mockDto });

    const result = await getSecondsA4SewVsFab();

    expect(axiosClient.get).toHaveBeenCalledOnce();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/seconds-a4/sew-vs-fab/');
    expect(result).toEqual(mockDto);
  });

  it('passes year and cut_num filters in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    await getSecondsA4SewVsFab({ year: 2025, cut_num: 2 });

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('year=2025');
    expect(url).toContain('cut_num=2');
  });

  it('returns empty array when no data', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    const result = await getSecondsA4SewVsFab();
    expect(result).toEqual([]);
  });

  it('throws on HTTP error', async () => {
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'Server error' }, status: 500 } });

    await expect(getSecondsA4SewVsFab()).rejects.toThrow('Server error');
  });
});

describe('kpi.js - getSecondsA4ByStyle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches from seconds-a4/by-style/ endpoint', async () => {
    const mockDto = [{ label: 'Style-A', value: 500 }, { label: 'Style-B', value: 300 }];
    axiosClient.get.mockResolvedValueOnce({ data: mockDto });

    const result = await getSecondsA4ByStyle();

    expect(axiosClient.get).toHaveBeenCalledOnce();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/seconds-a4/by-style/');
    expect(result).toEqual(mockDto);
  });

  it('passes filters in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    await getSecondsA4ByStyle({ year: 2025, color: 'red' });

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('year=2025');
    expect(url).toContain('color=red');
  });

  it('returns empty array when no data', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    const result = await getSecondsA4ByStyle();
    expect(result).toEqual([]);
  });

  it('throws on HTTP error', async () => {
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'DB error' }, status: 503 } });

    await expect(getSecondsA4ByStyle()).rejects.toThrow('DB error');
  });
});

describe('kpi.js - getSecondsA4ByColor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches from seconds-a4/by-color/ endpoint', async () => {
    const mockDto = [{ label: 'Red', value: 400 }, { label: 'Blue', value: 250 }];
    axiosClient.get.mockResolvedValueOnce({ data: mockDto });

    const result = await getSecondsA4ByColor();

    expect(axiosClient.get).toHaveBeenCalledOnce();
    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('/quality/kpis/seconds-a4/by-color/');
    expect(result).toEqual(mockDto);
  });

  it('passes filters in URL', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    await getSecondsA4ByColor({ year: 2025, line: 'L1' });

    const [url] = axiosClient.get.mock.calls[0];
    expect(url).toContain('year=2025');
    expect(url).toContain('line=L1');
  });

  it('returns empty array when no data', async () => {
    axiosClient.get.mockResolvedValueOnce({ data: [] });

    const result = await getSecondsA4ByColor();
    expect(result).toEqual([]);
  });

  it('throws on HTTP error', async () => {
    axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'Not found' }, status: 404 } });

    await expect(getSecondsA4ByColor()).rejects.toThrow('Not found');
  });
});

// ─── Slice 1: fetchVolatileDashboard ──────────────────────────────────────────
describe('kpi.js - fetchVolatileDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('sends dashboard=qcfa in FormData with context=plant', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: {} });

    await fetchVolatileDashboard(new File(['test'], 'test.xlsx'), 'qcfa', 'plant');

    const [, formData] = axiosClient.post.mock.calls[0];
    expect(formData.get('dashboard')).toBe('qcfa');
    expect(formData.get('context')).toBe('plant');
  });

  it('sends dashboard=container without context', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: {} });

    await fetchVolatileDashboard(new File(['test'], 'test.xlsx'), 'container');

    const [, formData] = axiosClient.post.mock.calls[0];
    expect(formData.get('dashboard')).toBe('container');
    expect(formData.get('context')).toBeNull();
  });

  it('returns camelCase-mapped response', async () => {
    const mockResponse = {
      containers_by_state: [{ name: '< 80%', value: 3 }],
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileDashboard(new File(['test'], 'test.xlsx'), 'container');

    expect(result).toHaveProperty('containersByState');
    expect(result.containersByState).toEqual([{ name: '< 80%', value: 3 }]);
  });

  it('throws on HTTP error', async () => {
    axiosClient.post.mockRejectedValueOnce({ response: { data: { error: 'Server error' }, status: 500 } });

    await expect(fetchVolatileDashboard(new File(['test'], 'test.xlsx'), 'qcfa'))
      .rejects.toThrow('Server error');
  });
});

// ─── Slice 3: Seconds A4 DTO mappings via mapVolatileKpisDto ────────────────
describe('kpi.js - mapVolatileKpisDto Seconds A4 mappings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maps seconds_a4 snake_case keys to camelCase', async () => {
    const mockResponse = {
      filter_options: { year: [2025], line: ['L1'] },
      executive_summary: { totals: { total_of_2ds: 45 } },
      weekly_trend: [{ name: '2DS', data: [] }],
      sew_vs_fab: [{ label: 'Sew', value: 150 }],
      by_style: [{ label: 'STYLE-A', value: 25 }],
      by_color: [{ label: 'Red', value: 30 }],
      by_line: [{ label: 'L1', value: 25 }],
      by_cut: [{ label: 'Cut 101', value: 25 }],
      pass_fail_weekly: [{ name: 'Pass', data: [] }],
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileDashboard(new File(['test'], 'test.xlsx'), 'seconds_a4');

    expect(result).toHaveProperty('filterOptions');
    expect(result).toHaveProperty('executiveSummary');
    expect(result).toHaveProperty('weeklyTrend');
    expect(result).toHaveProperty('sewVsFab');
    expect(result).toHaveProperty('byStyle');
    expect(result).toHaveProperty('byColor');
    expect(result).toHaveProperty('byLine');
    expect(result).toHaveProperty('byCut');
    expect(result).toHaveProperty('passFailWeekly');
    expect(result.weeklyTrend).toEqual([{ name: '2DS', data: [] }]);
    expect(result.byStyle).toEqual([{ label: 'STYLE-A', value: 25 }]);
  });

  it('sends dashboard=seconds_a4 in FormData', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: {} });

    await fetchVolatileDashboard(new File(['test'], 'test.xlsx'), 'seconds_a4');

    const [, formData] = axiosClient.post.mock.calls[0];
    expect(formData.get('dashboard')).toBe('seconds_a4');
  });
});

// ─── Slice 4: Seconds General DTO mappings via mapVolatileKpisDto ────────
describe('kpi.js - mapVolatileKpisDto Seconds General mappings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maps seconds_general snake_case keys to camelCase', async () => {
    const mockResponse = {
      filter_options: { customer: ['CUST_A'], style: ['ST-100'] },
      defects_by_customer: [{ label: 'CUST_A', value: 75 }],
      defects_by_style: [{ label: 'ST-100', value: 45 }],
      weekly_trend: [{ name: 'Defects', data: [{ x: 1, y: 30 }] }],
      sewing_vs_fabric: [{ label: 'Sewing', value: 55 }, { label: 'Fabric', value: 20 }],
      production_totals: { total_produced: 1550, total_fixed: 775, total_definitive: 465 },
      top_sewing_defects: [{ label: 'picado_aguja', value: 10 }],
      top_fabric_defects: [{ label: 'corrido_2', value: 20 }],
      fix_vs_definitive: [{ name: 'Fixed', data: [{ x: 1, y: 55 }] }],
      defects_by_color: [{ label: 'Red', value: 40 }],
      defects_by_size: [{ label: 'M', value: 30 }],
      defects_by_line: [{ label: 'Line 1', value: 25 }],
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileDashboard(new File(['test'], 'test.xlsx'), 'seconds_general');

    expect(result).toHaveProperty('defectsByCustomer');
    expect(result).toHaveProperty('defectsByStyle');
    expect(result).toHaveProperty('weeklyTrend');
    expect(result).toHaveProperty('sewingVsFabric');
    expect(result).toHaveProperty('productionTotals');
    expect(result).toHaveProperty('topSewingDefects');
    expect(result).toHaveProperty('topFabricDefects');
    expect(result).toHaveProperty('fixVsDefinitive');
    expect(result).toHaveProperty('defectsByColor');
    expect(result).toHaveProperty('defectsBySize');
    expect(result).toHaveProperty('defectsByLine');

    // Verify production_totals preserves nested keys
    expect(result.productionTotals).toEqual({ total_produced: 1550, total_fixed: 775, total_definitive: 465 });
    // Verify sewing_vs_fabric maps correctly
    expect(result.sewingVsFabric).toEqual([{ label: 'Sewing', value: 55 }, { label: 'Fabric', value: 20 }]);
  });

  it('sends dashboard=seconds_general in FormData', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: {} });

    await fetchVolatileDashboard(new File(['test'], 'test.xlsx'), 'seconds_general');

    const [, formData] = axiosClient.post.mock.calls[0];
    expect(formData.get('dashboard')).toBe('seconds_general');
  });

  it('handles empty arrays for all seconds_general keys', async () => {
    const mockResponse = {
      filter_options: {},
      defects_by_customer: [],
      defects_by_style: [],
      weekly_trend: [{ name: 'Defects', data: [] }],
      sewing_vs_fabric: [],
      production_totals: { total_produced: 0, total_fixed: 0, total_definitive: 0 },
      top_sewing_defects: [],
      top_fabric_defects: [],
      fix_vs_definitive: [{ name: 'Fixed', data: [] }, { name: 'Definitive', data: [] }],
      defects_by_color: [],
      defects_by_size: [],
      defects_by_line: [],
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileDashboard(new File(['test'], 'test.xlsx'), 'seconds_general');

    expect(result.defectsByCustomer).toEqual([]);
    expect(result.productionTotals).toEqual({ total_produced: 0, total_fixed: 0, total_definitive: 0 });
  });

  it('handles absent seconds_general keys gracefully (backward compat)', async () => {
    const mockResponse = {
      filter_options: {},
      // No seconds_general keys at all
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fetchVolatileDashboard(new File(['test'], 'test.xlsx'), 'seconds_general');

    expect(result.defectsByCustomer).toBeUndefined();
    expect(result.productionTotals).toBeUndefined();
  });
});

// ─── fetchAllSecondsGeneralKpis ──────────────────────────────────────────
describe('kpi.js - fetchAllSecondsGeneralKpis - live mode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns all seconds general KPI keys in live mode', async () => {
    // Mock all 11 live endpoint calls
    for (let i = 0; i < 11; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: [] });
    }

    const result = await fetchAllSecondsGeneralKpis({}, null);

    expect(result).toHaveProperty('defectsByCustomer');
    expect(result).toHaveProperty('defectsByStyle');
    expect(result).toHaveProperty('weeklyTrend');
    expect(result).toHaveProperty('sewingVsFabric');
    expect(result).toHaveProperty('productionTotals');
    expect(result).toHaveProperty('topSewingDefects');
    expect(result).toHaveProperty('topFabricDefects');
    expect(result).toHaveProperty('fixVsDefinitive');
    expect(result).toHaveProperty('defectsByColor');
    expect(result).toHaveProperty('defectsBySize');
    expect(result).toHaveProperty('defectsByLine');
    expect(axiosClient.get).toHaveBeenCalledTimes(11);
  });

  it('individual KPI failures become unavailable states in live mode', async () => {
    // 5 resolve, 6 reject
    for (let i = 0; i < 5; i++) {
      axiosClient.get.mockResolvedValueOnce({ data: [] });
    }
    for (let i = 0; i < 6; i++) {
      axiosClient.get.mockRejectedValueOnce({ response: { data: { error: 'Timeout' }, status: 504 } });
    }

    const result = await fetchAllSecondsGeneralKpis({}, null);

    // First 5 resolve successfully
    expect(result.defectsByCustomer).toEqual([]);
    expect(result.defectsByStyle).toEqual([]);
    expect(result.weeklyTrend).toEqual([]);
    expect(result.sewingVsFabric).toEqual([]);
    expect(result.productionTotals).toEqual([]);
    // Last 6 reject
    expect(result.topSewingDefects).toEqual(expect.objectContaining({ status: 'unavailable' }));
    expect(result.topFabricDefects).toEqual(expect.objectContaining({ status: 'unavailable' }));
    expect(result.fixVsDefinitive).toEqual(expect.objectContaining({ status: 'unavailable' }));
    expect(result.defectsByColor).toEqual(expect.objectContaining({ status: 'unavailable' }));
    expect(result.defectsBySize).toEqual(expect.objectContaining({ status: 'unavailable' }));
    expect(result.defectsByLine).toEqual(expect.objectContaining({ status: 'unavailable' }));
  });
});

describe('kpi.js - fetchAllSecondsGeneralKpis - volatile mode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns all seconds general KPIs from volatile response', async () => {
    const mockVolatileResponse = {
      defects_by_customer: [{ customer: 'C1', total: 50 }],
      defects_by_style: [{ style: 'S1', total: 30 }],
      weekly_trend: [{ name: 'Defects', data: [{ x: 'W1', y: 10 }] }],
      sewing_vs_fabric: [{ label: 'Sewing', value: 80 }, { label: 'Fabric', value: 20 }],
      production_totals: { total_produced: 1000, total_fixed: 500, total_definitive: 300 },
      top_sewing_defects: [{ label: 'Open Seam', value: 25 }],
      top_fabric_defects: [{ label: 'Hole', value: 15 }],
      fix_vs_definitive: [{ name: 'Fixed', data: [{ x: 'W1', y: 100 }] }],
      defects_by_color: [{ color: 'Red', total: 10 }],
      defects_by_size: [{ size: 'M', total: 20 }],
      defects_by_line: [{ team: 'L1', total: 40 }],
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockVolatileResponse });

    const result = await fetchAllSecondsGeneralKpis({}, new File(['test'], 'test.xlsx'));

    expect(result.defectsByCustomer).toEqual([{ customer: 'C1', total: 50 }]);
    expect(result.defectsByStyle).toEqual([{ style: 'S1', total: 30 }]);
    expect(result.weeklyTrend).toEqual([{ name: 'Defects', data: [{ x: 'W1', y: 10 }] }]);
    expect(result.sewingVsFabric).toEqual([{ label: 'Sewing', value: 80 }, { label: 'Fabric', value: 20 }]);
    expect(result.productionTotals).toEqual({ total_produced: 1000, total_fixed: 500, total_definitive: 300 });
    expect(result.topSewingDefects).toEqual([{ label: 'Open Seam', value: 25 }]);
    expect(result.topFabricDefects).toEqual([{ label: 'Hole', value: 15 }]);
    expect(result.fixVsDefinitive).toEqual([{ name: 'Fixed', data: [{ x: 'W1', y: 100 }] }]);
    expect(result.defectsByColor).toEqual([{ color: 'Red', total: 10 }]);
    expect(result.defectsBySize).toEqual([{ size: 'M', total: 20 }]);
    expect(result.defectsByLine).toEqual([{ team: 'L1', total: 40 }]);
  });

  it('falls back to unavailableKpi when volatile key is missing', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: { defects_by_customer: [] } });

    const result = await fetchAllSecondsGeneralKpis({}, new File(['test'], 'test.xlsx'));

    expect(result.defectsByCustomer).toEqual([]);
    expect(result.defectsByStyle).toEqual(expect.objectContaining({ status: 'unavailable' }));
    expect(result.productionTotals).toEqual(expect.objectContaining({ status: 'unavailable' }));
    expect(result.topSewingDefects).toEqual(expect.objectContaining({ status: 'unavailable' }));
  });

  it('does NOT fetch live KPIs when volatileFile is provided', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: { defects_by_customer: [] } });

    await fetchAllSecondsGeneralKpis({}, new File(['test'], 'test.xlsx'));

    expect(axiosClient.post).toHaveBeenCalledTimes(1);
    expect(axiosClient.get).not.toHaveBeenCalled();
  });
});

// ─── Slice 1: fetchVolatileDashboard + fetchAllContainerKpis integration ─────
describe('kpi.js - fetchAllContainerKpis uses fetchVolatileDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls fetchVolatileDashboard instead of fetchVolatileKpis in volatile mode', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: { containers_by_state: [] } });

    const result = await fetchAllContainerKpis({}, new File(['test'], 'test.xlsx'));

    // Should call the post endpoint with dashboard=container
    const [url, formData] = axiosClient.post.mock.calls[0];
    expect(url).toContain('/quality/kpis/volatile/');
    expect(formData.get('dashboard')).toBe('container');
    // containersByState comes through, others fall back to unavailableKpi
    expect(result.containersByState).toEqual([]);
    expect(result.topDefects).toEqual(expect.objectContaining({ status: 'unavailable' }));
  });
});
