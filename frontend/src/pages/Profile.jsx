import { useState, useEffect } from 'react';
import { UserCircle, Briefcase, IndianRupee } from 'lucide-react';
import api from '../services/api';

export default function Profile({ user }) {
  const [job, setJob] = useState('');
  const [baseIncome, setBaseIncome] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchProfile();
  }, [user]);

  const fetchProfile = async () => {
    try {
      const res = await api.getProfile(user);
      setJob(res.data.job);
      setBaseIncome(res.data.base_income);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      const incomeValue = baseIncome ? parseFloat(baseIncome) : 0;
      await api.updateProfile(user, { job, base_income: incomeValue });
      setMessage('Profile completely updated!');
    } catch (err) {
      setMessage('Failed to update profile.');
    }
    setSaving(false);
  };

  if (loading) return <div className="p-8 text-center animate-pulse text-accent-neon">Loading Profile...</div>;

  return (
    <div className="space-y-6 animate-[fadeIn_0.3s_ease-out]">
      <div className="glass-panel p-8 max-w-2xl">
        <h2 className="text-2xl font-bold mb-8 flex items-center">
          <UserCircle className="w-6 h-6 mr-3 text-accent-neon" />
          Financial Profile
        </h2>
        
        {message && (
          <div className="mb-6 p-4 rounded-xl bg-accent-green/10 border border-accent-green/50 text-accent-green">
            {message}
          </div>
        )}

        <form onSubmit={handleUpdate} className="space-y-6">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1 ml-1 flex items-center">
                 <Briefcase className="w-4 h-4 mr-2" /> Current Job Title
              </label>
              <input 
                type="text" 
                className="input-field" 
                value={job}
                onChange={e => setJob(e.target.value)}
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1 ml-1 flex items-center">
                 <IndianRupee className="w-4 h-4 mr-2" /> Base Monthly Income (₹)
              </label>
              <input 
                type="number" 
                className="input-field" 
                value={baseIncome}
                onChange={e => setBaseIncome(e.target.value)}
                required
              />
              <p className="text-xs text-gray-500 mt-2 ml-1">The AI Smart Budget is hard-locked to calculate your financial goals using this baseline income.</p>
            </div>
          </div>
          
          <button 
             type="submit" 
             disabled={saving}
             className="btn-primary py-3 px-6 mt-4 w-full md:w-auto"
          >
             {saving ? 'Updating...' : 'Save Changes'}
          </button>
        </form>
      </div>
    </div>
  );
}
