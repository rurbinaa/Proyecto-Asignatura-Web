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
    it('renders all 8 filter inputs', () => {
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={vi.fn()}
          onApply={vi.fn()}
          onReset={vi.fn()}
        />
      );

      // 8 inputs: desde, hasta, week, team, style, color, customer, batch
      const inputs = document.querySelectorAll('.filter-input');
      expect(inputs).toHaveLength(8);
    });

    it('inputs reflect filters prop values', () => {
      const filtersWithValues = {
        date_range: ['2026-01-01', '2026-01-31'],
        week: '5',
        team: '2',
        style: 'Style-X',
        color: 'Rojo',
        customer: 'Cliente-1',
        batch: '10',
      };

      render(
        <FilterBar
          filters={filtersWithValues}
          onFilterChange={vi.fn()}
          onApply={vi.fn()}
          onReset={vi.fn()}
        />
      );

      const inputs = document.querySelectorAll('.filter-input');
      expect(inputs[0]).toHaveValue('2026-01-01');
      expect(inputs[1]).toHaveValue('2026-01-31');
      expect(inputs[2]).toHaveValue('5');
      expect(inputs[3]).toHaveValue('2');
      expect(inputs[4]).toHaveValue('Style-X');
      expect(inputs[5]).toHaveValue('Rojo');
      expect(inputs[6]).toHaveValue('Cliente-1');
      expect(inputs[7]).toHaveValue('10');
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

      // Style input is the 5th input (index 4)
      const inputs = document.querySelectorAll('.filter-input');
      fireEvent.change(inputs[4], { target: { value: 'NewStyle' } });

      expect(onFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ style: 'NewStyle' })
      );
    });

    it('calls onApply when Aplicar Filtros button is clicked', () => {
      const onApply = vi.fn();
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={vi.fn()}
          onApply={onApply}
          onReset={vi.fn()}
        />
      );

      fireEvent.click(screen.getByRole('button', { name: /aplicar filtros/i }));

      expect(onApply).toHaveBeenCalledTimes(1);
    });

    it('calls onReset when Limpiar button is clicked', () => {
      const onReset = vi.fn();
      render(
        <FilterBar
          filters={defaultFilters}
          onFilterChange={vi.fn()}
          onApply={vi.fn()}
          onReset={onReset}
        />
      );

      fireEvent.click(screen.getByRole('button', { name: /limpiar/i }));

      expect(onReset).toHaveBeenCalledTimes(1);
    });
  });
});
