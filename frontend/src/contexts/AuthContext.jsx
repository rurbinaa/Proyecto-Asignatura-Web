import { createContext, useState, useEffect, useContext, useCallback } from 'react';
import axiosClient from '../api/axiosClient';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Task 1: Verify session on mount
  const checkSession = useCallback(async () => {
    try {
      const res = await axiosClient.get('auth/me/');
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

  // Task 4: Listen to the global 401 event
  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
    };

    window.addEventListener('auth-unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth-unauthorized', handleUnauthorized);
  }, []);

  const login = async (credentials) => {
    try {
      await axiosClient.post('auth/login/', credentials);
      await checkSession();
      return true;
    } catch {
      return false;
    }
  };

  const logout = async () => {
    try {
      await axiosClient.post('auth/logout/');
    } catch {}
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