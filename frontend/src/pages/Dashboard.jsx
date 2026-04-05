import { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  BarChart3, 
  BrainCircuit, 
  Wallet, 
  BellRing, 
  LogOut, 
  PlusCircle,
  LayoutDashboard
} from 'lucide-react';
import api from '../services/api';

import Overview from './Overview';
import AiForecast from './AiForecast';
import SmartBudget from './SmartBudget';
import Alerts from './Alerts';
import AddTransaction from './AddTransaction';

export default function Dashboard({ user, onLogout }) {
  const location = useLocation();

  const navLinks = [
    { path: "/", label: "Overview", icon: LayoutDashboard },
    { path: "/add", label: "New Transaction", icon: PlusCircle },
    { path: "/analysis", label: "Spending Analysis", icon: BarChart3 },
    { path: "/forecast", label: "AI Forecast", icon: BrainCircuit },
    { path: "/budget", label: "Smart Budget", icon: Wallet },
    { path: "/alerts", label: "Alerts", icon: BellRing },
  ];

  return (
    <div className="flex h-screen overflow-hidden text-gray-100">
      
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-navy-800 border-r border-navy-700 flex flex-col justify-between z-20 shadow-2xl relative">
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-10">
            <div className="w-10 h-10 bg-navy-900 rounded-xl border border-accent-neon flex items-center justify-center">
              <LogOut className="w-5 h-5 text-accent-neon transform -scale-x-100 rotate-180 opacity-0 absolute" />
              <Wallet className="w-5 h-5 text-accent-neon" />
            </div>
            <h1 className="text-xl font-bold text-white tracking-wider">Budget<span className="text-accent-neon">Mate</span>.</h1>
          </div>

          <nav className="space-y-2">
            {navLinks.map((link) => {
              const active = location.pathname === link.path;
              const Icon = link.icon;
              return (
                <Link 
                  key={link.path} 
                  to={link.path}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                    active 
                      ? 'bg-accent-neon/10 text-accent-neon border border-accent-neon/20 shadow-[inset_0_0_10px_rgba(100,255,218,0.1)]' 
                      : 'text-gray-400 hover:bg-navy-700/50 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{link.label}</span>
                  {link.path === '/alerts' && (
                    <span className="ml-auto flex h-2 w-2 rounded-full bg-accent-red animate-ping" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="p-6 border-t border-navy-700">
          <div className="flex items-center space-x-3 px-4 py-3 bg-navy-900/50 rounded-xl mb-4 border border-navy-700">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-accent-neon to-accent-blue flex items-center justify-center text-navy-900 font-bold">
              {user.charAt(0).toUpperCase()}
            </div>
            <span className="font-medium truncate">{user}</span>
          </div>
          <button 
            onClick={onLogout}
            className="flex items-center space-x-3 px-4 py-2 w-full text-gray-400 hover:text-accent-red transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative overflow-y-auto">
        {/* Background glow effects for aesthetic UI */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent-blue/5 rounded-full blur-[150px] mix-blend-screen pointer-events-none" />
        
        <header className="px-10 py-6 flex justify-between items-center sticky top-0 z-10 backdrop-blur-md bg-navy-900/60 border-b border-navy-800/50">
           <h2 className="text-2xl font-semibold capitalize">
              {navLinks.find(l => l.path === location.pathname)?.label || 'Dashboard'}
           </h2>
        </header>

        <div className="p-10 relative z-0">
          <Routes>
            <Route path="/" element={<Overview user={user} />} />
            <Route path="/analysis" element={<Overview user={user} />} />
            <Route path="/forecast" element={<AiForecast user={user} />} />
            <Route path="/budget" element={<SmartBudget user={user} />} />
            <Route path="/alerts" element={<Alerts user={user} />} />
            <Route path="/add" element={<AddTransaction user={user} />} />
          </Routes>
        </div>
      </main>

    </div>
  );
}
