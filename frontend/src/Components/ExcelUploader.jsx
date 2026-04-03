import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import * as XLSX from 'xlsx';
import { 
  UploadCloud, 
  FileSpreadsheet, 
  XCircle, 
  Loader2, 
  CheckCircle, 
  Eye, 
  AlertTriangle,
  X,
  RotateCcw
} from 'lucide-react';
import { uploadForPreview, confirmSession, rejectSession } from '../api/excel.js';
import './ExcelUploader.css';

const REQUIRED_COLUMNS = {
  "QC FA Plant": ["date", "week", "customer", "team", "coord", "po", "style", "batch", "color", "qty"],
  "QC FA Customer": ["date", "week", "customer", "line", "artcode", "po", "style", "batch", "color", "quantity"],
  "SecondsA4": ["year", "week", "date", "cut", "style", "color", "accepted", "rejected"],
  "Seconds General": ["date", "week", "picado", "manchas", "grasa", "tono", "fuera", "definitive"],
  "Container": ["container", "customer", "palette", "pass"]
};

const SHEET_GROUPS_MAP = {
  QFA: ["QC FA Plant", "QC FA Customer"],
  SECONDS: ["SecondsA4", "Seconds General"],
  CONTAINER: ["Container"],
  ALL: ["QC FA Plant", "QC FA Customer", "SecondsA4", "Seconds General", "Container"] 
};

export default function ExcelUploader() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [reportType, setReportType] = useState('QFA'); 
  const [errorMsg, setErrorMsg] = useState('');
  const [sheetPreviews, setSheetPreviews] = useState([]); 
  
  // New state machine: idle, analyzing, preview_ready, confirming, success, error
  const [uploadState, setUploadState] = useState('idle');
  const [sessionId, setSessionId] = useState(null);
  const [previewStats, setPreviewStats] = useState(null);
  const [apiError, setApiError] = useState('');
  const [importStats, setImportStats] = useState({ total: 0, inserted: 0, skipped: 0 });

  const cleanText = (text) => String(text || "").replace(/[^a-zA-Z0-9]/g, "").toLowerCase();

  const formatExcelDate = (serial) => {
    if (!serial || isNaN(serial)) return serial;
    const date = new Date(Math.round((serial - 25569) * 86400 * 1000));
    return date.toISOString().split('T')[0];
  };

  const findHeadersAndData = (rows, sheetName) => {
    const required = REQUIRED_COLUMNS[sheetName];
    if (!required) return null;
    
    for (let i = 0; i < Math.min(rows.length, 20); i++) {
      if (!rows[i] || rows[i].length === 0) continue;
      
      const potentialRow = rows[i].map(cell => cleanText(cell));
      
      const matchCount = required.filter(req => 
        potentialRow.some(cell => cell.includes(cleanText(req)))
      ).length;
      
      if (matchCount >= required.length - 1) {
        return { headers: rows[i], data: rows.slice(i + 1) };
      }
    }
    return null;
  };

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
      setErrorMsg('');
      setSheetPreviews([]);
      
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array', sheetRows: 200 });
          
          const targetSheets = SHEET_GROUPS_MAP[reportType];
          let newPreviews = [];
          let missingOrInvalidSheets = [];
          let totalProcessedRecords = 0;

          targetSheets.forEach(sheetName => {
            const worksheet = workbook.Sheets[sheetName];

            if (!worksheet) {
              missingOrInvalidSheets.push(`${sheetName} (Not found)`);
              return;
            }

            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: "" });
            
            if (jsonData.length > 0) {
              const result = findHeadersAndData(jsonData, sheetName);
              
              if (!result) {
                missingOrInvalidSheets.push(`${sheetName} (Invalid format/columns)`);
              } else {
                const { headers: rawHeaders, data: sheetData } = result;
                
                const dateIndices = rawHeaders.reduce((acc, header, idx) => {
                  if (cleanText(header).includes('date')) acc.push(idx);
                  return acc;
                }, []);

                const formattedRows = sheetData.map(row => {
                  const newRow = [...row];
                  dateIndices.forEach(idx => {
                    if (typeof newRow[idx] === 'number') {
                      newRow[idx] = formatExcelDate(newRow[idx]);
                    }
                  });
                  return newRow;
                });

                newPreviews.push({
                  sheetName,
                  headers: rawHeaders,
                  rows: formattedRows.slice(0, 5),
                  count: sheetData.length
                });

                totalProcessedRecords += sheetData.length;
              }
            }
          });

          if (newPreviews.length === 0) {
            setErrorMsg(`Could not process information. Issues with: ${missingOrInvalidSheets.join(', ')}`);
          } else {
            if (missingOrInvalidSheets.length > 0) {
              setErrorMsg(`Warning: Missing data or error in ${missingOrInvalidSheets.join(', ')}`);
            }
            setSheetPreviews(newPreviews);
            setImportStats({ total: totalProcessedRecords, inserted: 0, skipped: 0 });
          }

        } catch (error) {
          console.error(error);
          setErrorMsg('Error reading Excel. Please check the file.');
        }
      };
      reader.readAsArrayBuffer(file);
    }
  }, [reportType]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    accept: { 
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'], 
      'text/csv': ['.csv'] 
    }
  });

  const resetUploader = () => {
    setSelectedFile(null);
    setErrorMsg('');
    setUploadState('idle');
    setSheetPreviews([]);
    setImportStats({ total: 0, inserted: 0, skipped: 0 });
    setSessionId(null);
    setPreviewStats(null);
    setApiError('');
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setUploadState('analyzing');
    setApiError('');
    try {
      const result = await uploadForPreview(selectedFile);
      setSessionId(result.session_id);
      setPreviewStats(result.preview);
      setUploadState('preview_ready');
      if (result.warnings && result.warnings.length > 0) {
        setApiError(result.warnings.join('. '));
      }
    } catch (err) {
      setApiError(err.message);
      setUploadState('error');
    }
  };

  const handleConfirm = async () => {
    if (!sessionId) return;
    setUploadState('confirming');
    setApiError('');
    try {
      await confirmSession(sessionId);
      // Calculate stats from backend preview
      const stats = Object.values(previewStats || {});
      const total = stats.reduce((sum, s) => sum + (s.total || 0), 0);
      const newCount = stats.reduce((sum, s) => sum + (s.new || 0), 0);
      const modifiedCount = stats.reduce((sum, s) => sum + (s.modified || 0), 0);
      const unchangedCount = stats.reduce((sum, s) => sum + (s.unchanged || 0), 0);
      setImportStats({ total, inserted: newCount + modifiedCount, skipped: unchangedCount });
      setUploadState('success');
    } catch (err) {
      setApiError(err.message);
      setUploadState('error');
    }
  };

  const handleReject = async () => {
    if (sessionId) {
      try {
        await rejectSession(sessionId);
      } catch (err) {
        console.error('Failed to reject session:', err);
      }
    }
    resetUploader();
  };

  // Render backend preview stats
  const renderBackendStats = () => {
    if (!previewStats) return null;
    
    const stats = Object.entries(previewStats).map(([sheetName, data]) => ({
      sheetName,
      new: data.new || 0,
      modified: data.modified || 0,
      unchanged: data.unchanged || 0,
      warnings: data.warnings || 0,
      total: data.total || 0
    }));

    return (
      <div className="backend-stats-container">
        <h4 className="backend-stats-title">
          <CheckCircle size={18} />
          Backend Analysis Results
        </h4>
        <div className="backend-stats-grid">
          {stats.map((stat, idx) => (
            <div key={idx} className="backend-stat-card">
              <div className="backend-stat-sheet">{stat.sheetName}</div>
              <div className="backend-stat-items">
                <span className="stat-item positive">
                  <strong>{stat.new}</strong> New
                </span>
                <span className="stat-item warning">
                  <strong>{stat.modified}</strong> Modified
                </span>
                <span className="stat-item neutral">
                  <strong>{stat.unchanged}</strong> Unchanged
                </span>
                {stat.warnings > 0 && (
                  <span className="stat-item error">
                    <strong>{stat.warnings}</strong> Warnings
                  </span>
                )}
              </div>
              <div className="backend-stat-total">
                Total: <strong>{stat.total}</strong>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render error state
  const renderErrorState = () => (
    <div className="status-panel error-panel">
      <AlertTriangle className="error-main-icon" />
      <h3 className="status-title">Error</h3>
      <p className="status-subtitle">{apiError || 'An unexpected error occurred'}</p>
      <div className="error-actions">
        <button className="ingesta-btn-outline" onClick={resetUploader}>
          <RotateCcw size={18} />
          Try Again
        </button>
      </div>
    </div>
  );

  // Render analyzing state
  const renderAnalyzingState = () => (
    <div className="status-panel">
      <Loader2 className="spinner-icon" />
      <h3 className="status-title">Analyzing file...</h3>
      <p className="status-subtitle">
        Uploading {selectedFile?.name} to server for analysis
      </p>
    </div>
  );

  // Render confirming state
  const renderConfirmingState = () => (
    <div className="status-panel">
      <Loader2 className="spinner-icon" />
      <h3 className="status-title">Applying changes...</h3>
      <p className="status-subtitle">
        Confirming import and saving data to database
      </p>
    </div>
  );

  // Render success state
  const renderSuccessState = () => (
    <div className="status-panel success-panel">
      <CheckCircle className="success-main-icon" />
      <h3 className="status-title">Import Summary</h3>
      
      <div className="report-grid">
        <div className="report-card neutral">
          <span className="report-number">{importStats.total}</span>
          <span className="report-label">Read</span>
        </div>
        <div className="report-card positive">
          <span className="report-number">{importStats.inserted}</span>
          <span className="report-label">Integrated</span>
        </div>
        <div className="report-card warning">
          <span className="report-number">{importStats.skipped}</span>
          <span className="report-label">Skipped (Dup)</span>
        </div>
      </div>

      <button className="ingesta-btn-outline action-btn-margin" onClick={resetUploader}>
        Upload Another File
      </button>
    </div>
  );

  // Render preview ready state with actions
  const renderPreviewReadyState = () => (
    <>
      {/* Backend stats */}
      {renderBackendStats()}

      {/* Warning from backend */}
      {apiError && (
        <div className="error-alert">
          <AlertTriangle size={18} />
          <span>{apiError}</span>
        </div>
      )}

      {/* Local table preview - keep for visual reference */}
      {sheetPreviews.length > 0 && (
        <div className="preview-container">
          {sheetPreviews.map((preview, index) => (
            <div key={index} className="sheet-preview-section" style={{ marginBottom: '2rem' }}>
              <div className="preview-header">
                <Eye size={18} /> 
                <span className="preview-title">
                  Data Preview: <strong>{preview.sheetName}</strong> ({preview.count} rows detected)
                </span>
              </div>
              <div className="table-responsive">
                <table className="preview-table">
                  <thead>
                    <tr>{preview.headers.map((h, i) => <th key={i}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {preview.rows.map((row, i) => (
                      <tr key={i}>
                        {preview.headers.map((_, ci) => <td key={ci}>{row[ci] || '-'}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Confirm/Reject actions */}
      <div className="upload-actions">
        <button className="ingesta-btn-primary full-width-btn" onClick={handleConfirm}>
          Confirm & Import All ({Object.values(previewStats || {}).reduce((sum, s) => sum + (s.total || 0), 0)} Records)
        </button>
        <button className="ingesta-btn-outline full-width-btn" onClick={handleReject}>
          <X size={18} />
          Cancel Import
        </button>
      </div>
    </>
  );

  // Render idle state - file selected but not analyzed yet
  const renderIdleWithFile = () => (
    <>
      {/* Error message from local parsing */}
      {errorMsg && (
        <div className="error-alert">
          <AlertTriangle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Show table preview with Analyze button */}
      {selectedFile && sheetPreviews.length > 0 && (
        <div className="preview-container">
          {sheetPreviews.map((preview, index) => (
            <div key={index} className="sheet-preview-section" style={{ marginBottom: '2rem' }}>
              <div className="preview-header">
                <Eye size={18} /> 
                <span className="preview-title">
                  Data Preview: <strong>{preview.sheetName}</strong> ({preview.count} rows detected)
                </span>
              </div>
              <div className="table-responsive">
                <table className="preview-table">
                  <thead>
                    <tr>{preview.headers.map((h, i) => <th key={i}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {preview.rows.map((row, i) => (
                      <tr key={i}>
                        {preview.headers.map((_, ci) => <td key={ci}>{row[ci] || '-'}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}

          <div className="upload-actions">
            <button className="ingesta-btn-primary full-width-btn" onClick={handleAnalyze}>
              <UploadCloud size={18} />
              Analyze File
            </button>
          </div>
        </div>
      )}
    </>
  );

  return (
    <div className="uploader-container">
      <div className="report-selector-group">
        <label className="input-label">Data Import Type:</label>
        <select 
          className="input-field select-field" 
          value={reportType} 
          onChange={(e) => { setReportType(e.target.value); resetUploader(); }}
        >
          <option value="ALL">All Sheets (Import All)</option> 
          <option value="QFA">QC FA (Plant & Customer)</option>
          <option value="SECONDS">Seconds (A4 & General)</option>
          <option value="CONTAINER">Container Inspection</option>
        </select>
      </div>

      {/* State-based rendering */}
      {uploadState === 'analyzing' && renderAnalyzingState()}
      
      {uploadState === 'confirming' && renderConfirmingState()}
      
      {uploadState === 'success' && renderSuccessState()}
      
      {uploadState === 'error' && renderErrorState()}
      
      {uploadState === 'preview_ready' && renderPreviewReadyState()}
      
      {/* idle state - show dropzone or file with analyze button */}
      {uploadState === 'idle' && (
        <>
          <div {...getRootProps()} className={`dropzone ${isDragActive ? 'drag-active' : ''} ${errorMsg && sheetPreviews.length === 0 ? 'drag-error' : ''}`}>
            <input {...getInputProps()} />
            {selectedFile ? (
              <div className="file-preview">
                <FileSpreadsheet className="file-icon success-icon" />
                <div className="file-info">
                  <span className="file-name">{selectedFile.name}</span>
                </div>
                <button className="clear-btn" onClick={(e) => { e.stopPropagation(); resetUploader(); }}>
                  <XCircle size={20} />
                </button>
              </div>
            ) : (
              <div className="dropzone-content">
                <UploadCloud className="upload-icon" />
                <h3 className="dropzone-title">
                  Upload your file for: {reportType === 'ALL' ? 'All sheets' : SHEET_GROUPS_MAP[reportType].join(' + ')}
                </h3>
                <p className="dropzone-subtitle">Drag and drop or click to browse</p>
              </div>
            )}
          </div>

          {renderIdleWithFile()}
        </>
      )}
    </div>
  );
}