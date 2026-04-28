import { describe, it, expect, vi } from 'vitest';
import { createElement, useContext } from 'react';
import { render, screen } from '@testing-library/react';
import { useAuth } from './useAuth';
import { AuthProvider } from './AuthContext';

vi.mock('../api/axiosClient', () => ({
  tokenStorage: {
    getAccessToken: () => null,
    setTokens: () => {},
    clear: () => {},
  },
}));

vi.mock('../api/auth', () => ({
  getCurrentUserRequest: () => Promise.resolve(null),
  loginRequest: () => Promise.resolve({}),
  logoutRequest: () => Promise.resolve({}),
}));

describe('useAuth', () => {
  it('should be a function', () => {
    expect(typeof useAuth).toBe('function');
  });

  it('should return auth context values when used inside AuthProvider', () => {
    function DisplayAuth() {
      const auth = useAuth();

      return createElement('div', null,
        createElement('span', { 'data-testid': 'user-type' }, typeof auth.user),
        createElement('span', { 'data-testid': 'loading-type' }, typeof auth.loading),
        createElement('span', { 'data-testid': 'has-login' }, typeof auth.login),
        createElement('span', { 'data-testid': 'has-logout' }, typeof auth.logout),
        createElement('span', { 'data-testid': 'has-is-authenticated' }, typeof auth.isAuthenticated),
      );
    }

    render(createElement(AuthProvider, null,
      createElement(DisplayAuth),
    ));

    expect(screen.getByTestId('user-type')).toHaveTextContent('object');
    expect(screen.getByTestId('loading-type')).toHaveTextContent('boolean');
    expect(screen.getByTestId('has-login')).toHaveTextContent('function');
    expect(screen.getByTestId('has-logout')).toHaveTextContent('function');
    expect(screen.getByTestId('has-is-authenticated')).toHaveTextContent('boolean');
  });
});
