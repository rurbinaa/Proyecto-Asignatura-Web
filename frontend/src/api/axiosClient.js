import axios from 'axios';

const ACCESS_TOKEN_KEY = 'rift-access-token';
const REFRESH_TOKEN_KEY = 'rift-refresh-token';

const axiosClient = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

const safeStorage = {
  get(key) {
    try {
      return window.localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  set(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch {}
  },
  remove(key) {
    try {
      window.localStorage.removeItem(key);
    } catch {}
  },
};

export const tokenStorage = {
  getAccessToken() {
    return safeStorage.get(ACCESS_TOKEN_KEY);
  },
  setTokens({ access, refresh }) {
    if (access) {
      safeStorage.set(ACCESS_TOKEN_KEY, access);
    }
    if (refresh) {
      safeStorage.set(REFRESH_TOKEN_KEY, refresh);
    }
  },
  clear() {
    safeStorage.remove(ACCESS_TOKEN_KEY);
    safeStorage.remove(REFRESH_TOKEN_KEY);
  },
};

axiosClient.interceptors.request.use((config) => {
  const token = tokenStorage.getAccessToken();

  if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

axiosClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      tokenStorage.clear();
      window.dispatchEvent(new Event('auth-unauthorized'));
    }
    return Promise.reject(error);
  }
);

export const handleApiError = (error) => {
  if (error.response?.data?.detail) {
    return { message: error.response.data.detail };
  }

  if (error.response?.data?.error) {
    return { message: error.response.data.error };
  }

  if (error.message) {
    return { message: error.message };
  }

  return { message: 'Unexpected error' };
};

export default axiosClient;
