import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

function App() {
  const [user, setUser] = useState(localStorage.getItem('username') || null);

  const handleLogin = (username) => {
    localStorage.setItem('username', username);
    setUser(username);
  };

  const handleLogout = () => {
    localStorage.removeItem('username');
    setUser(null);
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-navy-900 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-navy-800 via-navy-900 to-[#020617] text-white">
        <Routes>
          <Route path="/login" element={!user ? <Login onLogin={handleLogin} /> : <Navigate to="/" />} />
          <Route path="/*" element={user ? <Dashboard user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
