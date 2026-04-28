/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { createInspection, createDefect, closeInspection } from './capture';
import axiosClient from './axiosClient';

vi.mock('./axiosClient');

describe('capture.js - createInspection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const inspectionPayload = {
    lot: 'LOT-001',
    style: 'N6165',
    size: 'M',
    color: 'Red',
  };

  it('success: POST /api/v1/inspections/ with data and returns created inspection', async () => {
    const mockResponse = { id: 42, ...inspectionPayload, status: 'open' };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await createInspection(inspectionPayload);

    expect(axiosClient.post).toHaveBeenCalledOnce();
    expect(axiosClient.post).toHaveBeenCalledWith('/api/v1/inspections/', inspectionPayload);
    expect(result).toEqual(mockResponse);
  });

  it('network error without response: falls back to undefined status', async () => {
    axiosClient.post.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(createInspection(inspectionPayload)).rejects.toThrow('Create inspection failed: undefined');
  });

  it('HTTP 400: throws with specific error message from JSON body', async () => {
    axiosClient.post.mockRejectedValueOnce({
      response: { data: { error: 'Lot already exists' }, status: 400 },
    });

    await expect(createInspection(inspectionPayload)).rejects.toThrow('Lot already exists');
  });

  it('HTTP 500 with no error key: falls back to status code', async () => {
    axiosClient.post.mockRejectedValueOnce({
      response: { data: {}, status: 500 },
    });

    await expect(createInspection(inspectionPayload)).rejects.toThrow('Create inspection failed: 500');
  });

  it('HTTP 500 with detail key but no error: falls back to status code', async () => {
    axiosClient.post.mockRejectedValueOnce({
      response: { data: { detail: 'Server timeout' }, status: 500 },
    });

    // Source only uses .error key, not .detail
    await expect(createInspection(inspectionPayload)).rejects.toThrow('Create inspection failed: 500');
  });
});

describe('capture.js - createDefect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const defectPayload = {
    inspection: 42,
    defect_type: 'Seam',
    defect_size: 'Small',
    coordinates_x: [10, 20],
    coordinates_y: [30, 40],
    defect_count: 2,
  };

  it('success: POST /api/v1/defects/ with data and returns created defect', async () => {
    const mockResponse = { id: 1, ...defectPayload };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await createDefect(defectPayload);

    expect(axiosClient.post).toHaveBeenCalledOnce();
    expect(axiosClient.post).toHaveBeenCalledWith('/api/v1/defects/', defectPayload);
    expect(result).toEqual(mockResponse);
  });

  it('network error without response: falls back to undefined status', async () => {
    axiosClient.post.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(createDefect(defectPayload)).rejects.toThrow('Create defect failed: undefined');
  });

  it('HTTP 404: throws with error message from response', async () => {
    axiosClient.post.mockRejectedValueOnce({
      response: { data: { error: 'Inspection not found' }, status: 404 },
    });

    await expect(createDefect(defectPayload)).rejects.toThrow('Inspection not found');
  });

  it('HTTP 500 with no data: falls back to status code message', async () => {
    axiosClient.post.mockRejectedValueOnce({
      response: { data: undefined, status: 500 },
    });

    await expect(createDefect(defectPayload)).rejects.toThrow('Create defect failed: 500');
  });
});

describe('capture.js - closeInspection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('success: POST /api/v1/inspections/{id}/close_inspection/ and returns result', async () => {
    const mockResponse = {
      id: 42,
      status: 'closed',
      result: 'PASS',
      sync_info: { synced: true },
    };
    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await closeInspection(42);

    expect(axiosClient.post).toHaveBeenCalledOnce();
    expect(axiosClient.post).toHaveBeenCalledWith('/api/v1/inspections/42/close_inspection/');
    expect(result).toEqual(mockResponse);
  });

  it('network error without response: falls back to undefined status', async () => {
    axiosClient.post.mockRejectedValueOnce(new TypeError('Network request failed'));

    await expect(closeInspection(1)).rejects.toThrow('Close inspection failed: undefined');
  });

  it('HTTP 404: throws with error from response body', async () => {
    axiosClient.post.mockRejectedValueOnce({
      response: { data: { error: 'Inspection not found' }, status: 404 },
    });

    await expect(closeInspection(999)).rejects.toThrow('Inspection not found');
  });

  it('HTTP 409: throws with conflict error message', async () => {
    axiosClient.post.mockRejectedValueOnce({
      response: { data: { error: 'Inspection already closed' }, status: 409 },
    });

    await expect(closeInspection(42)).rejects.toThrow('Inspection already closed');
  });

  it('HTTP 500 with no error key: falls back to status code', async () => {
    axiosClient.post.mockRejectedValueOnce({
      response: { data: null, status: 500 },
    });

    await expect(closeInspection(42)).rejects.toThrow('Close inspection failed: 500');
  });

  it('falls back to status code when error key is absent but detail is present', async () => {
    axiosClient.post.mockRejectedValueOnce({
      response: { data: { detail: 'Cannot close: defects pending' }, status: 400 },
    });

    // Source only uses .error key, not .detail
    await expect(closeInspection(42)).rejects.toThrow('Close inspection failed: 400');
  });
});

afterAll(() => vi.restoreAllMocks());
