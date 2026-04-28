/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import App from './App';

// ---------------------------------------------------------------------------
// Mock AuthProvider to avoid real side effects – just pass children through.
// ---------------------------------------------------------------------------
vi.mock('./contexts/AuthContext', () => ({
  AuthProvider: ({ children }) => children,
}));

// ---------------------------------------------------------------------------
// Mock useAuth – controlled per test via useAuth.mockReturnValue().
// ---------------------------------------------------------------------------
vi.mock('./contexts/useAuth', () => ({
  useAuth: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Mock every child component so we only test App's orchestration logic.
// Interactive components (Sidebar, ExcelUploader) expose buttons we can
// click to simulate user actions.
// ---------------------------------------------------------------------------
vi.mock('./Components/Sidebar.jsx', () => ({
  default: ({ onLogout, userRole, activeView, setActiveView }) => (
    <div data-testid="sidebar">
      <span data-testid="sidebar-role">{userRole}</span>
      <span data-testid="sidebar-view">{activeView}</span>

      <button
        data-testid="btn-view-capture"
        onClick={() => setActiveView('capture')}
      >
        Capture
      </button>
      <button
        data-testid="btn-view-excel"
        onClick={() => setActiveView('excel')}
      >
        Excel
      </button>
      <button
        data-testid="btn-view-dashboard"
        onClick={() => setActiveView('dashboard')}
      >
        Dashboard
      </button>
      <button data-testid="btn-logout" onClick={onLogout}>
        Logout
      </button>
    </div>
  ),
}));

vi.mock('./Components/Navbar.jsx', () => ({
  default: ({ user }) => (
    <div data-testid="navbar">
      <span data-testid="navbar-email">{user?.email || 'none'}</span>
    </div>
  ),
}));

vi.mock('./views/CaptureView.jsx', () => ({
  default: () => <div data-testid="capture-view">CaptureView</div>,
}));

vi.mock('./views/LoginView.jsx', () => ({
  default: () => <div data-testid="login-view">LoginView</div>,
}));

vi.mock('./Components/ExcelUploader.jsx', () => ({
  default: ({ onVolatileDashboard }) => (
    <div data-testid="excel-uploader">
      <button
        data-testid="btn-dashboard-fast"
        onClick={() => onVolatileDashboard?.('test.xlsx')}
      >
        View Dashboard (Fast Mode)
      </button>
    </div>
  ),
}));

vi.mock('./views/DashboardView.jsx', () => ({
  default: () => <div data-testid="dashboard-view">DashboardView</div>,
}));

vi.mock('./assets/RA-ICON_embed.svg?url', () => ({
  default: '/mock-favicon.svg',
}));

// ---------------------------------------------------------------------------
// Import the mocked useAuth so we can control it per test.
// ---------------------------------------------------------------------------
import { useAuth } from './contexts/useAuth';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function mockAuthState(overrides = {}) {
  const defaults = {
    user: null,
    loading: false,
    isAuthenticated: false,
    login: vi.fn(),
    logout: vi.fn(),
  };
  useAuth.mockReturnValue({ ...defaults, ...overrides });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  // -----------------------------------------------------------------------
  // Loading state
  // -----------------------------------------------------------------------
  describe('loading state', () => {
    it('should show a loading message while auth is being verified', () => {
      mockAuthState({ loading: true });
      render(<App />);
      expect(screen.getByText('Verificando sesión...')).toBeInTheDocument();
    });

    it('should not render any view while loading', () => {
      mockAuthState({ loading: true });
      render(<App />);
      expect(screen.queryByTestId('login-view')).not.toBeInTheDocument();
      expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Unauthenticated
  // -----------------------------------------------------------------------
  describe('unauthenticated state', () => {
    it('should render the LoginView when user is not authenticated', () => {
      mockAuthState({ user: null, isAuthenticated: false });
      render(<App />);

      expect(screen.getByTestId('login-view')).toBeInTheDocument();
    });

    it('should not render the app shell when unauthenticated', () => {
      mockAuthState({ user: null, isAuthenticated: false });
      render(<App />);

      expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
      expect(screen.queryByTestId('navbar')).not.toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Authenticated as operator
  // -----------------------------------------------------------------------
  describe('authenticated as operator', () => {
    beforeEach(() => {
      mockAuthState({
        user: { id: 1, email: 'op@test.com', role: 'operator' },
        isAuthenticated: true,
      });
    });

    it('should render the app shell (sidebar + navbar)', () => {
      render(<App />);

      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('navbar')).toBeInTheDocument();
    });

    it('should show CaptureView as the default view for operator', () => {
      render(<App />);

      expect(screen.getByTestId('capture-view')).toBeInTheDocument();
    });

    it('should pass the correct role to Sidebar', () => {
      render(<App />);

      expect(screen.getByTestId('sidebar-role')).toHaveTextContent('operator');
    });

    it('should pass the resolved active view to Sidebar', () => {
      render(<App />);

      expect(screen.getByTestId('sidebar-view')).toHaveTextContent('capture');
    });

    it('should display the user email in Navbar', () => {
      render(<App />);

      expect(screen.getByTestId('navbar-email')).toHaveTextContent('op@test.com');
    });

    it('should store the default view in localStorage on mount', async () => {
      render(<App />);

      await waitFor(() => {
        expect(localStorage.getItem('rift-activeView')).toBe('capture');
      });
    });

    it('should switch from CaptureView to DashboardView when view changes', () => {
      render(<App />);

      expect(screen.getByTestId('capture-view')).toBeInTheDocument();

      act(() => {
        screen.getByTestId('btn-view-dashboard').click();
      });

      expect(screen.getByTestId('dashboard-view')).toBeInTheDocument();
      expect(screen.queryByTestId('capture-view')).not.toBeInTheDocument();
    });

    it('should update localStorage when sidebar triggers view change', () => {
      render(<App />);

      act(() => {
        screen.getByTestId('btn-view-dashboard').click();
      });

      expect(localStorage.getItem('rift-activeView')).toBe('dashboard');
    });
  });

  // -----------------------------------------------------------------------
  // Authenticated as manager
  // -----------------------------------------------------------------------
  describe('authenticated as manager', () => {
    beforeEach(() => {
      mockAuthState({
        user: { id: 2, email: 'mgr@test.com', role: 'manager' },
        isAuthenticated: true,
      });
    });

    it('should render the app shell', () => {
      render(<App />);

      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('navbar')).toBeInTheDocument();
    });

    it('should show ExcelUploader as the default view for manager', () => {
      render(<App />);

      expect(screen.getByTestId('excel-uploader')).toBeInTheDocument();
    });

    it('should not show CaptureView for manager', () => {
      render(<App />);

      expect(screen.queryByTestId('capture-view')).not.toBeInTheDocument();
    });

    it('should pass the correct role to Sidebar', () => {
      render(<App />);

      expect(screen.getByTestId('sidebar-role')).toHaveTextContent('manager');
    });

    it('should display the manager email in Navbar', () => {
      render(<App />);

      expect(screen.getByTestId('navbar-email')).toHaveTextContent('mgr@test.com');
    });

    it('should store "excel" as the default view in localStorage on mount', async () => {
      render(<App />);

      await waitFor(() => {
        expect(localStorage.getItem('rift-activeView')).toBe('excel');
      });
    });
  });

  // -----------------------------------------------------------------------
  // Logout flow
  // -----------------------------------------------------------------------
  describe('logout flow', () => {
    it('should call the logout function from useAuth', () => {
      const mockLogout = vi.fn().mockResolvedValue(undefined);

      mockAuthState({
        user: { id: 1, email: 'op@test.com', role: 'operator' },
        isAuthenticated: true,
        logout: mockLogout,
      });

      render(<App />);

      act(() => {
        screen.getByTestId('btn-logout').click();
      });

      expect(mockLogout).toHaveBeenCalledTimes(1);
    });

    it('should remove the stored view from localStorage on logout', async () => {
      localStorage.setItem('rift-activeView', 'capture');

      mockAuthState({
        user: { id: 1, email: 'op@test.com', role: 'operator' },
        isAuthenticated: true,
        logout: vi.fn().mockResolvedValue(undefined),
      });

      render(<App />);

      act(() => {
        screen.getByTestId('btn-logout').click();
      });

      // handleLogout is async (await logout() + cleanup), so wait for it
      await waitFor(() => {
        expect(localStorage.getItem('rift-activeView')).toBeNull();
      });
    });
  });

  // -----------------------------------------------------------------------
  // Volatile (fast-mode) dashboard
  // -----------------------------------------------------------------------
  describe('volatile dashboard flow', () => {
    it('should switch from ExcelUploader to DashboardView when fast-mode is triggered', () => {
      mockAuthState({
        user: { id: 2, email: 'mgr@test.com', role: 'manager' },
        isAuthenticated: true,
      });

      render(<App />);

      expect(screen.getByTestId('excel-uploader')).toBeInTheDocument();

      act(() => {
        screen.getByTestId('btn-dashboard-fast').click();
      });

      expect(screen.getByTestId('dashboard-view')).toBeInTheDocument();
      expect(screen.queryByTestId('excel-uploader')).not.toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Favicon
  // -----------------------------------------------------------------------
  describe('favicon', () => {
    it('should set a favicon link element on mount', () => {
      render(<App />);

      const link = document.querySelector("link[rel*='icon']");
      expect(link).not.toBeNull();
    });

    it('should set the favicon href to the imported SVG URL', () => {
      render(<App />);

      const link = document.querySelector("link[rel*='icon']");
      expect(link?.getAttribute('href')).toBe('/mock-favicon.svg');
    });
  });
});
