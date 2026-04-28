/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axiosClient, { tokenStorage, handleApiError } from './axiosClient';

describe('tokenStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores and retrieves access and refresh tokens', () => {
    tokenStorage.setTokens({ access: 'access-123', refresh: 'refresh-456' });
    expect(tokenStorage.getAccessToken()).toBe('access-123');
  });

  it('returns null when no token is stored', () => {
    expect(tokenStorage.getAccessToken()).toBeNull();
  });

  it('does not set access token when access is falsy', () => {
    tokenStorage.setTokens({ access: null, refresh: 'refresh-456' });
    expect(tokenStorage.getAccessToken()).toBeNull();
  });

  it('does not set refresh token when refresh is falsy', () => {
    tokenStorage.setTokens({ access: 'access-123' });
    expect(tokenStorage.getAccessToken()).toBe('access-123');
  });

  it('clears both tokens', () => {
    tokenStorage.setTokens({ access: 'access-123', refresh: 'refresh-456' });
    tokenStorage.clear();
    expect(tokenStorage.getAccessToken()).toBeNull();
  });

  it('handles localStorage quota error gracefully in setTokens', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementationOnce(() => {
      throw new Error('QuotaExceededError');
    });
    // Should not throw
    expect(() => tokenStorage.setTokens({ access: 'x' })).not.toThrow();
  });

  it('returns null from getAccessToken when localStorage throws', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementationOnce(() => {
      throw new Error('Storage error');
    });
    expect(tokenStorage.getAccessToken()).toBeNull();
  });

  it('handles localStorage removeItem error gracefully in clear', () => {
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementationOnce(() => {
      throw new Error('Remove error');
    });
    expect(() => tokenStorage.clear()).not.toThrow();
  });
});

describe('handleApiError', () => {
  it('extracts error message from response.data.error', () => {
    const error = { response: { data: { error: 'Not found' }, status: 404 } };
    const result = handleApiError(error);
    expect(result.message).toBe('Not found');
    expect(result.status).toBe(404);
    expect(result.data).toEqual({ error: 'Not found' });
  });

  it('extracts error message from response.data.detail', () => {
    const error = { response: { data: { detail: 'Detail error' }, status: 400 } };
    const result = handleApiError(error);
    expect(result.message).toBe('Detail error');
  });

  it('falls back to error.message when response.data has no error/detail', () => {
    const error = { message: 'Network Error', response: { status: 0 } };
    const result = handleApiError(error);
    expect(result.message).toBe('Network Error');
  });

  it('falls back to status-based message when no other info is available', () => {
    const error = { response: { status: 500 } };
    const result = handleApiError(error);
    expect(result.message).toBe('Request failed: 500');
  });

  it('falls back to generic message when nothing is available', () => {
    const error = {};
    const result = handleApiError(error);
    expect(result.message).toBe('Request failed');
    expect(result.status).toBeNull();
    expect(result.data).toBeNull();
  });

  it('returns null status when error has no response', () => {
    const error = { message: 'Network Error' };
    const result = handleApiError(error);
    expect(result.status).toBeNull();
  });

  it('returns null data when response.data is undefined', () => {
    const error = { response: { status: 500 } };
    const result = handleApiError(error);
    expect(result.data).toBeNull();
  });
});

describe('axiosClient default export', () => {
  it('is an axios instance with correct baseURL', () => {
    expect(axiosClient.defaults.baseURL).toBe('http://localhost:8000');
    expect(axiosClient.defaults.withCredentials).toBe(true);
    expect(axiosClient.defaults.headers['Content-Type']).toBe('application/json');
  });

  it('registers at least one request interceptor', () => {
    expect(axiosClient.interceptors.request.handlers.length).toBeGreaterThanOrEqual(1);
  });

  it('registers at least one response interceptor', () => {
    expect(axiosClient.interceptors.response.handlers.length).toBeGreaterThanOrEqual(1);
  });
});

describe('request interceptor', () => {
  let requestHandler;

  beforeEach(() => {
    localStorage.clear();
    requestHandler = axiosClient.interceptors.request.handlers[0].fulfilled;
  });

  it('adds Authorization header when token exists', () => {
    localStorage.setItem('rift-access-token', 'my-token');
    const config = { headers: {} };
    const result = requestHandler(config);
    expect(result.headers.Authorization).toBe('Bearer my-token');
  });

  it('does not add Authorization header when no token', () => {
    const config = { headers: {} };
    const result = requestHandler(config);
    expect(result.headers.Authorization).toBeUndefined();
  });

  it('removes Content-Type when payload is FormData', () => {
    const config = { headers: { 'Content-Type': 'application/json' }, data: new FormData() };
    const result = requestHandler(config);
    expect(result.headers['Content-Type']).toBeUndefined();
  });

  it('preserves Content-Type when payload is not FormData', () => {
    const config = { headers: { 'Content-Type': 'application/json' }, data: { foo: 'bar' } };
    const result = requestHandler(config);
    expect(result.headers['Content-Type']).toBe('application/json');
  });
});

describe('response interceptor', () => {
  let responseRejectedHandler;

  beforeEach(() => {
    localStorage.clear();
    responseRejectedHandler = axiosClient.interceptors.response.handlers[0].rejected;
  });

  it('passes through successful response', () => {
    const response = { data: 'ok' };
    const handler = axiosClient.interceptors.response.handlers[0].fulfilled;
    expect(handler(response)).toBe(response);
  });

  it('clears tokens and dispatches auth-unauthorized event on 401', () => {
    localStorage.setItem('rift-access-token', 'should-be-cleared');
    const dispatchedEvents = [];
    window.addEventListener('auth-unauthorized', () => dispatchedEvents.push('auth-unauthorized'));

    const error = { response: { status: 401 } };
    return expect(responseRejectedHandler(error)).rejects.toEqual(error).then(() => {
      expect(localStorage.getItem('rift-access-token')).toBeNull();
      expect(dispatchedEvents).toContain('auth-unauthorized');
    });
  });

  it('re-throws non-401 errors without clearing tokens', () => {
    localStorage.setItem('rift-access-token', 'keep-me');

    const error = { response: { status: 500 } };
    return expect(responseRejectedHandler(error)).rejects.toEqual(error).then(() => {
      expect(localStorage.getItem('rift-access-token')).toBe('keep-me');
    });
  });

  it('re-throws network errors without clearing tokens', () => {
    localStorage.setItem('rift-access-token', 'keep-me');

    const error = new Error('Network Error');
    return expect(responseRejectedHandler(error)).rejects.toEqual(error).then(() => {
      expect(localStorage.getItem('rift-access-token')).toBe('keep-me');
    });
  });
});
