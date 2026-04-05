/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { uploadForPreview, confirmSession, rejectSession } from './excel.js';

// Mock fetch globally
global.fetch = vi.fn();

describe('excel.js - uploadForPreview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('success path: POST with FormData containing file returns parsed response', async () => {
    const mockFile = new File(['test content'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const mockResponse = {
      session_id: 1,
      status: 'pending',
      preview: { headers: ['A', 'B'], rows: [[1, 2]] },
      warnings: [],
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await uploadForPreview(mockFile);

    expect(global.fetch).toHaveBeenCalledOnce();
    const [url, options] = global.fetch.mock.calls[0];
    expect(options.method).toBe('POST');
    expect(url).toContain('/quality/excel/preview/');
    expect(options.body).toBeInstanceOf(FormData);
    const appendedFile = options.body.get('file');
    expect(appendedFile).toBeInstanceOf(File);
    expect(appendedFile.name).toBe(mockFile.name);
    expect(appendedFile.type).toBe(mockFile.type);
    expect(result).toEqual(mockResponse);
  });

  it('URL encodes special characters in filename', async () => {
    const mockFile = new File(['test'], 'file (1).xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ session_id: 1, status: 'pending', preview: {}, warnings: [] }),
    });

    await uploadForPreview(mockFile);

    const [url] = global.fetch.mock.calls[0];
    expect(url).toContain('file%20(1).xlsx');
  });

  it('network error: throws when fetch rejects', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    global.fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(uploadForPreview(mockFile)).rejects.toThrow('Failed to fetch');
  });

  it('HTTP 500 error: extracts error message from JSON body', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ error: 'Internal Server Error' }),
    });

    await expect(uploadForPreview(mockFile)).rejects.toThrow('Internal Server Error');
  });

  it('HTTP 500 with malformed JSON: falls back to status code', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.reject(new SyntaxError('Unexpected token')),
    });

    await expect(uploadForPreview(mockFile)).rejects.toThrow('Internal Server Error');
  });

  it('malformed JSON on success: propagates JSON parse error', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.reject(new SyntaxError('Unexpected token')),
    });

    await expect(uploadForPreview(mockFile)).rejects.toThrow('Unexpected token');
  });

  it('HTTP 400: throws with specific error message from JSON', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ error: 'Invalid file format' }),
    });

    await expect(uploadForPreview(mockFile)).rejects.toThrow('Invalid file format');
  });

  it('Response missing session_id: returns incomplete response (caller handles undefined)', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ status: 'pending' }), // no session_id
    });

    const result = await uploadForPreview(mockFile);

    expect(global.fetch).toHaveBeenCalledOnce();
    expect(result).toEqual({ status: 'pending' });
    expect(result.session_id).toBeUndefined();
  });
});

describe('excel.js - confirmSession', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('success path: POST with JSON header and correct URL returns response', async () => {
    const mockResponse = {
      session_id: 42,
      status: 'confirmed',
      message: 'Changes applied successfully',
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await confirmSession(42);

    expect(global.fetch).toHaveBeenCalledOnce();
    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toContain('/quality/excel/confirm/42/');
    expect(options.method).toBe('POST');
    expect(options.headers['Content-Type']).toBe('application/json');
    expect(result).toEqual(mockResponse);
  });

  it('404 error: throws "Session not found" message', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ error: 'Session not found' }),
    });

    await expect(confirmSession(999)).rejects.toThrow('Session not found');
  });

  it('fallback error: uses statusText when JSON is invalid', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.reject(new SyntaxError('Unexpected token')),
    });

    await expect(confirmSession(1)).rejects.toThrow('Internal Server Error');
  });

  it('HTTP 500: throws with status code when no error message', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({}),
    });

    await expect(confirmSession(1)).rejects.toThrow('Confirm failed: 500');
  });
});

describe('excel.js - rejectSession', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('success path: DELETE with correct URL returns response', async () => {
    const mockResponse = {
      session_id: 42,
      status: 'rejected',
      message: 'Changes discarded',
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await rejectSession(42);

    expect(global.fetch).toHaveBeenCalledOnce();
    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toContain('/quality/excel/reject/42/');
    expect(options.method).toBe('DELETE');
    expect(result).toEqual(mockResponse);
  });

  it('error path: throws with appropriate message on failed rejection', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ error: 'Session not found' }),
    });

    await expect(rejectSession(999)).rejects.toThrow('Session not found');
  });

  it('HTTP 500 error: throws with status code on server error', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({ error: 'Server error' }),
    });

    await expect(rejectSession(1)).rejects.toThrow('Server error');
  });
});

afterAll(() => vi.restoreAllMocks());
