import { useState, useEffect } from 'react';
import { Target, AlertTriangle } from 'lucide-react';
import api from '../services/api';

export default function SmartBudget({ user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState('');

  useEffect(() => {
    fetchData();
  }, [user, selectedMonth]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await api.getBudget(user, selectedMonth);
      setData(res.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  if (loading && !data) return <div className="text-center py-20 animate-pulse text-accent-neon">Loading Budgets...</div>;
  if (data?.error) return <div className="text-center py-20 text-gray-400">{data.error}</div>;

  return (
    <div className="space-y-6 animate-[fadeIn_0.3s_ease-out]">
      <div className="glass-panel p-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold mb-2 flex items-center">
              <Target className="w-6 h-6 mr-3 text-accent-neon" />
              50/30/20 Smart Budget
            </h2>
            <p className="text-gray-400">Automatically calculated using the 50/30/20 rule based on your total income: ₹{data.avg_monthly_income?.toLocaleString()}</p>
          </div>
          <div className="mt-4 md:mt-0 shrink-0">
            <input 
              type="month" 
              className="bg-navy-900 border border-navy-700 text-white px-4 py-2 rounded-xl focus:border-accent-neon focus:ring-1 focus:ring-accent-neon outline-none cursor-pointer"
              value={selectedMonth || data?.current_month || ''}
              onChange={(e) => setSelectedMonth(e.target.value)}
            />
          </div>
        </div>
        
        <div className="space-y-6">
          {Object.entries(data.category_budgets || {}).map(([cat, info]) => {
             const progress = info.usage_pct;
             const color = info.status === 'Over Budget' ? 'bg-accent-red' : info.status === 'Near Limit' ? 'bg-accent-yellow' : 'bg-accent-green';
             
             return (
               <div key={cat} className="p-4 rounded-xl bg-navy-900 border border-navy-700 hover:border-accent-neon/30 transition-colors">
                  <div className="flex justify-between items-end mb-2">
                     <div>
                        <h4 className="font-bold text-lg">{cat}</h4>
                        <span className="text-xs px-2 py-1 bg-navy-800 rounded-md text-gray-400">{info.category_type}</span>
                     </div>
                     <div className="text-right">
                        <div className="text-xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                           ₹{info.current_spent.toLocaleString()} <span className="text-sm font-normal text-gray-500">/ ₹{info.suggested_budget.toLocaleString()}</span>
                        </div>
                        <span className={`text-xs font-semibold ${info.status === 'Over Budget' ? 'text-accent-red' : info.status === 'Near Limit' ? 'text-accent-yellow' : 'text-accent-green'}`}>
                           {info.status}
                        </span>
                     </div>
                  </div>
                  
                  <div className="w-full h-3 rounded-full bg-navy-800 mt-3 overflow-hidden">
                     <div className={`h-full rounded-full ${color} transition-all duration-1000`} style={{ width: `${Math.min(progress, 100)}%` }} />
                  </div>
               </div>
             )
          })}
        </div>
      </div>
    </div>
  );
}
