import { useState, useEffect } from 'react';
import './App.css';
import Sidebar from './Components/Sidebar.jsx';
import Navbar from './Components/Navbar.jsx';
import CaptureView from './views/CaptureView.jsx';
import LoginView from './views/LoginView.jsx';
import ExcelUploader from './Components/ExcelUploader.jsx';
import DashboardView from './views/DashboardView.jsx';

import { AuthProvider, useAuth } from './contexts/AuthContext.jsx'; 

function AppContent() {
  const { user, loading, isAuthenticated, logout } = useAuth(); 

  const [activeView, setActiveView] = useState(() => {
    try {
      const stored = localStorage.getItem('rift-activeView');
      return stored || '';
    } catch {
      return '';
    }
  });
  
  const [volatileData, setVolatileData] = useState(null);
  const [volatileFile, setVolatileFile] = useState(null);

  useEffect(() => {
    if (isAuthenticated && user) {
      const storedView = localStorage.getItem('rift-activeView');
      if (!storedView) {
        const defaultView = user.role === 'manager' ? 'excel' : 'capture';
        setActiveView(defaultView);
        localStorage.setItem('rift-activeView', defaultView);
      }
    }
  }, [isAuthenticated, user]);

  const handleVolatileDashboard = (file) => {
    setVolatileFile(file);
    setActiveView('dashboard');
  };

  const handleLogout = async () => {
    await logout();
    localStorage.removeItem('rift-activeView');
    setActiveView('');
  };

  if (loading) {
    return <div className="app-loading">Verificando sesión...</div>;
  }

  if (!isAuthenticated || !user) {
    return <LoginView />;
  }

  return (
    <div className="app-layout">
      
      <Sidebar 
        userRole={user.role} 
        activeView={activeView} 
        setActiveView={(view) => {
          setActiveView(view);
          localStorage.setItem('rift-activeView', view);
        }} 
        setVolatileData={setVolatileData}
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
              <ExcelUploader onVolatileDashboard={handleVolatileDashboard} />
            </div>
          )}

          {activeView === 'dashboard' && (
            <DashboardView volatileData={volatileData} volatileFile={volatileFile} />
          )}

        </main>
      </div>
      
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}