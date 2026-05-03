/**
 * Integration tests for axiosClient — exercises interceptors and HTTP handling
 * via real requests intercepted by MSW at the network level.
 *
 * No vi.mock() — every request goes through axios → MSW.
 */
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../test/msw/server';
import axiosClient, { tokenStorage } from './axiosClient';
import { getCurrentUserRequest } from './auth';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => {
  server.resetHandlers();
  localStorage.clear();
});
afterAll(() => server.close());

describe('request interceptor — Authorization header', () => {
  it('adds Bearer token from localStorage on authenticated requests', async () => {
    localStorage.setItem('rift-access-token', 'my-secret-token');

    const user = await getCurrentUserRequest();

    // The MSW /me/ handler checks for Authorization and returns 200 only
    // when present. If this succeeds, the interceptor did its job.
    expect(user).toEqual({
      id: 1,
      email: 'test@example.com',
      role: 'manager',
    });
  });

  it('does NOT add Authorization header when no token is stored', async () => {
    // The MSW /me/ handler returns 401 when Authorization is absent.
    await expect(getCurrentUserRequest()).rejects.toThrow();
  });
});

describe('request interceptor — FormData Content-Type', () => {
  it('removes application/json Content-Type when payload is FormData', async () => {
    let capturedContentType;

    server.use(
      http.post('http://localhost:8000/api/echo-formdata/', async ({ request }) => {
        capturedContentType = request.headers.get('Content-Type');
        return HttpResponse.json({ ok: true });
      }),
    );

    const formData = new FormData();
    formData.append('field', 'value');

    await axiosClient.post('/api/echo-formdata/', formData);

    // The interceptor deletes Content-Type from axios config, so the runtime
    // (or Node adapter) should NOT send application/json.
    // In Node / MSW, when Content-Type is not explicitly set by axios,
    // the header might be absent or set by the runtime.
    expect(capturedContentType).not.toMatch(/^application\/json/);
  });
});

describe('response interceptor — 401 handling', () => {
  it('clears both tokens from localStorage on 401 response', async () => {
    localStorage.setItem('rift-access-token', 'should-be-cleared');
    localStorage.setItem('rift-refresh-token', 'should-be-cleared');

    // Override /me/ to always return 401 regardless of token
    server.use(
      http.get('http://localhost:8000/api/auth/me/', () => {
        return HttpResponse.json(
          { error: 'Not authenticated' },
          { status: 401 },
        );
      }),
    );

    await expect(getCurrentUserRequest()).rejects.toThrow();

    expect(localStorage.getItem('rift-access-token')).toBeNull();
    expect(localStorage.getItem('rift-refresh-token')).toBeNull();
  });

  it('dispatches auth-unauthorized event on 401', async () => {
    const events = [];
    window.addEventListener('auth-unauthorized', () => events.push('auth-unauthorized'));

    server.use(
      http.get('http://localhost:8000/api/auth/me/', () => {
        return HttpResponse.json(
          { error: 'Not authenticated' },
          { status: 401 },
        );
      }),
    );

    await expect(getCurrentUserRequest()).rejects.toThrow();

    expect(events).toContain('auth-unauthorized');
  });
});

describe('response interceptor — network error', () => {
  it('re-throws network errors without clearing tokens', async () => {
    localStorage.setItem('rift-access-token', 'keep-me');

    server.use(
      http.post('http://localhost:8000/api/network-error/', () => {
        return HttpResponse.error();
      }),
    );

    await expect(
      axiosClient.post('/api/network-error/'),
    ).rejects.toThrow();

    // Network errors (no response object) should NOT clear tokens
    expect(localStorage.getItem('rift-access-token')).toBe('keep-me');
  });
});
