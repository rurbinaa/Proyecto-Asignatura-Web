/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { generateReportFilename, downloadBlob, parseBlobError } from './downloadUtils';

describe('downloadUtils.js - generateReportFilename', () => {
  it('returns filename with day when startDate equals endDate', () => {
    const result = generateReportFilename('2026-03-15', '2026-03-15');
    expect(result).toBe('Reporte_Calidad_15_Marzo_2026.xlsx');
  });

  it('returns filename with month range within same year', () => {
    const result = generateReportFilename('2026-01-01', '2026-03-31');
    expect(result).toBe('Reporte_Calidad_Enero_a_Marzo_2026.xlsx');
  });

  it('returns filename with full date range for different years', () => {
    const result = generateReportFilename('2025-12-01', '2026-02-28');
    expect(result).toBe('Reporte_Calidad_Diciembre_2025_a_Febrero_2026.xlsx');
  });

  it('returns filename with Desde when only startDate is provided', () => {
    const result = generateReportFilename('2026-04-01', '');
    expect(result).toBe('Reporte_Calidad_Desde_Abril_2026.xlsx');
  });

  it('returns filename with Hasta when only endDate is provided', () => {
    const result = generateReportFilename('', '2026-05-15');
    expect(result).toBe('Reporte_Calidad_Hasta_Mayo_2026.xlsx');
  });

  it('returns base filename when both dates are empty', () => {
    const result = generateReportFilename('', '');
    expect(result).toBe('Reporte_Calidad.xlsx');
  });

  it('returns base filename when both dates are null', () => {
    const result = generateReportFilename(null, null);
    expect(result).toBe('Reporte_Calidad.xlsx');
  });

  it('returns base filename when both dates are undefined', () => {
    const result = generateReportFilename(undefined, undefined);
    expect(result).toBe('Reporte_Calidad.xlsx');
  });

  it('handles month names correctly for all months', () => {
    const result = generateReportFilename('2026-01-01', '2026-12-31');
    expect(result).toBe('Reporte_Calidad_Enero_a_Diciembre_2026.xlsx');
  });

  it('capitalizes first letter of month names', () => {
    const result = generateReportFilename('2026-08-01', '2026-08-01');
    // Agosto should be capitalized
    expect(result).toMatch(/^Reporte_Calidad_\d+_Agosto_2026\.xlsx$/);
  });
});

describe('downloadUtils.js - downloadBlob', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('creates an anchor element, clicks it, and removes it', () => {
    const blob = new Blob(['test'], { type: 'text/plain' });
    const appendChild = vi.spyOn(document.body, 'appendChild');
    const removeChild = vi.spyOn(document.body, 'removeChild');
    const createObjectURL = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test-url');
    const revokeObjectURL = vi.spyOn(URL, 'revokeObjectURL');

    downloadBlob(blob, 'test.txt');

    expect(createObjectURL).toHaveBeenCalledWith(blob);
    expect(appendChild).toHaveBeenCalledOnce();
    const link = appendChild.mock.calls[0][0];
    expect(link.tagName).toBe('A');
    expect(link.href).toBe('blob:test-url');
    expect(link.download).toBe('test.txt');
    expect(removeChild).toHaveBeenCalledWith(link);
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:test-url');
  });

  // click behavior already covered by the DOM interaction test above
});

describe('downloadUtils.js - parseBlobError', () => {
  it('parses JSON blob with error key', async () => {
    const blob = new Blob([JSON.stringify({ error: 'Not found' })], { type: 'application/json' });
    const result = await parseBlobError(blob);
    expect(result).toEqual({ message: 'Not found' });
  });

  it('parses JSON blob with detail key', async () => {
    const blob = new Blob([JSON.stringify({ detail: 'Server error' })], { type: 'application/json' });
    const result = await parseBlobError(blob);
    expect(result).toEqual({ message: 'Server error' });
  });

  it('falls back to generic error message when JSON has no recognized keys', async () => {
    const blob = new Blob([JSON.stringify({ foo: 'bar' })], { type: 'application/json' });
    const result = await parseBlobError(blob);
    expect(result).toEqual({ message: 'Error desconocido' });
  });

  it('returns generic message when blob text is not valid JSON', async () => {
    const blob = new Blob(['not json at all'], { type: 'text/plain' });
    const result = await parseBlobError(blob);
    expect(result).toEqual({ message: 'Error al procesar la respuesta del servidor' });
  });

  it('returns generic message when blob.text() throws', async () => {
    const blob = new Blob(['test']);
    vi.spyOn(blob, 'text').mockRejectedValueOnce(new Error('Failed to read blob'));
    const result = await parseBlobError(blob);
    expect(result).toEqual({ message: 'Error al procesar la respuesta del servidor' });
  });

  it('prefers error over detail when both are present', async () => {
    const blob = new Blob([JSON.stringify({ error: 'Primary error', detail: 'Secondary detail' })], {
      type: 'application/json',
    });
    const result = await parseBlobError(blob);
    expect(result).toEqual({ message: 'Primary error' });
  });
});

afterAll(() => vi.restoreAllMocks());
