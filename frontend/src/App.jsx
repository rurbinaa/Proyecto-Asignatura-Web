import { useState, useEffect } from 'react';
import './App.css';
import Sidebar from './Components/Sidebar.jsx';
import Navbar from './Components/Navbar.jsx';
import CaptureView from './views/CaptureView.jsx';
import LoginView from './views/LoginView.jsx';
import ExcelUploader from './Components/ExcelUploader.jsx';

const STORAGE_KEY = 'rift-user';

function App() {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }); 
  const [activeView, setActiveView] = useState(() => {
    try {
      const stored = localStorage.getItem('rift-activeView');
      return stored || '';
    } catch {
      return '';
    }
  });

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
    setActiveView(userData.role === 'manager' ? 'excel' : 'capture');
    localStorage.setItem('rift-activeView', userData.role === 'manager' ? 'excel' : 'capture');
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem('rift-activeView');
    setActiveView('');
  };

  if (!user) {
    return <LoginView onLogin={handleLogin} />;
  }

  return (
    <div className="app-layout">
      
      <Sidebar 
        userRole={user.role} 
        activeView={activeView} 
        setActiveView={setActiveView} 
        onLogout={handleLogout} 
      />

      <div className="main-wrapper">
        <Navbar user={user} />

        <main className="content-area">
          
          {activeView === 'capture' && user.role === 'operator' && <CaptureView />}

          {activeView === 'excel' && user.role === 'manager' && (
            <div className="card excel-view-card">
              <h2 className="section-title title-tight">Importation of batches (Excel)</h2>
              <p className="excel-subtitle">
                Drag your file to ingest multiple records into the system.
              </p>
              <ExcelUploader />
            </div>
          )}

        </main>
      </div>
      
    </div>
  );
}

export default App;