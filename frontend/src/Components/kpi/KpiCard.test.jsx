import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import KpiCard from './KpiCard';

describe('KpiCard', () => {
  describe('Rendering', () => {
    it('renders title when provided', () => {
      render(<KpiCard title="Test Title" />);
      expect(screen.getByText('Test Title')).toBeInTheDocument();
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
      expect(screen.getByText('Sin datos')).toBeInTheDocument();
    });
  });
});
