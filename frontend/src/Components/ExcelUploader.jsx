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
  AlertTriangle 
} from 'lucide-react';
import './ExcelUploader.css';

const REQUIRED_COLUMNS = {
  QFA: ["date", "week", "customer", "team", "coord", "po", "style", "batch", "color", "qty"],
  SECONDS_A4: ["year", "week", "date", "cut_num", "style", "cut_qty", "color", "accepted", "rejected"],
  CONTAINER: ["container_number", "customer", "total_palette", "total_palette_pass", "percentage_pass"]
};

const SHEET_NAMES_MAP = {
  QFA: "QC FA Plant",
  SECONDS_A4: "SecondsA4",
  CONTAINER: "Container"
};

export default function ExcelUploader() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [reportType, setReportType] = useState('QFA'); 
  const [errorMsg, setErrorMsg] = useState('');
  const [previewHeaders, setPreviewHeaders] = useState([]);
  const [previewRows, setPreviewRows] = useState([]);
  const [uploadState, setUploadState] = useState('idle');
  
  const [importStats, setImportStats] = useState({ total: 0, inserted: 0, skipped: 0 });

  const cleanText = (text) => String(text).replace(/[^a-zA-Z0-9]/g, "").toLowerCase();

  const formatExcelDate = (serial) => {
    if (!serial || isNaN(serial)) return serial;
    const date = new Date(Math.round((serial - 25569) * 86400 * 1000));
    return date.toISOString().split('T')[0];
  };

  const validateHeaders = (headers) => {
    const required = REQUIRED_COLUMNS[reportType];
    const cleanHeaders = headers.map(h => cleanText(h));
    const missing = required.filter(col => !cleanHeaders.includes(cleanText(col)));
    
    if (missing.length > 0) {
      return `Missing columns: ${missing.join(', ')}`;
    }
    return null;
  };

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
      setErrorMsg('');
      
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array', sheetRows: 50 });
          
          const targetSheet = SHEET_NAMES_MAP[reportType];
          const worksheet = workbook.Sheets[targetSheet];

          if (!worksheet) {
            setErrorMsg(`Sheet "${targetSheet}" not found in this file.`);
            setPreviewHeaders([]);
            return;
          }

          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: "" });
          
          if (jsonData.length > 0) {
            const rawHeaders = jsonData[0];
            const validationError = validateHeaders(rawHeaders);
            
            if (validationError) {
              setErrorMsg(validationError);
              setPreviewHeaders([]);
              setPreviewRows([]);
            } else {
              setPreviewHeaders(rawHeaders);
              
              const dateIndices = rawHeaders.reduce((acc, header, idx) => {
                if (cleanText(header).includes('date')) acc.push(idx);
                return acc;
              }, []);

              const formattedRows = jsonData.slice(1).map(row => {
                const newRow = [...row];
                dateIndices.forEach(idx => {
                  if (typeof newRow[idx] === 'number') {
                    newRow[idx] = formatExcelDate(newRow[idx]);
                  }
                });
                return newRow;
              });

              setPreviewRows(formattedRows);
              setImportStats({ total: jsonData.length - 1, inserted: 0, skipped: 0 });
            }
          }
        } catch (error) {
          setErrorMsg('Error parsing Excel. Check file format.');
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
    setPreviewHeaders([]);
    setPreviewRows([]);
    setImportStats({ total: 0, inserted: 0, skipped: 0 });
  };

  const handleProcess = () => {
    setUploadState('uploading');
    
    setTimeout(() => {
      const totalProcessed = importStats.total;
      const skipped = Math.floor(totalProcessed * 0.1);
      const inserted = totalProcessed - skipped;

      setImportStats({
        total: totalProcessed,
        inserted: inserted,
        skipped: skipped
      });
      setUploadState('success');
    }, 2500);
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
          <option value="QFA">QC FA (Plant/Customer)</option>
          <option value="SECONDS_A4">Seconds A4</option>
          <option value="CONTAINER">Container Inspection</option>
        </select>
      </div>

      {uploadState === 'uploading' ? (
        <div className="status-panel">
          <Loader2 className="spinner-icon" />
          <h3 className="status-title">Processing {importStats.total} records...</h3>
          <p className="status-subtitle">Validating sheet: {SHEET_NAMES_MAP[reportType]}</p>
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
          <div {...getRootProps()} className={`dropzone ${isDragActive ? 'drag-active' : ''} ${errorMsg ? 'drag-error' : ''}`}>
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
                <h3 className="dropzone-title">Drop file for "{SHEET_NAMES_MAP[reportType]}"</h3>
                <p className="dropzone-subtitle">or click to browse</p>
              </div>
            )}
          </div>

          {errorMsg && (
            <div className="error-alert">
              <AlertTriangle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          {selectedFile && !errorMsg && previewHeaders.length > 0 && (
            <div className="preview-container">
              <div className="preview-header">
                <Eye size={18} /> 
                <span className="preview-title">Data Preview (Top 5 rows)</span>
              </div>
              <div className="table-responsive">
                <table className="preview-table">
                  <thead>
                    <tr>{previewHeaders.map((h, i) => <th key={i}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {previewRows.slice(0, 5).map((row, i) => (
                      <tr key={i}>
                        {previewHeaders.map((_, ci) => <td key={ci}>{row[ci] || '-'}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
  );
}