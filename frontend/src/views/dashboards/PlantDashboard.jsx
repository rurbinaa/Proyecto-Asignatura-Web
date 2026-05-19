import QcfaKpiDashboard from './QcfaKpiDashboard';

/**
 * PlantDashboard — QC FA Plant view.
 * Fetches all QC FA KPIs with context=plant (table_type='QFA').
 */
export default function PlantDashboard({ volatileFile, isFastMode }) {
  return (
    <QcfaKpiDashboard
      context="plant"
      volatileFile={volatileFile}
      isFastMode={isFastMode}
    />
  );
}
