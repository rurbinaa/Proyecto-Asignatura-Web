import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DateRangePicker from './DateRangePicker';

describe('DateRangePicker', () => {
  it('keeps the selected local date without shifting to the previous day', () => {
    const onChange = vi.fn();

    render(
      <DateRangePicker
        startDate=""
        endDate="2025-12-01"
        onChange={onChange}
      />
    );

    expect(screen.getByText('01/12/2025')).toBeInTheDocument();

    fireEvent.click(screen.getAllByText('Select date')[0]);
    fireEvent.click(screen.getByRole('button', { name: '1' }));

    expect(onChange).toHaveBeenCalledWith({
      startDate: '2025-12-01',
      endDate: '2025-12-01',
    });
  });
});
