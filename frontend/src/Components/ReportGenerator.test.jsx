/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ReportGenerator from './ReportGenerator';

vi.mock('../api/reports', () => ({
  downloadQualityReport: vi.fn(),
  validateDateRange: vi.fn(),
}));

// Import the mocked functions to set up return values in tests
import { downloadQualityReport, validateDateRange } from '../api/reports';

describe('ReportGenerator', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('structure', () => {
    it('renders the report generator container', () => {
      const { container } = render(<ReportGenerator />);
      expect(container.querySelector('.report-generator')).toBeInTheDocument();
    });

    it('renders the title and subtitle', () => {
      render(<ReportGenerator />);
      expect(screen.getByText('Generate Quality Report')).toBeInTheDocument();
      expect(
        screen.getByText('Select whole months to export historical data'),
      ).toBeInTheDocument();
    });

    it('renders month inputs', () => {
      render(<ReportGenerator />);
      expect(screen.getByLabelText('From month')).toBeInTheDocument();
      expect(screen.getByLabelText('To month')).toBeInTheDocument();
    });

    it('renders the Generate Report button', () => {
      render(<ReportGenerator />);
      expect(screen.getByText('Generate Report')).toBeInTheDocument();
    });
  });

  describe('button disabled state', () => {
    it('is disabled when both months are empty', () => {
      render(<ReportGenerator />);
      const btn = screen.getByRole('button', { name: /generate report/i });
      expect(btn).toBeDisabled();
    });

    it('is disabled when only start month is filled', () => {
      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      const btn = screen.getByRole('button', { name: /generate report/i });
      expect(btn).toBeDisabled();
    });

    it('is disabled when only end month is filled', () => {
      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      const btn = screen.getByRole('button', { name: /generate report/i });
      expect(btn).toBeDisabled();
    });

    it('is enabled when both months are filled', () => {
      render(<ReportGenerator />);
      const startInput = screen.getByLabelText('From month');
      const endInput = screen.getByLabelText('To month');
      fireEvent.change(startInput, { target: { value: '2024-01' } });
      fireEvent.change(endInput, { target: { value: '2024-03' } });
      const btn = screen.getByRole('button', { name: /generate report/i });
      expect(btn).not.toBeDisabled();
    });
  });

  describe('generation flow - success', () => {
    it('calls downloadQualityReport when button is clicked', async () => {
      validateDateRange.mockReturnValue({ valid: true });
      downloadQualityReport.mockResolvedValue({ filename: 'report_2024_03.xlsx' });

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(downloadQualityReport).toHaveBeenCalledOnce();
      });
    });

    it('shows success message after successful generation', async () => {
      validateDateRange.mockReturnValue({ valid: true });
      downloadQualityReport.mockResolvedValue({ filename: 'report_2024_03.xlsx' });

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(
          screen.getByText('Report generated successfully'),
        ).toBeInTheDocument();
      });
    });

    it('shows the filename in success status', async () => {
      validateDateRange.mockReturnValue({ valid: true });
      downloadQualityReport.mockResolvedValue({ filename: 'report_2024_03.xlsx' });

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText('(report_2024_03.xlsx)')).toBeInTheDocument();
      });
    });
  });

  describe('generation flow - validation error', () => {
    it('does NOT call downloadQualityReport when validation fails', async () => {
      validateDateRange.mockReturnValue({
        valid: false,
        message: 'Invalid dates',
      });

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-03' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-01' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(downloadQualityReport).not.toHaveBeenCalled();
      });
    });
  });

  describe('generation flow - API error', () => {
    it('shows error message when downloadQualityReport throws', async () => {
      validateDateRange.mockReturnValue({ valid: true });
      downloadQualityReport.mockRejectedValue(new Error('Network error'));

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });

    it('shows the error status box', async () => {
      validateDateRange.mockReturnValue({ valid: true });
      downloadQualityReport.mockRejectedValue(new Error('API failure'));

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText('Error generating report')).toBeInTheDocument();
      });
    });
  });

  describe('generating state', () => {
    it('shows generating overlay while request is in flight', async () => {
      validateDateRange.mockReturnValue({ valid: true });
      // Keep the promise pending so we can observe the generating state
      downloadQualityReport.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ filename: 'test.xlsx' }), 1000),
          ),
      );

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      // The button text changes during generation
      expect(
        screen.getAllByText('Generating Report...').length,
      ).toBeGreaterThanOrEqual(1);
    });

    it('disables the generate button during generation', async () => {
      validateDateRange.mockReturnValue({ valid: true });
      downloadQualityReport.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ filename: 'test.xlsx' }), 1000),
          ),
      );

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      const btn = screen.getByRole('button', { name: /generating/i });
      expect(btn).toBeDisabled();
    });
  });

  describe('dismiss', () => {
    it('clears error message when dismiss button is clicked', async () => {
      validateDateRange.mockReturnValue({ valid: true });
      downloadQualityReport.mockRejectedValue(new Error('Dismiss me'));

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText('Dismiss me')).toBeInTheDocument();
      });

      // Click dismiss button
      const dismissBtn = screen.getByText('x');
      fireEvent.click(dismissBtn);

      await waitFor(() => {
        expect(screen.queryByText('Dismiss me')).not.toBeInTheDocument();
      });
    });

    it('clears success message when dismiss button is clicked', async () => {
      validateDateRange.mockReturnValue({ valid: true });
      downloadQualityReport.mockResolvedValue({ filename: 'test.xlsx' });

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(
          screen.getByText('Report generated successfully'),
        ).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('x'));

      await waitFor(() => {
        expect(
          screen.queryByText('Report generated successfully'),
        ).not.toBeInTheDocument();
      });
    });

    it('clears error when month selection changes', async () => {
      validateDateRange.mockReturnValue({ valid: true });
      downloadQualityReport.mockRejectedValue(new Error('Error msg'));

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText('Error msg')).toBeInTheDocument();
      });

      // Changing a month clears the error
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-02' },
      });

      expect(screen.queryByText('Error msg')).not.toBeInTheDocument();
    });
  });

  describe('validateDateRange interaction', () => {
    it('passes converted dates to validateDateRange', async () => {
      validateDateRange.mockReturnValue({ valid: true });
      downloadQualityReport.mockResolvedValue({ filename: 'test.xlsx' });

      render(<ReportGenerator />);
      fireEvent.change(screen.getByLabelText('From month'), {
        target: { value: '2024-01' },
      });
      fireEvent.change(screen.getByLabelText('To month'), {
        target: { value: '2024-03' },
      });
      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        // startDate: 2024-01-01, endDate: 2024-03-31 (March has 31 days)
        expect(validateDateRange).toHaveBeenCalledWith(
          '2024-01-01',
          '2024-03-31',
        );
      });
    });
  });
});
