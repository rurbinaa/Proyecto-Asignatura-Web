/**
 * ContainerDashboard — Container inspection view.
 *
 * Basic shell. Accepts props for DashboardShell forwarding compatibility.
 * Full analytics implementation deferred to a future phase.
 */
export default function ContainerDashboard({ volatileData, volatileFile }) {
  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Container Dashboard</h1>
      </div>
      <p>Container analytics coming soon.</p>
    </div>
  );
}
