/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from './Sidebar';

// Mock the SVG asset (Vite imports SVGs as URLs)
vi.mock('../assets/RA-ICON_embed.svg', () => ({ default: 'ra-icon-mock.svg' }));

describe('Sidebar', () => {
  const defaultProps = {
    userRole: 'manager',
    activeView: 'dashboard',
    setActiveView: vi.fn(),
    setVolatileFile: vi.fn(),
    onLogout: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('structure', () => {
    it('renders the sidebar with correct class', () => {
      const { container } = render(<Sidebar {...defaultProps} />);
      expect(container.querySelector('.sidebar')).toBeInTheDocument();
    });

    it('renders the logo image', () => {
      render(<Sidebar {...defaultProps} />);
      const img = screen.getByAltText('Rift Analytics');
      expect(img).toBeInTheDocument();
      expect(img).toHaveAttribute('src', 'ra-icon-mock.svg');
    });

    it('renders the logo text when not collapsed', () => {
      render(<Sidebar {...defaultProps} />);
      expect(screen.getByText('Rift Analytics')).toBeInTheDocument();
    });
  });

  describe('role-based navigation - manager', () => {
    it('shows Import Batches button for manager role', () => {
      render(<Sidebar {...defaultProps} userRole="manager" />);
      expect(screen.getByText('Import Batches')).toBeInTheDocument();
    });

    it('shows Dashboard button for manager role', () => {
      render(<Sidebar {...defaultProps} userRole="manager" />);
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    it('shows Quality Reports button for manager role', () => {
      render(<Sidebar {...defaultProps} userRole="manager" />);
      expect(screen.getByText('Quality Reports')).toBeInTheDocument();
    });

    it('does NOT show Touch Capture action anymore', () => {
      render(<Sidebar {...defaultProps} userRole="manager" />);
      expect(screen.queryByText('Touch Capture')).not.toBeInTheDocument();
    });
  });

  describe('active view highlighting', () => {
    it('adds active class to the activeView button (dashboard)', () => {
      render(<Sidebar {...defaultProps} userRole="manager" activeView="dashboard" />);
      const dashboardBtn = screen.getByText('Dashboard').closest('button');
      expect(dashboardBtn.classList.contains('active')).toBe(true);
    });

    it('adds active class to the activeView button (excel)', () => {
      render(<Sidebar {...defaultProps} userRole="manager" activeView="excel" />);
      const excelBtn = screen.getByText('Import Batches').closest('button');
      expect(excelBtn.classList.contains('active')).toBe(true);
    });

    it('adds active class to the activeView button (reports)', () => {
      render(<Sidebar {...defaultProps} userRole="manager" activeView="reports" />);
      const reportsBtn = screen.getByText('Quality Reports').closest('button');
      expect(reportsBtn.classList.contains('active')).toBe(true);
    });

    it('removes active class from other buttons', () => {
      render(<Sidebar {...defaultProps} userRole="manager" activeView="excel" />);
      const dashboardBtn = screen.getByText('Dashboard').closest('button');
      expect(dashboardBtn.classList.contains('active')).toBe(false);
    });
  });

  describe('navigation callbacks', () => {
    it('calls setActiveView with "excel" when Import Batches is clicked', () => {
      const setActiveView = vi.fn();
      render(
        <Sidebar
          {...defaultProps}
          userRole="manager"
          setActiveView={setActiveView}
        />,
      );
      fireEvent.click(screen.getByText('Import Batches'));
      expect(setActiveView).toHaveBeenCalledWith('excel');
    });

    it('calls setActiveView with "dashboard" and clears fast mode when Dashboard is clicked', () => {
      const setActiveView = vi.fn();
      const setVolatileFile = vi.fn();
      render(
        <Sidebar
          {...defaultProps}
          userRole="manager"
          setActiveView={setActiveView}
          setVolatileFile={setVolatileFile}
        />,
      );
      fireEvent.click(screen.getByText('Dashboard'));
      expect(setActiveView).toHaveBeenCalledWith('dashboard');
      expect(setVolatileFile).toHaveBeenCalledWith(null);
    });

    it('calls setActiveView with "reports" when Quality Reports is clicked', () => {
      const setActiveView = vi.fn();
      render(
        <Sidebar
          {...defaultProps}
          userRole="manager"
          setActiveView={setActiveView}
        />,
      );
      fireEvent.click(screen.getByText('Quality Reports'));
      expect(setActiveView).toHaveBeenCalledWith('reports');
    });
  });

  describe('logout', () => {
    it('calls onLogout when Log Out button is clicked', () => {
      const onLogout = vi.fn();
      render(<Sidebar {...defaultProps} onLogout={onLogout} />);
      fireEvent.click(screen.getByText('Log Out'));
      expect(onLogout).toHaveBeenCalledOnce();
    });
  });

  describe('collapse / expand', () => {
    it('starts in expanded state by default', () => {
      const { container } = render(<Sidebar {...defaultProps} />);
      expect(container.querySelector('.sidebar.collapsed')).not.toBeInTheDocument();
    });

    it('adds collapsed class when collapse button is clicked', () => {
      const { container } = render(<Sidebar {...defaultProps} />);
      const collapseBtn = container.querySelector('.top-toggle');
      fireEvent.click(collapseBtn);
      expect(container.querySelector('.sidebar.collapsed')).toBeInTheDocument();
    });

    it('hides text labels when collapsed', () => {
      const { container } = render(<Sidebar {...defaultProps} />);
      const collapseBtn = container.querySelector('.top-toggle');
      fireEvent.click(collapseBtn);
      expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
      expect(screen.queryByText('Rift Analytics')).not.toBeInTheDocument();
      expect(screen.queryByText('Log Out')).not.toBeInTheDocument();
    });

    it('shows expand button when collapsed', () => {
      const { container } = render(<Sidebar {...defaultProps} />);
      const collapseBtn = container.querySelector('.top-toggle');
      fireEvent.click(collapseBtn);
      const expandBtn = container.querySelector('.bottom-toggle');
      expect(expandBtn).toBeInTheDocument();
      expect(expandBtn).toHaveAttribute('title', 'Expand menu');
    });

    it('expands sidebar when expand button is clicked', () => {
      const { container } = render(<Sidebar {...defaultProps} />);
      // Collapse first
      fireEvent.click(container.querySelector('.top-toggle'));
      expect(container.querySelector('.sidebar.collapsed')).toBeInTheDocument();
      // Now expand
      fireEvent.click(container.querySelector('.bottom-toggle'));
      expect(container.querySelector('.sidebar.collapsed')).not.toBeInTheDocument();
    });

    it('renders collapse button with correct title in expanded state', () => {
      const { container } = render(<Sidebar {...defaultProps} />);
      const collapseBtn = container.querySelector('.top-toggle');
      expect(collapseBtn).toHaveAttribute('title', 'Collapse menu');
    });

    it('still shows nav items with title attribute when collapsed for tooltip access', () => {
      const { container } = render(
        <Sidebar {...defaultProps} userRole="manager" />,
      );
      const collapseBtn = container.querySelector('.top-toggle');
      fireEvent.click(collapseBtn);
      const navButtons = container.querySelectorAll('.sidebar-nav-item');
      expect(navButtons.length).toBeGreaterThanOrEqual(3);
      // Dashboard button
      const dashboardBtn = navButtons[1];
      expect(dashboardBtn).toHaveAttribute('title', 'Dashboard');
      // Quality Reports button
      const reportsBtn = navButtons[2];
      expect(reportsBtn).toHaveAttribute('title', 'Quality Reports');
    });
  });

  describe('setVolatileFile optional', () => {
    it('handles undefined setVolatileFile without crashing', () => {
      render(
        <Sidebar
          userRole="manager"
          activeView="excel"
          setActiveView={vi.fn()}
          onLogout={vi.fn()}
        // setVolatileFile not provided
        />,
      );
      fireEvent.click(screen.getByText('Dashboard'));
      // Should not throw - optional chaining handles undefined
    });
  });
});
