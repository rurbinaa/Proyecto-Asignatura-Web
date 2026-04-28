import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  mapLoginResponseDto,
  mapCurrentUserDto,
  loginRequest,
  getCurrentUserRequest,
  logoutRequest,
} from './auth';
import axiosClient from './axiosClient';

vi.mock('./axiosClient');

describe('auth adapter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maps login response DTO to token shape consumed by AuthContext', () => {
    const dto = { access: 'token-a', refresh: 'token-r', role: 'manager' };
    expect(mapLoginResponseDto(dto)).toEqual({ access: 'token-a', refresh: 'token-r' });
  });

  it('maps current user DTO preserving role contract', () => {
    const dto = {
      id: 1,
      email: 'manager@uniwell.com',
      first_name: 'Manager',
      last_name: 'User',
      role: 'manager',
      is_manager: true,
      is_operator: false,
    };

    expect(mapCurrentUserDto(dto)).toEqual(dto);
  });

  it('uses auth endpoints through adapter requests', async () => {
    axiosClient.post.mockResolvedValueOnce({ data: { access: 'a', refresh: 'r' } });
    axiosClient.get.mockResolvedValueOnce({ data: { role: 'manager' } });
    axiosClient.post.mockResolvedValueOnce({ data: { detail: 'ok' } });

    await loginRequest({ email: 'manager@uniwell.com', password: '1234' });
    await getCurrentUserRequest();
    await logoutRequest();

    expect(axiosClient.post).toHaveBeenCalledWith('/api/auth/login/', {
      email: 'manager@uniwell.com',
      password: '1234',
    });
    expect(axiosClient.get).toHaveBeenCalledWith('/api/auth/me/');
    expect(axiosClient.post).toHaveBeenLastCalledWith('/api/auth/logout/');
  });
});
