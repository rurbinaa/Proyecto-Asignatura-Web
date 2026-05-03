import { useState, useEffect } from 'react';
import axiosClient from '../../api/axiosClient';
import KpiCard from '../../Components/kpi/KpiCard';
import BarChartKpi from '../../Components/kpi/BarChartKpi';
import LineChartKpi from '../../Components/kpi/LineChartKpi';
import DonutChartKpi from '../../Components/kpi/DonutChartKpi';
import Masonry from 'react-masonry-css';
import '../DashboardView.css';

const SECONDS_GEN_BASE = '/quality/kpis/seconds-general';

/**
 * SecondsGeneralDashboard — Seconds General analytics view.
 *
 * Fetches 4 analytics from the SecondsGeneral backend endpoints:
 *   - Defects by Customer (bar chart)
 *   - Defects by Style (bar chart)
 *   - Weekly Trend (line chart)
 *   - Sewing vs Fabric Mix (donut chart)
 *
 * All data is sourced exclusively from SecondsGeneral data (spec isolation requirement).
 */
export default function SecondsGeneralDashboard() {
  const [defectsByCustomer, setDefectsByCustomer] = useState(null);
  const [defectsByStyle, setDefectsByStyle] = useState(null);
  const [weeklyTrend, setWeeklyTrend] = useState(null);
  const [sewingVsFabric, setSewingVsFabric] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchAnalytics() {
      setLoading(true);
      setError(null);

      try {
        const [custRes, styleRes, trendRes, mixRes] = await Promise.all([
          axiosClient.get(`${SECONDS_GEN_BASE}/defects-by-customer/`),
          axiosClient.get(`${SECONDS_GEN_BASE}/defects-by-style/`),
          axiosClient.get(`${SECONDS_GEN_BASE}/weekly-trend/`),
          axiosClient.get(`${SECONDS_GEN_BASE}/sewing-vs-fabric/`),
        ]);

        if (!cancelled) {
          setDefectsByCustomer(custRes.data);
          setDefectsByStyle(styleRes.data);
          setWeeklyTrend(trendRes.data);
          setSewingVsFabric(mixRes.data);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.response?.data?.detail || err.message || 'Failed to load analytics');
          setLoading(false);
        }
      }
    }

    fetchAnalytics();

    return () => {
      cancelled = true;
    };
  }, []);

  const seriesForWeeklyTrend = weeklyTrend && weeklyTrend.length > 0
    ? weeklyTrend.map((s) => ({
        name: s.name || 'Defects',
        data: s.data || [],
      }))
    : [];

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Seconds General Analytics</h1>
      </div>

      <Masonry
        breakpointCols={{ default: 2, 768: 1 }}
        className="dashboard-masonry"
        columnClassName="dashboard-masonry-column"
      >
        {/* Defects by Customer */}
        <KpiCard title="Defects by Customer" loading={loading} error={error}>
          {defectsByCustomer && defectsByCustomer.length > 0 ? (
            <BarChartKpi
              data={defectsByCustomer}
              color="#3b82f6"
              xAxisLabel="Customer"
              yAxisLabel="Total Defects"
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Defects by Style */}
        <KpiCard title="Defects by Style" loading={loading} error={error}>
          {defectsByStyle && defectsByStyle.length > 0 ? (
            <BarChartKpi
              data={defectsByStyle}
              color="#8b5cf6"
              horizontal
              xAxisLabel="Total Defects"
              yAxisLabel="Style"
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Weekly Trend */}
        <KpiCard title="Weekly Trend" loading={loading} error={error}>
          {seriesForWeeklyTrend.length > 0 ? (
            <LineChartKpi
              series={seriesForWeeklyTrend}
              xAxisLabel="Week"
              yAxisLabel="Defects"
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>

        {/* Sewing vs Fabric Mix */}
        <KpiCard title="Sewing vs Fabric" loading={loading} error={error}>
          {sewingVsFabric && sewingVsFabric.length > 0 ? (
            <DonutChartKpi
              data={sewingVsFabric}
              showSliceLabels
            />
          ) : (
            <div className="null-message">
              {loading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </KpiCard>
      </Masonry>
    </div>
  );
}
