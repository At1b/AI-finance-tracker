# BudgetMate ✨
A modern, AI-powered Personal Finance Tracker featuring a Python Flask REST backend, and a stunning React frontend built with Vite & Tailwind CSS.

## Features
- **Semantic Category Classifier**: AI intercepts your expense description and automatically selects the category for you.
- **Smart Budget Matrix**: Automatically divides your income using the 50/30/20 rule and renders visual, dynamic progress bars based on real-time spending.
- **Smart Alerts Engine**: Detects monthly anomalies, spending spikes, and generates critical warnings if your financial health score crashes.
- **Polynomial Regression AI Forecast**: Analyzes historical spending variance and plots a beautifully rendered 3-month predictive line chart to forecast your future expenses.

---

## 🚀 Setup & Installation Instructions

Because this leverages a Client-Server architecture, you will need to start both the Python Backend API and the React Web Application separately.

### 1. Backend Setup (Flask API)
The backend powers the SQLite database and all the complex AI logic.

First, open your terminal at the root directory of this project (`Finance-Tracker/`).

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python api.py
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 api.py
```

*The backend is now running live on `http://127.0.0.1:5000/`. Leave this terminal open!*

### 2. Frontend Setup (React SPA)
The frontend handles the gorgeous UI and data visualization.

Open a **second, new terminal** and move into the frontend directory:
```bash
cd frontend
npm install
npm run dev
```

*The frontend is now running! Look at your terminal output to find the exact Local port (e.g., `http://localhost:5173/` or `http://localhost:5174/`). Open that link in your browser.*

---

## 🧪 Testing the AI
If you want to immediately see all four AI engines light up, follow this quick test sequence on the React App:

1. Register any username/password combination (it creates the account automatically).
2. Go to **New Transaction** and add `Income` of `$50,000`. (Check the **Smart Budget** tab to see your progress bars initialize!).
3. Add an `Expense`. Under description type `"Uber ride to airport"`. Watch the AI automatically select the **Transport** category!
4. Add an `Expense`. Type `"Down payment for sports car"` and put an absurdly high amount like `$85,000`. 
5. Head to the **Alerts** tab to see the AI dynamically calculate a poor health score and warn you about an anomaly spike!
6. Add two back-dated expenses from 1 and 2 months ago, then visit the **AI Forecast** tab to watch the regression model graph your financial future.