import axios from 'axios';

const axiosClient = axios.create({
  baseURL: 'http://localhost:8000/api/',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      window.dispatchEvent(new Event('auth-unauthorized'));
    }
    return Promise.reject(error);
  }
);

export default axiosClient;

export const AXIOS_CODES = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500,
};

export const isAuthError = (error) => {
  return error.response?.status === AXIOS_CODES.UNAUTHORIZED;
};

export const handleApiError = (error) => {
  if (isAuthError(error)) {
    window.dispatchEvent(new Event('auth-unauthorized'));
    return { message: 'Sesión expirada. Por favor, inicie sesión nuevamente.' };
  }
  
  if (error.response?.data?.error) {
    return { message: error.response.data.error };
  }
  
  if (error.response?.data?.detail) {
    return { message: error.response.data.detail };
  }
  
  if (!error.response) {
    return { message: 'Error de conexión. Verifique su red.' };
  }
  
  return { message: `Error ${error.response.status}: ${error.response.statusText}` };
};