import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileSpreadsheet, XCircle, FileWarning, Loader2, CheckCircle } from 'lucide-react';
import './ExcelUploader.css';

export default function ExcelUploader() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Controla en qué fase de la subida estamos
  const [uploadState, setUploadState] = useState('idle'); // 'idle', 'uploading', 'success', 'error'
  const [report, setReport] = useState(null);

  const onDrop = useCallback((acceptedFiles, fileRejections) => {
    if (fileRejections.length > 0) {
      setSelectedFile(null);
      setErrorMsg('Formato inválido. Por favor sube archivos .xlsx, .xls o .csv.');
      return;
    }

    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      setErrorMsg('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv']
    }
  });

  const resetUploader = (e) => {
    if (e) e.stopPropagation();
    setSelectedFile(null);
    setErrorMsg('');
    setUploadState('idle');
    setReport(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    // Cambiamos a Fase 2: Pantalla de carga
    setUploadState('uploading');

    // 🚀 MOCK: Simulamos el tiempo de procesamiento del backend (3 segundos)
    setTimeout(() => {
      // Simulamos la respuesta exitosa del backend con el reporte (Fase 3)
      setReport({
        total: 1500,
        inserted: 1480,
        skipped: 20 // Registros omitidos por ser duplicados
      });
      setUploadState('success');
    }, 3000);
  };

  // ==========================================
  // FASE 2: VISTA DE CARGA (SPINNER)
  // ==========================================
  if (uploadState === 'uploading') {
    return (
      <div className="uploader-container">
        <div className="status-panel">
          <Loader2 className="spinner-icon" />
          <h3 className="status-title">Procesando archivo...</h3>
          <p className="status-subtitle">El servidor está validando y guardando los registros. Esto puede tomar un momento.</p>
        </div>
      </div>
    );
  }

  // ==========================================
  // FASE 3: VISTA DE REPORTE
  // ==========================================
  if (uploadState === 'success' && report) {
    return (
      <div className="uploader-container">
        <div className="status-panel success-panel">
          <CheckCircle className="success-main-icon" />
          <h3 className="status-title">¡Importación Exitosa!</h3>
          
          <div className="report-grid">
            <div className="report-card neutral">
              <span className="report-number">{report.total}</span>
              <span className="report-label">Filas Leídas</span>
            </div>
            <div className="report-card positive">
              <span className="report-number">{report.inserted}</span>
              <span className="report-label">Integrados</span>
            </div>
            <div className="report-card warning">
              <span className="report-number">{report.skipped}</span>
              <span className="report-label">Omitidos (Duplicados)</span>
            </div>
          </div>

          <button className="ingesta-btn ingesta-btn-outline action-btn-margin" onClick={resetUploader}>
            Subir Otro Archivo
          </button>
        </div>
      </div>
    );
  }

  // ==========================================
  // FASE 1: VISTA PRINCIPAL (DRAG & DROP)
  // ==========================================
  return (
    <div className="uploader-container">
      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'drag-active' : ''} ${errorMsg ? 'drag-error' : ''}`}
      >
        <input {...getInputProps()} />
        
        {selectedFile ? (
          <div className="file-preview">
            <FileSpreadsheet className="file-icon success-icon" />
            <div className="file-info">
              <span className="file-name">{selectedFile.name}</span>
              <span className="file-size">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
            </div>
            <button className="clear-btn" onClick={resetUploader} title="Quitar archivo">
              <XCircle size={20} />
            </button>
          </div>
        ) : (
          <div className="dropzone-content">
            <UploadCloud className={`upload-icon ${isDragActive ? 'bounce' : ''}`} />
            <h3 className="dropzone-title">
              {isDragActive ? 'Suelta el archivo Excel aquí...' : 'Arrastra y suelta tu Excel aquí'}
            </h3>
            <p className="dropzone-subtitle">o haz clic para explorar tus archivos</p>
            <p className="dropzone-hint">Formatos soportados: .xlsx, .xls, .csv</p>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="error-alert">
          <FileWarning size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {selectedFile && !errorMsg && (
        <div className="upload-actions">
          <button className="ingesta-btn ingesta-btn-primary full-width-btn" onClick={handleUpload}>
            Procesar e Importar Lotes
          </button>
        </div>
      )}
    </div>
  );
}