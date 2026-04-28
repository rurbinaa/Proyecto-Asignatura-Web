import { useState } from 'react';
import './CaptureView.css';
import urlShirt from '../assets/camisa_front.svg';
import urlShirtBack from '../assets/camisa_back.svg';
import urlPants from '../assets/pants_front.svg';
import urlPantsBack from '../assets/pants_back.svg';
import MockupContainer from '../Components/mockupContainer.jsx';
import DefectPopover from '../Components/DefectPopover.jsx'; 

import { 
  createInspection,
  createDefect,
  closeInspection,
} from '../api/capture.js'; 

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
    'fabric_run': 50, 'uncut_thread': 40, 'pleat': 30, 'dirt_mark': 20, 'needle_holes': 15,
  };

  const MOCK_GARMENTS = [
    { id: "shirt", name: "Shirt / T-Shirt" },
    { id: "pants", name: "Pants" }
  ];

export default function CaptureView() {
  const [step, setStep] = useState('selection'); 
  const [syncState, setSyncState] = useState('idle'); // idle | capturing | sending | success | error
  
  const [lot, setLot] = useState('');
  const [styleInput, setStyleInput] = useState('');
  const [sizeInput, setSizeInput] = useState('');
  const [colorInput, setColorInput] = useState('');
  const [garment, setGarment] = useState('');
  
  const [currentDefects, setCurrentDefects] = useState([]);
  const [lastSubmission, setLastSubmission] = useState(null);
  const [viewSide, setViewSide] = useState('front');
  
  const [isEditMode, setIsEditMode] = useState(false);

  const [isPopoverOpen, setIsPopoverOpen] = useState(false);
  const [pendingCoords, setPendingCoords] = useState(null);


  const handleStartCapture = () => {
    if (!lot.trim() || !garment || !styleInput.trim() || !sizeInput.trim() || !colorInput.trim()) {
      alert("Please fill out all fields (Lot, Garment Type, Style, Size, and Color) to continue.");
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

  const handleUndoLastDefect = async () => {
    if (!lastSubmission) return;
    
    // If we have an inspectionId stored from last submission, call the API
    // For now, we only clear local state since inspectionId isn't persisted
    console.log("Undoing last defect submission locally");
    setCurrentDefects(lastSubmission);
    setLastSubmission(null);
    alert("Last submission cleared");
  };

  const handleSaveToDB = async () => {
    if (isEditMode || isPopoverOpen) {
      alert("Please finalize defect selection or exit edit mode before saving.");
      return;
    }

    setSyncState('sending');

    try {
      // Group defects by type + size + side (existing logic)
      const groupedDefects = Object.values(currentDefects.reduce((acc, defect) => {
        const detailValue = defect.defectSize || defect.defectCount || defect.notes || "N/A";
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
        
        // Push scalar coordinates, not wrapped in array
        acc[key].coordinates_x.push(defect.coordinates_x);
        acc[key].coordinates_y.push(defect.coordinates_y);
        acc[key].pointsCount += 1;
        
        return acc;
      }, {}));

      // Step 1: Create inspection with normalized color
      const inspection = await createInspection({
        lot: lot,
        style: styleInput,
        size: sizeInput,
        color: colorInput.toLowerCase().replace(/ /g, '_'),
      });

      // Step 2: Send each grouped defect to the API
      for (const group of groupedDefects) {
        // Normalize defect type: convert underscores to spaces to match backend DefectType names
        const normalizedDefectType = group.defectType.replace(/_/g, ' ');
        
        await createDefect({
          inspection: inspection.id,
          defect_type: normalizedDefectType,
          defect_size: group.defectSize || '',
          coordinates_x: group.coordinates_x,
          coordinates_y: group.coordinates_y,
          defect_count: group.pointsCount,
        });
      }

      // Step 3: Close inspection and sync to QualityQcFa
      const result = await closeInspection(inspection.id);

      // Step 4: Show result based on sync status
      if (result.quality_data_sync && result.quality_data_sync.status === 'synced') {
        const message = result.result === 'PASS' 
          ? `Inspection PASSED!\n\nDefects found: ${result.total_defects}`
          : `Inspection REJECTED!\n\nDefects found: ${result.total_defects}`;
        alert(message);
      } else if (result.quality_data_sync && result.quality_data_sync.status === 'no_match') {
        alert(`Inspection ${result.result} but no matching QC record found.\nDefects captured: ${result.total_defects}`);
      } else {
        alert(`Inspection ${result.result}\nDefects: ${result.total_defects}`);
      }

      // Clear UI for next inspection
      setLastSubmission(currentDefects);
      setCurrentDefects([]);
      setIsEditMode(false);
      setViewSide('front');
      setSyncState('success');

    } catch (error) {
      console.error("Error saving to DB:", error);
      alert(`Error saving data: ${error.message}`);
      setSyncState('error');
    }
  };

  if (step === 'selection') {
    return (
      <div className="capture-view">
        <div className="capture-header">
          <h2 className="section-title">Capture Setup</h2>
        </div>

        <div className="card capture-setup-card">
          
          <div className="input-group spacing-normal">
            <label className="input-label">Lot Number</label>
            <input 
              type="text" 
              className="popover-input"
              placeholder="e.g. L-90210"
              value={lot} 
              onChange={(e) => setLot(e.target.value)} 
            />
          </div>

          <div className="input-group spacing-normal">
            <label className="input-label">Garment Shape (SVG)</label>
            <select className="input-field" value={garment} onChange={(e) => setGarment(e.target.value)}>
              <option value="">Choose shape...</option>
              {MOCK_GARMENTS.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </div>

          <div className="input-group spacing-normal">
            <label className="input-label">Style</label>
            <input 
              type="text" 
              className="popover-input" 
              placeholder="e.g. Slim Fit, V-Neck"
              value={styleInput} 
              onChange={(e) => setStyleInput(e.target.value)} 
            />
          </div>

          <div className="input-group spacing-normal">
            <label className="input-label">Size</label>
            <input 
              type="text" 
              className="popover-input" 
              placeholder="e.g. M, 32, XL"
              value={sizeInput} 
              onChange={(e) => setSizeInput(e.target.value)} 
            />
          </div>

          <div className="input-group spacing-large">
            <label className="input-label">Color</label>
            <input 
              type="text" 
              className="popover-input" 
              placeholder="e.g. Navy Blue, Red"
              value={colorInput} 
              onChange={(e) => setColorInput(e.target.value)} 
            />
          </div>

          <button className="ingesta-btn ingesta-btn-primary btn-full" onClick={handleStartCapture}>
            Start Inspection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="capture-view">
      
      <div className="capture-header-flex">
        <div>
          <h2 className="section-title title-tight">Quality Control</h2>
          <p className="capture-subtitle">
            Inspecting: <span>Lot {lot} | {styleInput} | Size {sizeInput} | {colorInput}</span>
          </p>
        </div>
        <button className="ingesta-btn ingesta-btn-outline" onClick={() => { 
          setStep('selection'); 
          setIsEditMode(false); 
          handleClosePopover();
          // Clear inspection-specific state
          setCurrentDefects([]);
          setLastSubmission(null);
          setLot('');
          setStyleInput('');
          setSizeInput('');
          setColorInput('');
          setGarment('');
          setSyncState('idle');
        }}>
          Back to Setup
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
            disabled={isEditMode || isPopoverOpen || currentDefects.length === 0 || syncState === 'sending'}
          >
            {syncState === 'sending' ? 'Sending...' : 'Send'}
          </button>
        </div>

      </div>
      
    </div>
  );
}