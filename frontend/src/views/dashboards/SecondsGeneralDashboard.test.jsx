/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import SecondsGeneralDashboard from './SecondsGeneralDashboard';
import axiosClient from '../../api/axiosClient';

vi.mock('../../api/axiosClient');

vi.mock('../../Components/kpi/KpiCard', () => ({
  default: ({ title, children, error }) => (
    <section className="kpi-card">
      <h2>{title}</h2>
      {error && <div className="error-message">{error}</div>}
      <div>{children}</div>
    </section>
  ),
}));

vi.mock('../../Components/kpi/BarChartKpi', () => ({
  default: () => <div>BarChartKpi</div>,
}));

vi.mock('../../Components/kpi/LineChartKpi', () => ({
  default: () => <div>LineChartKpi</div>,
}));

vi.mock('../../Components/kpi/DonutChartKpi', () => ({
  default: () => <div>DonutChartKpi</div>,
}));

describe('SecondsGeneralDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches defects-by-customer endpoint on mount', async () => {
    axiosClient.get.mockResolvedValue({ data: [] });

    render(<SecondsGeneralDashboard />);

    await waitFor(() => {
      expect(axiosClient.get).toHaveBeenCalled();
    });

    const urls = axiosClient.get.mock.calls.map(([url]) => url);
    expect(urls).toContain('/quality/kpis/seconds-general/defects-by-customer/');
  });

  it('fetches defects-by-style endpoint on mount', async () => {
    axiosClient.get.mockResolvedValue({ data: [] });

    render(<SecondsGeneralDashboard />);

    await waitFor(() => {
      expect(axiosClient.get).toHaveBeenCalled();
    });

    const urls = axiosClient.get.mock.calls.map(([url]) => url);
    expect(urls).toContain('/quality/kpis/seconds-general/defects-by-style/');
  });

  it('fetches weekly-trend endpoint on mount', async () => {
    axiosClient.get.mockResolvedValue({ data: [] });

    render(<SecondsGeneralDashboard />);

    await waitFor(() => {
      expect(axiosClient.get).toHaveBeenCalled();
    });

    const urls = axiosClient.get.mock.calls.map(([url]) => url);
    expect(urls).toContain('/quality/kpis/seconds-general/weekly-trend/');
  });

  it('fetches sewing-vs-fabric endpoint on mount', async () => {
    axiosClient.get.mockResolvedValue({ data: [] });

    render(<SecondsGeneralDashboard />);

    await waitFor(() => {
      expect(axiosClient.get).toHaveBeenCalled();
    });

    const urls = axiosClient.get.mock.calls.map(([url]) => url);
    expect(urls).toContain('/quality/kpis/seconds-general/sewing-vs-fabric/');
  });

  it('makes exactly 4 API calls on mount', async () => {
    axiosClient.get.mockResolvedValue({ data: [] });

    render(<SecondsGeneralDashboard />);

    await waitFor(() => {
      expect(axiosClient.get).toHaveBeenCalledTimes(4);
    });
  });

  it('renders Defects by Customer bar chart card', async () => {
    axiosClient.get.mockResolvedValue({ data: [] });

    render(<SecondsGeneralDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Defects by Customer')).toBeInTheDocument();
    });
  });

  it('renders Defects by Style bar chart card', async () => {
    axiosClient.get.mockResolvedValue({ data: [] });

    render(<SecondsGeneralDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Defects by Style')).toBeInTheDocument();
    });
  });

  it('renders Weekly Trend line chart card', async () => {
    axiosClient.get.mockResolvedValue({ data: [] });

    render(<SecondsGeneralDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Weekly Trend')).toBeInTheDocument();
    });
  });

  it('renders Sewing vs Fabric donut chart card', async () => {
    axiosClient.get.mockResolvedValue({ data: [] });

    render(<SecondsGeneralDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Sewing vs Fabric')).toBeInTheDocument();
    });
  });

  it('renders dashboard title', async () => {
    axiosClient.get.mockResolvedValue({ data: [] });

    render(<SecondsGeneralDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Seconds General Analytics')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully — still attempts all 4 calls', async () => {
    axiosClient.get.mockRejectedValue(new Error('Network error'));

    render(<SecondsGeneralDashboard />);

    // Even on error, all 4 endpoints were attempted
    await waitFor(() => {
      expect(axiosClient.get).toHaveBeenCalledTimes(4);
    });
  });
});
