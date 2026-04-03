import './FilterBar.css';

export default function FilterBar({ filters, onFilterChange, onApply, onReset }) {
  const handleChange = (field, value) => {
    onFilterChange({ ...filters, [field]: value });
  };

  const handleDateRangeChange = (index, value) => {
    const newRange = [...filters.date_range];
    newRange[index] = value;
    onFilterChange({ ...filters, date_range: newRange });
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
          <input
            type="number"
            className="filter-input"
            min="1"
            max="52"
            value={filters.week}
            onChange={(e) => handleChange('week', e.target.value)}
            placeholder="1-52"
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Team</label>
          <input
            type="number"
            className="filter-input"
            value={filters.team}
            onChange={(e) => handleChange('team', e.target.value)}
            placeholder="#"
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Estilo</label>
          <input
            type="text"
            className="filter-input"
            value={filters.style}
            onChange={(e) => handleChange('style', e.target.value)}
            placeholder="Estilo"
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Color</label>
          <input
            type="text"
            className="filter-input"
            value={filters.color}
            onChange={(e) => handleChange('color', e.target.value)}
            placeholder="Color"
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Cliente</label>
          <input
            type="text"
            className="filter-input"
            value={filters.customer}
            onChange={(e) => handleChange('customer', e.target.value)}
            placeholder="Cliente"
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Batch</label>
          <input
            type="number"
            className="filter-input"
            value={filters.batch}
            onChange={(e) => handleChange('batch', e.target.value)}
            placeholder="#"
          />
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
