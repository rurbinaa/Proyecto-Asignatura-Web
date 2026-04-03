import { useState } from 'react';
import './Sidebar.css';
import { Factory, Hand, Database, LogOut, ChevronLeft, ChevronRight } from 'lucide-react';

export default function Sidebar({ userRole, activeView, setActiveView, onLogout }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}> 
    
      <div className="sidebar-logo">
        <Factory className="sidebar-logo-icon" />
        
        {!isCollapsed && <span className="sidebar-logo-text">Rift Analytics</span>}
        
        {!isCollapsed && (
          <button 
            className="sidebar-toggle top-toggle" 
            onClick={() => setIsCollapsed(true)}
            title="Colapsar menú"
          >
            <ChevronLeft className="sidebar-nav-icon" />
          </button>
        )}
      </div>
      
      <nav className="sidebar-nav">
          
          {userRole === 'operator' && (
            <button 
              className={`sidebar-nav-item ${activeView === 'capture' ? 'active' : ''}`} 
              title={isCollapsed ? "Captura Táctil" : ""}
              onClick={() => setActiveView('capture')}
            >
              <Hand className="sidebar-nav-icon" />
              {!isCollapsed && <span>Captura Táctil</span>}
            </button>
          )}

          {userRole === 'manager' && (
            <button 
              className={`sidebar-nav-item ${activeView === 'excel' ? 'active' : ''}`} 
              title={isCollapsed ? "Importar Lotes" : ""}
              onClick={() => setActiveView('excel')}
            >
              <Database className="sidebar-nav-icon" />
              {!isCollapsed && <span>Importar Lotes</span>}
            </button>
          )}
          
      </nav>

      {!isCollapsed ? (
        <button className="sidebar-logout" onClick={onLogout}>
          <LogOut className="sidebar-nav-icon" />
          <span>Log Out</span>
        </button>
      ) : (
        <button 
          className="sidebar-toggle bottom-toggle" 
          onClick={() => setIsCollapsed(false)}
          title="Ampliar menú"
        >
          <ChevronRight className="sidebar-nav-icon" />
        </button>
      )}

    </aside>
  );
}