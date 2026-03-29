import { useState } from 'react';
import urlShirt from '../assets/shirt.svg';
import MockupContainer from '../Components/mockupContainer.jsx';

function CaptureView() {
  
  const [currentDefects, setCurrentDefects] = useState([]);
  const handleDefectsUpdate = (updateMarkes) => {
    setCurrentDefects(updateMarkes);
    console.log('Updated defects:', updateMarkes);
  };

  return (
    <div stile={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width:'100vw', minHeight:'60vh', padding:'20px' }}>
      
      <MockupContainer 
        garmentUrl={urlShirt} 
        onMarkersChange={handleDefectsUpdate} 
      />
      
    </div>
  );
}

export default CaptureView;