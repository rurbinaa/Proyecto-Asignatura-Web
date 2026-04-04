import './FilterBar.css';

export default function FilterBar({ filters, onFilterChange, onApply, onReset, filterOptions }) {
  const handleChange = (field, value) => {
    onFilterChange({ ...filters, [field]: value });
  };

  const handleDateRangeChange = (index, value) => {
    const newRange = [...filters.date_range];
    newRange[index] = value;
    onFilterChange({ ...filters, date_range: newRange });
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
          list={`${field}-list`}
        />
      );
    }
    return (
      <>
        <select
          className="filter-input"
          value={filters[field]}
          onChange={(e) => handleChange(field, e.target.value)}
        >
          <option value="">{placeholder}</option>
          {options.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        <datalist id={`${field}-list`}>
          {options.map((opt) => (
            <option key={opt} value={opt} />
          ))}
        </datalist>
      </>
    );
  };

  return (
    <div className="filter-bar">
      <div className="filter-row">
        <div className="filter-group date-range-group">
          <label className="filter-label">Desde</label>
          <input
            type="date"
            className="filter-input"
            value={filters.date_range[0] || ''}
            onChange={(e) => handleDateRangeChange(0, e.target.value)}
          />
        </div>

        <div className="filter-group date-range-group">
          <label className="filter-label">Hasta</label>
          <input
            type="date"
            className="filter-input"
            value={filters.date_range[1] || ''}
            onChange={(e) => handleDateRangeChange(1, e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Semana</label>
          {renderSelect('week', 'Semana', 'Semana')}
        </div>

        <div className="filter-group">
          <label className="filter-label">Team</label>
          {renderSelect('team', 'Team', '#')}
        </div>

        <div className="filter-group">
          <label className="filter-label">Estilo</label>
          {renderSelect('style', 'Estilo', 'Estilo')}
        </div>

        <div className="filter-group">
          <label className="filter-label">Color</label>
          {renderSelect('color', 'Color', 'Color')}
        </div>

        <div className="filter-group">
          <label className="filter-label">Cliente</label>
          {renderSelect('customer', 'Cliente', 'Cliente')}
        </div>

        <div className="filter-group">
          <label className="filter-label">Batch</label>
          {renderSelect('batch', 'Batch', '#')}
        </div>
      </div>

      <div className="filter-actions">
        <button className="filter-btn-primary" onClick={onApply}>
          Aplicar Filtros
        </button>
        <button className="filter-btn-outline" onClick={onReset}>
          Limpiar
        </button>
      </div>
    </div>
  );
}
