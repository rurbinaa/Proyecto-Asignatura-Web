import QcfaKpiDashboard from './QcfaKpiDashboard';

/**
 * CustomerDashboard — QC FA Customer view.
 * Fetches all QC FA KPIs with context=customer (table_type='QFC').
 */
export default function CustomerDashboard({ volatileFile, isFastMode }) {
  return (
    <QcfaKpiDashboard
      context="customer"
      volatileFile={volatileFile}
      isFastMode={isFastMode}
    />
  );
}
