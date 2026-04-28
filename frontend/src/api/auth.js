import axiosClient from './axiosClient';

export function mapLoginResponseDto(dto) {
  return {
    access: dto?.access,
    refresh: dto?.refresh,
  };
}

export function mapCurrentUserDto(dto) {
  return dto;
}

export async function loginRequest(credentials) {
  const response = await axiosClient.post('/api/auth/login/', credentials);
  return mapLoginResponseDto(response.data);
}

export async function getCurrentUserRequest() {
  const response = await axiosClient.get('/api/auth/me/');
  return mapCurrentUserDto(response.data);
}

export async function logoutRequest() {
  const response = await axiosClient.post('/api/auth/logout/');
  return response.data;
}
