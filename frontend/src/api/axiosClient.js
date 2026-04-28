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

export const handleApiError = (error) => {
  const data = error.response?.data;
  const message =
    data?.error ||
    data?.detail ||
    error.message ||
    (error.response?.status ? `Request failed: ${error.response.status}` : 'Request failed');

  return {
    message,
    status: error.response?.status ?? null,
    data: data ?? null,
  };
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

export default axiosClient;
