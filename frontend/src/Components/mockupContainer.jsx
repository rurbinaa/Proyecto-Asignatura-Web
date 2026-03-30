import { useState, useRef, useEffect } from 'react';
import './mockupContainer.css';

export default function MockupContainer({ garmentUrl, confirmedMarkers, isEditMode, onDefectPlacePending, onRemoveConfirmedMarker }) {
  const containerRef = useRef(null);
  
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

    const svgElement = containerRef.current.querySelector('svg');
    if (!svgElement) return;
    
    const rect = svgElement.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const percentageX = (x / rect.width) * 100;
    const percentageY = (y / rect.height) * 100;

    console.log(`Pending placement -> X: ${percentageX.toFixed(2)}%, Y: ${percentageY.toFixed(2)}%`);

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
      style={{ 
        position: 'relative',
        cursor: isEditMode ? 'default' : 'crosshair' 
      }}
    >

      {renderedSvg ? (
        <div
          ref={containerRef}
          onClick={handlePathClick}
          dangerouslySetInnerHTML={{ __html: renderedSvg}}
          className="svg_injector"
          style={{
            opacity: isEditMode ? 0.5 : 1,
            transition: 'opacity 0.3s ease'
          }}
        />
      ) : (
        <p>Loading SVG...</p>
      )}

      {confirmedMarkers.map((mk) => (
        <div
          key={mk.id}
          className="point-marker"
          onClick={(e) => handleRemoveMarker(e, mk.id)}
          title={isEditMode ? `Delete: ${mk.type_name}` : `Defect: ${mk.type_name} (${mk.extra_detail})`}
          style={{
            position: 'absolute',
            left: `${mk.x}%`,
            top: `${mk.y}%`,
            transform: 'translate(-50%, -50%)',
            width: '32px',
            height: '32px',
            backgroundColor: '#ef4444',
            border: isEditMode ? '3px dashed white' : '3px solid white',
            borderRadius: '50%',
            pointerEvents: 'auto',
            cursor: isEditMode ? 'pointer' : 'default',
            boxShadow: '0 3px 6px rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease',
          }}
        >
          {isEditMode && (
            <span style={{ color: 'white', fontSize: '14px', fontWeight: 'bold' }}>✕</span>
          )}
        </div>
      ))}
    </div>
  );
}