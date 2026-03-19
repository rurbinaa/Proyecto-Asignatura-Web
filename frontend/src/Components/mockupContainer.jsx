import { useState, useRef, use, useEffect } from 'react';
import './mockupContainer.css';

export default function MockupContainer( { garmentUrl } ) {
  const containerRef = useRef(null);
  const [renderedSvg, SetRenderedSvg] = useState(null);
  const [marker, setmarker] = useState(null);

  useEffect(() => {
    if (!garmentUrl) return;

    setmarker(null);

    fetch(garmentUrl)
      .then((res) => res.text())
      .then((data) => SetRenderedSvg(data))
      .catch((err) => console.error('Error loading SVG:', err));
      }, [garmentUrl]);

  const handlePathClick = (e) => {
    if (e.target.tagName.toLowerCase() !== 'path') {
      return; 
    }

    const svgElement = containerRef.current.querySelector('svg');
    if (!svgElement) return;
    
    const rect = svgElement.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const porcentajeX = (x / rect.width) * 100;
    const porcentajeY = (y / rect.height) * 100;

    console.log(`Garment click -> X: ${porcentajeX.toFixed(2)}%, Y: ${porcentajeY.toFixed(2)}%`);
    setmarker({ x: porcentajeX, y: porcentajeY });
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

      {marker && (
        <div
          className="point-marker"
          style={{
            left: `${marker.x}%`,
            top: `${marker.y}%`,
            transform: 'translate(-50%, -50%)',
            width: '16px',
            height: '16px',
            backgroundColor: 'red',
            border: '2px solid white',
            borderRadius: '50%',
            pointerEvents: 'none',
          }}
        />
      )}
    </div>
  );
}