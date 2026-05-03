import { useState, Suspense, lazy } from 'react';
import './DashboardShell.css';

const PlantDashboard = lazy(() => import('./dashboards/PlantDashboard'));
const CustomerDashboard = lazy(() => import('./dashboards/CustomerDashboard'));
const SecondsA4Dashboard = lazy(() => import('./dashboards/SecondsA4Dashboard'));
const SecondsGeneralDashboard = lazy(() => import('./dashboards/SecondsGeneralDashboard'));
const ContainerDashboard = lazy(() => import('./dashboards/ContainerDashboard'));

const SHEETS = {
  plant: { label: 'QC FA Plant', Component: PlantDashboard },
  customer: { label: 'QC FA Customer', Component: CustomerDashboard },
  seconds_a4: { label: 'Seconds A4', Component: SecondsA4Dashboard },
  seconds_gen: { label: 'Seconds General', Component: SecondsGeneralDashboard },
  container: { label: 'Container', Component: ContainerDashboard },
};

const DEFAULT_SHEET = 'plant';

function resolveSheet(key) {
  return SHEETS[key] || SHEETS[DEFAULT_SHEET];
}

/**
 * DashboardShell — Internal navigation container for the 5 sheet-aligned dashboards.
 *
 * Uses React.lazy + Suspense for on-demand loading. The active sheet is managed
 * via local state (`activeSheet`), preserving the `/dashboard` URL contract.
 */
export default function DashboardShell({ volatileData, volatileFile }) {
  const [activeSheet, setActiveSheet] = useState(DEFAULT_SHEET);
  const sheet = resolveSheet(activeSheet);
  const ActiveComponent = sheet.Component;

  return (
    <div className="dashboard-shell">
      <nav className="dashboard-shell-tabs" role="tablist">
        {Object.entries(SHEETS).map(([key, { label }]) => (
          <button
            key={key}
            role="tab"
            aria-selected={activeSheet === key}
            onClick={() => setActiveSheet(key)}
            className={`dashboard-shell-tab ${activeSheet === key ? 'active' : ''}`.trim()}
          >
            {label}
          </button>
        ))}
      </nav>

      <div className="dashboard-shell-content" role="tabpanel">
        <Suspense fallback={<div>Loading dashboard...</div>}>
          <ActiveComponent volatileData={volatileData} volatileFile={volatileFile} />
        </Suspense>
      </div>
    </div>
  );
}

export { DEFAULT_SHEET, SHEETS, resolveSheet };
