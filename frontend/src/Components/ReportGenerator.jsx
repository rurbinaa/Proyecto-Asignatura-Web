import { useState } from 'react';
import { FileSpreadsheet, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { downloadQualityReport, validateDateRange } from '../api/reports';
import './ReportGenerator.css';

function monthToDateRange(startMonth, endMonth) {
  if (!startMonth || !endMonth) {
    return { startDate: '', endDate: '' };
  }

  const [startYear, startMonthIndex] = startMonth.split('-').map(Number);
  const [endYear, endMonthIndex] = endMonth.split('-').map(Number);

  const startDate = `${startYear}-${String(startMonthIndex).padStart(2, '0')}-01`;
  const endDateObject = new Date(endYear, endMonthIndex, 0);
  const endDate = `${endYear}-${String(endMonthIndex).padStart(2, '0')}-${String(endDateObject.getDate()).padStart(2, '0')}`;

  return { startDate, endDate };
}

export default function ReportGenerator() {
  const [monthRange, setMonthRange] = useState({ startMonth: '', endMonth: '' });
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [lastFilename, setLastFilename] = useState('');

  const isGenerating = status === 'generating';

  const handleMonthChange = (field, value) => {
    setMonthRange((current) => ({ ...current, [field]: value }));
    setError(null);
    setSuccess(null);
  };

  const handleGenerate = async () => {
    const { startDate, endDate } = monthToDateRange(monthRange.startMonth, monthRange.endMonth);
    const validation = validateDateRange(startDate, endDate);
    if (!validation.valid) {
      setError(validation.message);
      return;
    }

    setStatus('generating');
    setError(null);
    setSuccess(null);

    try {
      const result = await downloadQualityReport(startDate, endDate);
      setStatus('success');
      setSuccess('Report generated successfully');
      setLastFilename(result.filename);
    } catch (err) {
      setStatus('error');
      setError(err.message);
    }
  };

  const handleDismiss = () => {
    setStatus('idle');
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="report-generator">
      <div className="report-header">
        <FileSpreadsheet size={24} className="report-icon" />
        <div className="report-title-container">
          <h3 className="report-title">Generate Quality Report</h3>
          <p className="report-subtitle">Select whole months to export historical data</p>
        </div>
      </div>

      <div className="report-controls">
        <div className="report-month-range">
          <div className="report-month-group">
            <label className="report-month-label" htmlFor="report-start-month">From month</label>
            <input
              id="report-start-month"
              className="report-month-input"
              type="month"
              value={monthRange.startMonth}
              onChange={(e) => handleMonthChange('startMonth', e.target.value)}
            />
          </div>

          <div className="report-month-group">
            <label className="report-month-label" htmlFor="report-end-month">To month</label>
            <input
              id="report-end-month"
              className="report-month-input"
              type="month"
              value={monthRange.endMonth}
              onChange={(e) => handleMonthChange('endMonth', e.target.value)}
            />
          </div>
        </div>

        <button
          className="generate-btn"
          onClick={handleGenerate}
          disabled={isGenerating || !monthRange.startMonth || !monthRange.endMonth}
        >
          {isGenerating ? (
            <>
              <Loader2 size={18} className="spinner" />
              Generating Report...
            </>
          ) : (
            <>
              <FileSpreadsheet size={18} />
              Generate Report
            </>
          )}
        </button>
      </div>

      {isGenerating && (
        <div className="generating-overlay">
          <div className="generating-backdrop" />
          <div className="report-status generating">
            <Loader2 size={20} className="spinner" />
            <div className="status-content">
              <span className="status-title">Generating Report...</span>
              <span className="status-message">
                Processing historical data. This process may take several minutes
                depending on the volume of information.
              </span>
            </div>
          </div>
        </div>
      )}

      {status === 'error' && error && (
        <div className="report-status error">
          <AlertCircle size={20} />
          <div className="status-content">
            <span className="status-title">Error generating report</span>
            <span className="status-message">{error}</span>
          </div>
          <button className="dismiss-btn" onClick={handleDismiss} type="button">
            x
          </button>
        </div>
      )}

      {status === 'success' && success && (
        <div className="report-status success">
          <CheckCircle size={20} />
          <div className="status-content">
            <span className="status-title">Report generated</span>
            <span className="status-message">
              {success}
              {lastFilename && <span className="filename"> ({lastFilename})</span>}
            </span>
          </div>
          <button className="dismiss-btn" onClick={handleDismiss} type="button">
            x
          </button>
        </div>
      )}
    </div>
  );
}
