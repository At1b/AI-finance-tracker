"""
AI Expense Predictor Module
Uses a pure-Python polynomial trend fit to predict next month's spending
based on historical transaction data.
"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import random


class ExpensePredictor:
    """ML-based expense prediction engine."""

    def __init__(self, db_path="finance.db"):
        self.db_path = db_path

    def get_monthly_data(self, username):
        """
        Fetches transaction data and aggregates it by month.
        Returns: dict with monthly totals, category breakdowns, and payment mode data.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT category, amount, type, payment_mode, date FROM transactions WHERE username = ?",
            (username,)
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        # Aggregate by month
        monthly_expenses = defaultdict(float)
        monthly_income = defaultdict(float)
        monthly_category = defaultdict(lambda: defaultdict(float))
        monthly_payment = defaultdict(lambda: defaultdict(float))

        for category, amount, txn_type, payment_mode, date_str in rows:
            try:
                # Extract year-month key
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                month_key = dt.strftime("%Y-%m")

                if txn_type == "Expense":
                    monthly_expenses[month_key] += amount
                    monthly_category[month_key][category] += amount
                else:
                    monthly_income[month_key] += amount

                monthly_payment[month_key][payment_mode] += amount
            except (ValueError, TypeError):
                continue

        return {
            "monthly_expenses": dict(monthly_expenses),
            "monthly_income": dict(monthly_income),
            "monthly_category": dict(monthly_category),
            "monthly_payment": dict(monthly_payment),
        }

    def _solve_linear_system(self, matrix, vector):
        """Solve a small linear system using Gaussian elimination."""
        size = len(vector)
        augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]

        for pivot_index in range(size):
            pivot_row = max(range(pivot_index, size), key=lambda row: abs(augmented[row][pivot_index]))
            if abs(augmented[pivot_row][pivot_index]) < 1e-12:
                return None

            if pivot_row != pivot_index:
                augmented[pivot_index], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_index]

            pivot_value = augmented[pivot_index][pivot_index]
            for column in range(pivot_index, size + 1):
                augmented[pivot_index][column] /= pivot_value

            for row in range(size):
                if row == pivot_index:
                    continue
                factor = augmented[row][pivot_index]
                if factor == 0:
                    continue
                for column in range(pivot_index, size + 1):
                    augmented[row][column] -= factor * augmented[pivot_index][column]

        return [augmented[index][size] for index in range(size)]

    def _fit_polynomial(self, x_values, y_values, degree):
        """Fit a polynomial of the requested degree using least squares."""
        degree = max(1, degree)
        size = degree + 1

        power_sums = [sum((x ** power) for x in x_values) for power in range(2 * degree + 1)]
        matrix = [[power_sums[row + column] for column in range(size)] for row in range(size)]
        vector = [sum((x ** row) * y for x, y in zip(x_values, y_values)) for row in range(size)]

        coefficients = self._solve_linear_system(matrix, vector)
        if coefficients is None:
            return None

        return coefficients

    def _evaluate_polynomial(self, coefficients, x_value):
        return sum(coefficient * (x_value ** index) for index, coefficient in enumerate(coefficients))

    def _r_squared(self, y_values, predictions):
        mean_y = sum(y_values) / max(len(y_values), 1)
        total_variance = sum((value - mean_y) ** 2 for value in y_values)
        residual_variance = sum((actual - predicted) ** 2 for actual, predicted in zip(y_values, predictions))

        if total_variance <= 0:
            return 0.0

        return max(0.0, 1 - (residual_variance / total_variance))

    def predict_next_month(self, username):
        """
        Predicts next month's spending using ML.
        
        Strategy:
        - 3+ months of data: Polynomial Regression (degree 2) for trend detection
        - 2 months: Linear extrapolation
        - 1 month: Return that month's data as baseline estimate
        
        Returns a dict with predictions, confidence, and breakdown.
        """
        data = self.get_monthly_data(username)

        if data is None:
            return {"error": "No transaction data found. Add some transactions first!"}

        monthly_expenses = data["monthly_expenses"]
        monthly_category = data["monthly_category"]

        if not monthly_expenses:
            return {"error": "No expense data found. Add some expense transactions!"}

        # Sort months chronologically
        sorted_months = sorted(monthly_expenses.keys())
        expense_values = [monthly_expenses[m] for m in sorted_months]
        n_months = len(sorted_months)

        # Determine next month
        last_month_dt = datetime.strptime(sorted_months[-1] + "-01", "%Y-%m-%d")
        next_month_dt = (last_month_dt.replace(day=28) + timedelta(days=4)).replace(day=1)
        next_month_str = next_month_dt.strftime("%B %Y")

        # --- ML PREDICTION ---
        if n_months >= 3:
            # Use polynomial regression (degree 2) in pure Python.
            x_values = list(range(n_months))
            degree = min(2, n_months - 1)
            coefficients = self._fit_polynomial(x_values, expense_values, degree)

            if coefficients is None:
                change = expense_values[-1] - expense_values[-2]
                predicted_total = max(0, expense_values[-1] + change)
                confidence = 40.0
            else:
                predicted_total = max(0, self._evaluate_polynomial(coefficients, n_months))
                fitted_values = [self._evaluate_polynomial(coefficients, x) for x in x_values]
                confidence = max(0, min(100, self._r_squared(expense_values, fitted_values) * 100))

            # Trend analysis
            if n_months >= 2:
                recent_change = ((expense_values[-1] - expense_values[-2]) / max(expense_values[-2], 1)) * 100
            else:
                recent_change = 0

            method = "Polynomial Regression (ML)"

        elif n_months == 2:
            # Linear extrapolation
            change = expense_values[1] - expense_values[0]
            predicted_total = max(0, expense_values[1] + change)
            confidence = 45.0
            recent_change = ((expense_values[1] - expense_values[0]) / max(expense_values[0], 1)) * 100
            method = "Linear Extrapolation"

        else:
            # Single month baseline
            predicted_total = expense_values[0]
            confidence = 25.0
            recent_change = 0
            method = "Baseline Estimate (1 month)"

        # --- CATEGORY-WISE PREDICTION ---
        # Calculate average proportions from last 3 months (or available)
        recent_months = sorted_months[-min(3, n_months):]
        category_proportions = defaultdict(float)
        category_counts = defaultdict(int)

        for month in recent_months:
            month_total = monthly_expenses.get(month, 0)
            if month_total > 0 and month in monthly_category:
                for cat, amount in monthly_category[month].items():
                    category_proportions[cat] += amount / month_total
                    category_counts[cat] += 1

        # Average the proportions
        predicted_categories = {}
        for cat in category_proportions:
            avg_proportion = category_proportions[cat] / category_counts[cat]
            predicted_categories[cat] = round(predicted_total * avg_proportion, 2)

        # --- TREND CLASSIFICATION ---
        if recent_change > 10:
            trend = "📈 Rising"
            trend_color = "#FF5252"
            trend_advice = "Your spending is trending upward. Consider reviewing discretionary expenses."
        elif recent_change < -10:
            trend = "📉 Declining"
            trend_color = "#00E676"
            trend_advice = "Great job! Your spending is decreasing. Keep it up!"
        else:
            trend = "➡️ Stable"
            trend_color = "#FFD740"
            trend_advice = "Your spending is relatively stable. Look for small savings opportunities."

        return {
            "predicted_total": round(predicted_total, 2),
            "next_month": next_month_str,
            "confidence": round(confidence, 1),
            "method": method,
            "trend": trend,
            "trend_color": trend_color,
            "trend_advice": trend_advice,
            "recent_change_pct": round(recent_change, 1),
            "predicted_categories": predicted_categories,
            "historical_months": sorted_months,
            "historical_expenses": expense_values,
            "n_months_used": n_months,
        }


def seed_sample_data(username, db_path="finance.db"):
    """
    Seeds 5 months of realistic sample transaction data for testing
    the AI prediction feature. Creates a clear upward trend in spending.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            category TEXT,
            amount REAL,
            type TEXT,
            payment_mode TEXT,
            date TEXT,
            description TEXT DEFAULT ''
        )
    """)

    # Add description column if upgrading from old schema
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN description TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    # Clear existing sample data for this user (to avoid duplicates)
    cursor.execute("DELETE FROM transactions WHERE username = ?", (username,))

    today = datetime.today()
    payment_modes = ["Cash", "Credit Card", "Debit Card", "UPI", "Bank Transfer"]

    # Base spending per category with sample descriptions
    category_data = {
        "Food": {
            "base": 3500,
            "descriptions": [
                "Lunch at office canteen", "Swiggy dinner delivery", "Groceries from BigBasket",
                "Coffee at Starbucks", "Zomato biryani order", "Fruits and vegetables market",
                "Dominos pizza weekend", "Breakfast idli dosa", "Ice cream parlour",
                "KFC bucket meal", "Tea and snacks evening", "Milk bread eggs daily",
            ],
        },
        "Transport": {
            "base": 1500,
            "descriptions": [
                "Uber ride to office", "Ola cab airport drop", "Metro card recharge",
                "Petrol fill up car", "Bus fare daily commute", "Auto rickshaw market",
                "Rapido bike taxi", "Parking charges mall", "Toll charges highway",
                "Car service maintenance", "Train ticket booking", "Cab ride to station",
            ],
        },
        "Shopping": {
            "base": 2500,
            "descriptions": [
                "Amazon headphones order", "Flipkart phone case", "New shoes Nike store",
                "Clothing shopping mall", "Birthday gift for friend", "Myntra dress sale",
                "Books from Amazon", "Laptop bag backpack", "Electronics gadget purchase",
                "Home decor curtains", "Cosmetics Nykaa order", "Gaming controller online",
            ],
        },
        "Bills": {
            "base": 4000,
            "descriptions": [
                "Electricity bill monthly", "Mobile recharge Jio", "Internet broadband Airtel",
                "Netflix subscription", "House rent payment", "Gym membership monthly",
                "Health insurance premium", "Doctor consultation visit", "Medicine pharmacy",
                "Spotify premium music", "Society maintenance charges", "Water bill payment",
            ],
        },
        "Other": {
            "base": 1000,
            "descriptions": [
                "Movie tickets cinema", "Haircut salon grooming", "Laundry dry cleaning",
                "Donation charity temple", "Party celebration friends", "Newspaper subscription",
                "ATM bank charges", "Spa massage relaxation", "Fine traffic challan",
                "Festival decoration items", "Pet food supplies", "Hobby art supplies",
            ],
        },
    }

    transactions = []

    for month_offset in range(5, 0, -1):
        # Calculate the month date
        month_date = today.replace(day=1) - timedelta(days=30 * month_offset)

        # Growth factor: spending increases ~8-12% each month (shows trend)
        growth = 1 + (5 - month_offset) * 0.09

        # Add income (salary)
        salary_date = month_date.replace(day=1)
        transactions.append((
            username, "N/A",
            round(random.uniform(45000, 55000), 2),
            "Income", "Bank Transfer",
            salary_date.strftime("%Y-%m-%d"), "Monthly salary"
        ))

        # Add freelance income (some months)
        if random.random() > 0.4:
            freelance_date = month_date.replace(day=random.randint(10, 20))
            transactions.append((
                username, "N/A",
                round(random.uniform(5000, 15000), 2),
                "Income", "UPI",
                freelance_date.strftime("%Y-%m-%d"), "Freelance project payment"
            ))

        # Add expenses across the month
        for category, cat_info in category_data.items():
            base_amount = cat_info["base"]
            descriptions = cat_info["descriptions"]
            n_txns = random.randint(3, 6)
            monthly_total = base_amount * growth

            for i in range(n_txns):
                day = random.randint(1, 28)
                txn_date = month_date.replace(day=day)
                amount = round(monthly_total / n_txns * random.uniform(0.7, 1.3), 2)
                payment = random.choice(payment_modes)
                desc = random.choice(descriptions)

                transactions.append((
                    username, category, amount, "Expense", payment,
                    txn_date.strftime("%Y-%m-%d"), desc
                ))

    # Insert all transactions
    cursor.executemany(
        "INSERT INTO transactions (username, category, amount, type, payment_mode, date, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
        transactions
    )
    conn.commit()
    conn.close()

    return len(transactions)
