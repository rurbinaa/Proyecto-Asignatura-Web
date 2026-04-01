import { useState } from 'react';
import './Sidebar.css';
import { Factory, Hand, LogOut, ChevronLeft, ChevronRight } from 'lucide-react';

export default function Sidebar() {
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
          <button className="sidebar-nav-item active" title={isCollapsed ? "Captura Táctil" : ""}>
            <Hand className="sidebar-nav-icon" />
            {!isCollapsed && <span>Captura Táctil</span>}
          </button>
      </nav>

      {!isCollapsed ? (
        <button className="sidebar-logout">
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