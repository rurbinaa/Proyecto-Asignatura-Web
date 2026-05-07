/**
 * SecondsA4FilterBar — Dedicated filter surface for Seconds A4 analytics.
 *
 * Accepts the same prop shape as FilterBar for DashboardShell compatibility
 * but only surfaces year and line filters relevant to Seconds A4.
 * Falls back to shared CSS from FilterBar.css.
 */
import './FilterBar.css';

export default function SecondsA4FilterBar({ filters, onFilterChange, onReset, filterOptions }) {
  const handleChange = (field, value) => {
    onFilterChange({ ...filters, [field]: value });
  };

  const renderSelect = (field, label, placeholder) => {
    const options = filterOptions?.[field] || [];
    if (options.length === 0) {
      return (
        <input
          type="text"
          className="filter-input"
          value={filters[field] || ''}
          onChange={(e) => handleChange(field, e.target.value)}
          placeholder={placeholder}
        />
      );
    }
    return (
      <select
        id={field}
        className="filter-input"
        value={filters[field] || ''}
        onChange={(e) => handleChange(field, e.target.value)}
      >
        <option value="">{placeholder}</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    );
  };

  return (
    <div className="filter-bar">
      <div className="filter-row">
        <div className="filter-group">
          <label className="filter-label">Year</label>
          {renderSelect('year', 'Year', 'Select Year')}
        </div>

        <div className="filter-group">
          <label className="filter-label">Line</label>
          {renderSelect('line', 'Line', 'Select Line')}
        </div>

        <div className="filter-group filter-group-actions">
          <label className="filter-label">Actions</label>
          <button className="filter-btn-outline" onClick={onReset}>
            Clear
          </button>
        </div>
      </div>
    </div>
  );
}
