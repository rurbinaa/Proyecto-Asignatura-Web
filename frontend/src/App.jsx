import { useState } from 'react';
import urlShirt from './assets/shirt.svg';
import MockupContainer from './Components/mockupContainer.jsx';

function App() {
  
  const [currentDefects, setCurrentDefects] = useState([]);
  const handleDefectsUpdate = (updateMarkes) => {
    setCurrentDefects(updateMarkes);

    console.log('Updated defects:', updateMarkes);
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width:'100vw', minHeight:'60vh', padding:'20px' }}>
      
      <MockupContainer 
        garmentUrl={urlShirt} 
        onMarkersChange={handleDefectsUpdate} 
      />
      
    </div>
  );
}

export default App;