import { useState, useEffect } from 'react';
import { ArrowUpRight, ArrowDownRight, Wallet, PieChart, Pencil, Trash2, X } from 'lucide-react';
import api from '../services/api';

export default function Overview({ user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingTx, setEditingTx] = useState(null);

  const categories = ["Food", "Transport", "Shopping", "Entertainment", "Bills", "Health", "Other", "Income"];

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

  const handleDelete = async (id) => {
    if (window.confirm("Are you sure you want to delete this transaction?")) {
      try {
        await api.deleteTransaction(id, user);
        fetchData();
      } catch (err) {
        console.error("Failed to delete transaction", err);
      }
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.updateTransaction(editingTx, user);
      setEditingTx(null);
      fetchData(); // Refresh UI instantly
    } catch (err) {
      console.error("Failed to update transaction", err);
    }
  };

  if (loading) return <div className="text-center py-20 animate-pulse text-accent-neon">Loading Overview...</div>;
  if (!data) return <div className="text-center py-20">Error loading data.</div>;

  const { overview, transactions } = data;

  return (
    <div className="space-y-6 animate-[fadeIn_0.3s_ease-out] relative">
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
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Transaction History Data Table */}
        <div className="xl:col-span-2 glass-panel p-6 rounded-xl overflow-hidden flex flex-col">
          <h3 className="text-xl font-bold mb-6">Transaction History</h3>
          
          <div className="overflow-x-auto flex-1 max-h-[500px]">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-navy-900/90 backdrop-blur z-10 text-xs uppercase text-gray-400">
                <tr>
                  <th className="py-4 px-4 font-semibold tracking-wider">Date</th>
                  <th className="py-4 px-4 font-semibold tracking-wider">Description</th>
                  <th className="py-4 px-4 font-semibold tracking-wider">Category</th>
                  <th className="py-4 px-4 font-semibold tracking-wider text-right">Amount</th>
                  <th className="py-4 px-4 font-semibold tracking-wider text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-700/50">
                {transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-navy-800/50 transition-colors group">
                    <td className="py-4 px-4 whitespace-nowrap text-sm text-gray-300">{tx.date}</td>
                    <td className="py-4 px-4 font-medium text-white max-w-[200px] truncate">{tx.description || '--'}</td>
                    <td className="py-4 px-4">
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-navy-800 text-gray-300 border border-navy-700">
                        {tx.category}
                      </span>
                    </td>
                    <td className={`py-4 px-4 text-right font-bold whitespace-nowrap ${tx.type === 'Income' ? 'text-accent-green' : 'text-white'}`}>
                      {tx.type === 'Income' ? '+' : '-'}₹{tx.amount.toLocaleString()}
                    </td>
                    <td className="py-4 px-4 text-center">
                      <div className="flex items-center justify-center space-x-3 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => setEditingTx(tx)} className="text-gray-400 hover:text-accent-blue transition-colors">
                          <Pencil className="w-5 h-5" />
                        </button>
                        <button onClick={() => handleDelete(tx.id)} className="text-gray-400 hover:text-accent-red transition-colors">
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {transactions.length === 0 && (
              <div className="text-center py-10 text-gray-400">No transactions recorded yet.</div>
            )}
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="glass-panel p-6 h-fit">
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
                      <div className="h-full rounded-full bg-accent-blue transition-all duration-1000" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      </div>

      {/* Interactive Edit Modal */}
      {editingTx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-sm bg-navy-900/80 animate-[fadeIn_0.2s_ease-out]">
          <div className="bg-navy-900 w-full max-w-lg rounded-2xl border border-navy-700 shadow-2xl overflow-hidden p-8 animate-[slideUp_0.3s_ease-out]">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold bg-gradient-to-r from-accent-neon to-accent-blue bg-clip-text text-transparent">
                Edit Transaction
              </h3>
              <button onClick={() => setEditingTx(null)} className="text-gray-400 hover:text-white transition-colors">
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1 ml-1">Type</label>
                  <select 
                    className="input-field cursor-pointer py-3"
                    value={editingTx.type}
                    onChange={e => setEditingTx({ ...editingTx, type: e.target.value, category: e.target.value === 'Income' ? 'Income' : 'Other' })}
                  >
                    <option value="Expense">📤 Expense</option>
                    <option value="Income">📥 Income</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1 ml-1">Date</label>
                  <input 
                    type="date" required
                    className="input-field py-3" 
                    value={editingTx.date}
                    onChange={e => setEditingTx({ ...editingTx, date: e.target.value })}
                  />
                </div>
              </div>

              {editingTx.type === 'Expense' && (
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1 ml-1">Description</label>
                  <input 
                    type="text" required
                    className="input-field py-3" 
                    value={editingTx.description}
                    onChange={e => setEditingTx({ ...editingTx, description: e.target.value })}
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1 ml-1">Category</label>
                  <select 
                    className="input-field cursor-pointer py-3"
                    value={editingTx.category}
                    onChange={e => setEditingTx({ ...editingTx, category: e.target.value })}
                    disabled={editingTx.type === 'Income'}
                  >
                    {categories.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1 ml-1">Amount (₹)</label>
                  <input 
                    type="number" step="0.01" required
                    className="input-field py-3" 
                    value={editingTx.amount}
                    onChange={e => setEditingTx({ ...editingTx, amount: e.target.value })}
                  />
                </div>
              </div>

              <button type="submit" className="btn-primary w-full py-3 mt-4">
                Save Changes
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
