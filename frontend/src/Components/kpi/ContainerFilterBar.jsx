import DateRangePicker from '../DateRangePicker';
import './FilterBar.css';

/**
 * ContainerFilterBar — Container-specific filter surface.
 *
 * Owns only Container-valid live filters: customer, date_range,
 * from_date, and to_date. Does NOT use or depend on the QFA
 * FilterOptionsView or QFA-only filter fields (week, team, style,
 * color, batch).
 *
 * Reuses DateRangePicker and FilterBar.css as shared low-level
 * primitives, consistent with the per-sheet specialized filter
 * architecture.
 */
export default function ContainerFilterBar({ filters, onFilterChange, onReset, customerOptions = [] }) {
  const handleChange = (field, value) => {
    onFilterChange({ ...filters, [field]: value });
  };

  const handleDateRangeChange = (range) => {
    const startDate = range.startDate || '';
    const endDate = range.endDate || '';

    if (startDate && endDate) {
      onFilterChange({
        ...filters,
        date_range: [startDate, endDate],
        from_date: '',
        to_date: '',
      });
      return;
    }

    onFilterChange({
      ...filters,
      date_range: ['', ''],
      from_date: startDate,
      to_date: endDate,
    });
  };

  return (
    <div className="filter-bar">
      <div className="filter-row">
        <div className="filter-group date-range-group">
          <label className="filter-label">Date</label>
          <DateRangePicker
            startDate={filters.date_range?.[0] || filters.from_date || ''}
            endDate={filters.date_range?.[1] || filters.to_date || ''}
            onChange={handleDateRangeChange}
            size="small"
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Customer</label>
          <select
            className="filter-input"
            value={filters.customer || ''}
            onChange={(e) => handleChange('customer', e.target.value)}
          >
            <option value="">Select Customer</option>
            {customerOptions.map((customer) => (
              <option key={customer} value={customer}>{customer}</option>
            ))}
          </select>
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
