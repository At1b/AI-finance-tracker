"""
Smart Budget Advisor Module
Analyzes historical spending patterns and generates intelligent 
per-category budget recommendations using the 50/30/20 framework
adapted to the user's actual spending behavior.
"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict


# Category classification for the 50/30/20 rule
NEEDS_CATEGORIES = {"Bills", "Transport"}          # 50% — Essentials
WANTS_CATEGORIES = {"Food", "Shopping", "Other"}   # 30% — Discretionary
# 20% goes to Savings (not a spending category)


class BudgetAdvisor:
    """Smart budget recommendation engine based on spending patterns."""

    def __init__(self, db_path="finance.db"):
        self.db_path = db_path

    def get_user_data(self, username):
        """Fetch all transactions for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT category, amount, type, payment_mode, date FROM transactions WHERE username = ?",
            (username,)
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_user_profile(self, username):
        """Fetch the user's hardcoded base income profile."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT base_income FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            conn.close()
            return float(row[0]) if row and row[0] else 0.0
        except sqlite3.OperationalError:
            conn.close()
            return 0.0

    def generate_budget(self, username, target_month=None):
        """
        Generates smart budget suggestions based on spending patterns.
        
        Strategy:
        1. Calculate average monthly income
        2. Apply 50/30/20 rule as the ideal framework
        3. Adjust budgets based on actual spending patterns
        4. Flag overspending categories
        5. Generate actionable suggestions
        
        Returns a comprehensive budget report dict.
        """
        rows = self.get_user_data(username)

        if not rows:
            return {"error": "No transaction data found. Add some transactions first!"}

        # --- Aggregate by month ---
        monthly_income = defaultdict(float)
        monthly_expenses = defaultdict(float)
        monthly_category_spending = defaultdict(lambda: defaultdict(float))
        all_categories = {"Food", "Transport", "Shopping", "Bills", "Other"}

        for category, amount, txn_type, payment_mode, date_str in rows:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                month_key = dt.strftime("%Y-%m")

                if txn_type == "Income":
                    monthly_income[month_key] += amount
                else:
                    monthly_expenses[month_key] += amount
                    monthly_category_spending[month_key][category] += amount
                    all_categories.add(category)
            except (ValueError, TypeError):
                continue

        if not monthly_expenses:
            return {"error": "No expense data found. Add some expense transactions!"}

        sorted_months = sorted(monthly_expenses.keys())
        n_months = len(sorted_months)

        # --- Calculate base limits ---
        profile_income = self.get_user_profile(username)
        # Use hard-locked profile income if configured, else dynamically sum historical transactions
        if profile_income > 0:
            avg_monthly_income = profile_income
        else:
            avg_monthly_income = sum(monthly_income.values()) / max(len(monthly_income), 1)
            
        avg_monthly_expense = sum(monthly_expenses.values()) / n_months

        # Current month data
        current_month = target_month if target_month else datetime.today().strftime("%Y-%m")
        current_month_spending = monthly_category_spending.get(current_month, {})
        current_month_total = sum(current_month_spending.values())

        # If no explicit target_month and no current month data, use the latest month available
        if not target_month and not current_month_spending and sorted_months:
            current_month = sorted_months[-1]
            current_month_spending = monthly_category_spending.get(current_month, {})
            current_month_total = sum(current_month_spending.values())

        # --- Per-category averages (last 3 months or available) ---
        recent_months = sorted_months[-min(3, n_months):]
        category_averages = defaultdict(float)
        category_month_counts = defaultdict(int)
        category_max = defaultdict(float)
        category_min = defaultdict(lambda: float('inf'))

        for month in recent_months:
            for cat, amount in monthly_category_spending[month].items():
                category_averages[cat] += amount
                category_month_counts[cat] += 1
                category_max[cat] = max(category_max[cat], amount)
                category_min[cat] = min(category_min[cat], amount)

        for cat in category_averages:
            category_averages[cat] /= category_month_counts[cat]

        # --- Apply 50/30/20 Rule with adjustments ---
        ideal_needs_budget = avg_monthly_income * 0.50
        ideal_wants_budget = avg_monthly_income * 0.30
        ideal_savings = avg_monthly_income * 0.20

        # Distribute ideal budgets across categories proportionally
        total_needs_avg = sum(category_averages[c] for c in all_categories if c in NEEDS_CATEGORIES)
        total_wants_avg = sum(category_averages[c] for c in all_categories if c in WANTS_CATEGORIES)

        category_budgets = {}
        for cat in all_categories:
            if cat == "N/A":
                continue

            avg_spend = category_averages.get(cat, 0)

            if cat in NEEDS_CATEGORIES:
                # Needs: allocate proportionally from 50% pool
                if total_needs_avg > 0:
                    ideal_share = ideal_needs_budget * (avg_spend / total_needs_avg)
                else:
                    ideal_share = ideal_needs_budget / max(len(NEEDS_CATEGORIES & all_categories), 1)
            else:
                # Wants: allocate proportionally from 30% pool
                if total_wants_avg > 0:
                    ideal_share = ideal_wants_budget * (avg_spend / total_wants_avg)
                else:
                    ideal_share = ideal_wants_budget / max(len(WANTS_CATEGORIES & all_categories), 1)

            # Smart adjustment: blend ideal with actual (70% ideal, 30% historical)
            # This makes the budget realistic while nudging toward the ideal
            suggested_budget = round(ideal_share * 0.7 + avg_spend * 0.3, 2)

            # Ensure budget is at least 80% of average (not too aggressive)
            suggested_budget = max(suggested_budget, avg_spend * 0.80)

            current_spent = current_month_spending.get(cat, 0)
            budget_remaining = suggested_budget - current_spent
            usage_pct = (current_spent / suggested_budget * 100) if suggested_budget > 0 else 0

            # Status classification
            if usage_pct > 100:
                status = "🔴 Over Budget"
                status_color = "#FF5252"
                priority = "HIGH"
            elif usage_pct > 80:
                status = "🟡 Near Limit"
                status_color = "#FFD740"
                priority = "MEDIUM"
            elif usage_pct > 50:
                status = "🟢 On Track"
                status_color = "#69F0AE"
                priority = "LOW"
            else:
                status = "✅ Well Under"
                status_color = "#00E676"
                priority = "NONE"

            cat_type = "Need" if cat in NEEDS_CATEGORIES else "Want"

            category_budgets[cat] = {
                "suggested_budget": suggested_budget,
                "average_spending": round(avg_spend, 2),
                "current_spent": round(current_spent, 2),
                "remaining": round(budget_remaining, 2),
                "usage_pct": round(usage_pct, 1),
                "status": status,
                "status_color": status_color,
                "priority": priority,
                "category_type": cat_type,
                "monthly_min": round(category_min.get(cat, 0), 2),
                "monthly_max": round(category_max.get(cat, 0), 2),
            }

        # --- Generate actionable suggestions ---
        suggestions = []

        # Overall savings check
        actual_savings_rate = ((avg_monthly_income - avg_monthly_expense) / avg_monthly_income * 100) if avg_monthly_income > 0 else 0

        if actual_savings_rate < 10:
            suggestions.append({
                "icon": "🚨",
                "title": "Low Savings Alert",
                "text": f"You're only saving {actual_savings_rate:.1f}% of your income. Target at least 20%. "
                        f"Try reducing discretionary spending by ₹{(avg_monthly_income * 0.20 - (avg_monthly_income - avg_monthly_expense)):,.0f}/month.",
                "severity": "HIGH",
                "color": "#FF5252"
            })
        elif actual_savings_rate < 20:
            gap = avg_monthly_income * 0.20 - (avg_monthly_income - avg_monthly_expense)
            suggestions.append({
                "icon": "💡",
                "title": "Savings Improvement",
                "text": f"You're saving {actual_savings_rate:.1f}%, close to the ideal 20%. "
                        f"Cut ₹{gap:,.0f}/month more to hit your target.",
                "severity": "MEDIUM",
                "color": "#FFD740"
            })
        else:
            suggestions.append({
                "icon": "🏆",
                "title": "Great Savings!",
                "text": f"You're saving {actual_savings_rate:.1f}% of your income — above the 20% target. Keep it up!",
                "severity": "LOW",
                "color": "#00E676"
            })

        # Per-category suggestions (only for over-budget or near-limit)
        over_budget_cats = [(c, d) for c, d in category_budgets.items() if d["usage_pct"] > 80]
        over_budget_cats.sort(key=lambda x: x[1]["usage_pct"], reverse=True)

        for cat, data in over_budget_cats[:3]:  # Top 3 problem areas
            overage = data["current_spent"] - data["suggested_budget"]
            if overage > 0:
                suggestions.append({
                    "icon": "✂️",
                    "title": f"Cut {cat} Spending",
                    "text": f"You've exceeded your {cat} budget by ₹{overage:,.0f}. "
                            f"Your average is ₹{data['average_spending']:,.0f}/month — try staying below ₹{data['suggested_budget']:,.0f}.",
                    "severity": "HIGH",
                    "color": "#FF5252"
                })
            else:
                suggestions.append({
                    "icon": "⚠️",
                    "title": f"{cat} Approaching Limit",
                    "text": f"You've used {data['usage_pct']:.0f}% of your {cat} budget. "
                            f"Only ₹{data['remaining']:,.0f} remaining for this month.",
                    "severity": "MEDIUM",
                    "color": "#FFD740"
                })

        # Find the highest-growth category
        if n_months >= 2:
            last_month = sorted_months[-1]
            prev_month = sorted_months[-2]
            growth_cats = {}
            for cat in all_categories:
                prev_amt = monthly_category_spending[prev_month].get(cat, 0)
                last_amt = monthly_category_spending[last_month].get(cat, 0)
                if prev_amt > 0:
                    growth = ((last_amt - prev_amt) / prev_amt) * 100
                    growth_cats[cat] = growth

            if growth_cats:
                fastest_growing = max(growth_cats, key=growth_cats.get)
                growth_rate = growth_cats[fastest_growing]
                if growth_rate > 15:
                    suggestions.append({
                        "icon": "📈",
                        "title": f"{fastest_growing} Growing Fast",
                        "text": f"Your {fastest_growing} spending grew {growth_rate:.0f}% last month. "
                                f"Monitor this category to prevent budget creep.",
                        "severity": "MEDIUM",
                        "color": "#E040FB"
                    })

        # --- Build final report ---
        total_suggested_budget = sum(d["suggested_budget"] for d in category_budgets.values())

        return {
            "avg_monthly_income": round(avg_monthly_income, 2),
            "avg_monthly_expense": round(avg_monthly_expense, 2),
            "actual_savings_rate": round(actual_savings_rate, 1),
            "ideal_savings": round(ideal_savings, 2),
            "total_suggested_budget": round(total_suggested_budget, 2),
            "current_month": current_month,
            "current_month_total": round(current_month_total, 2),
            "category_budgets": category_budgets,
            "suggestions": suggestions,
            "n_months_analyzed": n_months,
            "framework": "50/30/20 Rule (Adapted)",
            "needs_budget": round(ideal_needs_budget, 2),
            "wants_budget": round(ideal_wants_budget, 2),
        }
