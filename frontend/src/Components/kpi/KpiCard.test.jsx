import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import KpiCard from './KpiCard';

describe('KpiCard', () => {
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

    it('center content (loading/error/empty) preserves min-height of 168px', () => {
      render(<KpiCard title="Test Card" loading={true} />);
      const bodyElement = document.querySelector('.kpi-card > div:nth-child(2)');
      expect(bodyElement).toBeInTheDocument();
      // Body still 120px min, but center content inside has 168px min for vertical centering
      expect(bodyElement.style.minHeight).toBe('120px');
      const centerContent = bodyElement.querySelector('div[style*="min-height: 168px"]');
      expect(centerContent).toBeInTheDocument();
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
      // Loading state shows a spinner div with animation
      const spinner = document.querySelector('div[style*="animation"]');
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
