import { useState } from 'react';
import { FileSpreadsheet, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import DateRangePicker from './DateRangePicker';
import { downloadQualityReport, validateDateRange } from '../api/reports';
import './ReportGenerator.css';

export default function ReportGenerator() {
  const [dateRange, setDateRange] = useState({ startDate: '', endDate: '' });
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [lastFilename, setLastFilename] = useState('');

  const isGenerating = status === 'generating';

  const handleDateChange = (newRange) => {
    setDateRange(newRange);
    setStatus('idle');
    setError(null);
    setSuccess(null);
  };

  const handleGenerate = async () => {
    const validation = validateDateRange(dateRange.startDate, dateRange.endDate);
    if (!validation.valid) {
      setStatus('error');
      setError(validation.message);
      return;
    }

    setStatus('generating');
    setError(null);
    setSuccess(null);

    try {
      const result = await downloadQualityReport(dateRange.startDate, dateRange.endDate);
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
          <p className="report-subtitle">Select the period to export historical data</p>
        </div>
      </div>

      <div className="report-controls">
        <DateRangePicker
          startDate={dateRange.startDate}
          endDate={dateRange.endDate}
          onChange={handleDateChange}
        />

        <button
          className="generate-btn"
          onClick={handleGenerate}
          disabled={isGenerating || !dateRange.startDate || !dateRange.endDate}
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
            ×
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
            ×
          </button>
        </div>
      )}
    </div>
  );
}
