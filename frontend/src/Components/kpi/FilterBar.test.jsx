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
          onReset={vi.fn()}
        />
      );

      expect(screen.getByText('Date')).toBeInTheDocument();
      expect(screen.getByText('Week')).toBeInTheDocument();
      expect(screen.getByText('Team')).toBeInTheDocument();
      expect(screen.getByText('Style')).toBeInTheDocument();
    });
  });

  describe('Dual-line toggle (customer context)', () => {
    const customerFilters = {
      ...defaultFilters,
      includeDualLines: false,
      lineCode: '',
    };

    it('RED - renders dual-line checkbox when context is customer', () => {
      render(
        <FilterBar
          filters={customerFilters}
          onFilterChange={vi.fn()}
          onReset={vi.fn()}
          context="customer"
          filterOptions={{ line_code: ['35-36', '10-12'] }}
        />
      );

      expect(screen.getByLabelText(/dual lines/i)).toBeInTheDocument();
      const checkbox = screen.getByRole('checkbox', { name: /dual lines/i });
      expect(checkbox).not.toBeChecked();
    });

    it('RED - does NOT render dual-line checkbox when context is plant', () => {
      render(
        <FilterBar
          filters={customerFilters}
          onFilterChange={vi.fn()}
          onReset={vi.fn()}
          context="plant"
          filterOptions={{ line_code: ['35-36'] }}
        />
      );

      expect(screen.queryByLabelText(/dual lines/i)).not.toBeInTheDocument();
    });

    it('RED - does NOT render dual-line checkbox when context is not provided', () => {
      render(
        <FilterBar
          filters={customerFilters}
          onFilterChange={vi.fn()}
          onReset={vi.fn()}
          filterOptions={{ line_code: ['35-36'] }}
        />
      );

      expect(screen.queryByLabelText(/dual lines/i)).not.toBeInTheDocument();
    });

    it('RED - renders line_code selector when dual lines are enabled and options exist', () => {
      const filtersWithDual = { ...customerFilters, includeDualLines: true };

      render(
        <FilterBar
          filters={filtersWithDual}
          onFilterChange={vi.fn()}
          onReset={vi.fn()}
          context="customer"
          filterOptions={{ line_code: ['35-36', '10-12', '20-21'] }}
        />
      );

      const lineCodeSelect = screen.getByLabelText(/line code/i);
      expect(lineCodeSelect).toBeInTheDocument();
      // Verify options
      const options = lineCodeSelect.querySelectorAll('option');
      expect(options).toHaveLength(4); // placeholder + 3 values
      expect(options[0].value).toBe('');
      expect(options[1].value).toBe('35-36');
      expect(options[2].value).toBe('10-12');
      expect(options[3].value).toBe('20-21');
    });

    it('RED - does NOT render line_code selector when dual lines are disabled', () => {
      render(
        <FilterBar
          filters={customerFilters}
          onFilterChange={vi.fn()}
          onReset={vi.fn()}
          context="customer"
          filterOptions={{ line_code: ['35-36'] }}
        />
      );

      expect(screen.queryByLabelText(/line code/i)).not.toBeInTheDocument();
    });

    it('RED - does NOT render line_code selector when no line_code options exist', () => {
      const filtersWithDual = { ...customerFilters, includeDualLines: true };

      render(
        <FilterBar
          filters={filtersWithDual}
          onFilterChange={vi.fn()}
          onReset={vi.fn()}
          context="customer"
          filterOptions={{ line_code: [] }}
        />
      );

      expect(screen.queryByLabelText(/line code/i)).not.toBeInTheDocument();
    });

    it('RED - toggling checkbox calls onFilterChange with includeDualLines updated', () => {
      const onFilterChange = vi.fn();

      render(
        <FilterBar
          filters={customerFilters}
          onFilterChange={onFilterChange}
          onReset={vi.fn()}
          context="customer"
          filterOptions={{ line_code: ['35-36'] }}
        />
      );

      const checkbox = screen.getByRole('checkbox', { name: /dual lines/i });
      fireEvent.click(checkbox);

      expect(onFilterChange).toHaveBeenCalledTimes(1);
      const updatedFilters = onFilterChange.mock.calls[0][0];
      expect(updatedFilters.includeDualLines).toBe(true);
    });

    it('RED - selecting a line_code calls onFilterChange with lineCode updated', () => {
      const onFilterChange = vi.fn();
      const filtersWithDual = { ...customerFilters, includeDualLines: true };

      render(
        <FilterBar
          filters={filtersWithDual}
          onFilterChange={onFilterChange}
          onReset={vi.fn()}
          context="customer"
          filterOptions={{ line_code: ['35-36', '10-12'] }}
        />
      );

      const selector = screen.getByLabelText(/line code/i);
      fireEvent.change(selector, { target: { value: '35-36' } });

      expect(onFilterChange).toHaveBeenCalledTimes(1);
      const updatedFilters = onFilterChange.mock.calls[0][0];
      expect(updatedFilters.lineCode).toBe('35-36');
    });

    it('RED - clearing line_code selector updates filters with empty lineCode', () => {
      const onFilterChange = vi.fn();
      const filtersWithDual = { ...customerFilters, includeDualLines: true, lineCode: '35-36' };

      render(
        <FilterBar
          filters={filtersWithDual}
          onFilterChange={onFilterChange}
          onReset={vi.fn()}
          context="customer"
          filterOptions={{ line_code: ['35-36', '10-12'] }}
        />
      );

      const selector = screen.getByLabelText(/line code/i);
      fireEvent.change(selector, { target: { value: '' } });

      const updatedFilters = onFilterChange.mock.calls[0][0];
      expect(updatedFilters.lineCode).toBe('');
    });
  });

  describe('Interactions', () => {
    it('calls onFilterChange when input changes', () => {
      const onFilterChange = vi.fn();
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={onFilterChange}
          onReset={vi.fn()}
        />
      );

      // Style input is the 3rd input (index 2) after DateRangePicker
      const inputs = document.querySelectorAll('.filter-input');
      fireEvent.change(inputs[2], { target: { value: 'NewStyle' } });

      expect(onFilterChange).toHaveBeenCalled();
    });

    it('does not render Apply Filters button', () => {
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={vi.fn()}
          onReset={vi.fn()}
        />
      );

      expect(screen.queryByRole('button', { name: /apply filters/i })).not.toBeInTheDocument();
    });

    it('calls onReset when Clear button is clicked', () => {
      const onReset = vi.fn();
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={vi.fn()}
          onReset={onReset}
        />
      );

      fireEvent.click(screen.getByRole('button', { name: /clear/i }));

      expect(onReset).toHaveBeenCalledTimes(1);
    });

    it('renders Clear inside the filter row actions group', () => {
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={vi.fn()}
          onReset={vi.fn()}
        />
      );

      expect(screen.getByText('Actions')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument();
    });
  });
});
