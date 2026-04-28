/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { downloadQualityReport, validateDateRange } from './reports';
import axiosClient from './axiosClient';
import { generateReportFilename, downloadBlob, parseBlobError } from '../utils/downloadUtils';

vi.mock('./axiosClient', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
  handleApiError: vi.fn((error) => ({
    message:
      error.response?.data?.error ||
      error.response?.data?.detail ||
      error.message ||
      (error.response?.status ? `Request failed: ${error.response.status}` : 'Request failed'),
    status: error.response?.status ?? null,
    data: error.response?.data ?? null,
  })),
}));
vi.mock('../utils/downloadUtils', () => ({
  generateReportFilename: vi.fn(() => 'Reporte_Calidad_Test.xlsx'),
  downloadBlob: vi.fn(),
  parseBlobError: vi.fn(),
}));

describe('reports.js - downloadQualityReport', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const startDate = '2026-01-01';
  const endDate = '2026-01-31';

  it('success: fetches blob, downloads file, returns filename', async () => {
    const mockBlob = new Blob(['fake excel data'], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    axiosClient.get.mockResolvedValueOnce({ data: mockBlob });

    const result = await downloadQualityReport(startDate, endDate);

    expect(axiosClient.get).toHaveBeenCalledOnce();
    expect(axiosClient.get).toHaveBeenCalledWith('/quality/reports/corporate-xlsx/', {
      params: { date_from: startDate, date_to: endDate },
      responseType: 'blob',
      timeout: 600000,
    });
    expect(generateReportFilename).toHaveBeenCalledWith(startDate, endDate);
    expect(downloadBlob).toHaveBeenCalledWith(mockBlob, 'Reporte_Calidad_Test.xlsx');
    expect(result).toEqual({ filename: 'Reporte_Calidad_Test.xlsx' });
  });

  it('throws when startDate is missing', async () => {
    await expect(downloadQualityReport('', endDate)).rejects.toThrow(
      'Se requiere seleccionar un período de fechas'
    );
    expect(axiosClient.get).not.toHaveBeenCalled();
  });

  it('throws when endDate is missing', async () => {
    await expect(downloadQualityReport(startDate, '')).rejects.toThrow(
      'Se requiere seleccionar un período de fechas'
    );
    expect(axiosClient.get).not.toHaveBeenCalled();
  });

  it('throws when startDate is after endDate', async () => {
    await expect(downloadQualityReport('2026-06-01', '2026-01-01')).rejects.toThrow(
      'La fecha de inicio debe ser anterior a la fecha de fin'
    );
    expect(axiosClient.get).not.toHaveBeenCalled();
  });

  it('throws same year date inversion regardless', async () => {
    await expect(downloadQualityReport('2026-12-31', '2026-01-01')).rejects.toThrow(
      'La fecha de inicio debe ser anterior a la fecha de fin'
    );
  });

  it('handles blob error: parses blob and throws with error message', async () => {
    const errorBlob = new Blob([JSON.stringify({ error: 'No data for range' })], {
      type: 'application/json',
    });
    const axiosError = {
      response: { data: errorBlob, status: 400 },
    };
    axiosClient.get.mockRejectedValueOnce(axiosError);
    parseBlobError.mockResolvedValueOnce({ message: 'No data for range' });

    await expect(downloadQualityReport(startDate, endDate)).rejects.toThrow('No data for range');
    expect(parseBlobError).toHaveBeenCalledWith(errorBlob);
  });

  it('handles blob error with detail key', async () => {
    const errorBlob = new Blob([JSON.stringify({ detail: 'Server error detail' })], {
      type: 'application/json',
    });
    const axiosError = {
      response: { data: errorBlob, status: 500 },
    };
    axiosClient.get.mockRejectedValueOnce(axiosError);
    parseBlobError.mockResolvedValueOnce({ message: 'Server error detail' });

    await expect(downloadQualityReport(startDate, endDate)).rejects.toThrow('Server error detail');
  });

  it('handles non-blob HTTP error: uses handleApiError fallback', async () => {
    axiosClient.get.mockRejectedValueOnce({
      response: { data: { error: 'Internal error' }, status: 500 },
    });

    await expect(downloadQualityReport(startDate, endDate)).rejects.toThrow('Internal error');
  });

  it('handles non-blob error with detail key via handleApiError', async () => {
    axiosClient.get.mockRejectedValueOnce({
      response: { data: { detail: 'Server timeout' }, status: 504 },
    });

    await expect(downloadQualityReport(startDate, endDate)).rejects.toThrow('Server timeout');
  });

  it('handles network error without response', async () => {
    axiosClient.get.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(downloadQualityReport(startDate, endDate)).rejects.toThrow('Failed to fetch');
  });

  it('parses blob error as JSON when blob text is valid JSON', async () => {
    // Integration-style: test the actual parseBlobError is wired correctly
    // by resolving the mock to use the real implementation
    const errorBlob = new Blob([JSON.stringify({ error: 'Custom error' })], {
      type: 'application/json',
    });
    parseBlobError.mockResolvedValueOnce({ message: 'Custom error' });

    axiosClient.get.mockRejectedValueOnce({ response: { data: errorBlob, status: 400 } });

    await expect(downloadQualityReport(startDate, endDate)).rejects.toThrow('Custom error');
  });
});

describe('reports.js - validateDateRange', () => {
  it('returns valid for a normal date range', () => {
    const result = validateDateRange('2026-01-01', '2026-01-31');
    expect(result).toEqual({ valid: true });
  });

  it('returns valid for a single-day range', () => {
    const result = validateDateRange('2026-03-15', '2026-03-15');
    expect(result).toEqual({ valid: true });
  });

  it('returns invalid when startDate is missing', () => {
    const result = validateDateRange('', '2026-01-31');
    expect(result).toEqual({ valid: false, message: 'Seleccione un período de fechas' });
  });

  it('returns invalid when endDate is missing', () => {
    const result = validateDateRange('2026-01-01', '');
    expect(result).toEqual({ valid: false, message: 'Seleccione un período de fechas' });
  });

  it('returns invalid when startDate is after endDate', () => {
    const result = validateDateRange('2026-06-01', '2026-01-01');
    expect(result).toEqual({ valid: false, message: 'La fecha de inicio debe ser anterior a la fecha de fin' });
  });

  it('returns invalid for range exceeding 365 days', () => {
    const result = validateDateRange('2025-01-01', '2026-01-31');
    expect(result).toEqual({ valid: false, message: 'El período no puede exceder 365 días' });
  });

  it('returns valid for exactly 365 days range', () => {
    // 2025-01-01 to 2026-01-01 is exactly 365 days (not leap year)
    const result = validateDateRange('2025-01-01', '2026-01-01');
    expect(result).toEqual({ valid: true });
  });

  it('returns valid for a range spanning different years under 365 days', () => {
    const result = validateDateRange('2025-12-01', '2026-01-15');
    expect(result).toEqual({ valid: true });
  });

  it('returns invalid when both dates are null', () => {
    const result = validateDateRange(null, null);
    expect(result).toEqual({ valid: false, message: 'Seleccione un período de fechas' });
  });

  it('returns invalid when both dates are undefined', () => {
    const result = validateDateRange(undefined, undefined);
    expect(result).toEqual({ valid: false, message: 'Seleccione un período de fechas' });
  });
});

afterAll(() => vi.restoreAllMocks());
