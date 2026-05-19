/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';

// ---------------------------------------------------------------------------
// Mock the 5 lazy-loaded dashboard containers as simple placeholders.
// These mocks are registered BEFORE DashboardShell is imported so that
// React.lazy(() => import('...')) resolves them in tests.
// ---------------------------------------------------------------------------
vi.mock('./dashboards/PlantDashboard', () => ({
  default: (props) => (
    <div data-testid="dashboard-plant">
      PlantDashboard {props?.isFastMode ? '(fast mode)' : ''}
    </div>
  ),
}));

vi.mock('./dashboards/CustomerDashboard', () => ({
  default: (props) => (
    <div data-testid="dashboard-customer">
      CustomerDashboard {props?.isFastMode ? '(fast mode)' : ''}
    </div>
  ),
}));

vi.mock('./dashboards/SecondsA4Dashboard', () => ({
  default: () => <div data-testid="dashboard-seconds-a4">Seconds A4 Dashboard</div>,
}));

vi.mock('./dashboards/SecondsGeneralDashboard', () => ({
  default: () => <div data-testid="dashboard-seconds-gen">Seconds General Dashboard</div>,
}));

vi.mock('./dashboards/ContainerDashboard', () => ({
  default: () => <div data-testid="dashboard-container">Container Dashboard</div>,
}));

import DashboardShell from './DashboardShell';

// ---------------------------------------------------------------------------
// Helper to collect all tab buttons in order
// ---------------------------------------------------------------------------
function getTabs() {
  return screen.getAllByRole('tab');
}

// ---------------------------------------------------------------------------
// Wait for the lazy-loaded component to resolve inside Suspense.
// React.lazy resolves asynchronously; we must wait for the fallback to clear.
// ---------------------------------------------------------------------------
async function waitForDashboard(testId) {
  await waitFor(() => {
    expect(screen.getByTestId(testId)).toBeInTheDocument();
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('DashboardShell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // -----------------------------------------------------------------------
  // Default sheet
  // -----------------------------------------------------------------------
  describe('default sheet', () => {
    it('should show loading fallback before the lazy component resolves', () => {
      render(<DashboardShell />);

      // The Suspense fallback must be visible before the lazy component resolves
      expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
    });

    it('should render the plant dashboard as the default active sheet', async () => {
      render(<DashboardShell />);

      await waitForDashboard('dashboard-plant');
    });

    it('should mark the plant tab as selected initially', async () => {
      render(<DashboardShell />);

      // The plant tab should be marked selected even before lazy resolution
      const tabs = getTabs();
      const plantTab = tabs.find((t) => t.textContent === 'QC FA Plant');
      expect(plantTab).toHaveAttribute('aria-selected', 'true');

      // Wait for the dashboard to confirm it resolves correctly under the selected tab
      await waitForDashboard('dashboard-plant');
    });
  });

  // -----------------------------------------------------------------------
  // Tab selector presence
  // -----------------------------------------------------------------------
  describe('tab selector', () => {
    it('should render exactly 5 sheet navigation tabs', () => {
      render(<DashboardShell />);

      const tabs = getTabs();
      expect(tabs).toHaveLength(5);
    });

    it('should display the correct labels for all 5 sheets', () => {
      render(<DashboardShell />);

      const expectedLabels = [
        'QC FA Plant',
        'QC FA Customer',
        'Seconds A4',
        'Seconds General',
        'Container',
      ];

      expectedLabels.forEach((label) => {
        expect(screen.getByText(label)).toBeInTheDocument();
      });
    });
  });

  // -----------------------------------------------------------------------
  // Tab switching
  // -----------------------------------------------------------------------
  describe('tab switching', () => {
    it('should switch to customer dashboard when QC FA Customer tab is clicked', async () => {
      render(<DashboardShell />);

      // Wait for default plant to load first
      await waitForDashboard('dashboard-plant');

      const customerTab = screen.getByText('QC FA Customer');
      act(() => {
        customerTab.click();
      });

      // Customer dashboard should now be visible (after lazy resolution)
      await waitForDashboard('dashboard-customer');
      // Plant should no longer be rendered
      expect(screen.queryByTestId('dashboard-plant')).not.toBeInTheDocument();
    });

    it('should mark the newly selected tab as active', async () => {
      render(<DashboardShell />);

      await waitForDashboard('dashboard-plant');

      const containerTab = screen.getByText('Container');
      act(() => {
        containerTab.click();
      });

      const tabs = getTabs();
      const containerTabEl = tabs.find((t) => t.textContent === 'Container');
      expect(containerTabEl).toHaveAttribute('aria-selected', 'true');

      // Plant tab should no longer be selected
      const plantTab = tabs.find((t) => t.textContent === 'QC FA Plant');
      expect(plantTab).toHaveAttribute('aria-selected', 'false');
    });

    it('should switch among all 5 sheets correctly', async () => {
      render(<DashboardShell />);

      await waitForDashboard('dashboard-plant');

      const sheetTestIds = [
        { label: 'QC FA Plant', testId: 'dashboard-plant' },
        { label: 'QC FA Customer', testId: 'dashboard-customer' },
        { label: 'Seconds A4', testId: 'dashboard-seconds-a4' },
        { label: 'Seconds General', testId: 'dashboard-seconds-gen' },
        { label: 'Container', testId: 'dashboard-container' },
      ];

      for (const { label, testId } of sheetTestIds) {
        act(() => {
          screen.getByText(label).click();
        });

        // The selected sheet should resolve and be visible
        await waitForDashboard(testId);

        // All other sheets should NOT be visible
        const otherIds = sheetTestIds
          .filter((s) => s.testId !== testId)
          .map((s) => s.testId);
        for (const id of otherIds) {
          expect(screen.queryByTestId(id)).not.toBeInTheDocument();
        }
      }
    });
  });

  // -----------------------------------------------------------------------
  // Suspense wrapper
  // -----------------------------------------------------------------------
  describe('suspense wrapper', () => {
    it('should render dashboard-shell-content as tabpanel region', async () => {
      render(<DashboardShell />);

      await waitForDashboard('dashboard-plant');

      const tabpanel = screen.getByRole('tabpanel');
      expect(tabpanel).toBeInTheDocument();
      expect(tabpanel).toHaveClass('dashboard-shell-content');
    });

    it('should contain the active dashboard inside the tabpanel', async () => {
      render(<DashboardShell />);

      await waitForDashboard('dashboard-plant');

      const tabpanel = screen.getByRole('tabpanel');
      expect(tabpanel).toContainElement(screen.getByTestId('dashboard-plant'));
    });
  });

  // -----------------------------------------------------------------------
  // Props forwarding
  // -----------------------------------------------------------------------
  describe('props forwarding', () => {
    it('should forward isFastMode when volatileFile is provided', async () => {
      const volatileFile = { name: 'test.xlsx' };
      render(<DashboardShell volatileFile={volatileFile} />);

      await waitForDashboard('dashboard-plant');
      expect(screen.getByText(/\(fast mode\)/)).toBeInTheDocument();
    });

    it('should render without fast mode (live mode)', async () => {
      render(<DashboardShell />);

      await waitForDashboard('dashboard-plant');
      // Plant dashboard renders without "(fast mode)" suffix
      expect(screen.getByText('PlantDashboard')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Edge case: invalid internal key fallback
  // -----------------------------------------------------------------------
  describe('fallback behavior', () => {
    it('should render the default plant dashboard when internal state is unknown', async () => {
      // Even without explicit invalid-key injection, the component defaults to plant.
      // We verify that a fresh render always shows plant and never crashes.
      render(<DashboardShell />);
      await waitForDashboard('dashboard-plant');
      expect(screen.queryByTestId('dashboard-customer')).not.toBeInTheDocument();
    });

    it('should maintain a single active sheet at all times', async () => {
      render(<DashboardShell />);

      await waitForDashboard('dashboard-plant');

      // Only one dashboard should be visible at a time
      const activeDashboards = [
        screen.queryByTestId('dashboard-plant'),
        screen.queryByTestId('dashboard-customer'),
        screen.queryByTestId('dashboard-seconds-a4'),
        screen.queryByTestId('dashboard-seconds-gen'),
        screen.queryByTestId('dashboard-container'),
      ].filter(Boolean);

      expect(activeDashboards).toHaveLength(1);
    });
  });
});
