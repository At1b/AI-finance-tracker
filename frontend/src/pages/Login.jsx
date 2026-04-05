import { useState } from 'react';
import { Wallet, Fingerprint } from 'lucide-react';
import api from '../services/api';

export default function Login({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      if (isLogin) {
        const res = await api.login(username, password);
        onLogin(res.data.username);
      } else {
        await api.register(username, password);
        const res = await api.login(username, password);
        onLogin(res.data.username);
      }
    } catch (err) {
      setError(err.response?.data?.error || "Connection error. Is backend running?");
    }
    setLoading(false);
  };

  return (
    <div className="flex items-center justify-center min-h-screen p-4 overflow-hidden relative">
      {/* Decorative Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent-neon/20 rounded-full blur-[120px] mix-blend-screen pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-purple/20 rounded-full blur-[100px] mix-blend-screen pointer-events-none" />

      <div className="glass-panel w-full max-w-md p-8 relative z-10 animate-[fadeIn_0.5s_ease-out]">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-navy-900 rounded-2xl border border-accent-neon flex items-center justify-center mb-4 shadow-[0_0_15px_rgba(100,255,218,0.3)]">
            <Wallet className="w-8 h-8 text-accent-neon" />
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-accent-neon to-accent-blue bg-clip-text text-transparent">
            BudgetMate
          </h1>
          <p className="text-gray-400 mt-2 text-sm text-center">AI-Powered Financial Intelligence</p>
        </div>

        {error && (
          <div className="bg-accent-red/10 border border-accent-red/50 text-accent-red p-3 rounded-xl mb-6 text-sm text-center animate-pulse">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1 ml-1">Username</label>
            <input 
              type="text" 
              required
              className="input-field" 
              placeholder="pete_the_saver"
              value={username}
              onChange={e => setUsername(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1 ml-1">Password</label>
            <div className="relative">
              <input 
                type="password" 
                required
                className="input-field pr-12" 
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
              <Fingerprint className="absolute right-4 top-3.5 w-5 h-5 text-gray-500" />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="btn-primary w-full py-3.5 mt-4 text-lg"
          >
            {loading ? "Authenticating..." : (isLogin ? "Secure Login" : "Create Account")}
          </button>
        </form>

        <div className="mt-8 text-center">
          <button 
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            className="text-sm text-gray-400 hover:text-accent-neon transition-colors"
          >
            {isLogin ? "New here? " : "Already tracking? "}
            <span className="font-semibold">{isLogin ? "Create an account" : "Sign in instead"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
