import { User } from 'lucide-react';

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-user">
        <span className="navbar-email">operario@uniwell.com</span>
        <User className="navbar-user-icon" />
      </div>
    </header>
  );
}