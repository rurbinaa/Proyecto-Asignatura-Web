/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { useContext, useState, useCallback } from 'react';
import { AuthContext, AuthProvider } from './AuthContext';

// ---------------------------------------------------------------------------
// Token store: shared in-memory state so our mock is realistic and
// predictable.  setTokens() writes into it, getAccessToken() reads it.
// ---------------------------------------------------------------------------
const tokenStore = { access: null, refresh: null };

vi.mock('../api/axiosClient', () => ({
  tokenStorage: {
    getAccessToken: vi.fn(() => tokenStore.access),
    setTokens: vi.fn(({ access, refresh }) => {
      if (access) tokenStore.access = access;
      if (refresh) tokenStore.refresh = refresh;
    }),
    clear: vi.fn(() => {
      tokenStore.access = null;
      tokenStore.refresh = null;
    }),
  },
}));

vi.mock('../api/auth', () => ({
  getCurrentUserRequest: vi.fn(),
  loginRequest: vi.fn(),
  logoutRequest: vi.fn(),
}));

import { tokenStorage } from '../api/axiosClient';
import { getCurrentUserRequest, loginRequest, logoutRequest } from '../api/auth';

// ---------------------------------------------------------------------------
// Helper: consumer component that exposes context values and provides
//          buttons to invoke login / logout.
// ---------------------------------------------------------------------------
function TestConsumer() {
  const ctx = useContext(AuthContext);
  const [loginResult, setLoginResult] = useState(null);

  const handleLogin = useCallback(async () => {
    const ok = await ctx.login({ email: 'test@test.com', password: 's3cret' });
    setLoginResult(String(ok));
  }, [ctx]);

  const handleLogout = useCallback(async () => {
    await ctx.logout();
  }, [ctx]);

  return (
    <div>
      <span data-testid="user">{ctx.user ? JSON.stringify(ctx.user) : 'null'}</span>
      <span data-testid="loading">{String(ctx.loading)}</span>
      <span data-testid="is-authenticated">{String(ctx.isAuthenticated)}</span>
      <span data-testid="login-result">{loginResult}</span>

      <button data-testid="btn-login" onClick={handleLogin}>Login</button>
      <button data-testid="btn-logout" onClick={handleLogout}>Logout</button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>,
  );
}

// ---------------------------------------------------------------------------
// Helpers: wait for a given loading state, then assert on user/auth
// ---------------------------------------------------------------------------
function waitForLoading(value) {
  return waitFor(() => {
    expect(screen.getByTestId('loading')).toHaveTextContent(value);
  });
}

const waitForLoaded = () => waitForLoading('false');

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    tokenStore.access = null;
    tokenStore.refresh = null;
    localStorage.clear();
  });

  // -----------------------------------------------------------------------
  // Session check on mount
  // -----------------------------------------------------------------------
  describe('session check on mount', () => {
    it('should end with loading=false and user=null when no token exists', async () => {
      renderWithProvider();
      await waitForLoaded();

      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
    });

    it('should restore user when a valid token exists', async () => {
      const mockUser = { id: 1, email: 'op@test.com', role: 'operator' };
      tokenStore.access = 'valid-token';
      getCurrentUserRequest.mockResolvedValue(mockUser);

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent(JSON.stringify(mockUser));
      });
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
    });

    it('should clear user when token is expired / request fails', async () => {
      tokenStore.access = 'expired-token';
      getCurrentUserRequest.mockRejectedValue(new Error('Unauthorized'));

      renderWithProvider();
      await waitForLoaded();

      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
    });
  });

  // -----------------------------------------------------------------------
  // Login
  // -----------------------------------------------------------------------
  describe('login', () => {
    it('should call loginRequest with credentials, set tokens, and populate user on success', async () => {
      const mockUser = { id: 1, email: 'test@test.com', role: 'operator' };
      const credentials = { email: 'test@test.com', password: 's3cret' };

      loginRequest.mockResolvedValue({ access: 'new-token', refresh: 'new-refresh' });
      getCurrentUserRequest.mockResolvedValue(mockUser);

      renderWithProvider();
      await waitForLoaded();

      act(() => {
        screen.getByTestId('btn-login').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('login-result')).toHaveTextContent('true');
      });

      expect(loginRequest).toHaveBeenCalledWith(credentials);
      expect(tokenStorage.setTokens).toHaveBeenCalledWith({
        access: 'new-token',
        refresh: 'new-refresh',
      });

      // After login checkSession runs and populates user
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent(JSON.stringify(mockUser));
      });
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
    });

    it('should return false and clear state on login failure', async () => {
      loginRequest.mockRejectedValue(new Error('Invalid credentials'));

      renderWithProvider();
      await waitForLoaded();

      act(() => {
        screen.getByTestId('btn-login').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('login-result')).toHaveTextContent('false');
      });

      expect(tokenStorage.clear).toHaveBeenCalled();
      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
    });
  });

  // -----------------------------------------------------------------------
  // Logout
  // -----------------------------------------------------------------------
  describe('logout', () => {
    async function arrangeAuthenticated() {
      const mockUser = { id: 1, email: 'op@test.com', role: 'operator' };
      tokenStore.access = 'has-token';
      getCurrentUserRequest.mockResolvedValue(mockUser);

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
      });

      return mockUser;
    }

    it('should clear user and token on logout', async () => {
      await arrangeAuthenticated();

      act(() => {
        screen.getByTestId('btn-logout').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
      });
      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(tokenStorage.clear).toHaveBeenCalled();
    });

    it('should call logoutRequest on logout', async () => {
      await arrangeAuthenticated();
      logoutRequest.mockResolvedValue({});

      act(() => {
        screen.getByTestId('btn-logout').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
      });

      // logoutRequest is called inside the logout handler before clear
      expect(logoutRequest).toHaveBeenCalled();
    });

    it('should clear state even if logoutRequest fails', async () => {
      await arrangeAuthenticated();
      logoutRequest.mockRejectedValue(new Error('Network error'));

      act(() => {
        screen.getByTestId('btn-logout').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
      });
      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(tokenStorage.clear).toHaveBeenCalled();
    });
  });

  // -----------------------------------------------------------------------
  // auth-unauthorized event
  // -----------------------------------------------------------------------
  describe('auth-unauthorized event', () => {
    async function arrangeAuthenticated() {
      const mockUser = { id: 1, email: 'op@test.com', role: 'operator' };
      tokenStore.access = 'has-token';
      getCurrentUserRequest.mockResolvedValue(mockUser);

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
      });
    }

    it('should clear user and token when event is dispatched', async () => {
      await arrangeAuthenticated();

      act(() => {
        window.dispatchEvent(new Event('auth-unauthorized'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
      });
      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(tokenStorage.clear).toHaveBeenCalled();
    });
  });
});
