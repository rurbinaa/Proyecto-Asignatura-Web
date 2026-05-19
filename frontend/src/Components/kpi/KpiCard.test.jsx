import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import KpiCard from './KpiCard';

describe('KpiCard', () => {
  describe('bodyMinHeight', () => {
    it('applies bodyMinHeight to the card body reducing Masonry reflow risk', () => {
      render(
        <KpiCard title="Stable Card" bodyMinHeight={360}>
          <span>Content</span>
        </KpiCard>
      );
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement).toBeInTheDocument();
      expect(bodyElement.style.minHeight).toBe('360px');
    });

    it('preserves body minHeight across loading state when bodyMinHeight is set', () => {
      render(
        <KpiCard title="Loading Card" loading bodyMinHeight={360} />
      );
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement).toBeInTheDocument();
      expect(bodyElement.style.minHeight).toBe('360px');
    });

    it('preserves body minHeight across error state when bodyMinHeight is set', () => {
      render(
        <KpiCard title="Error Card" error="Fail" bodyMinHeight={360} />
      );
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement).toBeInTheDocument();
      expect(bodyElement.style.minHeight).toBe('360px');
    });

    it('preserves body minHeight across empty state when bodyMinHeight is set', () => {
      render(
        <KpiCard title="Empty Card" bodyMinHeight={360} />
      );
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement).toBeInTheDocument();
      expect(bodyElement.style.minHeight).toBe('360px');
    });

    it('preserves body minHeight when children + bodyMinHeight are set together', () => {
      render(
        <KpiCard title="Content Card" bodyMinHeight={360}>
          <span data-testid="chart">Chart</span>
        </KpiCard>
      );
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement).toBeInTheDocument();
      expect(bodyElement.style.minHeight).toBe('360px');
      expect(screen.getByTestId('chart')).toBeInTheDocument();
    });

    it('defaults to 120px minHeight when bodyMinHeight is not provided (backward compat)', () => {
      render(<KpiCard title="Default"><span>Content</span></KpiCard>);
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement).toBeInTheDocument();
      expect(bodyElement.style.minHeight).toBe('120px');
    });
  });
  describe('loadingLabel', () => {
    it('shows custom label when loadingLabel prop is provided during loading', () => {
      render(<KpiCard title="Chart Card" loading loadingLabel="Rendering chart…" />);
      expect(screen.getByText('Rendering chart…')).toBeInTheDocument();
    });

    it('shows spinner alongside custom label when loadingLabel is provided', () => {
      render(<KpiCard title="Chart Card" loading loadingLabel="Loading data…" />);
      // Spinner should still be present
      const spinner = document.querySelector('.kpi-loader');
      expect(spinner).toBeInTheDocument();
      expect(screen.getByText('Loading data…')).toBeInTheDocument();
    });

    it('does not show loadingLabel when not loading even if prop is passed', () => {
      render(
        <KpiCard title="Chart Card" loadingLabel="Rendering…">
          <span>Content</span>
        </KpiCard>
      );
      expect(screen.queryByText('Rendering…')).not.toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('does not render loadingLabel text when loadingLabel prop is not provided (backward compat)', () => {
      render(<KpiCard title="Basic Card" loading />);
      // The spinner should still render
      const spinner = document.querySelector('.kpi-loader');
      expect(spinner).toBeInTheDocument();
      // No custom text label should appear
      expect(screen.queryByText('Rendering')).not.toBeInTheDocument();
      expect(screen.queryByText('Loading')).not.toBeInTheDocument();
    });
  });

  describe('Rendering', () => {
    it('renders title when provided', () => {
      render(<KpiCard title="Test Title" />);
      expect(screen.getByText('Test Title')).toBeInTheDocument();
    });

    it('body has min-height of 120px for consistent card sizing in grid layout', () => {
      render(<KpiCard title="Test Card"><span>Content</span></KpiCard>);
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement).toBeInTheDocument();
      expect(bodyElement.style.minHeight).toBe('120px');
    });

    it('centers loading content vertically when loading prop is true', () => {
      render(<KpiCard title="Test Card" loading={true} />);
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement).toBeInTheDocument();
      // Body uses flex centering when loading
      expect(bodyElement.style.display).toBe('flex');
      expect(bodyElement.style.alignItems).toBe('center');
      expect(bodyElement.style.justifyContent).toBe('center');
      // Spinner is rendered via CSS class
      const spinner = document.querySelector('.kpi-loader');
      expect(spinner).toBeInTheDocument();
    });

    it('renders children when data is present', () => {
      render(
        <KpiCard title="Test Card">
          <span>Chart Data</span>
        </KpiCard>
      );
      expect(screen.getByText('Chart Data')).toBeInTheDocument();
    });

    it('renders loading state when loading prop is true', () => {
      render(<KpiCard title="Loading Card" loading={true} />);
      // Loading state shows a spinner via CSS class
      const spinner = document.querySelector('.kpi-loader');
      expect(spinner).toBeInTheDocument();
    });

    it('renders error state when error prop is provided', () => {
      render(<KpiCard title="Error Card" error="Something went wrong" />);
      expect(screen.getByText('Error: Something went wrong')).toBeInTheDocument();
    });

    it('renders empty state when no children and not loading and no error', () => {
      render(<KpiCard title="Empty Card" />);
      expect(screen.getByText('No data')).toBeInTheDocument();
    });
  });

  describe('Loading behavior', () => {
    it('body uses flex column layout when NOT loading so chart fills the card', () => {
      render(
        <KpiCard title="Chart Card">
          <span>Chart</span>
        </KpiCard>
      );
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement.style.display).toBe('flex');
      expect(bodyElement.style.flexDirection).toBe('column');
      // No centering when not loading — charts should top-align
      expect(bodyElement.style.alignItems).toBe('');
      expect(bodyElement.style.justifyContent).toBe('');
    });

    it('does not render children when loading even if children are present', () => {
      render(
        <KpiCard title="Test" loading>
          <span data-testid="child-content">Should not appear</span>
        </KpiCard>
      );
      // Spinner should be visible
      expect(document.querySelector('.kpi-loader')).toBeInTheDocument();
      // Children should NOT be rendered
      expect(screen.queryByTestId('child-content')).not.toBeInTheDocument();
    });

    it('does not render spinner when not loading', () => {
      render(<KpiCard title="Test"><span>Content</span></KpiCard>);
      expect(document.querySelector('.kpi-loader')).not.toBeInTheDocument();
    });
  });

  describe('Layout and Spacing', () => {
    it('card body has no padding - charts handle their own padding for consistency', () => {
      render(<KpiCard title="Test Card"><span>Content</span></KpiCard>);
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement).toBeInTheDocument();
      // padding: '0' is set so charts can manage their own internal padding
      expect(bodyElement.style.padding).toBe('0px');
    });

    it('card body uses overflow-x visible to allow natural overflow behavior', () => {
      render(<KpiCard title="Test Card"><span>Content</span></KpiCard>);
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement).toBeInTheDocument();
      expect(bodyElement.style.overflowX).toBe('visible');
    });

    it('chart container takes full width without dead space', () => {
      render(
        <KpiCard title="Test Card">
          <div data-testid="chart-content">Chart</div>
        </KpiCard>
      );
      const chartContainer = document.querySelector('.kpi-card > div:nth-child(2) > div');
      expect(chartContainer).toBeInTheDocument();
      expect(chartContainer.style.width).toBe('100%');
    });

    it('card has overflow visible for natural flow in grid layout', () => {
      render(<KpiCard title="Test Card"><span>Content</span></KpiCard>);
      const cardElement = document.querySelector('.kpi-card');
      expect(cardElement).toBeInTheDocument();
      expect(cardElement.style.overflow).toBe('visible');
    });
  });
});
