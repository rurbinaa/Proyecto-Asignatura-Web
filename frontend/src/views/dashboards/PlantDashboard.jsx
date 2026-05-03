import QcfaKpiDashboard from './QcfaKpiDashboard';

/**
 * PlantDashboard — QC FA Plant view.
 * Fetches all QC FA KPIs with context=plant (table_type='QFA').
 */
export default function PlantDashboard({ volatileData, volatileFile }) {
  return (
    <QcfaKpiDashboard
      context="plant"
      volatileData={volatileData}
      volatileFile={volatileFile}
    />
  );
}
