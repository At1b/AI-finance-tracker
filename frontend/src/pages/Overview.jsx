import { useState, useEffect } from 'react';
import { ArrowUpRight, ArrowDownRight, Wallet, PieChart } from 'lucide-react';
import api from '../services/api';

export default function Overview({ user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      const res = await api.getTransactions(user);
      setData(res.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  if (loading) return <div className="text-center py-20 animate-pulse text-accent-neon">Loading Overview...</div>;
  if (!data) return <div className="text-center py-20">Error loading data.</div>;

  const { overview, transactions } = data;

  return (
    <div className="space-y-6 animate-[fadeIn_0.3s_ease-out]">
      {/* Top Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-6 flex justify-between items-center group glass-panel-hover">
          <div>
            <p className="text-gray-400 text-sm font-medium">Total Balance / Savings</p>
            <h3 className="text-3xl font-bold mt-2 text-white">₹{overview.savings.toLocaleString()}</h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-accent-neon/20 flex items-center justify-center border border-accent-neon/30 text-accent-neon group-hover:bg-accent-neon group-hover:text-navy-900 transition-colors">
            <Wallet />
          </div>
        </div>

        <div className="glass-panel p-6 flex justify-between items-center group glass-panel-hover">
          <div>
            <p className="text-gray-400 text-sm font-medium">Monthly Income</p>
            <h3 className="text-3xl font-bold mt-2 text-accent-green">₹{overview.total_income.toLocaleString()}</h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-accent-green/20 flex items-center justify-center border border-accent-green/30 text-accent-green">
            <ArrowUpRight />
          </div>
        </div>

        <div className="glass-panel p-6 flex justify-between items-center group glass-panel-hover">
          <div>
            <p className="text-gray-400 text-sm font-medium">Monthly Expenses</p>
            <h3 className="text-3xl font-bold mt-2 text-accent-red">₹{overview.total_expense.toLocaleString()}</h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-accent-red/20 flex items-center justify-center border border-accent-red/30 text-accent-red">
            <ArrowDownRight />
          </div>
        </div>
      </div>

      {/* Main Content Split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Transactions List */}
        <div className="lg:col-span-2 glass-panel p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold">Recent Transactions</h3>
          </div>
          
          <div className="space-y-4">
            {transactions.slice(0, 5).map((tx) => (
              <div key={tx.id} className="flex justify-between items-center p-4 rounded-xl bg-navy-900/50 border border-navy-700/50 hover:bg-navy-700/50 transition-colors">
                <div className="flex items-center space-x-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${tx.type === 'Income' ? 'bg-accent-green/20 text-accent-green' : 'bg-accent-red/20 text-accent-red'}`}>
                    {tx.type === 'Income' ? <ArrowUpRight className="w-5 h-5"/> : <ArrowDownRight className="w-5 h-5"/>}
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-100">{tx.description || tx.category}</h4>
                    <span className="text-xs text-gray-400">{tx.date} • {tx.category}</span>
                  </div>
                </div>
                <div className={`font-bold ${tx.type === 'Income' ? 'text-accent-green' : 'text-gray-100'}`}>
                  {tx.type === 'Income' ? '+' : '-'}₹{tx.amount.toLocaleString()}
                </div>
              </div>
            ))}
            {transactions.length === 0 && (
              <div className="text-center py-10 text-gray-400">No transactions yet. Add some!</div>
            )}
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="glass-panel p-6">
          <h3 className="text-xl font-bold mb-6 flex items-center">
            <PieChart className="w-5 h-5 mr-2 text-accent-blue" /> Expense Breakdown
          </h3>
          <div className="space-y-4">
            {Object.entries(overview.category_breakdown)
              .sort((a, b) => b[1] - a[1])
              .map(([cat, amt]) => {
                const pct = overview.total_expense > 0 ? (amt / overview.total_expense) * 100 : 0;
                return (
                  <div key={cat}>
                    <div className="flex justify-between mb-1 text-sm">
                      <span className="text-gray-300">{cat}</span>
                      <span className="font-medium text-white">₹{amt.toLocaleString()}</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-navy-900">
                      <div className="h-full rounded-full bg-accent-blue" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      </div>
    </div>
  );
}
