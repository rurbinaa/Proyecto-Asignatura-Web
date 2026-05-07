/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import useVolatileDashboardCache, { clearVolatileCache } from './useVolatileDashboardCache';
import { fetchVolatileDashboard } from '../api/kpi';

vi.mock('../api/kpi', () => ({
  fetchVolatileDashboard: vi.fn(),
}));

describe('useVolatileDashboardCache', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearVolatileCache();
  });

  it('returns loading=true while fetching, then data on success', async () => {
    const mockData = { aqlByStyle: [] };
    fetchVolatileDashboard.mockResolvedValueOnce(mockData);

    const file = new File(['test'], 'test.xlsx', { lastModified: 1000 });
    const { result } = renderHook(() =>
      useVolatileDashboardCache(file, 'qcfa', 'plant'),
    );

    // Initially loading
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();

    // Wait for resolution
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
  });

  it('returns cached data on second render with same key (no re-fetch)', async () => {
    const mockData = { aqlByStyle: [{ label: 'A', value: 1.5 }] };
    fetchVolatileDashboard.mockResolvedValueOnce(mockData);

    const file = new File(['test'], 'test.xlsx', { lastModified: 1000 });

    // First render — cache miss
    const { result, rerender } = renderHook(() =>
      useVolatileDashboardCache(file, 'qcfa', 'plant'),
    );
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(mockData);

    // Second render — cache hit (no additional fetchVolatileDashboard call)
    rerender();
    expect(result.current.data).toEqual(mockData);
    expect(fetchVolatileDashboard).toHaveBeenCalledTimes(1);
  });

  it('returns error state on fetch failure', async () => {
    fetchVolatileDashboard.mockRejectedValueOnce(new Error('Failed'));

    const file = new File(['test'], 'test.xlsx');
    const { result } = renderHook(() =>
      useVolatileDashboardCache(file, 'qcfa'),
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe('Failed');
  });

  it('returns null data and no loading when file is null (live mode)', () => {
    const { result } = renderHook(() =>
      useVolatileDashboardCache(null, 'qcfa'),
    );

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('different dashboards with same file are cached separately', async () => {
    fetchVolatileDashboard.mockResolvedValue({});

    const file = new File(['test'], 'test.xlsx', { lastModified: 1000 });

    // Render for qcfa
    const { result: qcfaResult } = renderHook(
      ({ f, d, c }) => useVolatileDashboardCache(f, d, c),
      { initialProps: { f: file, d: 'qcfa', c: 'plant' } },
    );
    await waitFor(() => expect(qcfaResult.current.loading).toBe(false));

    // Render for container
    const { result: containerResult } = renderHook(
      ({ f, d, c }) => useVolatileDashboardCache(f, d, c),
      { initialProps: { f: file, d: 'container', c: null } },
    );
    await waitFor(() => expect(containerResult.current.loading).toBe(false));

    // Two separate fetches
    expect(fetchVolatileDashboard).toHaveBeenCalledTimes(2);
  });

  it('refetches when context changes on same file and dashboard', async () => {
    const mockDataPlant = { executiveSummary: { totals: { total_of_2ds: 100 } } };
    const mockDataCustomer = { executiveSummary: { totals: { total_of_2ds: 200 } } };
    fetchVolatileDashboard
      .mockResolvedValueOnce(mockDataPlant)
      .mockResolvedValueOnce(mockDataCustomer);

    const file = new File(['test'], 'test.xlsx', { lastModified: 1000 });

    // Initial render with context=plant
    const { result, rerender } = renderHook(
      ({ f, d, c }) => useVolatileDashboardCache(f, d, c),
      { initialProps: { f: file, d: 'seconds_a4', c: 'plant' } },
    );
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(mockDataPlant);
    expect(fetchVolatileDashboard).toHaveBeenCalledTimes(1);

    // Rerender with same props — cache hit, no refetch
    rerender({ f: file, d: 'seconds_a4', c: 'plant' });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(fetchVolatileDashboard).toHaveBeenCalledTimes(1);

    // Context changes to 'customer' — should refetch
    rerender({ f: file, d: 'seconds_a4', c: 'customer' });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(mockDataCustomer);
    expect(fetchVolatileDashboard).toHaveBeenCalledTimes(2);
  });
});
