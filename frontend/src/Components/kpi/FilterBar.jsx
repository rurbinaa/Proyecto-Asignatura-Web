import DateRangePicker from '../DateRangePicker';
import './FilterBar.css';

export default function FilterBar({ filters, onFilterChange, onApply, onReset, filterOptions }) {
  const handleChange = (field, value) => {
    onFilterChange({ ...filters, [field]: value });
  };

  const handleDateRangeChange = (range) => {
    onFilterChange({ ...filters, date_range: [range.startDate || '', range.endDate || ''] });
  };

  const renderSelect = (field, label, placeholder) => {
    const options = filterOptions?.[field] || [];
    if (options.length === 0) {
      return (
        <input
          type="text"
          className="filter-input"
          value={filters[field]}
          onChange={(e) => handleChange(field, e.target.value)}
          placeholder={placeholder}
        />
      );
    }
    return (
      <>
        <label htmlFor={field} className="filter-label">{label}</label>
        <select
          id={field}
          className="filter-input"
          value={filters[field]}
          onChange={(e) => handleChange(field, e.target.value)}
        >
          <option value="">{placeholder}</option>
          {options.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </>
    );
  };

  return (
    <div className="filter-bar">
      <div className="filter-row">
        <div className="filter-group date-range-group">
          <label className="filter-label">Date</label>
          <DateRangePicker
            startDate={filters.date_range?.[0] || ''}
            endDate={filters.date_range?.[1] || ''}
            onChange={handleDateRangeChange}
            size="small"
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Week</label>
          {renderSelect('week', 'Week', 'Week')}
        </div>

        <div className="filter-group">
          <label className="filter-label">Team</label>
          {renderSelect('team', 'Team', 'Select Team')}
        </div>

        <div className="filter-group">
          <label className="filter-label">Style</label>
          {renderSelect('style', 'Style', 'Select Style')}
        </div>

        <div className="filter-group">
          <label className="filter-label">Color</label>
          {renderSelect('color', 'Color', 'Select Color')}
        </div>

        <div className="filter-group">
          <label className="filter-label">Customer</label>
          {renderSelect('customer', 'Customer', 'Select Customer')}
        </div>

        <div className="filter-group">
          <label className="filter-label">Batch</label>
          {renderSelect('batch', 'Batch', 'Select Batch')}
        </div>
      </div>

      <div className="filter-actions">
        <button className="filter-btn-primary" onClick={onApply}>
          Apply Filters
        </button>
        <button className="filter-btn-outline" onClick={onReset}>
          Clear
        </button>
      </div>
    </div>
  );
}
