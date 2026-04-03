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
  Clock
} from 'lucide-react';
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
  const [uploadState, setUploadState] = useState('idle');
  const [importStats, setImportStats] = useState({ total: 0, inserted: 0, skipped: 0 });
  const [showComingSoon, setShowComingSoon] = useState(false);

  const cleanText = (text) => String(text || "").replace(/[^a-zA-Z0-9]/g, "").toLowerCase();

  const formatExcelDate = (serial) => {
    if (serial == null || serial === '') return serial;

    // Already a valid YYYY-MM-DD string
    if (typeof serial === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(serial)) {
      return serial;
    }

    // Excel serial number (e.g. 45665)
    if (typeof serial === 'number') {
      const date = new Date(Math.round((serial - 25569) * 86400 * 1000));
      if (!isNaN(date.getTime())) {
        return date.toISOString().split('T')[0];
      }
      return serial;
    }

    // String date in various formats (MM/DD/YYYY, DD-MM-YYYY, etc.)
    if (typeof serial === 'string') {
      const date = new Date(serial);
      if (!isNaN(date.getTime())) {
        return date.toISOString().split('T')[0];
      }
    }

    return serial;
  };

  const findHeadersAndData = (rows, sheetName) => {
    const required = REQUIRED_COLUMNS[sheetName];
    if (!required) return null;
    
    for (let i = 0; i < Math.min(rows.length, 40); i++) {
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
    maxSize: 10 * 1024 * 1024, // 10 MB limit
    onDropRejected: (rejectedFiles) => {
      const tooLarge = rejectedFiles.some(f => f.errors.some(e => e.code === 'file-too-large'));
      if (tooLarge) {
        setErrorMsg('File is too large. Maximum size is 10 MB.');
      }
    },
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
  };

  const handleProcess = () => {
    // TODO: Connect to backend import endpoint when auth & API are ready
    setShowComingSoon(true);
  };

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

      {uploadState === 'uploading' ? (
        <div className="status-panel">
          <Loader2 className="spinner-icon" />
          <h3 className="status-title">Processing {importStats.total} records...</h3>
          <p className="status-subtitle">
            Extracting data from: {reportType === 'ALL' ? 'All sheets' : SHEET_GROUPS_MAP[reportType].join(' and ')}
          </p>
        </div>
      ) : uploadState === 'success' ? (
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
      ) : (
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

          {errorMsg && (
            <div className="error-alert">
              <AlertTriangle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

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
                <button className="ingesta-btn-primary full-width-btn" onClick={handleProcess}>
                  Confirm & Import All ({importStats.total} Records)
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>

      {/* Coming Soon Modal — backend integration pending */}
      {showComingSoon && (
        <div className="modal-overlay" onClick={() => setShowComingSoon(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <Clock className="modal-icon" />
            <h3 className="modal-title">Coming Soon</h3>
            <p className="modal-description">
              The import functionality is under development. Your file has been validated and 
              <strong> {importStats.total} records</strong> are ready to be processed.
            </p>
            <p className="modal-hint">Backend integration will be available in the next release.</p>
            <button 
              className="modal-close-btn" 
              onClick={() => setShowComingSoon(false)}
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </div>
  );
}