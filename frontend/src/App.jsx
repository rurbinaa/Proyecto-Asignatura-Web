import { useState, useEffect } from 'react';
import './App.css';
import Sidebar from './Components/Sidebar.jsx';
import Navbar from './Components/Navbar.jsx';
import LoginView from './views/LoginView.jsx';
import ExcelUploader from './Components/ExcelUploader.jsx';
import DashboardView from './views/DashboardView.jsx';
import faviconUrl from './assets/RA-ICON_embed.svg?url';

import { AuthProvider } from './contexts/AuthContext.jsx'; 
import { useAuth } from './contexts/useAuth';

function AppContent() {
  const { user, loading, isAuthenticated, logout } = useAuth(); 

  const [activeView, setActiveView] = useState(() => {
    try {
      const stored = localStorage.getItem('rift-activeView');
      return stored === 'excel' || stored === 'dashboard' ? stored : '';
    } catch {
      return '';
    }
  });
  
  const [volatileData, setVolatileData] = useState(null);
  const [volatileFile, setVolatileFile] = useState(null);
  const defaultView = 'excel';
  const resolvedActiveView = activeView || (isAuthenticated && user ? defaultView : '');

  useEffect(() => {
    if (isAuthenticated && user) {
      const storedView = localStorage.getItem('rift-activeView');
      if (!storedView) {
        localStorage.setItem('rift-activeView', defaultView);
      }
    }
  }, [defaultView, isAuthenticated, user]);

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
          activeView={resolvedActiveView} 
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
          
          {resolvedActiveView === 'excel' && (
            <div className="card excel-view-card">
              <h2 className="section-title title-tight">Importation of batches (Excel)</h2>
              <p className="excel-subtitle">
                Drag your file to ingest multiple records into the system.
              </p>
              <ExcelUploader onVolatileDashboard={handleVolatileDashboard} />
            </div>
          )}

          {resolvedActiveView === 'dashboard' && (
            <DashboardView volatileData={volatileData} volatileFile={volatileFile} />
          )}

        </main>
      </div>
      
    </div>
  );
}

export default function App() {
  useEffect(() => {
    const link = document.querySelector("link[rel*='icon']") || document.createElement('link');
    link.rel = 'icon';
    link.href = faviconUrl;
    if (!link.parentNode) document.head.appendChild(link);
  }, []);

  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
