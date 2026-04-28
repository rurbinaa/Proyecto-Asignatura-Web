import { useRef, useState, useCallback } from 'react';
import './mockupContainer.css';

export default function MockupContainer({ garmentUrl, confirmedMarkers, isEditMode, onDefectPlacePending, onRemoveConfirmedMarker, pendingCoords }) {
  const wrapperRef = useRef(null);
  const canvasRef = useRef(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [showOutsideWarning, setShowOutsideWarning] = useState(false);
  const canvasDrawnRef = useRef(false);
  const lastUrlRef = useRef(null);

  const handleImageLoad = useCallback((e) => {
    const img = e.target;
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (canvasDrawnRef.current && lastUrlRef.current === garmentUrl) return;

    const ctx = canvas.getContext('2d');
    canvas.width = img.naturalWidth || 512;
    canvas.height = img.naturalHeight || 512;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);
    setImageLoaded(true);
    canvasDrawnRef.current = true;
    lastUrlRef.current = garmentUrl;
  }, [garmentUrl]);

  const isPixelOpaque = useCallback((x, y) => {
    const canvas = canvasRef.current;
    if (!canvas || !imageLoaded) return false;

    const xNorm = Math.round(x);
    const yNorm = Math.round(y);

    if (xNorm < 0 || xNorm >= canvas.width || yNorm < 0 || yNorm >= canvas.height) return false;

    const ctx = canvas.getContext('2d');
    const pixel = ctx.getImageData(xNorm, yNorm, 1, 1).data;
    return pixel[3] > 10;
  }, [imageLoaded]);

  const handleImageClick = useCallback((e) => {
    if (isEditMode) return;
    if (!wrapperRef.current || !imageLoaded) return;

    const rect = wrapperRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const percentageX = (x / rect.width) * 100;
    const percentageY = (y / rect.height) * 100;

    const canvas = canvasRef.current;
    const svgX = Math.round((percentageX / 100) * canvas.width);
    const svgY = Math.round((percentageY / 100) * canvas.height);

    if (!isPixelOpaque(svgX, svgY)) {
      setShowOutsideWarning(true);
      setTimeout(() => setShowOutsideWarning(false), 1000);
      return;
    }

    if (onDefectPlacePending) {
      onDefectPlacePending({ x: percentageX, y: percentageY });
    }
  }, [isEditMode, imageLoaded, isPixelOpaque, onDefectPlacePending]);

  const handleRemoveMarker = (e, idToRemove) => {
    e.stopPropagation();
    if (!isEditMode) return;
    if (onRemoveConfirmedMarker) {
      onRemoveConfirmedMarker(idToRemove);
    }
  };

  return (
    <div
      className={`mockup-wrapper ${isEditMode ? 'edit-mode' : ''}`}
      ref={wrapperRef}
    >
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      {garmentUrl ? (
        <img
          src={garmentUrl}
          alt="Garment Mockup"
          onClick={handleImageClick}
          onLoad={handleImageLoad}
          className="svg_injector garment-image"
          draggable="false"
        />
      ) : (
        <p>Loading image...</p>
      )}

      {showOutsideWarning && (
        <div className="outside-garment-warning">
          Click inside the garment
        </div>
      )}

      {confirmedMarkers.map((mk) => (
        <div
          key={mk.id}
          className={`defect-marker-wrapper ${isEditMode ? 'editable' : ''}`}
          onClick={(e) => handleRemoveMarker(e, mk.id)}
          title={isEditMode ? `Delete: ${mk.type_name}` : `Defect: ${mk.type_name} (${mk.defectSize || mk.defectCount || mk.notes})`}
          style={{
            left: `${mk.coordinates_x}%`,
            top: `${mk.coordinates_y}%`
          }}
        >
          {isEditMode ? (
            <div className="defect-marker-edit-button">
              <span className="defect-marker-edit-icon">✕</span>
            </div>
          ) : (
            <div className="defect-marker-radar-base">
              <div className="defect-marker-radar-pulse" />
              <div className="defect-marker-radar-center" />
            </div>
          )}
        </div>
      ))}

      {pendingCoords && (
        <div 
          className="pending-marker"
          style={{
            left: `${pendingCoords.x}%`,
            top: `${pendingCoords.y}%`
          }}
        />
      )}
      
    </div>
  );
}