import { useState, useRef, useEffect } from 'react';
import './mockupContainer.css';

export default function MockupContainer({ garmentUrl, confirmedMarkers, isEditMode, onDefectPlacePending, onRemoveConfirmedMarker }) {
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
      className="mockup-wrapper" 
      ref={wrapperRef}
      style={{ 
        position: 'relative',
        cursor: isEditMode ? 'default' : 'crosshair' 
      }}
    >
      {renderedSvg ? (
        <div
          onClick={handlePathClick}
          dangerouslySetInnerHTML={{ __html: renderedSvg}}
          className="svg_injector"
          style={{
            opacity: isEditMode ? 0.6 : 1,
            transition: 'opacity 0.3s ease',
            width: '100%', 
            height: '100%',
            display: 'block' 
          }}
        />
      ) : (
        <p>Loading SVG...</p>
      )}

      {confirmedMarkers.map((mk) => (
        <div
          key={mk.id}
          className="defect-marker-wrapper"
          onClick={(e) => handleRemoveMarker(e, mk.id)}
          title={isEditMode ? `Delete: ${mk.type_name}` : `Defect: ${mk.type_name} (${mk.extra_detail})`}
          style={{
            position: 'absolute',
            left: `${mk.x}%`,
            top: `${mk.y}%`,
            transform: 'translate(-50%, -50%)',
            width: '32px',
            height: '32px',
            pointerEvents: 'auto',
            cursor: isEditMode ? 'pointer' : 'default',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)', 
            zIndex: 100,
          }}
        >
          {isEditMode ? (
            <div
              className="defect-marker-edit-button"
              style={{
                width: '28px',
                height: '28px',
                backgroundColor: '#ef4444',
                border: '2px solid white',
                borderRadius: '50%',
                boxShadow: '0 4px 8px rgba(239, 68, 68, 0.6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span style={{ color: 'white', fontSize: '12px', fontWeight: 'bold' }}>✕</span>
            </div>
          ) : (
            <div
              className="defect-marker-radar-base"
              style={{
                width: '100%',
                height: '100%',
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div
                className="defect-marker-radar-pulse"
                style={{
                  position: 'absolute',
                  width: '100%',
                  height: '100%',
                  border: '2px solid rgba(239, 68, 68, 0.6)',
                  borderRadius: '50%',
                }}
              />
              
              <div
                className="defect-marker-radar-center"
                style={{
                  width: '12px',
                  height: '12px',
                  backgroundColor: '#ef4444',
                  borderRadius: '50%',
                  zIndex: 2,
                }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}