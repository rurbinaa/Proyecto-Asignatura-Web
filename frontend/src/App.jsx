import urlShirt from './assets/shirt.svg';
import MockupContainer from './Components/mockupContainer.jsx';

function App() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width:'100vw', minHeight:'60vh', padding:'20px' }}>
      
      <MockupContainer garmentUrl={urlShirt} />
      
    </div>
  );
}

export default App;