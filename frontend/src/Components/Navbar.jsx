import { User } from 'lucide-react';
import './Navbar.css';

export default function Navbar({ user }) {
  return (
    <header className="navbar">
      <div className="navbar-user">
        <span className="navbar-email">{user?.email || 'Usuario'}</span>
        <User className="navbar-user-icon" />
      </div>
    </header>
  );
}