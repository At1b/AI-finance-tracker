from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import bcrypt
from datetime import datetime
import os

from predictor import ExpensePredictor
from budget_advisor import BudgetAdvisor
from smart_alerts import SmartAlerts
from category_classifier import CategoryClassifier


app = Flask(__name__)
# Enable CORS for the local React app running on port 5173
CORS(app, resources={r"/api/*": {"origins": "*"}})

DB_NAME = "finance.db"

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT UNIQUE, 
            password TEXT,
            job TEXT DEFAULT 'Unknown',
            base_income REAL DEFAULT 0.0
        )
    """)
    # Try gracefully migrating old db schemas
    try:
        c.execute("ALTER TABLE users ADD COLUMN job TEXT DEFAULT 'Unknown'")
        c.execute("ALTER TABLE users ADD COLUMN base_income REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass # Columns probably already exist
    
    conn.commit()
    conn.close()

init_db()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()

    if result and bcrypt.checkpw(password.encode(), result[0].encode()):
        return jsonify({"message": "Login successful", "username": username}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    job = data.get('job', 'Unknown')
    base_income = float(data.get('base_income', 0.0))
    
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt).decode()
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO users (username, password, job, base_income) VALUES (?, ?, ?, ?)", 
                  (username, hashed_password, job, base_income))
        conn.commit()
        conn.close()
        return jsonify({"message": "Registration successful"}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Username already exists"}), 400

@app.route('/api/user/profile', methods=['GET', 'PUT'])
def user_profile():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username required"}), 400
        
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute("SELECT job, base_income FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        if result:
            return jsonify(dict(result)), 200
        return jsonify({"error": "User not found"}), 404
        
    if request.method == 'PUT':
        data = request.json
        job = data.get('job', 'Unknown')
        base_income = float(data.get('base_income', 0.0))
        
        c.execute("UPDATE users SET job = ?, base_income = ? WHERE username = ?", (job, base_income, username))
        conn.commit()
        conn.close()
        return jsonify({"message": "Profile updated successfully"}), 200

@app.route('/api/transactions', methods=['GET', 'POST', 'DELETE', 'PUT'])
def transactions():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username required"}), 400

    conn = get_db()
    c = conn.cursor()

    if request.method == 'GET':
        c.execute('''SELECT * FROM transactions 
                     WHERE username=? 
                     ORDER BY date DESC LIMIT 100''', (username,))
        records = c.fetchall()
        
        # calculate some stats for overview
        c.execute("SELECT sum(amount) FROM transactions WHERE username=? AND category != 'Income' AND type='Expense'", (username,))
        total_expense = c.fetchone()[0] or 0
        c.execute("SELECT sum(amount) FROM transactions WHERE username=? AND category = 'Income'", (username,))
        total_income = c.fetchone()[0] or 0

        # group by category
        c.execute('''SELECT category, sum(amount) FROM transactions 
                     WHERE username=? AND type='Expense' AND category != 'Income' 
                     GROUP BY category''', (username,))
        category_breakdown = {row[0]: row[1] for row in c.fetchall()}

        return jsonify({
            "transactions": [dict(r) for r in records],
            "overview": {
                "total_expense": total_expense,
                "total_income": total_income,
                "savings": total_income - total_expense,
                "category_breakdown": category_breakdown
            }
        })

    elif request.method == 'POST':
        data = request.json
        c.execute('''INSERT INTO transactions (username, date, amount, category, type, description)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (username, data['date'], data['amount'], data['category'], data['type'], data.get('description', '')))
        conn.commit()
        return jsonify({"message": "Transaction added"}), 201
        
    elif request.method == 'DELETE':
        data = request.json
        tx_id = data.get('id')
        c.execute('DELETE FROM transactions WHERE id=? AND username=?', (tx_id, username))
        conn.commit()
        return jsonify({"message": "Transaction deleted"}), 200
        
    elif request.method == 'PUT':
        data = request.json
        tx_id = data.get('id')
        c.execute('''UPDATE transactions 
                     SET date=?, amount=?, category=?, type=?, description=? 
                     WHERE id=? AND username=?''',
                  (data['date'], data['amount'], data['category'], data['type'], data.get('description', ''), tx_id, username))
        conn.commit()
        return jsonify({"message": "Transaction updated"}), 200

@app.route('/api/ai/predict-category', methods=['POST'])
def predict_category():
    data = request.json
    description = data.get('description', '')
    classifier = CategoryClassifier()
    result = classifier.classify(description)
    return jsonify(result)

@app.route('/api/ai/forecast', methods=['GET'])
def ai_forecast():
    username = request.args.get('username')
    predictor = ExpensePredictor()
    
    # Get standard prediction
    next_month = predictor.predict_next_month(username)
    
    # Get chart data
    data = predictor.get_monthly_data(username)
    
    return jsonify({"prediction": next_month, "history": data})

@app.route('/api/ai/budget', methods=['GET'])
def budget_advise():
    username = request.args.get('username')
    month = request.args.get('month')
    advisor = BudgetAdvisor(DB_NAME)
    result = advisor.generate_budget(username, target_month=month)
    return jsonify(result)

@app.route('/api/ai/alerts', methods=['GET'])
def alerts():
    username = request.args.get('username')
    engine = SmartAlerts()
    active_alerts = engine.generate_alerts(username)
    
    critical_count = sum(1 for a in active_alerts if a.get('severity') == 'CRITICAL')
    high_count = sum(1 for a in active_alerts if a.get('severity') == 'HIGH')
    medium_count = sum(1 for a in active_alerts if a.get('severity') == 'MEDIUM')
    ok_count = sum(1 for a in active_alerts if a.get('severity') == 'OK')
    
    health_score = max(0, 100 - critical_count * 30 - high_count * 15 - medium_count * 5 + ok_count * 10)
    health_score = min(health_score, 100)

    if not active_alerts:
        health_score = 100

    return jsonify({
        "health_score": health_score,
        "active_alerts": active_alerts
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
