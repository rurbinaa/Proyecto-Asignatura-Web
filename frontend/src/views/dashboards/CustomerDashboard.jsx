import QcfaKpiDashboard from './QcfaKpiDashboard';

/**
 * CustomerDashboard — QC FA Customer view.
 * Fetches all QC FA KPIs with context=customer (table_type='QFC').
 */
export default function CustomerDashboard({ volatileData, volatileFile }) {
  return (
    <QcfaKpiDashboard
      context="customer"
      volatileData={volatileData}
      volatileFile={volatileFile}
    />
  );
}
