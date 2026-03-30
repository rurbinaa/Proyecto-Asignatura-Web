import { useState, useMemo, useEffect, useRef } from 'react';

import { 
  MdOutlineFormatColorFill, // Para Manchas
  MdDangerous, // Para Roturas/Roturas de costura
  MdStraighten, // Para Medidas/Uneven
  MdGesture, // Para Hilos sueltos
  MdCropDin, // Para Skip Stitch / Espaciado
  MdOutlineAssignmentLate, // Generico profesional para el resto
  MdDoNotDisturbAlt, // Para Dirt mark o cosas que molestan
  MdScatterPlot // Para Needle Holes
} from 'react-icons/md';
import { LuScissors } from 'react-icons/lu';

const GENERIC_ICON = MdOutlineAssignmentLate;

const MOCK_DEFECT_LIST = [
  { id: 'loose_thread', name: 'Loose Thread', detail: 'Quantity (est)', icon: MdGesture },
  { id: 'stain', name: 'Stain/Oil/Soil', detail: 'Size (cm approx)', icon: MdOutlineFormatColorFill },
  { id: 'broken_stitch', name: 'Broken Stitch', detail: 'Description', icon: LuScissors },
  { id: 'open_seam', name: 'Open Seam', detail: 'Description', icon: MdDangerous },
  { id: 'skip_stitch', name: 'Skip Stitch', detail: 'Description', icon: MdCropDin },
  { id: 'fabric_run', name: 'Fabric Run', detail: 'Length (cm approx)', icon: MdStraighten },
  { id: 'uncut_thread', name: 'Uncut Thread', detail: 'Quantity (est)', icon: LuScissors },
  { id: 'pleat', name: 'Pleat', detail: 'Description', icon: MdDoNotDisturbAlt },
  { id: 'dirt_mark', name: 'Dirt Marck', detail: 'Description', icon: MdDoNotDisturbAlt },
  { id: 'needle_holes', name: 'Needle Holes', detail: 'Description', icon: MdScatterPlot },

  // --- El resto de los 30+ defectos usan el genérico profesional ---
  { id: 'uneven', name: 'Uneven', detail: 'Description', icon: MdStraighten },
  { id: 'hi_low', name: 'Hi Low', detail: 'Description', icon: GENERIC_ICON },
  { id: 'run_off_stitch', name: 'Run Off Stitch', detail: 'Description', icon: GENERIC_ICON },
  { id: 'raw_edge', name: 'Raw Edge', detail: 'Description', icon: GENERIC_ICON },
  { id: 'tear', name: 'Tear', detail: 'Description', icon: MdDangerous },
  { id: 'big_neck', name: 'Big/Litter Neck', detail: 'Measurements diff', icon: GENERIC_ICON },
  { id: 'uneven_sleeve', name: 'Uneven Sleeve', detail: 'Description', icon: GENERIC_ICON },
  { id: 'out_measurements', name: 'Out of Measurements', detail: 'Measurement (cm)', icon: MdStraighten },
  { id: 'var_tension_stitch', name: 'Variation Tension Stitch', detail: 'Description', icon: GENERIC_ICON },
  { id: 'excess_fabric', name: 'Excess Fabric', detail: 'Area', icon: GENERIC_ICON },
  { id: 'hitched', name: 'Hitched', detail: 'Description', icon: GENERIC_ICON },
  { id: 'po_mixed', name: 'PO Mixed', detail: 'Description', icon: GENERIC_ICON },
  { id: 'transfer_leve', name: 'Transfer Peel off, Leve', detail: 'Area', icon: GENERIC_ICON },
  { id: 'wrong_transfer', name: 'Wrong Transfer', detail: 'Description', icon: GENERIC_ICON },
  { id: 'missing_transfer', name: 'Missing Transfer', detail: 'Description', icon: GENERIC_ICON },
  { id: 'missing_label_info', name: 'Missing information Label', detail: 'Label type', icon: GENERIC_ICON },
  { id: 'wrong_label', name: 'Wrong Label', detail: 'Description', icon: GENERIC_ICON },
  { id: 'damaged_label', name: 'Damaged Label', detail: 'Description', icon: GENERIC_ICON },
  { id: 'missing_label', name: 'Missing Label', detail: 'Label type', icon: GENERIC_ICON },
  { id: 'shine', name: 'Shine', detail: 'Description', icon: GENERIC_ICON },
  { id: ' contamination', name: 'Contamination', detail: 'Description', icon: GENERIC_ICON },
  { id: 'construction_defect', name: 'Construction Defect', detail: 'Description', icon: GENERIC_ICON },
  { id: 'mill_flaw', name: 'Mill Flaw', detail: 'Description', icon: GENERIC_ICON },
  { id: ' fabric_run', name: 'Fabric Run', detail: 'Length (cm approx)', icon: GENERIC_ICON },
  { id: 'puckering', name: 'Puckering', detail: 'Description', icon: GENERIC_ICON },
  { id: ' slanted', name: 'Slanted', detail: 'Description', icon: GENERIC_ICON },
  { id: ' pocket', name: 'Pocket', detail: 'Description', icon: GENERIC_ICON },
  { id: ' sticker_inside', name: 'Defects Sticker inside', detail: 'Description', icon: GENERIC_ICON },
  { id: 'label_slanted', name: 'Label Slanted', detail: 'Description', icon: GENERIC_ICON },
  { id: ' shadding', name: 'Shadding', detail: 'Description', icon: GENERIC_ICON },
  { id: 'missing_packing', name: 'Missing Packing Trims', detail: 'Trims name', icon: GENERIC_ICON },
  { id: ' missing_print', name: 'Missing Print/Embroidery', detail: 'Description', icon: GENERIC_ICON },
  { id: 'wrong_packing', name: 'Wrong Packing Trims', detail: 'Trims name', icon: GENERIC_ICON },
  { id: 'wrong_po', name: 'Wrong PO', detail: 'PO Number', icon: GENERIC_ICON },
  { id: ' wrong_folding', name: 'Wrong Folding Method', detail: 'Description', icon: GENERIC_ICON },
  { id: 'wrong_size', name: 'Wrong Size Attached', detail: 'Description', icon: GENERIC_ICON },
  { id: 'label_placement', name: 'Label Placement', detail: 'Description', icon: GENERIC_ICON }
];

const MOCK_FREQUENCY_MAP = {
  'loose_thread': 150, 'stain': 120, 'broken_stitch': 90, 'open_seam': 80, 'skip_stitch': 60,
  ' fabric_run': 50, 'uncut_thread': 40, 'pleat': 30, ' dirt_mark': 20, 'needle_holes': 15,
};

export default function DefectPopover({ coordinates, onClose, onSave }) {
  const popoverRef = useRef(null);

  // TODO: Estos setters marcan warning ahora, pero se usarán en el useEffect para cargar la API real del backend.
  const [defectList, setDefectList] = useState(MOCK_DEFECT_LIST);
  const [frequencyMap, setFrequencyMap] = useState(MOCK_FREQUENCY_MAP);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDefect, setSelectedDefect] = useState(null); 
  const [extraDetail, setExtraDetail] = useState('');

  const [position, setPosition] = useState({ x: -1000, y: -1000 });
  const [isReady, setIsReady] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    /* const fetchDefectsData = async () => { ... } */
  }, []);

  useEffect(() => {
    const container = document.querySelector('.garment-container');
    if (container && popoverRef.current) {
      const containerRect = container.getBoundingClientRect();
      const popoverRect = popoverRef.current.getBoundingClientRect();

      let startX = containerRect.left + (coordinates.x / 100) * containerRect.width + 20;
      let startY = containerRect.top + (coordinates.y / 100) * containerRect.height - 20;

      if (startX + popoverRect.width > window.innerWidth) startX = window.innerWidth - popoverRect.width - 20;
      if (startY + popoverRect.height > window.innerHeight) startY = window.innerHeight - popoverRect.height - 20;
      
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
    document.body.style.cursor = 'grabbing';
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
      if (isDragging) {
        setIsDragging(false);
        document.body.style.cursor = 'default';
      }
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
      .map(defect => ({ ...defect, frequency: frequencyMap[defect.id] || 0 }))
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 10);
  }, [defectList, frequencyMap]);

  const filteredList = useMemo(() => {
    if (!searchTerm.trim()) return [];
    
    if (selectedDefect && searchTerm === selectedDefect.name) return [];

    const lowerSearch = searchTerm.toLowerCase();
    return defectList.filter(defect => defect.name.toLowerCase().includes(lowerSearch)).slice(0, 5); 
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

    const finalizedDefect = {
      x: Number(coordinates.x.toFixed(2)), 
      y: Number(coordinates.y.toFixed(2)), 
      type_id: selectedDefect.id,
      type_name: selectedDefect.name,
      extra_detail: extraDetail || 'N/A',
      id: Date.now() 
    };
    
    onSave(finalizedDefect);
  };

  return (
    <div 
      ref={popoverRef} 
      className="popover" 
      style={{ 
        position: 'fixed',
        left: `${position.x}px`, 
        top: `${position.y}px`,
        opacity: isReady ? 1 : 0, 
        zIndex: 9999,
        transform: 'none', 
        boxShadow: isDragging ? '0 15px 40px rgba(0,0,0,0.4)' : '0 8px 30px rgba(0,0,0,0.2)', 
        transition: isDragging ? 'none' : 'box-shadow 0.2s ease',
        margin: 0
      }}
    >
      <div 
        className="popover-header" 
        onMouseDown={handleMouseDown} 
        style={{ 
          cursor: isDragging ? 'grabbing' : 'grab', 
          padding: '10px 0', 
          marginTop: '-10px', 
          borderBottom: '1px solid #e5e7eb',
          marginBottom: '15px',
          userSelect: 'none' 
        }}
      >
        <h3 className="popover-title" style={{ margin: 0, fontSize: '14px', fontWeight: '700' }}>
          Identify Defect <span style={{fontSize: '11px', color: 'var(--text-muted)', fontWeight: 'normal'}}>(Drag here to move)</span>
        </h3>
        <button className="popover-close" onClick={onClose} title="Cancel" style={{ top: '8px' }}>✕</button>
      </div>
      
      <div className="popover-section" style={{ position: 'relative' }}>
        <input 
          type="text" 
          className="popover-input" 
          placeholder=" Search defect type... (e.g. Stain)"
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            if (selectedDefect && e.target.value !== selectedDefect.name) {
              setSelectedDefect(null);
            }
          }}
        />
        {filteredList.length > 0 && (
          <ul className="popover-autocomplete-list" style={{ position: 'absolute', top: '100%', left: 0, right: 0, backgroundColor: 'white', border: '1px solid #d1d5db', borderRadius: '6px', zIndex: 110, listStyle: 'none', padding: '4px 0', marginTop: '2px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)'}}>
            {filteredList.map(defect => {
              const Icon = defect.icon; 
              return (
                <li key={defect.id} onClick={() => handleSelectDefect(defect)} style={{ padding: '8px 12px', cursor: 'pointer', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>
                  <Icon style={{ fontSize: '16px', color: '#606D80' }} />
                  {defect.name}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="popover-section">
        <p className="popover-subtitle">Frequent Defects (Tap to select)</p>
        
        <div className="defects-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
          {top10Defects.map(defect => {
            const IconComponent = defect.icon;
            return (
              <button 
                key={defect.id} 
                className={`defect-tag ${selectedDefect?.id === defect.id ? 'selected' : ''}`} 
                onClick={() => handleSelectDefect(defect)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '80px',
                  padding: '8px',
                  gap: '6px',
                  backgroundColor: selectedDefect?.id === defect.id ? 'var(--primary)' : '#f3f4f6',
                  color: selectedDefect?.id === defect.id ? 'white' : 'var(--bg-dark)',
                  border: selectedDefect?.id === defect.id ? '2px solid var(--primary-hover)' : '1px solid #d1d5db',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  whiteSpace: 'normal', 
                }}
              >
                <IconComponent style={{ fontSize: '26px' }} />
                
                <span style={{ fontSize: '11px', textAlign: 'center', lineHeight: '1.2', fontWeight: '600' }}>
                  {defect.name}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {selectedDefect && (
        <div className="popover-section" style={{ borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
          <p className="popover-subtitle">Required Detail for <span style={{color: 'var(--primary)', fontWeight: 'bold'}}>{selectedDefect.name}</span></p>
          <input 
            type="text" 
            inputMode={isNumericDetail ? "decimal" : "text"} 
            className="popover-input" 
            placeholder={`Enter ${selectedDefect.detail}...`} 
            value={extraDetail} 
            onChange={handleDetailChange}
          />
        </div>
      )}

      <button className="popover-save" onClick={handleConfirmSave}>Confirm & Add Defect</button>
    </div>
  );
}