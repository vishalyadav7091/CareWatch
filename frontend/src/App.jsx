import React, { useState } from 'react';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import { authService } from './services/api';

export default function App() {
  const [user, setUser] = useState(() => authService.getCurrentUser());

  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
  };

  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return <Dashboard user={user} onLogout={handleLogout} />;
}
