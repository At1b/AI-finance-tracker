import { useState, useEffect } from 'react';
import { Bell, AlertOctagon, AlertTriangle, Info } from 'lucide-react';
import api from '../services/api';

export default function Alerts({ user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      const res = await api.getAlerts(user);
      setData(res.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  if (loading) return <div className="text-center py-20 animate-pulse text-accent-neon">Scanning transactions...</div>;
  if (!data?.active_alerts) return <div className="text-center py-20">No alerts available</div>;

  const { health_score, active_alerts } = data;
  
  const getSeverityIcon = (sec) => {
     if (sec === 'CRITICAL') return <AlertOctagon className="w-6 h-6 text-accent-red" />;
     if (sec === 'HIGH') return <AlertTriangle className="w-6 h-6 text-accent-yellow" />;
     return <Info className="w-6 h-6 text-accent-blue" />;
  }

  return (
    <div className="space-y-6 animate-[fadeIn_0.3s_ease-out]">
      <div className="glass-panel p-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold flex items-center">
            <Bell className="w-6 h-6 mr-3 text-accent-neon" />
            Active Alerts
          </h2>
          <div className="px-4 py-2 rounded-xl bg-navy-900 border border-navy-700 flex items-center shrink-0">
             <span className="text-gray-400 mr-2">Health Score</span>
             <span className={`text-xl font-bold ${health_score > 70 ? 'text-accent-green' : health_score > 40 ? 'text-accent-yellow' : 'text-accent-red'}`}>
                {health_score}/100
             </span>
          </div>
        </div>

        {active_alerts.length === 0 ? (
          <div className="text-center py-12 px-6 border border-dashed border-navy-700 bg-navy-900/50 rounded-2xl">
             <div className="w-16 h-16 bg-accent-green/10 rounded-full flex items-center justify-center mx-auto mb-4 text-accent-green">
                <CheckCircle2 className="w-8 h-8" />
             </div>
             <h3 className="text-xl font-bold text-white mb-2">All Clear!</h3>
             <p className="text-gray-400">Your financial health is looking perfect. No alerts triggered.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
             {active_alerts.map((alert, i) => (
               <div key={i} className="flex space-x-4 p-5 rounded-2xl bg-navy-900 border border-navy-700 hover:border-accent-neon/30 transition-all hover:-translate-y-1">
                  <div className="mt-1">{getSeverityIcon(alert.severity)}</div>
                  <div>
                     <div className="flex items-center space-x-2 mb-1">
                        <span className={`text-xs px-2 py-0.5 rounded font-bold ${
                           alert.severity === 'CRITICAL' ? 'bg-accent-red/20 text-accent-red' : 
                           alert.severity === 'HIGH' ? 'bg-accent-yellow/20 text-accent-yellow' : 'bg-accent-blue/20 text-accent-blue'
                        }`}>{alert.severity}</span>
                        <h4 className="font-bold text-white">{alert.type}</h4>
                     </div>
                     <p className="text-gray-400 text-sm mt-2">{alert.message}</p>
                  </div>
               </div>
             ))}
          </div>
        )}
      </div>
    </div>
  );
}
