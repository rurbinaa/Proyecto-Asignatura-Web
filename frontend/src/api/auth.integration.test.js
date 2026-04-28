/**
 * Integration tests for auth.js — real HTTP calls intercepted by MSW.
 * No vi.mock() — these tests exercise the full axios → MSW round-trip.
 */
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { server } from '../test/msw/server';
import { loginRequest, getCurrentUserRequest, logoutRequest, mapLoginResponseDto } from './auth';
import { tokenStorage } from './axiosClient';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => {
  server.resetHandlers();
  localStorage.clear();
});
afterAll(() => server.close());

describe('auth integration — login', () => {
  it('returns access/refresh tokens with valid credentials', async () => {
    const credentials = { email: 'test@example.com', password: 'correct' };

    const result = await loginRequest(credentials);

    expect(result).toEqual({
      access: 'fake-access-token',
      refresh: 'fake-refresh-token',
    });
  });

  it('stores returned tokens in localStorage', async () => {
    const credentials = { email: 'test@example.com', password: 'correct' };

    const tokens = await loginRequest(credentials);
    tokenStorage.setTokens(tokens);

    expect(localStorage.getItem('rift-access-token')).toBe('fake-access-token');
    expect(localStorage.getItem('rift-refresh-token')).toBe('fake-refresh-token');
  });

  it('throws when credentials are invalid (401)', async () => {
    const credentials = { email: 'test@example.com', password: 'wrong' };

    await expect(loginRequest(credentials)).rejects.toThrow();
  });
});

describe('auth integration — getCurrentUserRequest', () => {
  it('returns user data when Authorization header is present', async () => {
    localStorage.setItem('rift-access-token', 'valid-token');

    const user = await getCurrentUserRequest();

    expect(user).toEqual({
      id: 1,
      email: 'test@example.com',
      role: 'operator',
    });
  });

  it('fails with 401 when no token is stored', async () => {
    await expect(getCurrentUserRequest()).rejects.toThrow();
  });
});

describe('auth integration — logoutRequest', () => {
  it('succeeds and returns confirmation', async () => {
    const result = await logoutRequest();

    expect(result).toEqual({ detail: 'Logged out' });
  });
});

describe('auth integration — mapLoginResponseDto', () => {
  it('extracts only access and refresh from the DTO', () => {
    const dto = { access: 'token-a', refresh: 'token-r', role: 'manager', extra: true };

    const result = mapLoginResponseDto(dto);

    expect(result).toEqual({ access: 'token-a', refresh: 'token-r' });
  });

  it('handles undefined gracefully', () => {
    expect(mapLoginResponseDto(undefined)).toEqual({
      access: undefined,
      refresh: undefined,
    });
  });
});
