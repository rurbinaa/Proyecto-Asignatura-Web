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
            title="Collapse menu"
          >
            <ChevronLeft className="sidebar-nav-icon" />
          </button>
        )}
      </div>
      
      <nav className="sidebar-nav">
          
          {userRole === 'operator' && (
            <button 
              className={`sidebar-nav-item ${activeView === 'capture' ? 'active' : ''}`} 
              title={isCollapsed ? "Touch Capture" : ""}
              onClick={() => setActiveView('capture')}
            >
              <Hand className="sidebar-nav-icon" />
              {!isCollapsed && <span>Touch Capture</span>}
            </button>
          )}

          {userRole === 'manager' && (
            <button 
              className={`sidebar-nav-item ${activeView === 'excel' ? 'active' : ''}`} 
              title={isCollapsed ? "Import Batches" : ""}
              onClick={() => setActiveView('excel')}
            >
              <Database className="sidebar-nav-icon" />
              {!isCollapsed && <span>Import Batches</span>}
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