import { useState } from 'react';
import './CaptureView.css';
import urlShirt from '../assets/shirt.svg';
import urlShirtBack from '../assets/shirt.svg';
import urlPants from '../assets/pants.svg';
import urlPantsBack from '../assets/pants.svg'; 
import MockupContainer from '../Components/mockupContainer.jsx'; 
import DefectPopover from '../Components/DefectPopover.jsx'; 

import { 
  MdOutlineFormatColorFill, 
  MdDangerous, 
  MdStraighten, 
  MdGesture, 
  MdCropDin, 
  MdOutlineAssignmentLate, 
  MdDoNotDisturbAlt, 
  MdScatterPlot 
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

    // --- El resto de los defectos usan el genérico ---
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
    { id: 'contamination', name: 'Contamination', detail: 'Description', icon: GENERIC_ICON },
    { id: 'construction_defect', name: 'Construction Defect', detail: 'Description', icon: GENERIC_ICON },
    { id: 'mill_flaw', name: 'Mill Flaw', detail: 'Description', icon: GENERIC_ICON },
    { id: 'fabric_run', name: 'Fabric Run', detail: 'Length (cm approx)', icon: GENERIC_ICON },
    { id: 'puckering', name: 'Puckering', detail: 'Description', icon: GENERIC_ICON },
    { id: 'slanted', name: 'Slanted', detail: 'Description', icon: GENERIC_ICON },
    { id: 'pocket', name: 'Pocket', detail: 'Description', icon: GENERIC_ICON },
    { id: 'sticker_inside', name: 'Defects Sticker inside', detail: 'Description', icon: GENERIC_ICON },
    { id: 'label_slanted', name: 'Label Slanted', detail: 'Description', icon: GENERIC_ICON },
    { id: 'shadding', name: 'Shadding', detail: 'Description', icon: GENERIC_ICON },
    { id: 'missing_packing', name: 'Missing Packing Trims', detail: 'Trims name', icon: GENERIC_ICON },
    { id: 'missing_print', name: 'Missing Print/Embroidery', detail: 'Description', icon: GENERIC_ICON },
    { id: 'wrong_packing', name: 'Wrong Packing Trims', detail: 'Trims name', icon: GENERIC_ICON },
    { id: 'wrong_po', name: 'Wrong PO', detail: 'PO Number', icon: GENERIC_ICON },
    { id: 'wrong_folding', name: 'Wrong Folding Method', detail: 'Description', icon: GENERIC_ICON },
    { id: 'wrong_size', name: 'Wrong Size Attached', detail: 'Description', icon: GENERIC_ICON },
    { id: 'label_placement', name: 'Label Placement', detail: 'Description', icon: GENERIC_ICON }
  ];
  
  const MOCK_FREQUENCY_MAP = {
    'loose_thread': 150, 'stain': 120, 'broken_stitch': 90, 'open_seam': 80, 'skip_stitch': 60,
    ' fabric_run': 50, 'uncut_thread': 40, 'pleat': 30, ' dirt_mark': 20, 'needle_holes': 15,
  };

const MOCK_LOTS = [
  { id: "LOT-001", name: "Morning Shift" },
  { id: "LOT-002", name: "Evening Shift" },
  { id: "LOT-003", name: "Urgent" }
];

const MOCK_GARMENTS = [
  { id: "shirt", name: "Shirt / T-Shirt" },
  { id: "pants", name: "Pants" }
];

export default function CaptureView() {
  const [step, setStep] = useState('selection'); 
  const [lot, setLot] = useState('');
  const [garment, setGarment] = useState('');
  const [currentDefects, setCurrentDefects] = useState([]);
  const [lastSubmission, setLastSubmission] = useState(null);
  const [viewSide, setViewSide] = useState('front');
  
  const [isEditMode, setIsEditMode] = useState(false);

  const [isPopoverOpen, setIsPopoverOpen] = useState(false);
  const [pendingCoords, setPendingCoords] = useState(null);


  const handleStartCapture = () => {
    if (!lot || !garment) {
      alert("Please select a Lot and a Garment Type to continue.");
      return;
    }
    setStep('capture');
  };
  
  const handleDefectPlacePending = (coords) => {
    setPendingCoords(coords);
    setIsPopoverOpen(true); 
  };

  const handleClosePopover = () => {
    setIsPopoverOpen(false);
    setPendingCoords(null);
  };

  const handleSaveDefectFromPopover = (finalizedDefect) => {
    const defectWithSide = {...finalizedDefect, side: viewSide};
    setCurrentDefects(prev => [...prev, defectWithSide]);
    setIsPopoverOpen(false);
    setPendingCoords(null);
  };

  const handleRemoveConfirmedMarker = (idToRemove) => {
    setCurrentDefects(prev => prev.filter(defect => defect.id !== idToRemove));
  };

  const handleUndoLastDefect = () => {
    if (!lastSubmission) return;
    console.log("Undoing shipment to the backend");
    setCurrentDefects(lastSubmission);
    setLastSubmission(null);
    alert("Shipment canceled");
  };

  const handleSaveToDB = async () => {
    if (isEditMode || isPopoverOpen) {
      alert("Please finalize defect selection or exit edit mode before saving.");
      return;
    }

    const groupedDefects = Object.values(currentDefects.reduce((acc, defect) => {

      const detailValue = defect.defectSize || defect.defectCount || defect.notes || "N/A";
      // Agrupamos por ID del defecto + Detalle + Lado
      const key = `${defect.defectType}-${detailValue}-${defect.side}`;
      
      if (!acc[key]) {
        acc[key] = {
          defectType: defect.defectType,
          defectSize: defect.defectSize,
          notes: defect.notes,
          side: defect.side,
          pointsCount: 0,
          coordinates_x: [],
          coordinates_y: []
        };
      }
      
      acc[key].coordinates_x.push(defect.coordinates_x);
      acc[key].coordinates_y.push(defect.coordinates_y);
      acc[key].pointsCount += 1;
      
      return acc;
    }, {}));

    const formattedDefects = groupedDefects.map(group => ({
      defectType: group.defectType,
      defectSize: group.defectSize,
      defectCount: group.pointsCount,
      notes: group.notes,
      coordinates_x: group.coordinates_x,
      coordinates_y: group.coordinates_y,
      side: group.side
    }));

    const payload = { 
      lot_id: lot, 
      garment_type: garment, 
      defects: formattedDefects // Lista agrupada
    };
    
    console.log("Payload agrupado para Django:", payload);

    try {
      setLastSubmission(currentDefects);
      setCurrentDefects([]);
      setIsEditMode(false);
      setViewSide('front');
      alert(`Success! Envió agrupado a la BD.`);

    } catch (error) {
      console.error("Error saving to DB:", error);
      alert("Error saving data. Check console.");
    }
  };

  if (step === 'selection') {
    return (
      <div className="capture-view">
        <div className="capture-header">
          <h2 className="section-title">Capture Setup</h2>
        </div>

        <div className="card capture-setup-card">
          <div className="input-group" style={{ marginBottom: '20px' }}>
            <label className="input-label">Select Lot to Inspect</label>
            <select className="input-field" value={lot} onChange={(e) => setLot(e.target.value)}>
              <option value="">Choose a lot</option>
              {MOCK_LOTS.map((item) => <option key={item.id} value={item.id}>{item.id} ({item.name})</option>)}
            </select>
          </div>

          <div className="input-group" style={{ marginBottom: '30px' }}>
            <label className="input-label">Garment Type</label>
            <select className="input-field" value={garment} onChange={(e) => setGarment(e.target.value)}>
              <option value="">Choose garment</option>
              {MOCK_GARMENTS.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </div>

          <button className="ingesta-btn ingesta-btn-primary" style={{ width: '100%', cursor: 'pointer' }} onClick={handleStartCapture}>
            Start Touch Capture
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="capture-view">
      
      <div className="capture-header-flex">
        <div>
          <h2 className="section-title" style={{ marginBottom: '4px' }}>Quality Control</h2>
          <p className="capture-subtitle">
            Inspecting: <span>{lot} ({garment})</span>
          </p>
        </div>
        <button className="ingesta-btn ingesta-btn-outline" onClick={() => { setStep('selection'); setIsEditMode(false); handleClosePopover(); }}>
          Cancel / Back
        </button>
      </div>

      <div className="card garment-area garment-area-layout">
        
        <div className="garment-column garment-container">
          <div className="view-toggle-container">
            <button 
              className={`ingesta-btn flex-btn ${viewSide === 'front' ? 'btn-edit-mode active' : 'btn-undo'}`} 
              onClick={() => { setViewSide('front'); setPendingCoords(null); setIsPopoverOpen(false);}}
            >
              Front View
            </button>
            <button
              className={`ingesta-btn flex-btn ${viewSide === 'back' ? 'btn-edit-mode active': 'btn-undo'}`}
              onClick={() => { setViewSide('back'); setPendingCoords(null); setIsPopoverOpen(false);}}
            >
              Back View
            </button>
          </div>

          <div className="garment-instructions">
            <span className={isEditMode ? 'instruction-delete' : 'instruction-normal'}>
              {isEditMode ? 'Delete Mode Active. Tap a marker to remove it.' : `Tap the ${viewSide} of the garment to indentify a defect.`}
            </span>
          </div>

          <MockupContainer 
            garmentUrl={garment === 'pants' ? (viewSide === 'front' ?  urlPants : urlPantsBack) : (viewSide === 'front' ? urlShirt : urlShirtBack)} 
            confirmedMarkers={currentDefects.filter(d => d.side === viewSide)}
            isEditMode={isEditMode} 
            onDefectPlacePending={handleDefectPlacePending}
            onRemoveConfirmedMarker={handleRemoveConfirmedMarker}
            pendingCoords={pendingCoords}
          />

          {isPopoverOpen && pendingCoords && (
            <DefectPopover 
              coordinates={pendingCoords}
              onClose={handleClosePopover}
              onSave={handleSaveDefectFromPopover}
              defectList={MOCK_DEFECT_LIST}
              frequencyMap={MOCK_FREQUENCY_MAP}
            />
          )}
        </div>

        <div className="control-panel">
          
          <h3 className="panel-title">
            Defects: {currentDefects.length}
          </h3>

          <button 
            onClick={() => setIsEditMode(!isEditMode)} 
            className={`ingesta-btn btn-edit-mode ${isEditMode ? 'active' : 'inactive'}`}
          >
            {isEditMode ? 'Done Editing' : 'Edit / Delete Markers'}
          </button>

          <button 
            onClick={handleUndoLastDefect} 
            disabled={!lastSubmission || isEditMode}
            className="ingesta-btn btn-undo" 
            title="Undo last added defect"
          >
            Undo Last
          </button>

          <div className="flex-spacer"></div>

          <button 
            className="ingesta-btn ingesta-btn-primary btn-send" 
            onClick={handleSaveToDB} 
            disabled={isEditMode || isPopoverOpen || currentDefects.length === 0}
          >
            Send
          </button>
        </div>

      </div>
      
    </div>
  );
}