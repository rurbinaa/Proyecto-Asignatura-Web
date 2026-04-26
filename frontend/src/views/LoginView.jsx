import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import RA_ICON from '../assets/RA-ICON_embed.svg';
import './LoginView.css';

export default function LoginView() {
  const { login } = useAuth(); 
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      const success = await login({ email, password });
      
      if (!success) {
        setError('Invalid credentials or server error.');
      }
    } catch (err) {
      setError('Connection error. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <img src={RA_ICON} alt="Rift Analytics Logo" className="login-logo-img" />
          <h2 className="login-title">Rift Analytics <span className="login-subtitle">for</span></h2>
          <p className="login-company">Uniwell Apparel</p>
          <p className="login-credentials">Enter your credentials</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="input-group">
            <label className="input-label">Email</label>
            <input 
              type="email" 
              className="input-field" 
              placeholder="e.g. manager@uniwell.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="input-group">
            <label className="input-label">Password</label>
            <input 
              type="password" 
              className="input-field" 
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && <p className="error-text">{error}</p>}

          <button type="submit" className="login-button" disabled={isLoading}>
            {isLoading ? 'Authenticating...' : 'Log In'}
          </button>
        </form>
      </div>
    </div>
  );
}
