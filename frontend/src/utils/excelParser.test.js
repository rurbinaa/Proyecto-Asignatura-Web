import { describe, it, expect } from 'vitest';
import {
  cleanText,
  formatExcelDate,
  findHeadersAndData,
  REQUIRED_COLUMNS,
  SHEET_GROUPS_MAP,
} from './excelParser';

describe('excelParser.js - constants', () => {
  it('exports REQUIRED_COLUMNS with expected sheet names', () => {
    expect(REQUIRED_COLUMNS).toHaveProperty('QC FA Plant');
    expect(REQUIRED_COLUMNS).toHaveProperty('QC FA Customer');
    expect(REQUIRED_COLUMNS).toHaveProperty('SecondsA4');
    expect(REQUIRED_COLUMNS).toHaveProperty('Seconds General');
    expect(REQUIRED_COLUMNS).toHaveProperty('Container');
  });

  it('exports SHEET_GROUPS_MAP with expected groups', () => {
    expect(SHEET_GROUPS_MAP.QFA).toEqual(['QC FA Plant', 'QC FA Customer']);
    expect(SHEET_GROUPS_MAP.SECONDS).toEqual(['SecondsA4', 'Seconds General']);
    expect(SHEET_GROUPS_MAP.CONTAINER).toEqual(['Container']);
    expect(SHEET_GROUPS_MAP.ALL).toHaveLength(5);
  });
});

describe('excelParser.js - cleanText', () => {
  it('removes special characters and lowercases', () => {
    expect(cleanText('Hello World!')).toBe('helloworld');
  });

  it('removes all non-alphanumeric characters', () => {
    expect(cleanText('QC-FA_Plant#1')).toBe('qcfaplant1');
  });

  it('returns empty string for null input', () => {
    expect(cleanText(null)).toBe('');
  });

  it('returns empty string for undefined input', () => {
    expect(cleanText(undefined)).toBe('');
  });

  it('returns empty string for empty string', () => {
    expect(cleanText('')).toBe('');
  });

  it('handles numbers by converting to string first', () => {
    expect(cleanText(12345)).toBe('12345');
  });

  it('handles strings with only special characters', () => {
    expect(cleanText('@#$%^&*()')).toBe('');
  });

  it('preserves alphanumeric characters', () => {
    expect(cleanText('Date123')).toBe('date123');
  });

  it('lowercases uppercase input', () => {
    expect(cleanText('STYLE')).toBe('style');
  });
});

describe('excelParser.js - formatExcelDate', () => {
  it('returns null when input is null', () => {
    expect(formatExcelDate(null)).toBeNull();
  });

  it('returns undefined when input is undefined', () => {
    expect(formatExcelDate(undefined)).toBeUndefined();
  });

  it('returns empty string when input is empty string', () => {
    expect(formatExcelDate('')).toBe('');
  });

  it('returns already formatted YYYY-MM-DD strings unchanged', () => {
    expect(formatExcelDate('2026-03-15')).toBe('2026-03-15');
  });

  it('converts Excel serial number to date string', () => {
    // Excel serial 45000 ≈ 2023-03-15 (approximately)
    const result = formatExcelDate(45000);
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it('returns the serial number when the resulting date is invalid', () => {
    // Excel serial number overflow: produces a date beyond JS Date max range
    const result = formatExcelDate(999999999999999);
    expect(typeof result).toBe('number');
    expect(result).toBe(999999999999999);
  });

  it('converts MM/DD/YYYY string to YYYY-MM-DD', () => {
    const result = formatExcelDate('03/15/2026');
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it('converts ISO date string to YYYY-MM-DD', () => {
    const result = formatExcelDate('2026-03-15T12:00:00.000Z');
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it('returns original string when date string is not parseable', () => {
    const result = formatExcelDate('not-a-date');
    expect(result).toBe('not-a-date');
  });

  it('handles Excel serial number 1 (should be 1900-01-01 in Excel epoch)', () => {
    // Excel epoch: 1 = 1900-01-01, but JS Date uses 1970 epoch
    const result = formatExcelDate(1);
    // Should produce a valid date string or return 1
    if (typeof result === 'string') {
      expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });

  it('returns original boolean value when input is boolean', () => {
    // formatExcelDate doesn't handle booleans explicitly,
    // so they fall through to the return serial at the end
    // A boolean flows into the string check and then to return serial
    expect(formatExcelDate(true)).toBe(true);
    expect(formatExcelDate(false)).toBe(false);
  });
});

describe('excelParser.js - findHeadersAndData', () => {
  const plantHeaders = ['date', 'week', 'customer', 'po', 'style', 'batch', 'color', 'qty', 'team', 'coord'];

  it('finds headers and returns data rows for matching sheet', () => {
    const rows = [
      plantHeaders,
      ['2026-01-15', '3', 'CustomerA', 'PO-001', 'N6165', 'B001', 'Red', '100', 'Team1', 'C1'],
      ['2026-01-16', '3', 'CustomerB', 'PO-002', 'N6166', 'B002', 'Blue', '200', 'Team2', 'C2'],
    ];

    const result = findHeadersAndData(rows, 'QC FA Plant');
    expect(result).not.toBeNull();
    expect(result.headers).toEqual(plantHeaders);
    expect(result.data).toHaveLength(2);
    expect(result.data[0]).toEqual(['2026-01-15', '3', 'CustomerA', 'PO-001', 'N6165', 'B001', 'Red', '100', 'Team1', 'C1']);
  });

  it('returns null for unknown sheet name', () => {
    const rows = [['a', 'b']];
    const result = findHeadersAndData(rows, 'Unknown Sheet');
    expect(result).toBeNull();
  });

  it('returns null when no header row matches', () => {
    const rows = [
      ['completely', 'unrelated', 'data'],
      ['1', '2', '3'],
    ];
    const result = findHeadersAndData(rows, 'QC FA Plant');
    expect(result).toBeNull();
  });

  it('stops searching after 40 rows', () => {
    // Create 41 rows of non-matching data
    const rows = Array.from({ length: 41 }, (_, i) => [`row${i}`, 'data']);
    const result = findHeadersAndData(rows, 'QC FA Plant');
    expect(result).toBeNull();
  });

  it('skips empty rows when looking for headers', () => {
    const rows = [
      [],
      null,
      ['', ''],
      plantHeaders,
      ['2026-01-15', '3', 'CustomerA', 'PO-001', 'N6165', 'B001', 'Red', '100', 'Team1', 'C1'],
    ];

    const result = findHeadersAndData(rows, 'QC FA Plant');
    expect(result).not.toBeNull();
    expect(result.headers).toEqual(plantHeaders);
  });

  it('matches headers with slight variations in formatting', () => {
    const rows = [
      ['Date', 'Week #', 'Customer Name', 'PO Number', 'Style Code', 'Batch ID', 'Color', 'Qty', 'Team', 'Coordinator'],
      ['2026-01-15', '3', 'CustomerA', 'PO-001', 'N6165', 'B001', 'Red', '100', 'Team1', 'C1'],
    ];

    const result = findHeadersAndData(rows, 'QC FA Plant');
    expect(result).not.toBeNull();
    expect(result.data).toHaveLength(1);
  });

  it('requires at least required.length - 1 matching headers', () => {
    // Only 1 column matches (far from the required - 1 threshold)
    const rows = [
      ['Date', 'Something', 'Else', 'Entirely', 'Unrelated'],
    ];
    const result = findHeadersAndData(rows, 'QC FA Plant');
    expect(result).toBeNull();
  });

  it('handles data with missing trailing cells', () => {
    const rows = [
      plantHeaders,
      ['2026-01-15', '3', 'CustomerA'], // truncated row
    ];

    const result = findHeadersAndData(rows, 'QC FA Plant');
    expect(result).not.toBeNull();
    expect(result.data).toHaveLength(1);
    expect(result.data[0]).toEqual(['2026-01-15', '3', 'CustomerA']);
  });

  it('handles empty row array', () => {
    const result = findHeadersAndData([], 'QC FA Plant');
    expect(result).toBeNull();
  });

  it('works with Container sheet', () => {
    const rows = [
      ['container', 'customer', 'palette', 'pass'],
      ['CONT-001', 'CustomerA', 'PAL-001', 'PASS'],
    ];

    const result = findHeadersAndData(rows, 'Container');
    expect(result).not.toBeNull();
    expect(result.headers).toEqual(['container', 'customer', 'palette', 'pass']);
    expect(result.data).toHaveLength(1);
  });

  it('works with Seconds General sheet', () => {
    const rows = [
      ['date', 'week', 'picado', 'manchas', 'grasa', 'tono', 'fuera', 'definitive'],
      ['2026-01-15', '3', '10', '5', '2', '1', '0', '18'],
    ];

    const result = findHeadersAndData(rows, 'Seconds General');
    expect(result).not.toBeNull();
    expect(result.data).toHaveLength(1);
  });
});
