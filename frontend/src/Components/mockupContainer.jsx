import { useState, useRef, useEffect, use } from 'react';
import './mockupContainer.css';

export default function MockupContainer( { garmentUrl, onMarkersChange } ) {
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

  return (
    <div className="mockup-wrapper" style={{ position: 'relative'}}>

      {renderedSvg ? (
        <div
          ref={containerRef}
          onClick={handlePathClick}
          dangerouslySetInnerHTML={{ __html: renderedSvg}}
          className="svg_injector"
        />
      ) : (
        <p>Loading SVG...</p>
      )}

      {marker.map((mk) => (
        <div
          key={mk.id}
          className="point-marker"
          style={{
            position: 'absolute',
            left: `${mk.x}%`,
            top: `${mk.y}%`,
            transform: 'translate(-50%, -50%)',
            width: '16px',
            height: '16px',
            backgroundColor: 'red',
            border: '2px solid white',
            borderRadius: '50%',
            pointerEvents: 'none',
          }}
        />
      ))}
    </div>
  );
}