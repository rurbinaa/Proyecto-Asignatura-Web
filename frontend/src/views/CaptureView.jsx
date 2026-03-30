import { useState } from 'react';
import urlShirt from '../assets/shirt.svg'; 
import MockupContainer from '../Components/mockupContainer.jsx'; 
import DefectPopover from '../Components/DefectPopover.jsx'; 

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
  
  // Operario toco la camisa -> capturamos coords y abrimos menú
  const handleDefectPlacePending = (coords) => {
    setPendingCoords(coords);
    setIsPopoverOpen(true); // Se desbloquea tras el toque
  };

  // Operario cancelo el menu Popover
  const handleClosePopover = () => {
    setIsPopoverOpen(false);
    setPendingCoords(null);
  };

  // Operario guardo en el Popover -> unimos todo y guardamos en la lista principal
  const handleSaveDefectFromPopover = (finalizedDefect) => {
    setCurrentDefects(prev => [...prev, finalizedDefect]);
    setIsPopoverOpen(false);
    setPendingCoords(null);
  };

  // Operario borro un defecto confirmado (en modo edicion)
  const handleRemoveConfirmedMarker = (idToRemove) => {
    setCurrentDefects(prev => prev.filter(defect => defect.id !== idToRemove));
  };

  const handleSaveToDB = async () => {
    if (isEditMode || isPopoverOpen) {
      alert("Please finalize defect selection or exit edit mode before saving.");
      return;
    }

    const payload = { 
      lot_id: lot, 
      garment_type: garment, 
      defects: currentDefects
    };
    
    console.log("Payload ready for Backend:", payload);

    try {

      alert(`Simulation Success! Sent ${currentDefects.length} detailed defects to DB.`);
      
      setStep('selection');
      setCurrentDefects([]);
      setLot('');
      setGarment('');
      setIsEditMode(false);

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

        <div className="card" style={{ maxWidth: '500px', margin: '0 auto', width: '100%' }}>
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
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 className="section-title" style={{ marginBottom: '4px' }}>Quality Control</h2>
          <p style={{ color: '#606D80', fontSize: '14px', fontWeight: '500' }}>
            Inspecting: <span style={{ color: '#567EBB' }}>{lot} ({garment})</span>
          </p>
        </div>
        <button className="ingesta-btn ingesta-btn-outline" onClick={() => { setStep('selection'); setIsEditMode(false); handleClosePopover(); }} style={{ cursor: 'pointer' }}>
          Cancel / Back
        </button>
      </div>

      <div className="card garment-area" style={{ position: 'relative', display: 'flex', flexDirection: 'column' }}>
        
        <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px', padding: '0 20px' }}>
          <span style={{ fontSize: '14px', color: isEditMode ? '#ef4444' : '#606D80', fontWeight: isEditMode ? 'bold' : 'normal' }}>
            {isEditMode ? 'Delete Mode Active. Tap a marker to remove it.' : 'Tap the garment to identify a defect.'}
          </span>
          
          <button onClick={() => setIsEditMode(!isEditMode)} className="ingesta-btn" style={{ backgroundColor: isEditMode ? '#ef4444' : 'transparent', color: isEditMode ? 'white' : '#ef4444', border: '1px solid #ef4444', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>
            {isEditMode ? '✓ Done' : '✏️ Edit / Delete'}
          </button>
        </div>

        <div className="garment-container" style={{ position: 'relative' }}>
          
          <MockupContainer 
            garmentUrl={urlShirt} 
            confirmedMarkers={currentDefects}
            isEditMode={isEditMode} 
            onDefectPlacePending={handleDefectPlacePending}
            onRemoveConfirmedMarker={handleRemoveConfirmedMarker}
          />

          {isPopoverOpen && pendingCoords && (
            <DefectPopover 
              coordinates={pendingCoords}
              onClose={handleClosePopover}
              onSave={handleSaveDefectFromPopover}
            />
          )}

        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
        <button className="ingesta-btn ingesta-btn-primary" style={{ padding: '16px 32px', fontSize: '16px', opacity: (isEditMode || isPopoverOpen) ? 0.5 : 1, cursor: (isEditMode || isPopoverOpen) ? 'not-allowed' : 'pointer' }} onClick={handleSaveToDB} disabled={isEditMode || isPopoverOpen}>
          Save Record to DB ({currentDefects.length} detailed defects)
        </button>
      </div>
      
    </div>
  );
}