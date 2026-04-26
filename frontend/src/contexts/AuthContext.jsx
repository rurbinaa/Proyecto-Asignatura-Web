import { createContext, useState, useEffect, useContext, useCallback } from 'react';
import axiosClient, { tokenStorage } from '../api/axiosClient';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkSession = useCallback(async () => {
    if (!tokenStorage.getAccessToken()) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const res = await axiosClient.get('/api/auth/me/');
      setUser(res.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  useEffect(() => {
    const handleUnauthorized = () => {
      tokenStorage.clear();
      setUser(null);
    };

    window.addEventListener('auth-unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth-unauthorized', handleUnauthorized);
  }, []);

  const login = async (credentials) => {
    try {
      const response = await axiosClient.post('/api/auth/login/', credentials);
      tokenStorage.setTokens({
        access: response.data.access,
        refresh: response.data.refresh,
      });
      setLoading(true);
      await checkSession();
      return true;
    } catch {
      tokenStorage.clear();
      setUser(null);
      setLoading(false);
      return false;
    }

  };

  const logout = async () => {
    try {
      await axiosClient.post('/api/auth/logout/');
    } catch {}
    tokenStorage.clear();
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
