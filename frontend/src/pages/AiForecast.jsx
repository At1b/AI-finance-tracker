import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ComposedChart } from 'recharts';
import { TrendingUp, Sparkles } from 'lucide-react';
import api from '../services/api';

export default function AiForecast({ user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      const res = await api.getForecast(user);
      setData(res.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  if (loading) return <div className="text-center py-20 animate-pulse text-accent-neon">Loading AI Models...</div>;
  if (!data?.prediction || data.prediction.error) return <div className="text-center py-20 text-gray-400">Need more data to generate forecast (minimum 2 months).</div>;

  const { prediction, history } = data;
  
  // Transform data for recharts
  const chartData = [];
  const sortedMonths = Object.keys(history.monthly_expenses).sort();
  sortedMonths.forEach(m => {
    chartData.push({ month: m, actual: history.monthly_expenses[m] });
  });
  
  // Fake projecting next 3 months visually for UI demo purposes since logic is in backend
  // For a full implementation, the backend would send an array of 3 future projections
  // Here we just use the backend's "next_month" actual value
  const lastAmt = chartData[chartData.length - 1].actual;
  const predAmt = parseFloat(prediction.next_month.replace(/[^\d.]/g, ''));
  chartData.push({ 
    month: "Next Month", 
    forecast: predAmt,
    range: [Math.max(0, predAmt - 500), predAmt + 500] 
  });

  return (
    <div className="space-y-6 animate-[fadeIn_0.4s_ease-out]">
      {/* Big Prediction Card */}
      <div className="glass-panel p-8 relative overflow-hidden group">
         <div className="absolute top-0 right-0 w-96 h-96 bg-accent-neon/5 rounded-full blur-[100px] pointer-events-none group-hover:bg-accent-neon/10 transition-colors" />
         
         <div className="flex justify-between items-start relative z-10">
            <div>
               <h3 className="text-gray-400 font-medium">Predicted Spending ({prediction.method})</h3>
               <h1 className="text-5xl font-bold mt-2 text-white">{prediction.next_month}</h1>
               <div className="flex items-center mt-4 space-x-3">
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold bg-navy-900 border ${prediction.trend === 'Declining' ? 'text-accent-green border-accent-green/30' : 'text-accent-red border-accent-red/30'}`}>
                     Trend: {prediction.trend}
                  </span>
                  <span className="text-sm text-gray-400">
                     ({prediction.recent_change_pct > 0 ? '+' : ''}{prediction.recent_change_pct}% vs last month)
                  </span>
               </div>
            </div>
            
            <div className="text-right">
               <div className="inline-block p-4 rounded-2xl bg-navy-900/50 border border-accent-neon/20">
                  <div className="flex items-center text-accent-neon mb-1">
                     <Sparkles className="w-5 h-5 mr-2" />
                     <span className="font-bold">AI Confidence</span>
                  </div>
                  <div className="text-2xl font-bold text-white">{prediction.confidence}%</div>
               </div>
            </div>
         </div>
      </div>

      {/* AI Insight */}
      <div className="glass-panel p-6 bg-accent-neon/5 border-accent-neon/20 flex items-start space-x-4">
         <div className="p-3 bg-accent-neon/20 rounded-xl text-accent-neon">
            <Sparkles className="w-6 h-6" />
         </div>
         <div>
            <h3 className="text-accent-neon font-bold text-lg">AI Insight</h3>
            <p className="text-gray-300 mt-1 leading-relaxed">{prediction.trend_advice}</p>
         </div>
      </div>

      {/* Chart */}
      <div className="glass-panel p-6">
         <h3 className="text-xl font-bold mb-6 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-accent-blue" />
            3-Month Spending Outlook
         </h3>
         <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
               <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#233554" />
                  <XAxis dataKey="month" stroke="#8892B0" tick={{fill: '#8892B0'}} />
                  <YAxis stroke="#8892B0" tick={{fill: '#8892B0'}} />
                  <Tooltip 
                     contentStyle={{ backgroundColor: '#112240', borderColor: '#233554', borderRadius: '12px' }}
                     itemStyle={{ color: '#fff' }}
                  />
                  <Line type="monotone" dataKey="actual" stroke="#448AFF" strokeWidth={3} dot={{r: 6}} />
                  <Line type="monotone" dataKey="forecast" stroke="#64FFDA" strokeWidth={3} strokeDasharray="5 5" dot={{r: 6}} />
               </ComposedChart>
            </ResponsiveContainer>
         </div>
      </div>
    </div>
  );
}
