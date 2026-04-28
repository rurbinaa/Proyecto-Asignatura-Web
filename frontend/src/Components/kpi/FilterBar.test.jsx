import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import FilterBar from './FilterBar';

describe('FilterBar', () => {
  const defaultFilters = {
    date_range: ['', ''],
    week: '',
    team: '',
    style: '',
    color: '',
    customer: '',
    batch: '',
  };

  describe('Rendering', () => {
    it('renders filter inputs with DateRangePicker', () => {
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={vi.fn()}
          onApply={vi.fn()}
          onReset={vi.fn()}
        />
      );

      // 6 text inputs: week, team, style, color, customer, batch (date inputs are in DateRangePicker)
      const inputs = document.querySelectorAll('.filter-input');
      expect(inputs).toHaveLength(6);
    });

    it('renders DateRangePicker for date selection', () => {
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={vi.fn()}
          onApply={vi.fn()}
          onReset={vi.fn()}
        />
      );

      expect(document.querySelector('.date-range-picker')).toBeInTheDocument();
    });

    it('renders filter labels in English', () => {
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={vi.fn()}
          onApply={vi.fn()}
          onReset={vi.fn()}
        />
      );

      expect(screen.getByText('Date')).toBeInTheDocument();
      expect(screen.getByText('Week')).toBeInTheDocument();
      expect(screen.getByText('Team')).toBeInTheDocument();
      expect(screen.getByText('Style')).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('calls onFilterChange when input changes', () => {
      const onFilterChange = vi.fn();
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={onFilterChange}
          onApply={vi.fn()}
          onReset={vi.fn()}
        />
      );

      // Style input is the 3rd input (index 2) after DateRangePicker
      const inputs = document.querySelectorAll('.filter-input');
      fireEvent.change(inputs[2], { target: { value: 'NewStyle' } });

      expect(onFilterChange).toHaveBeenCalled();
    });

    it('calls onApply when Apply Filters button is clicked', () => {
      const onApply = vi.fn();
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={vi.fn()}
          onApply={onApply}
          onReset={vi.fn()}
        />
      );

      fireEvent.click(screen.getByRole('button', { name: /apply filters/i }));

      expect(onApply).toHaveBeenCalledTimes(1);
    });

    it('calls onReset when Clear button is clicked', () => {
      const onReset = vi.fn();
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={vi.fn()}
          onApply={vi.fn()}
          onReset={onReset}
        />
      );

      fireEvent.click(screen.getByRole('button', { name: /clear/i }));

      expect(onReset).toHaveBeenCalledTimes(1);
    });
  });
});