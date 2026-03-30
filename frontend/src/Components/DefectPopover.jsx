import { useState, useMemo, useEffect, useRef } from 'react';

const MOCK_DEFECT_LIST = [
  { id: 'uneven', name: 'Uneven', detail: 'Description' },
  { id: 'broken_stitch', name: 'Broken Stitch', detail: 'Description' },
  { id: 'open_seam', name: 'Open Seam', detail: 'Description' },
  { id: 'hi_low', name: 'Hi Low', detail: 'Description' },
  { id: 'run_off_stitch', name: 'Run Off Stitch', detail: 'Description' },
  { id: 'raw_edge', name: 'Raw Edge', detail: 'Description' },
  { id: 'needle_holes', name: 'Needle Holes', detail: 'Description' },
  { id: 'tear', name: 'Tear', detail: 'Description' },
  { id: 'loose_thread', name: 'Loose Thread', detail: 'Quantity (est)' },
  { id: 'uncut_thread', name: 'Uncut Thread', detail: 'Quantity (est)' },
  { id: 'big_neck', name: 'Big/Litter Neck', detail: 'Measurements diff' },
  { id: 'uneven_sleeve', name: 'Uneven Sleeve', detail: 'Description' },
  { id: 'out_measurements', name: 'Out of Measurements', detail: 'Measurement (cm)' },
  { id: 'var_tension_stitch', name: 'Variation Tension Stitch', detail: 'Description' },
  { id: 'excess_fabric', name: 'Excess Fabric', detail: 'Area' },
  { id: 'hitched', name: 'Hitched', detail: 'Description' },
  { id: 'po_mixed', name: 'PO Mixed', detail: 'Description' },
  { id: 'transfer_leve', name: 'Transfer Peel off, Leve', detail: 'Area' },
  { id: 'wrong_transfer', name: 'Wrong Transfer', detail: 'Description' },
  { id: 'missing_transfer', name: 'Missing Transfer', detail: 'Description' },
  { id: 'missing_label_info', name: 'Missing information Label', detail: 'Label type' },
  { id: 'wrong_label', name: 'Wrong Label', detail: 'Description' },
  { id: 'damaged_label', name: 'Damaged Label', detail: 'Description' },
  { id: 'missing_label', name: 'Missing Label', detail: 'Label type' },
  { id: 'shine', name: 'Shine', detail: 'Description' },
  { id: 'skip_stitch', name: 'Skip Stitch', detail: 'Description' },
  { id: 'pleat', name: 'Pleat', detail: 'Description' },
  { id: 'dirt_mark', name: 'Dirt Marck', detail: 'Description' },
  { id: 'missing_operation', name: 'Missing operation', detail: 'Operation name' },
  { id: 'stain', name: 'Stain/Oil/Soil', detail: 'Size (cm approx)' },
  { id: 'contamination', name: 'Contamination', detail: 'Description' },
  { id: 'construction_defect', name: 'Construction Defect', detail: 'Description' },
  { id: 'mill_flaw', name: 'Mill Flaw', detail: 'Description' },
  { id: 'fabric_run', name: 'Fabric Run', detail: 'Length (cm approx)' },
  { id: 'puckering', name: 'Puckering', detail: 'Description' },
  { id: 'slanted', name: 'Slanted', detail: 'Description' },
  { id: 'pocket', name: 'Pocket', detail: 'Description' },
  { id: 'sticker_inside', name: 'Defects Sticker inside', detail: 'Description' },
  { id: 'label_slanted', name: 'Label Slanted', detail: 'Description' },
  { id: 'shadding', name: 'Shadding', detail: 'Description' },
  { id: 'missing_packing', name: 'Missing Packing Trims', detail: 'Trims name' },
  { id: 'missing_print', name: 'Missing Print/Embroidery', detail: 'Description' },
  { id: 'wrong_packing', name: 'Wrong Packing Trims', detail: 'Trims name' },
  { id: 'wrong_po', name: 'Wrong PO', detail: 'PO Number' },
  { id: 'wrong_folding', name: 'Wrong Folding Method', detail: 'Description' },
  { id: 'wrong_size', name: 'Wrong Size Attached', detail: 'Description' },
  { id: 'label_placement', name: 'Label Placement', detail: 'Description' }
];

const MOCK_FREQUENCY_MAP = {
  'loose_thread': 150, 'stain': 120, 'broken_stitch': 90, 'open_seam': 80, 'skip_stitch': 60,
  'fabric_run': 50, 'uncut_thread': 40, 'pleat': 30, 'dirt_mark': 20, 'needle_holes': 15,
};

export default function DefectPopover({ coordinates, onClose, onSave }) {
  // --- REFERENCIAS ---
  const popoverRef = useRef(null);

  // --- STATES DE DATOS (API Ready) ---
  const [defectList, setDefectList] = useState(MOCK_DEFECT_LIST);
  const [frequencyMap, setFrequencyMap] = useState(MOCK_FREQUENCY_MAP);

  // --- STATES DE INTERFAZ ---
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDefect, setSelectedDefect] = useState(null); 
  const [extraDetail, setExtraDetail] = useState('');

  // 🔴 CAMBIO: Posición inicial fuera de pantalla, y agregamos isReady
  const [position, setPosition] = useState({ x: -1000, y: -1000 });
  const [isReady, setIsReady] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  // --- CONTRATO DE API: GET /defects (Comentado para pruebas) ---
  useEffect(() => {
    /* const fetchDefectsData = async () => {
      // ...
    };
    fetchDefectsData();
    */
  }, []);

  // 🔴 CAMBIO: Calcular la posición inicial en PÍXELES REALES de la pantalla
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


  // DRAGGABLE LOGIC FUNCTIONS
  const handleMouseDown = (e) => {
    if (e.target.tagName.toLowerCase() === 'input' || e.target.tagName.toLowerCase() === 'button' || e.target.tagName.toLowerCase() === 'li') {
      return;
    }
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

      // 🔴 CAMBIO: Matemáticas directas sobre la ventana entera (window), no el contenedor
      let newXPixels = e.clientX - dragOffset.x;
      let newYPixels = e.clientY - dragOffset.y;

      // 🔴 CAMBIO: Constraints usando window.innerWidth/Height
      if (newXPixels < 0) newXPixels = 0;
      if (newXPixels + popoverRect.width > window.innerWidth) {
        newXPixels = window.innerWidth - popoverRect.width;
      }
      
      if (newYPixels < 0) newYPixels = 0;
      if (newYPixels + popoverRect.height > window.innerHeight) {
        newYPixels = window.innerHeight - popoverRect.height;
      }

      // 🔴 CAMBIO: Guardamos directamente los píxeles, sin convertir a porcentaje
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
    const lowerSearch = searchTerm.toLowerCase();
    return defectList.filter(defect => defect.name.toLowerCase().includes(lowerSearch)).slice(0, 5); 
  }, [searchTerm, defectList]);

  const handleSelectDefect = (defect) => {
    setSelectedDefect(defect);
    setSearchTerm(defect.name); 
    setExtraDetail(''); 
  };

  const handleConfirmSave = () => {
    if (!selectedDefect) {
      alert("Please select a defect type first.");
      return;
    }
    const finalizedDefect = {
      ...coordinates,
      type_id: selectedDefect.id,
      type_name: selectedDefect.name,
      extra_detail: extraDetail || 'N/A',
      id: Date.now() 
    };
    onSave(finalizedDefect);
  };

  // RENDER
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
      {/* DRAGGABLE HEADER: Usamos la cabecera como zona de agarre */}
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
      
      {/* BUSQUEDA Y AUTOCOMPLETADO */}
      <div className="popover-section" style={{ position: 'relative' }}>
        <input 
          type="text" 
          className="popover-input" 
          placeholder=" Search defect type... (e.g. Stain)"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        {filteredList.length > 0 && (
          <ul className="popover-autocomplete-list" style={{ position: 'absolute', top: '100%', left: 0, right: 0, backgroundColor: 'white', border: '1px solid #d1d5db', borderRadius: '6px', zIndex: 110, listStyle: 'none', padding: '4px 0', marginTop: '2px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)'}}>
            {filteredList.map(defect => (
              <li key={defect.id} onClick={() => handleSelectDefect(defect)} style={{ padding: '8px 12px', cursor: 'pointer', fontSize: '13px' }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>
                {defect.name}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* (TOP 10) */}
      <div className="popover-section">
        <p className="popover-subtitle">Frequent Defects (Tap to select)</p>
        <div className="defects-grid">
          {top10Defects.map(defect => (
            <button key={defect.id} className={`defect-tag ${selectedDefect?.id === defect.id ? 'selected' : ''}`} onClick={() => handleSelectDefect(defect)}>
              {defect.name}
            </button>
          ))}
        </div>
      </div>

      {/* DETALLE DINAMICO */}
      {selectedDefect && (
        <div className="popover-section" style={{ borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
          <p className="popover-subtitle">Required Detail for <span style={{color: 'var(--primary)', fontWeight: 'bold'}}>{selectedDefect.name}</span></p>
          <input type="text" className="popover-input" placeholder={`Enter ${selectedDefect.detail}...`} value={extraDetail} onChange={(e) => setExtraDetail(e.target.value)}/>
        </div>
      )}

      <button className="popover-save" onClick={handleConfirmSave}>Confirm & Add Defect</button>
    </div>
  );
}