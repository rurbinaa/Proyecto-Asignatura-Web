import { Factory, Hand, LogOut } from 'lucide-react';

export default function Sidebar() {
  return (
    <aside className="sidebar"> 
    
      <div className="sidebar-logo">
        <Factory className="sidebar-logo-icon" />
        <span className="sidebar-logo-text">Rift Analytics</span>
      </div>
      
      <nav className="sidebar-nav">
          <button className="sidebar-nav-item active">
            <Hand className="sidebar-nav-icon" />
            <span>Captura Táctil</span>
          </button>
      </nav>

      <button className="sidebar-logout">
        <LogOut className="sidebar-nav-icon" />
        <span>Cerrar Sesión</span>
      </button>        


    </aside>
  );
}