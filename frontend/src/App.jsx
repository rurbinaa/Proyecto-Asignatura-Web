import './App.css';
import Sidebar from './Components/Sidebar.jsx';
import Navbar from './Components/Navbar.jsx';
import CaptureView from './views/captureView';

function App() {
  return (
    <div className="app-layout">
      
      <Sidebar />

      <div className="main-wrapper">
    
        <Navbar />

        <main className="content-area">
          <CaptureView />
        </main>

      </div>
      
    </div>
  );
}

export default App;