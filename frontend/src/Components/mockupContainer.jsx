import { useState, useRef, useEffect } from 'react';
import './mockupContainer.css';

export default function MockupContainer( { garmentUrl, onMarkersChange, isEditMode } ) {
  const containerRef = useRef(null);

  const [renderedSvg, SetRenderedSvg] = useState(null);
  const [marker, setmarker] = useState([]);

  useEffect(() => {
    if (!garmentUrl) return;
    setmarker([]);
    fetch(garmentUrl)
      .then((res) => res.text())
      .then((data) => SetRenderedSvg(data))
      .catch((err) => console.error('Error loading SVG:', err));
    }, [garmentUrl]);

  useEffect(() => {
    if (onMarkersChange) {
      onMarkersChange(marker);
    }
  }, [marker, onMarkersChange]);

  const handlePathClick = (e) => {

    if (isEditMode) return;

    if (e.target.tagName.toLowerCase() !== 'path') {
      return; 
    }

    const svgElement = containerRef.current.querySelector('svg');
    if (!svgElement) return;
    
    const rect = svgElement.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const percentageX = (x / rect.width) * 100;
    const percentageY = (y / rect.height) * 100;

    console.log(`Garment click -> X: ${percentageX.toFixed(2)}%, Y: ${percentageY.toFixed(2)}%`);
    setmarker([...marker, { x: percentageX, y: percentageY, id: Date.now() }]);
  };

  const handleRemoveMarker = (e, idToRemove) => {
    e.stopPropagation();
    if (!isEditMode) return;

    const updateMarkers = marker.filter(mk => mk.id !== idToRemove);
    setmarker(updateMarkers);
  }

  return (
    <div className="mockup-wrapper" style={{ position: 'relative'}}>

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

      {marker.map((mk) => (
        <div
          key={mk.id}
          className="point-marker"
          onClick={(e) => handleRemoveMarker(e, mk.id)}
          title={isEditMode ? "Delete marker" : "Defect"}
          style={{
            position: 'absolute',
            left: `${mk.x}%`,
            top: `${mk.y}%`,
            transform: 'translate(-50%, -50%)',
            width: '32px',
            height: '32px',
            backgroundColor: 'red',
            border: isEditMode? '2px dashed white' : '3px solid white',
            borderRadius: '50%',
            pointerEvents: 'auto',
            cursor: isEditMode? 'pointer' : 'default',
            boxShadow: '0 3px 6px rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2 ease',
          }}
        >
          {isEditMode && (
          <span style={{ color: 'white', fontSize: '14px', fontWeight: 'bold' }}>X</span>
          )}
        </div>
      ))}
    </div>
  );
}