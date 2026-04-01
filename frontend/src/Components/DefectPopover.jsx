import './DefectPopover.css';
import { useState, useMemo, useEffect, useRef } from 'react';

export default function DefectPopover({ coordinates, onClose, onSave, defectList = [], frequencyMap = {} }) {
  const popoverRef = useRef(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDefect, setSelectedDefect] = useState(null); 
  const [extraDetail, setExtraDetail] = useState('');

  const [position, setPosition] = useState({ x: -1000, y: -1000 });
  const [isReady, setIsReady] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const container = document.querySelector('.garment-container');
    if (container && popoverRef.current) {
      const containerRect = container.getBoundingClientRect();
      const popoverRect = popoverRef.current.getBoundingClientRect();

      let startX = containerRect.left - popoverRect.width - 20; 
      
      if (startX < 20) startX = 20; 

      let startY = containerRect.top + (coordinates.y / 100) * containerRect.height - (popoverRect.height / 2);
      
      if (startY < 20) startY = 20;
      if (startY + popoverRect.height > window.innerHeight) {
        startY = window.innerHeight - popoverRect.height - 20;
      }
      
      setPosition({ x: startX, y: startY });
      setIsReady(true);
    }
  }, [coordinates]);

  const handleMouseDown = (e) => {
    if (['input', 'button', 'li'].includes(e.target.tagName.toLowerCase())) return;
    if (!popoverRef.current) return;
    
    setIsDragging(true);
    const rect = popoverRef.current.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging || !popoverRef.current) return;

      const popoverRect = popoverRef.current.getBoundingClientRect();

      let newXPixels = e.clientX - dragOffset.x;
      let newYPixels = e.clientY - dragOffset.y;

      if (newXPixels < 0) newXPixels = 0;
      if (newXPixels + popoverRect.width > window.innerWidth) {
        newXPixels = window.innerWidth - popoverRect.width;
      }
      
      if (newYPixels < 0) newYPixels = 0;
      if (newYPixels + popoverRect.height > window.innerHeight) {
        newYPixels = window.innerHeight - popoverRect.height;
      }

      setPosition({
        x: newXPixels,
        y: newYPixels
      });
    };

    const handleMouseUp = () => {
      if (isDragging) setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragOffset]);

  const top10Defects = useMemo(() => {
    return defectList
      ?.map(defect => ({ ...defect, frequency: frequencyMap[defect.id] || 0 }))
      ?.sort((a, b) => b.frequency - a.frequency)
      ?.slice(0, 10) || [];
  }, [defectList, frequencyMap]);

  const filteredList = useMemo(() => {
    if (!searchTerm.trim()) return [];
    if (selectedDefect && searchTerm === selectedDefect.name) return [];

    const lowerSearch = searchTerm.toLowerCase();
    return defectList?.filter(defect => defect.name.toLowerCase().includes(lowerSearch))?.slice(0, 5) || []; 
  }, [searchTerm, defectList, selectedDefect]);

  const handleSelectDefect = (defect) => {
    setSelectedDefect(defect);
    setSearchTerm(defect.name); 
    setExtraDetail(''); 
  };

  const isNumericDetail = useMemo(() => {
    if (!selectedDefect) return false;
    const detailLower = selectedDefect.detail.toLowerCase();
    return detailLower.includes('cm') || 
           detailLower.includes('quantity') || 
           detailLower.includes('measurement') || 
           detailLower.includes('size') ||
           detailLower.includes('area');
  }, [selectedDefect]);

  const handleDetailChange = (e) => {
    const val = e.target.value;
    if (isNumericDetail) {
      if (val === '' || /^[0-9]*\.?[0-9]*$/.test(val)) {
        setExtraDetail(val);
      }
    } else {
      setExtraDetail(val);
    }
  };

  const handleConfirmSave = () => {
    if (!selectedDefect) {
      alert("Please select a defect type first.");
      return;
    }
    if (isNumericDetail && !extraDetail.trim()) {
      alert(`Please enter a valid number for ${selectedDefect.detail}.`);
      return;
    }

    const detailLower = selectedDefect.detail.toLowerCase();
    const isSize = detailLower.includes('cm') || detailLower.includes('measurement') || detailLower.includes('area');
    const isCount = detailLower.includes('quantity');

    const finalizedDefect = {
      coordinates_x: Number(coordinates.x.toFixed(2)), 
      coordinates_y: Number(coordinates.y.toFixed(2)), 
      defectType: selectedDefect.id,
      defectSize: isSize ? extraDetail : null,
      defectCount : isCount ? extraDetail : null,
      notes: (!isSize && !isCount) ? (extraDetail || 'N/A') : "",
      type_name: selectedDefect.name,
      id: Date.now() 
    };
    
    onSave(finalizedDefect);
  };

  return (
    <div 
      ref={popoverRef} 
      className={`popover ${isDragging ? 'dragging' : ''}`} 
      style={{ 
        left: `${position.x}px`, 
        top: `${position.y}px`,
        opacity: isReady ? 1 : 0
      }}
    >
      <div 
        className={`popover-header ${isDragging ? 'dragging' : ''}`} 
        onMouseDown={handleMouseDown} 
      >
        <h3 className="popover-title">
          Identify Defect <span>(Drag here to move)</span>
        </h3>
        <button className="popover-close" onClick={onClose} title="Cancel">✕</button>
      </div>
         
      {!selectedDefect ? (
        <>
          <div className="popover-section relative-section">
            <input 
              type="text" 
              className="popover-input" 
              placeholder=" Search defect type... (e.g. Stain)"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {filteredList.length > 0 && (
              <ul className="popover-autocomplete-list">
                {filteredList.map(defect => {
                  const Icon = defect.icon; 
                  return (
                    <li 
                      key={defect.id} 
                      className="popover-autocomplete-item" 
                      onClick={() => handleSelectDefect(defect)}
                    >
                      <Icon className="autocomplete-icon" />
                      {defect.name}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <div className="popover-section no-margin-bottom">
            <p className="popover-subtitle">Frequent Defects (Tap to select)</p>
            <div className="defects-grid">
              {top10Defects.map(defect => {
                const IconComponent = defect.icon;
                return (
                  <button 
                    key={defect.id} 
                    className="defect-tag" 
                    onClick={() => handleSelectDefect(defect)}
                  >
                    <IconComponent className="grid-icon" />
                    <span>{defect.name}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </>
      ) : (
        <div className="popover-section slide-in no-margin-bottom">
          
          <div className="selected-defect-card">
            <div className="selected-defect-info">
              <selectedDefect.icon className="grid-icon icon-primary" />
              <span className="highlight-name text-md">{selectedDefect.name}</span>
            </div>
            <button 
              className="change-defect-btn" 
              onClick={() => { setSelectedDefect(null); setSearchTerm(''); }}
            >
              Change
            </button>
          </div>

          <div className="margin-top-md">
            <p className="popover-subtitle">
              Required Detail:
            </p>
            <input 
              type="text" 
              inputMode={isNumericDetail ? "decimal" : "text"} 
              className="popover-input focus-input" 
              placeholder={`Enter ${selectedDefect.detail}...`} 
              value={extraDetail} 
              onChange={handleDetailChange}
              autoFocus 
            />
          </div>

          <button className="popover-save" onClick={handleConfirmSave}>
            Confirm & Add Defect
          </button>
          
        </div>
      )}

    </div>
  );
}