/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { withRoleProtection } from './withRoleProtection';

// ---------------------------------------------------------------------------
// Mock useAuth so we can control authentication state for each test.
// ---------------------------------------------------------------------------
vi.mock('../contexts/useAuth', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '../contexts/useAuth';

// ---------------------------------------------------------------------------
// Test component to wrap
// ---------------------------------------------------------------------------
function DummyComponent({ label = 'default' }) {
  return <div data-testid="protected-content">{label}</div>;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function setupLocationReplace() {
  const originalLocation = window.location;
  delete window.location;
  window.location = { ...originalLocation, replace: vi.fn() };
}

const mockedAuth = (overrides = {}) => ({
  user: null,
  loading: false,
  isAuthenticated: false,
  ...overrides,
});

describe('withRoleProtection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    setupLocationReplace();
  });

  // -----------------------------------------------------------------------
  // Loading state
  // -----------------------------------------------------------------------
  describe('loading state', () => {
    it('should return null while auth is loading', () => {
      useAuth.mockReturnValue(mockedAuth({ loading: true }));

      const Protected = withRoleProtection(DummyComponent, ['manager']);
      const { container } = render(<Protected label="test" />);

      // Nothing rendered
      expect(container.innerHTML).toBe('');
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('should not redirect while loading', () => {
      useAuth.mockReturnValue(mockedAuth({ loading: true }));

      const Protected = withRoleProtection(DummyComponent, ['manager']);
      render(<Protected />);

      expect(window.location.replace).not.toHaveBeenCalled();
    });
  });

  // -----------------------------------------------------------------------
  // Authenticated with matching role
  // -----------------------------------------------------------------------
  describe('authenticated with correct role', () => {
    it('should render the wrapped component when user role is allowed', () => {
      useAuth.mockReturnValue(mockedAuth({
        user: { id: 1, role: 'manager' },
        isAuthenticated: true,
      }));

      const Protected = withRoleProtection(DummyComponent, ['manager']);
      render(<Protected label="hello" />);

      expect(screen.getByTestId('protected-content')).toHaveTextContent('hello');
    });

    it('should pass props through to the wrapped component', () => {
      useAuth.mockReturnValue(mockedAuth({
        user: { id: 1, role: 'manager' },
        isAuthenticated: true,
      }));

      const Protected = withRoleProtection(DummyComponent, ['manager']);
      const { container } = render(<Protected label="prop-test" />);

      expect(screen.getByTestId('protected-content')).toHaveTextContent('prop-test');
    });

    it('should render with multiple allowed roles', () => {
      useAuth.mockReturnValue(mockedAuth({
        user: { id: 1, role: 'supervisor' },
        isAuthenticated: true,
      }));

      const Protected = withRoleProtection(DummyComponent, ['manager', 'supervisor', 'admin']);
      render(<Protected label="multi" />);

      expect(screen.getByTestId('protected-content')).toHaveTextContent('multi');
    });
  });

  // -----------------------------------------------------------------------
  // Authenticated with wrong role
  // -----------------------------------------------------------------------
  describe('authenticated with wrong role', () => {
    it('should redirect to / when role is not in allowed list', () => {
      useAuth.mockReturnValue(mockedAuth({
        user: { id: 1, role: 'analyst' },
        isAuthenticated: true,
      }));

      const Protected = withRoleProtection(DummyComponent, ['manager']);
      const { container } = render(<Protected />);

      expect(container.innerHTML).toBe('');
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(window.location.replace).toHaveBeenCalledWith('/');
    });

    it('should clear rift-activeView from localStorage on redirect', () => {
      localStorage.setItem('rift-activeView', 'dashboard');
      useAuth.mockReturnValue(mockedAuth({
        user: { id: 1, role: 'analyst' },
        isAuthenticated: true,
      }));

      const Protected = withRoleProtection(DummyComponent, ['manager']);
      render(<Protected />);

      expect(localStorage.getItem('rift-activeView')).toBeNull();
    });
  });

  // -----------------------------------------------------------------------
  // Not authenticated
  // -----------------------------------------------------------------------
  describe('not authenticated', () => {
    it('should redirect to / when user is null', () => {
      useAuth.mockReturnValue(mockedAuth({ user: null }));

      const Protected = withRoleProtection(DummyComponent, ['manager']);
      const { container } = render(<Protected />);

      expect(container.innerHTML).toBe('');
      expect(window.location.replace).toHaveBeenCalledWith('/');
    });

    it('should clear rift-activeView when user is null', () => {
      localStorage.setItem('rift-activeView', 'dashboard');
      useAuth.mockReturnValue(mockedAuth({ user: null }));

      const Protected = withRoleProtection(DummyComponent, ['manager']);
      render(<Protected />);

      expect(localStorage.getItem('rift-activeView')).toBeNull();
    });
  });

  // -----------------------------------------------------------------------
  // Empty allowedRoles (any authenticated user)
  // -----------------------------------------------------------------------
  describe('empty allowedRoles', () => {
    it('should render when allowedRoles is empty and user is authenticated', () => {
      useAuth.mockReturnValue(mockedAuth({
        user: { id: 1, role: 'manager' },
        isAuthenticated: true,
      }));

      const Protected = withRoleProtection(DummyComponent);
      render(<Protected label="any-role" />);

      expect(screen.getByTestId('protected-content')).toHaveTextContent('any-role');
    });

    it('should redirect when allowedRoles is empty and user is null', () => {
      useAuth.mockReturnValue(mockedAuth({ user: null }));

      const Protected = withRoleProtection(DummyComponent);
      render(<Protected />);

      expect(window.location.replace).toHaveBeenCalledWith('/');
    });
  });
});
