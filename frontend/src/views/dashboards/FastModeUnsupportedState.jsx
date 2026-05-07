/**
 * FastModeUnsupportedState — Reusable banner for dashboards that do not
 * support Fast Mode (volatile Excel data).
 *
 * Renders a visible message indicating that the dashboard cannot display
 * data while a volatile file is active, without making any HTTP requests
 * or falling back to live database queries.
 *
 * @param {object} props
 * @param {string} [props.message] — Optional custom message override.
 *        Falls back to a default generic message if not provided.
 */
export default function FastModeUnsupportedState({ message }) {
  const defaultMessage =
    'Fast Mode no soportado: este dashboard no está disponible en modo rápido. ' +
    'Seleccioná un dashboard QC FA, Container o volvé al modo de base de datos ' +
    'para visualizar estos datos.';

  return (
    <div className="fast-mode-unsupported" role="status" aria-live="polite">
      <strong>Fast mode no soportado:</strong>{' '}
      {message || defaultMessage}
    </div>
  );
}
