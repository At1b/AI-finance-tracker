import { useState, useEffect, useRef } from 'react';
import { Sparkles, CheckCircle2 } from 'lucide-react';
import api from '../services/api';

export default function AddTransaction({ user }) {
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    amount: '',
    category: 'Other',
    type: 'Expense',
    description: ''
  });
  
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [isClassifying, setIsClassifying] = useState(false);
  const [success, setSuccess] = useState(false);
  
  const categories = ["Food", "Transport", "Shopping", "Entertainment", "Bills", "Health", "Other", "Income"];
  const debounceRef = useRef(null);

  // Auto-classify when description changes
  useEffect(() => {
    if (formData.type === 'Income' || formData.description.length < 3) {
      setAiSuggestion(null);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      setIsClassifying(true);
      try {
        const res = await api.predictCategory(formData.description);
        setAiSuggestion(res.data);
        if (res.data.category && categories.includes(res.data.category)) {
          setFormData(prev => ({ ...prev, category: res.data.category }));
        }
      } catch (err) {
        console.error("AI Classification Error");
      }
      setIsClassifying(false);
    }, 400);

    return () => clearTimeout(debounceRef.current);
  }, [formData.description]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.addTransaction(formData, user);
      setSuccess(true);
      setFormData({ ...formData, amount: '', description: '' });
      setAiSuggestion(null);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="max-w-2xl mx-auto animate-[fadeIn_0.3s_ease-out]">
      <div className="glass-panel p-8 relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-accent-neon/10 rounded-full blur-[80px] pointer-events-none" />

        <div className="flex justify-between items-center mb-8 relative z-10">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
            New Transaction
          </h2>
          
          {success && (
            <div className="flex items-center text-accent-green bg-accent-green/10 px-4 py-2 rounded-full text-sm animate-bounce">
              <CheckCircle2 className="w-4 h-4 mr-2" /> Added!
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2 ml-1">Type</label>
              <select 
                className="input-field cursor-pointer"
                value={formData.type}
                onChange={e => {
                  const type = e.target.value;
                  setFormData(prev => ({ ...prev, type, category: type === 'Income' ? 'Income' : 'Other' }));
                }}
              >
                <option value="Expense">📤 Expense</option>
                <option value="Income">📥 Income</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2 ml-1">Date</label>
              <input 
                type="date" 
                required
                className="input-field" 
                value={formData.date}
                onChange={e => setFormData({ ...formData, date: e.target.value })}
              />
            </div>
          </div>

          {formData.type === 'Expense' && (
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2 ml-1">Description</label>
              <input 
                type="text" 
                required
                className="input-field" 
                placeholder="e.g., Uber ride to airport, Grocery at Walmart"
                value={formData.description}
                onChange={e => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-6">
            <div className="relative">
              <label className="block text-sm font-medium text-gray-400 mb-2 ml-1">Category</label>
              <select 
                className="input-field cursor-pointer"
                value={formData.category}
                onChange={e => setFormData({ ...formData, category: e.target.value })}
                disabled={formData.type === 'Income'}
              >
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>

              {aiSuggestion && formData.type === 'Expense' && (
                <div className="absolute -top-1 right-1 flex items-center text-xs text-accent-neon font-medium">
                  <Sparkles className="w-3 h-3 mr-1" />
                  AI Set ({aiSuggestion.confidence}%)
                </div>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2 ml-1">Amount (₹)</label>
              <input 
                type="number" 
                step="0.01"
                required
                className="input-field" 
                placeholder="0.00"
                value={formData.amount}
                onChange={e => setFormData({ ...formData, amount: e.target.value })}
              />
            </div>
          </div>

          <button type="submit" className="btn-primary w-full py-4 mt-4 text-lg">
            Save Transaction
          </button>
        </form>
      </div>
    </div>
  );
}
