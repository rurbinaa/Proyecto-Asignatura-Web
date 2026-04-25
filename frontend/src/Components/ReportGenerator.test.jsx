import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import ReportGenerator from './ReportGenerator';
import { downloadQualityReport, validateDateRange } from '../api/reports';

vi.mock('../api/reports', () => ({
  downloadQualityReport: vi.fn(),
  validateDateRange: vi.fn(),
}));

vi.mock('./DateRangePicker', () => ({
  default: ({ onChange }) => (
    <div>
      <button type="button" onClick={() => onChange({ startDate: '2026-03-01', endDate: '2026-03-31' })}>
        Set valid range
      </button>
      <button type="button" onClick={() => onChange({ startDate: '', endDate: '' })}>
        Clear range
      </button>
    </div>
  ),
}));

describe('ReportGenerator', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    validateDateRange.mockReturnValue({ valid: true });
  });

  it('keeps generate button disabled until a full range is selected', () => {
    render(<ReportGenerator />);

    const generateButton = screen.getByRole('button', { name: /generate report/i });
    expect(generateButton).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: /set valid range/i }));
    expect(generateButton).not.toBeDisabled();
  });

  it('shows validation errors without triggering the download request', async () => {
    validateDateRange.mockReturnValue({ valid: false, message: 'Select a valid period' });
    render(<ReportGenerator />);

    fireEvent.click(screen.getByRole('button', { name: /set valid range/i }));

    const generateButton = screen.getByRole('button', { name: /^generate report$/i });
    await waitFor(() => {
      expect(generateButton).not.toBeDisabled();
    });

    fireEvent.click(generateButton);

    expect(await screen.findByText('Select a valid period')).toBeInTheDocument();
    expect(downloadQualityReport).not.toHaveBeenCalled();
  });

  it('downloads and shows success feedback when the report request succeeds', async () => {
    downloadQualityReport.mockResolvedValue({ filename: 'Reporte_Calidad_Marzo_2026.xlsx' });
    render(<ReportGenerator />);

    fireEvent.click(screen.getByRole('button', { name: /set valid range/i }));

    const generateButton = screen.getByRole('button', { name: /^generate report$/i });
    await waitFor(() => {
      expect(generateButton).not.toBeDisabled();
    });

    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(downloadQualityReport).toHaveBeenCalledWith('2026-03-01', '2026-03-31');
    });

    expect(await screen.findByText('Report generated')).toBeInTheDocument();
    expect(screen.getByText(/Reporte_Calidad_Marzo_2026.xlsx/)).toBeInTheDocument();
  });

  it('shows API errors and allows dismissing the feedback', async () => {
    downloadQualityReport.mockRejectedValue(new Error('Backend unavailable'));
    render(<ReportGenerator />);

    fireEvent.click(screen.getByRole('button', { name: /set valid range/i }));

    const generateButton = screen.getByRole('button', { name: /^generate report$/i });
    await waitFor(() => {
      expect(generateButton).not.toBeDisabled();
    });

    fireEvent.click(generateButton);

    expect(await screen.findByText('Backend unavailable')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '×' }));

    await waitFor(() => {
      expect(screen.queryByText('Backend unavailable')).not.toBeInTheDocument();
    });
  });
});
