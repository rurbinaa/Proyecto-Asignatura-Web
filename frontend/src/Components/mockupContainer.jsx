import { useState, useRef, useEffect } from 'react';
import './mockupContainer.css';

export default function MockupContainer({ garmentUrl, confirmedMarkers, isEditMode, onDefectPlacePending, onRemoveConfirmedMarker, pendingCoords }) {
  const wrapperRef = useRef(null); 
  const [renderedSvg, setRenderedSvg] = useState(null);

  useEffect(() => {
    if (!garmentUrl) return;
    fetch(garmentUrl)
      .then((res) => res.text())
      .then((data) => setRenderedSvg(data))
      .catch((err) => console.error('Error loading SVG:', err));
  }, [garmentUrl]);

  const handlePathClick = (e) => {
    if (isEditMode) return;
    if (e.target.tagName.toLowerCase() !== 'path') return; 
    if (!wrapperRef.current) return;
    
    const rect = wrapperRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const percentageX = (x / rect.width) * 100;
    const percentageY = (y / rect.height) * 100;

    if (onDefectPlacePending) {
      onDefectPlacePending({ x: percentageX, y: percentageY });
    }
  };

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
      {renderedSvg ? (
        <div
          onClick={handlePathClick}
          dangerouslySetInnerHTML={{ __html: renderedSvg}}
          className="svg_injector"
        />
      ) : (
        <p>Loading SVG...</p>
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