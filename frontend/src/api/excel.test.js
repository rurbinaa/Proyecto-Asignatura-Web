/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { uploadForPreview, confirmSession, rejectSession } from './excel.js';
import axiosClient from './axiosClient';

vi.mock('./axiosClient');

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

    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });
    const result = await uploadForPreview(mockFile);
    expect(axiosClient.post).toHaveBeenCalledOnce();
    const [url, formData] = axiosClient.post.mock.calls[0];
    expect(url).toContain('/quality/excel/preview/');
    expect(formData).toBeInstanceOf(FormData);
    const appendedFile = formData.get('file');
    expect(appendedFile).toBeInstanceOf(File);
    expect(appendedFile.name).toBe(mockFile.name);
    expect(appendedFile.type).toBe(mockFile.type);
    expect(result).toEqual(mockResponse);
  });

  it('URL encodes special characters in filename', async () => {
    const mockFile = new File(['test'], 'file (1).xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    axiosClient.post.mockResolvedValueOnce({ data: { session_id: 1, status: 'pending', preview: {}, warnings: [] } });
    await uploadForPreview(mockFile);
    const [url] = axiosClient.post.mock.calls[0];
    expect(url).toContain('file%20(1).xlsx');
  });

  it('network error: throws when fetch rejects', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    axiosClient.post.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    await expect(uploadForPreview(mockFile)).rejects.toThrow('Failed to fetch');
  });

  it('HTTP 500 error: extracts error message from JSON body', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    axiosClient.post.mockRejectedValueOnce({ response: { data: { error: 'Internal Server Error' }, status: 500 } });
    await expect(uploadForPreview(mockFile)).rejects.toThrow('Internal Server Error');
  });

  it('HTTP 500 with malformed JSON: falls back to status code', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    axiosClient.post.mockRejectedValueOnce({ response: { data: undefined, status: 500, statusText: 'Internal Server Error' } });
    await expect(uploadForPreview(mockFile)).rejects.toThrow('Preview failed: 500');
  });

  it('malformed JSON on success: propagates JSON parse error', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    axiosClient.post.mockRejectedValueOnce(new SyntaxError('Unexpected token'));
    await expect(uploadForPreview(mockFile)).rejects.toThrow('Unexpected token');
  });

  it('HTTP 400: throws with specific error message from JSON', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    axiosClient.post.mockRejectedValueOnce({ response: { data: { error: 'Invalid file format' }, status: 400 } });
    await expect(uploadForPreview(mockFile)).rejects.toThrow('Invalid file format');
  });

  it('Response missing session_id: returns incomplete response (caller handles undefined)', async () => {
    const mockFile = new File(['test'], 'test.xlsx');

    axiosClient.post.mockResolvedValueOnce({ data: { status: 'pending' } });
    const result = await uploadForPreview(mockFile);
    expect(axiosClient.post).toHaveBeenCalledOnce();
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

    axiosClient.post.mockResolvedValueOnce({ data: mockResponse });
    const result = await confirmSession(42);
    expect(axiosClient.post).toHaveBeenCalledOnce();
    const [url] = axiosClient.post.mock.calls[0];
    expect(url).toContain('/quality/excel/confirm/42/');
    expect(result).toEqual(mockResponse);
  });

  it('404 error: throws "Session not found" message', async () => {
    axiosClient.post.mockRejectedValueOnce({ response: { data: { error: 'Session not found' }, status: 404 } });
    await expect(confirmSession(999)).rejects.toThrow('Session not found');
  });

  it('fallback error: uses statusText when JSON is invalid', async () => {
    axiosClient.post.mockRejectedValueOnce({ response: { data: undefined, status: 500, statusText: 'Internal Server Error' } });
    await expect(confirmSession(1)).rejects.toThrow('Confirm failed: 500');
  });

  it('HTTP 500: throws with status code when no error message', async () => {
    axiosClient.post.mockRejectedValueOnce({ response: { data: {}, status: 500, statusText: 'Internal Server Error' } });
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

    axiosClient.delete.mockResolvedValueOnce({ data: mockResponse });
    const result = await rejectSession(42);
    expect(axiosClient.delete).toHaveBeenCalledOnce();
    const [url] = axiosClient.delete.mock.calls[0];
    expect(url).toContain('/quality/excel/reject/42/');
    expect(result).toEqual(mockResponse);
  });

  it('error path: throws with appropriate message on failed rejection', async () => {
    axiosClient.delete.mockRejectedValueOnce({ response: { data: { error: 'Session not found' }, status: 404 } });
    await expect(rejectSession(999)).rejects.toThrow('Session not found');
  });

  it('HTTP 500 error: throws with status code on server error', async () => {
    axiosClient.delete.mockRejectedValueOnce({ response: { data: { error: 'Server error' }, status: 500 } });
    await expect(rejectSession(1)).rejects.toThrow('Server error');
  });
});

afterAll(() => vi.restoreAllMocks());
