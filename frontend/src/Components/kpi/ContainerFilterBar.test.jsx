/** @vitest-environment jsdom */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ContainerFilterBar from './ContainerFilterBar';

vi.mock('../DateRangePicker', () => ({
  default: ({ startDate, endDate }) => (
    <div className="date-range-picker" data-testid="date-range-picker">
      {startDate} – {endDate}
    </div>
  ),
}));

describe('ContainerFilterBar', () => {
  const defaultFilters = {
    date_range: ['', ''],
    from_date: '',
    to_date: '',
    customer: '',
  };

  const onFilterChange = vi.fn();
  const onReset = vi.fn();

  describe('Date range visibility (hideDateRange prop)', () => {
    it('renders Date label and DateRangePicker when hideDateRange is not set (default)', () => {
      render(
        <ContainerFilterBar
          filters={defaultFilters}
          onFilterChange={onFilterChange}
          onReset={onReset}
        />
      );

      expect(screen.getByText('Date')).toBeInTheDocument();
      expect(screen.getByTestId('date-range-picker')).toBeInTheDocument();
    });

    it('renders DateRangePicker when hideDateRange is false', () => {
      render(
        <ContainerFilterBar
          filters={defaultFilters}
          onFilterChange={onFilterChange}
          onReset={onReset}
          hideDateRange={false}
        />
      );

      expect(screen.getByText('Date')).toBeInTheDocument();
      expect(screen.getByTestId('date-range-picker')).toBeInTheDocument();
    });

    it('hides Date label and DateRangePicker when hideDateRange is true', () => {
      render(
        <ContainerFilterBar
          filters={defaultFilters}
          onFilterChange={onFilterChange}
          onReset={onReset}
          hideDateRange
        />
      );

      expect(screen.queryByText('Date')).not.toBeInTheDocument();
      expect(screen.queryByTestId('date-range-picker')).not.toBeInTheDocument();
    });

    it('still renders Customer filter when hideDateRange is true', () => {
      render(
        <ContainerFilterBar
          filters={defaultFilters}
          onFilterChange={onFilterChange}
          onReset={onReset}
          hideDateRange
        />
      );

      expect(screen.getByText('Customer')).toBeInTheDocument();
      expect(screen.getByText('Clear')).toBeInTheDocument();
    });

    it('uses text input for Customer when customerOptions is empty (volatile mode)', () => {
      render(
        <ContainerFilterBar
          filters={defaultFilters}
          onFilterChange={onFilterChange}
          onReset={onReset}
          hideDateRange
          customerOptions={[]}
        />
      );

      const customerInput = document.querySelector('.filter-input');
      expect(customerInput.tagName).toBe('INPUT');
      expect(customerInput.getAttribute('type')).toBe('text');
      expect(customerInput.getAttribute('placeholder')).toBe('Select Customer');
    });

    it('uses select for Customer when customerOptions has values (live mode)', () => {
      render(
        <ContainerFilterBar
          filters={defaultFilters}
          onFilterChange={onFilterChange}
          onReset={onReset}
          customerOptions={['Customer A', 'Customer B']}
        />
      );

      const customerSelect = document.querySelector('.filter-group:not(.date-range-group) .filter-input');
      // Should be a SELECT when options are provided
      expect(customerSelect.tagName).toBe('SELECT');
      expect(customerSelect.options.length).toBe(3); // placeholder + 2 options
      expect(customerSelect.options[1].value).toBe('Customer A');
      expect(customerSelect.options[2].value).toBe('Customer B');
    });
  });
});
