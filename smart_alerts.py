"""
Smart Alerts Engine
Monitors spending patterns and generates real-time warnings:
  - Budget overrun alerts
  - Unusual spending spike detection
  - Recurring bill reminders
  - Low savings warnings
  - Category-specific overspending
  - Daily/weekly spending pace alerts
"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict


class SmartAlerts:
    """Generates intelligent financial alerts based on spending patterns."""

    def __init__(self, db_path="finance.db"):
        self.db_path = db_path

    def get_user_data(self, username):
        """Fetch all transactions for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT category, amount, type, payment_mode, date, COALESCE(description, '') FROM transactions WHERE username = ?",
            (username,)
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def generate_alerts(self, username):
        """
        Analyze spending and generate all applicable alerts.
        Returns a list of alert dicts sorted by severity.
        """
        rows = self.get_user_data(username)
        if not rows:
            return []

        alerts = []
        today = datetime.today()
        current_month = today.strftime("%Y-%m")
        current_day = today.day
        days_in_month = 30  # Approximate

        # --- Aggregate data ---
        monthly_income = defaultdict(float)
        monthly_expenses = defaultdict(float)
        monthly_category = defaultdict(lambda: defaultdict(float))
        daily_expenses = defaultdict(float)
        all_categories = set()

        for category, amount, txn_type, payment_mode, date_str, desc in rows:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                month_key = dt.strftime("%Y-%m")

                if txn_type == "Income":
                    monthly_income[month_key] += amount
                else:
                    monthly_expenses[month_key] += amount
                    monthly_category[month_key][category] += amount
                    daily_expenses[date_str] += amount
                    all_categories.add(category)
            except (ValueError, TypeError):
                continue

        sorted_months = sorted(monthly_expenses.keys())
        n_months = len(sorted_months)

        if n_months == 0:
            return []

        # --- Current month data ---
        current_expense = monthly_expenses.get(current_month, 0)
        current_income = monthly_income.get(current_month, 0)
        current_categories = monthly_category.get(current_month, {})

        # Average from previous months (excluding current)
        prev_months = [m for m in sorted_months if m != current_month]
        if prev_months:
            avg_monthly_expense = sum(monthly_expenses[m] for m in prev_months) / len(prev_months)
            avg_monthly_income = sum(monthly_income[m] for m in prev_months if m in monthly_income) / max(len([m for m in prev_months if m in monthly_income]), 1)
        else:
            avg_monthly_expense = current_expense
            avg_monthly_income = current_income

        # ======================================================
        # ALERT 1: Spending Pace Alert
        # ======================================================
        if current_day > 0 and current_expense > 0:
            projected_month_total = (current_expense / max(current_day, 1)) * days_in_month
            pace_ratio = projected_month_total / max(avg_monthly_expense, 1)

            if pace_ratio > 1.3:
                alerts.append({
                    "type": "SPENDING_PACE",
                    "icon": "🏃",
                    "title": "Spending Pace Too Fast",
                    "message": (
                        f"At your current pace, you'll spend ₹{projected_month_total:,.0f} this month — "
                        f"that's {((pace_ratio - 1) * 100):.0f}% more than your average of ₹{avg_monthly_expense:,.0f}. "
                        f"You've spent ₹{current_expense:,.0f} in just {current_day} days."
                    ),
                    "severity": "HIGH",
                    "color": "#FF5252",
                })
            elif pace_ratio > 1.1:
                alerts.append({
                    "type": "SPENDING_PACE",
                    "icon": "⚡",
                    "title": "Slightly Above Average Pace",
                    "message": (
                        f"You're on track to spend ₹{projected_month_total:,.0f} this month, "
                        f"which is {((pace_ratio - 1) * 100):.0f}% above your monthly average. Keep an eye on it."
                    ),
                    "severity": "MEDIUM",
                    "color": "#FFD740",
                })

        # ======================================================
        # ALERT 2: Category Overspending
        # ======================================================
        if prev_months:
            for category in all_categories:
                if category == "N/A":
                    continue
                prev_cat_avg = sum(
                    monthly_category[m].get(category, 0) for m in prev_months
                ) / len(prev_months)

                current_cat = current_categories.get(category, 0)

                if prev_cat_avg > 0 and current_cat > prev_cat_avg * 1.5:
                    overage_pct = ((current_cat / prev_cat_avg) - 1) * 100
                    alerts.append({
                        "type": "CATEGORY_OVERSPEND",
                        "icon": "📛",
                        "title": f"{category} Overspending",
                        "message": (
                            f"Your {category} spending (₹{current_cat:,.0f}) is {overage_pct:.0f}% higher "
                            f"than your average of ₹{prev_cat_avg:,.0f}/month. Consider reviewing these expenses."
                        ),
                        "severity": "HIGH",
                        "color": "#FF5252",
                    })
                elif prev_cat_avg > 0 and current_cat > prev_cat_avg * 1.2:
                    alerts.append({
                        "type": "CATEGORY_WARNING",
                        "icon": "⚠️",
                        "title": f"{category} Rising",
                        "message": (
                            f"Your {category} spending (₹{current_cat:,.0f}) is above your average "
                            f"of ₹{prev_cat_avg:,.0f}. Still within range but trending up."
                        ),
                        "severity": "MEDIUM",
                        "color": "#FFD740",
                    })

        # ======================================================
        # ALERT 3: Savings Rate Warning
        # ======================================================
        if avg_monthly_income > 0:
            actual_savings = avg_monthly_income - avg_monthly_expense
            savings_rate = (actual_savings / avg_monthly_income) * 100

            if savings_rate < 5:
                alerts.append({
                    "type": "SAVINGS_CRITICAL",
                    "icon": "🚨",
                    "title": "Critical: Almost No Savings",
                    "message": (
                        f"Your savings rate is only {savings_rate:.1f}%. You're saving just "
                        f"₹{actual_savings:,.0f}/month. Financial experts recommend saving at least 20% "
                        f"(₹{avg_monthly_income * 0.20:,.0f}/month) for financial security."
                    ),
                    "severity": "CRITICAL",
                    "color": "#D50000",
                })
            elif savings_rate < 15:
                alerts.append({
                    "type": "SAVINGS_LOW",
                    "icon": "💡",
                    "title": "Low Savings Rate",
                    "message": (
                        f"You're saving {savings_rate:.1f}% of your income (₹{actual_savings:,.0f}/month). "
                        f"Try to reach the recommended 20% target by cutting ₹{(avg_monthly_income * 0.20 - actual_savings):,.0f}/month."
                    ),
                    "severity": "MEDIUM",
                    "color": "#FFD740",
                })
            else:
                alerts.append({
                    "type": "SAVINGS_GOOD",
                    "icon": "✅",
                    "title": "Healthy Savings",
                    "message": (
                        f"Great! You're saving {savings_rate:.1f}% of your income (₹{actual_savings:,.0f}/month). "
                        f"You're above the recommended 20% target."
                    ),
                    "severity": "OK",
                    "color": "#00E676",
                })

        # ======================================================
        # ALERT 4: Spending Spike Detection
        # ======================================================
        if len(daily_expenses) >= 5:
            daily_vals = list(daily_expenses.values())
            avg_daily = sum(daily_vals) / len(daily_vals)
            std_daily = (sum((x - avg_daily) ** 2 for x in daily_vals) / len(daily_vals)) ** 0.5

            # Check recent 3 days for spikes
            recent_dates = sorted(daily_expenses.keys(), reverse=True)[:3]
            for date_key in recent_dates:
                daily_amt = daily_expenses[date_key]
                if std_daily > 0 and daily_amt > avg_daily + 2 * std_daily:
                    alerts.append({
                        "type": "SPIKE",
                        "icon": "📊",
                        "title": f"Spending Spike on {date_key}",
                        "message": (
                            f"You spent ₹{daily_amt:,.0f} on {date_key}, which is "
                            f"significantly above your daily average of ₹{avg_daily:,.0f}. "
                            f"This is {((daily_amt / avg_daily) - 1) * 100:.0f}% above normal."
                        ),
                        "severity": "MEDIUM",
                        "color": "#E040FB",
                    })

        # ======================================================
        # ALERT 5: Month-over-Month Increase
        # ======================================================
        if n_months >= 2:
            last_month = sorted_months[-1]
            prev_month = sorted_months[-2]
            mom_change = monthly_expenses[last_month] - monthly_expenses[prev_month]
            mom_pct = (mom_change / max(monthly_expenses[prev_month], 1)) * 100

            if mom_pct > 20:
                alerts.append({
                    "type": "MOM_INCREASE",
                    "icon": "📈",
                    "title": "Large Monthly Increase",
                    "message": (
                        f"Your spending increased {mom_pct:.0f}% from {prev_month} to {last_month} "
                        f"(₹{monthly_expenses[prev_month]:,.0f} → ₹{monthly_expenses[last_month]:,.0f}). "
                        f"That's ₹{mom_change:,.0f} more than the previous month."
                    ),
                    "severity": "HIGH",
                    "color": "#FF5252",
                })
            elif mom_pct > 10:
                alerts.append({
                    "type": "MOM_INCREASE",
                    "icon": "📊",
                    "title": "Moderate Monthly Increase",
                    "message": (
                        f"Your spending rose {mom_pct:.0f}% month-over-month. "
                        f"Keep monitoring to prevent further increases."
                    ),
                    "severity": "MEDIUM",
                    "color": "#FFD740",
                })

        # ======================================================
        # ALERT 6: High Single-Category Dependency
        # ======================================================
        if current_expense > 0 and current_categories:
            for cat, amt in current_categories.items():
                if cat == "N/A":
                    continue
                cat_pct = (amt / current_expense) * 100
                if cat_pct > 45:
                    alerts.append({
                        "type": "CATEGORY_CONCENTRATION",
                        "icon": "🎯",
                        "title": f"{cat} Dominates Spending",
                        "message": (
                            f"{cat} accounts for {cat_pct:.0f}% of your total expenses this month "
                            f"(₹{amt:,.0f} out of ₹{current_expense:,.0f}). Consider diversifying or reducing this category."
                        ),
                        "severity": "MEDIUM",
                        "color": "#448AFF",
                    })

        # ======================================================
        # ALERT 7: Income vs Expense Imbalance
        # ======================================================
        if current_income > 0 and current_expense > current_income:
            deficit = current_expense - current_income
            alerts.append({
                "type": "DEFICIT",
                "icon": "🔴",
                "title": "Spending Exceeds Income!",
                "message": (
                    f"This month you've spent ₹{current_expense:,.0f} but earned only ₹{current_income:,.0f}. "
                    f"You're running a deficit of ₹{deficit:,.0f}. Immediate action needed."
                ),
                "severity": "CRITICAL",
                "color": "#D50000",
            })

        # ======================================================
        # ALERT 8: No Income Recorded (if we have months)
        # ======================================================
        if current_month in monthly_expenses and current_month not in monthly_income and current_day > 5:
            alerts.append({
                "type": "NO_INCOME",
                "icon": "💼",
                "title": "No Income Recorded This Month",
                "message": (
                    f"You have expenses recorded for {current_month} but no income yet. "
                    f"Remember to log your income to keep your financial picture accurate."
                ),
                "severity": "LOW",
                "color": "#8892B0",
            })

        # Sort by severity priority
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "OK": 4}
        alerts.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 3))

        return alerts
