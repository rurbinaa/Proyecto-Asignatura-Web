import ReportGenerator from '../Components/ReportGenerator';
import './DashboardView.css';

/**
 * QualityReportsView — Standalone navigable view for generating quality reports.
 *
 * Sits at the same navigation level as Import Batches and Dashboard.
 * Manager-only access, consistent with the rest of the app.
 */
export default function QualityReportsView() {
  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Quality Reports</h1>
      </div>
      <ReportGenerator />
    </div>
  );
}
