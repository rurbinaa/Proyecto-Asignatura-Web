import { useState, useRef, useEffect } from 'react';
import { Calendar, ChevronLeft, ChevronRight, X } from 'lucide-react';
import './DateRangePicker.css';

const MONTHS_ES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
const DAYS_ES = ['Lun', 'Mar', 'Mier', 'Jue', 'Vie', 'Sab', 'Dom'];

function parseDateString(value) {
  if (!value) return null;
  const [year, month, day] = value.split('-').map(Number);
  if (!year || !month || !day) return null;
  return new Date(year, month - 1, day);
}

function formatDateString(date) {
  return [
    date.getFullYear(),
    (date.getMonth() + 1).toString().padStart(2, '0'),
    date.getDate().toString().padStart(2, '0'),
  ].join('-');
}

function getDaysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year, month) {
  const day = new Date(year, month, 1).getDay();
  return day === 0 ? 6 : day - 1;
}

export default function DateRangePicker({ startDate, endDate, onChange, minDate, maxDate, size = 'medium' }) {
  const [isOpen, setIsOpen] = useState(false);
  const [viewYear, setViewYear] = useState(() => {
    const now = new Date();
    const parsedEndDate = parseDateString(endDate);
    return parsedEndDate ? parsedEndDate.getFullYear() : now.getFullYear();
  });
  const [viewMonth, setViewMonth] = useState(() => {
    const now = new Date();
    const parsedEndDate = parseDateString(endDate);
    return parsedEndDate ? parsedEndDate.getMonth() : now.getMonth();
  });
  const [selecting, setSelecting] = useState('start');
  const containerRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const formatDisplay = (date) => {
    if (!date) return '';
    const parsedDate = parseDateString(date);
    if (!parsedDate) return '';

    return `${parsedDate.getDate().toString().padStart(2, '0')}/${(parsedDate.getMonth() + 1).toString().padStart(2, '0')}/${parsedDate.getFullYear()}`;
  };

  const handleDayClick = (day) => {
    const selectedDate = new Date(viewYear, viewMonth, day);
    const dateStr = formatDateString(selectedDate);

    if (selecting === 'start') {
      onChange({
        startDate: dateStr,
        endDate: endDate && dateStr > endDate ? '' : endDate,
      });
      setSelecting('end');
      return;
    }

    if (startDate && dateStr >= startDate) {
      onChange({ startDate, endDate: dateStr });
      setIsOpen(false);
      setSelecting('start');
      return;
    }

    onChange({ startDate: dateStr, endDate: startDate });
    setSelecting('end');
  };

  const prevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear(viewYear - 1);
    } else {
      setViewMonth(viewMonth - 1);
    }
  };

  const nextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear(viewYear + 1);
    } else {
      setViewMonth(viewMonth + 1);
    }
  };

  const clearDates = () => {
    onChange({ startDate: '', endDate: '' });
  };

  const isSelected = (day) => {
    const dateStr = `${viewYear}-${(viewMonth + 1).toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
    return dateStr === startDate || dateStr === endDate;
  };

  const isInRange = (day) => {
    const dateStr = `${viewYear}-${(viewMonth + 1).toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
    return startDate && endDate && dateStr > startDate && dateStr < endDate;
  };

  const isDisabled = (day) => {
    const date = new Date(viewYear, viewMonth, day);
    const parsedMinDate = parseDateString(minDate);
    const parsedMaxDate = parseDateString(maxDate);

    if (parsedMinDate && date < parsedMinDate) return true;
    if (parsedMaxDate && date > parsedMaxDate) return true;
    return false;
  };

  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(viewYear, viewMonth);
    const firstDay = getFirstDayOfMonth(viewYear, viewMonth);
    const days = [];

    for (let i = 0; i < firstDay; i += 1) {
      days.push(<div key={`empty-${i}`} className="calendar-day empty" />);
    }

    for (let day = 1; day <= daysInMonth; day += 1) {
      const disabled = isDisabled(day);
      const selected = isSelected(day);
      const inRange = isInRange(day);

      days.push(
        <button
          key={day}
          className={`calendar-day ${selected ? 'selected' : ''} ${inRange ? 'in-range' : ''} ${disabled ? 'disabled' : ''}`}
          onClick={() => !disabled && handleDayClick(day)}
          disabled={disabled}
          type="button"
        >
          {day}
        </button>
      );
    }

    return days;
  };

  return (
    <div className={`date-range-picker ${size}`} ref={containerRef}>
      <div className="date-inputs">
        <div className="date-input-group">
          <label className="date-label">From</label>
          <div className="date-display" onClick={() => setIsOpen(!isOpen)}>
            <Calendar size={16} className="date-icon" />
            <span className={startDate ? '' : 'placeholder'}>
              {startDate ? formatDisplay(startDate) : 'Select date'}
            </span>
          </div>
        </div>

        <div className="date-separator">to</div>

        <div className="date-input-group">
          <label className="date-label">To</label>
          <div className="date-display" onClick={() => setIsOpen(!isOpen)}>
            <Calendar size={16} className="date-icon" />
            <span className={endDate ? '' : 'placeholder'}>
              {endDate ? formatDisplay(endDate) : 'Select date'}
            </span>
          </div>
        </div>

        {(startDate || endDate) && (
          <button className="clear-btn" onClick={clearDates} type="button" title="Clear dates">
            <X size={16} />
          </button>
        )}
      </div>

      {isOpen && (
        <div className="calendar-popup">
          <div className="calendar-header">
            <button className="nav-btn" onClick={prevMonth} type="button">
              <ChevronLeft size={20} />
            </button>

            <span className="month-year">
              {MONTHS_ES[viewMonth]} {viewYear}
            </span>

            <button className="nav-btn" onClick={nextMonth} type="button">
              <ChevronRight size={20} />
            </button>
          </div>

          <div className="calendar-weekdays">
            {DAYS_ES.map((day) => (
              <div key={day} className="weekday">{day}</div>
            ))}
          </div>

          <div className="calendar-grid">
            {renderCalendar()}
          </div>

          <div className="calendar-footer">
            <span className="selection-indicator">
              {selecting === 'start' ? 'Select start date' : 'Select end date'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
