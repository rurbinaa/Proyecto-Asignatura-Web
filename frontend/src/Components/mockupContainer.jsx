import { useState, useRef } from 'react';
import './mockupContainer.css';

export default function MockupContainer() {
  const svgRef = useRef(null);
  const [marcador, setMarcador] = useState(null);

  const handlePathClick = (e) => {
    if (e.target.tagName.toLowerCase() !== 'path') {
      return; 
    }

    if (!svgRef.current) return;

    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const porcentajeX = (x / rect.width) * 100;
    const porcentajeY = (y / rect.height) * 100;

    console.log(`Clic en prenda -> X: ${porcentajeX.toFixed(2)}%, Y: ${porcentajeY.toFixed(2)}%`);
    setMarcador({ x: porcentajeX, y: porcentajeY });
  };

  return (
    <div className="mockup-wrapper">
      <svg
        ref={svgRef}
        viewBox="0 0 512.004 512.004"
        className="mockup-svg"
        xmlns="http://www.w3.org/2000/svg"
        xmlSpace="preserve"
        onClick={handlePathClick}
        style={{ cursor: 'crosshair' }}
      >
        <g>
          <path fill="#BDC3C7" d="M320.327,29.022c-11.079,24.514-35.69,41.596-64.335,41.596v441.379h97.103 c19.5,0,35.31-15.81,35.31-35.31V223.635l61.237,230.762c2.375,9.728,12.367,15.537,21.998,12.782l27.542-7.865 c9.234-2.639,14.663-12.164,12.235-21.451l-96.53-349.59c0,0,3.681-19.121-79.448-44.138l-15.007-15.007L320.327,29.022z"/>
          <g>
            <path fill="#E6E7E8" d="M191.67,29.038l-15.104,15.104C93.446,69.151,97.118,88.28,97.118,88.28l0.477,0.23l-0.494-0.23 L0.589,437.862c-2.436,9.287,3.001,18.812,12.226,21.451l27.542,7.865c9.64,2.754,19.624-3.054,22.007-12.782l61.237-230.78 v253.078c0,19.5,15.81,35.31,35.31,35.31h97.086V70.625C227.352,70.625,202.749,53.544,191.67,29.038"/>
            <path fill="#E6E7E8" d="M335.444,176.552c-4.873,0-8.828-3.946-8.828-8.828c0-14.601-11.882-26.483-26.483-26.483 c-4.873,0-8.828-3.946-8.828-8.828s3.955-8.828,8.828-8.828c14.424,0,27.251,6.956,35.31,17.682 c8.06-10.726,20.886-17.682,35.31-17.682c4.873,0,8.828,3.946,8.828,8.828s-3.955,8.828-8.828,8.828 c-14.601,0-26.483,11.882-26.483,26.483C344.271,172.606,340.316,176.552,335.444,176.552"/>
            <path fill="#E6E7E8" d="M449.643,454.396c2.375,9.737,12.367,15.537,21.998,12.791l27.542-7.874 c9.234-2.631,14.663-12.164,12.235-21.451l-5.553-20.1l-61.299,17.514L449.643,454.396z"/>
          </g>
          <path fill="#BDC3C7" d="M6.086,417.871l-5.5,19.986c-2.428,9.287,3.001,18.812,12.235,21.451l27.542,7.874 c9.631,2.745,19.624-3.054,21.998-12.791l5.014-19.006L6.086,417.871z"/>
          <path fill="#95A5A5" d="M225.382,0c-8.289,0-15.863,4.687-19.562,12.103l-2.763,5.553c0,0-5.447,5.438-11.388,11.379 c11.079,24.505,35.681,41.587,64.327,41.587s53.257-17.09,64.327-41.596l-11.343-11.352l-0.018-0.018l-2.79-5.57 C302.473,4.679,294.899,0,286.628,0H225.382z"/>
        </g>
      </svg>

      {marcador && (
        <div
          className="marcador-punto"
          style={{
            left: `${marcador.x}%`,
            top: `${marcador.y}%`,
          }}
        />
      )}
    </div>
  );
}