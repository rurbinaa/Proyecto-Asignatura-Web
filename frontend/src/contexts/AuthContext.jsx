import { useState, useEffect, useCallback, createContext } from 'react';
import { tokenStorage } from '../api/axiosClient';
import { getCurrentUserRequest, loginRequest, logoutRequest } from '../api/auth';

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext();

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
      const userDto = await getCurrentUserRequest();
      setUser(userDto);
    } catch {
      tokenStorage.clear();
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
      const tokenDto = await loginRequest(credentials);
      tokenStorage.setTokens({
        access: tokenDto.access,
        refresh: tokenDto.refresh,
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
      await logoutRequest();
    } catch (error) {
      void error;
    }
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
