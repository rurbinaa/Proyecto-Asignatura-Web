import { useState } from 'react';
import './Sidebar.css';
import { Database, LogOut, ChevronLeft, ChevronRight, ChartBar, FileText } from 'lucide-react';
import RA_ICON from '../assets/RA-ICON_embed.svg';

export default function Sidebar({ userRole, activeView, setActiveView, setVolatileData = () => {}, onLogout }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}> 
    
      <div className="sidebar-logo">
        <img src={RA_ICON} alt="Rift Analytics" className="sidebar-logo-img" />
        
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

          {userRole === 'manager' && (
            <button 
              className={`sidebar-nav-item ${activeView === 'dashboard' ? 'active' : ''}`} 
              title={isCollapsed ? "Dashboard" : ""}
              onClick={() => { setActiveView('dashboard'); setVolatileData?.(null); }}
            >
              <ChartBar className="sidebar-nav-icon" />
              {!isCollapsed && <span>Dashboard</span>}
            </button>
          )}

          {userRole === 'manager' && (
            <button 
              className={`sidebar-nav-item ${activeView === 'reports' ? 'active' : ''}`} 
              title={isCollapsed ? "Quality Reports" : ""}
              onClick={() => setActiveView('reports')}
            >
              <FileText className="sidebar-nav-icon" />
              {!isCollapsed && <span>Quality Reports</span>}
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
          title="Expand menu"
        >
          <ChevronRight className="sidebar-nav-icon" />
        </button>
      )}

    </aside>
  );
}
