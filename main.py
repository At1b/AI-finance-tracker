import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from collections import defaultdict
from login import LoginPage  # Import the login page
from predictor import ExpensePredictor, seed_sample_data
from budget_advisor import BudgetAdvisor
from category_classifier import CategoryClassifier
from smart_alerts import SmartAlerts

def open_finance_tracker(username):
    """This function starts the finance tracker after login."""
    global LOGGED_IN_USER
    LOGGED_IN_USER = username  # Store the logged-in username
    root.withdraw()  # Hide the login window
    new_root = tk.Tk()
    FinanceTracker(new_root, username)  # Open finance tracker
    new_root.mainloop()

def restart_app():
    """Restarts the application by reopening the login window."""
    new_root = tk.Tk()
    LoginPage(new_root, open_finance_tracker)
    new_root.mainloop()

class FinanceTracker:
    def __init__(self, root, username):
        self.root = root    
        self.root.title(f"{username}'s Personal Finance Tracker")
        self.root.geometry("900x700")
        self.root.configure(bg="#0A192F")  

        self.username = username  # Store the username

        # Database connection
        self.conn = sqlite3.connect("finance.db")
        self.cursor = self.conn.cursor()
        self.create_table()

        # UI Components
        self.classifier = CategoryClassifier()  # AI category classifier
        self._classify_after_id = None  # Debounce timer for real-time classification
        self.setup_ui()
    def create_table(self):
     """Creates the transactions table if it doesn't exist."""
     self.cursor.execute("""
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
         self.cursor.execute("ALTER TABLE transactions ADD COLUMN description TEXT DEFAULT ''")
     except sqlite3.OperationalError:
         pass  # Column already exists
     self.conn.commit()

    
    def setup_ui(self):
        # Set overall style
        style = ttk.Style(self.root)
        
        # Title Label
        ttk.Label(self.root, text="BudgetMate", font=("Montserrat", 24, "bold"), background="lightblue", foreground="black").pack(pady=15)
        
        """Sets up the user interface components."""
        # Use tk.Frame instead of ttk.Frame to allow background color
        self.input_frame = tk.Frame(self.root, bg="lightblue", padx=20, pady=20)
        self.input_frame.pack(pady=20)

        # Date Input using Calendar
        ttk.Label(self.input_frame, text="Date:", font=("Arial", 10), background="#0A192F", foreground="white").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.date_entry = DateEntry(self.input_frame, width=12, background='#0A192F', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)

        # Type Selection
        ttk.Label(self.input_frame, text="Type:", font=("Arial", 10), background="#0A192F", foreground="white").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.type_combobox = ttk.Combobox(self.input_frame, values=["Income", "Expense"], state="readonly", font=("Arial", 10))
        self.type_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.type_combobox.bind("<<ComboboxSelected>>", self.toggle_category_field)

        # Amount Input
        ttk.Label(self.input_frame, text="Amount:", font=("Arial", 10), background="#0A192F", foreground="white").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.amount_entry = ttk.Entry(self.input_frame, font=("Arial", 10))
        self.amount_entry.grid(row=2, column=1, padx=5, pady=5)

        # Category Input with Dropdown
        self.category_label = ttk.Label(self.input_frame, text="Category:", font=("Arial", 10), background="#0A192F", foreground="white")
        self.category_var = tk.StringVar()
        self.category_combobox = ttk.Combobox(self.input_frame, textvariable=self.category_var, values=["Food", "Transport", "Shopping", "Bills", "Other"], state="normal", font=("Arial", 10))

        # Description Input (for AI auto-categorization)
        self.desc_label = ttk.Label(self.input_frame, text="Description:", font=("Arial", 10), background="#0A192F", foreground="white")
        self.desc_entry = ttk.Entry(self.input_frame, font=("Arial", 10), width=25)
        self.desc_entry.bind("<KeyRelease>", self._on_desc_key)

        # AI Detection indicator
        self.ai_indicator_frame = tk.Frame(self.input_frame, bg="lightblue")
        self.ai_badge = tk.Label(self.ai_indicator_frame, text="", font=("Arial", 8), bg="lightblue", fg="#555")
        self.ai_badge.pack(side="left")

        # Payment Mode Selection
        ttk.Label(self.input_frame, text="Payment Mode:", font=("Arial", 10), background="#0A192F", foreground="white").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.payment_mode_combobox = ttk.Combobox(self.input_frame, values=["Cash", "Credit Card", "Debit Card", "UPI", "Bank Transfer"], state="readonly", font=("Arial", 10))
        self.payment_mode_combobox.grid(row=6, column=1, padx=5, pady=5)

        # Treeview for displaying transactions
        self.tree_frame = ttk.Frame(self.root)
        self.tree_frame.pack(pady=10)

        self.tree = ttk.Treeview(self.tree_frame, columns=("id", "description", "category", "amount", "type", "payment_mode", "date"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("description", text="Description")
        self.tree.heading("category", text="Category")
        self.tree.heading("amount", text="Amount")
        self.tree.heading("type", text="Type")
        self.tree.heading("payment_mode", text="Payment Mode")
        self.tree.heading("date", text="Date")

        self.tree.column("id", width=30)
        self.tree.column("description", width=150)
        self.tree.column("category", width=80)
        self.tree.column("amount", width=80)
        self.tree.column("type", width=70)
        self.tree.column("payment_mode", width=100)
        self.tree.column("date", width=90)
        self.tree.pack(pady=10)
        self.load_transactions()

        # Buttons
        self.add_button = tk.Button(self.input_frame, text="Add Transaction", command=self.add_transaction, width=20, bg="green", fg="white")
        self.add_button.grid(row=7, column=0, columnspan=3, pady=15)

        # --- Action Buttons Row ---
        btn_frame = tk.Frame(self.root, bg="#0A192F")
        btn_frame.pack(pady=10)

        # Spending Pattern Analysis
        self.analysis_button = tk.Button(btn_frame, text="📊 Spending Analysis", command=self.show_spending_analysis, width=22, bg="#1976D2", fg="white", font=("Arial", 9, "bold"))
        self.analysis_button.grid(row=0, column=0, padx=5, pady=3)

        # AI Forecast (merged prediction + forecast)
        self.forecast_button = tk.Button(btn_frame, text="📈 AI Forecast", command=self.show_ai_forecast, width=22, bg="#7C4DFF", fg="white", font=("Arial", 9, "bold"))
        self.forecast_button.grid(row=0, column=1, padx=5, pady=3)

        # Smart Budget Suggestions
        self.budget_button = tk.Button(btn_frame, text="💰 Smart Budget", command=self.show_budget_suggestions, width=22, bg="#00897B", fg="white", font=("Arial", 9, "bold"))
        self.budget_button.grid(row=0, column=2, padx=5, pady=3)

        # Smart Alerts
        self.alerts_button = tk.Button(btn_frame, text="🔔 Smart Alerts", command=self.show_smart_alerts, width=22, bg="#C62828", fg="white", font=("Arial", 9, "bold"))
        self.alerts_button.grid(row=1, column=0, padx=5, pady=3)

        # Utility row
        btn_frame2 = tk.Frame(self.root, bg="#0A192F")
        btn_frame2.pack(pady=5)

        self.test_data_button = tk.Button(btn_frame2, text="🧪 Load Test Data", command=self.load_test_data, width=22, bg="#FF6F00", fg="white", font=("Arial", 9))
        self.test_data_button.grid(row=0, column=0, padx=5)

        self.delete_button = tk.Button(btn_frame2, text="🗑️ Delete Transaction", command=self.delete_selected_record, width=22, bg="#455A64", fg="white", font=("Arial", 9))
        self.delete_button.grid(row=0, column=1, padx=5)

        self.logout_button = tk.Button(btn_frame2, text="🚪 Logout", command=self.logout, width=22, bg="#D32F2F", fg="white", font=("Arial", 9))
        self.logout_button.grid(row=0, column=2, padx=5)
        

    def apply_styles(self):
        """Apply the custom styles to the widgets."""
        style = ttk.Style()
        
        # General widget style
        style.configure("TLabel", font=("Arial", 10), background="#f4f4f9", foreground="black")
        style.configure("TButton", font=("Arial", 10), background="#4CAF50", foreground="white", padding=10)
        style.configure("TButton:hover", background="#45a049")

        # Accent buttons (Add, Show Analysis, etc.)
        style.configure("AccentButton.TButton", font=("Arial", 10, "bold"), background="#2196F3", foreground="white", padding=10)
        style.map("AccentButton.TButton", background=[('active', '#1976D2')])

        # Treeview styling
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#333", foreground="white")
        style.configure("Treeview", font=("Arial", 10), background="#f9f9f9", foreground="black", rowheight=25)
        style.map("Treeview", background=[('selected', '#4CAF50')])

        # Input frame styling
        style.configure("InputFrame.TFrame", background="#ffffff")

    def toggle_category_field(self, event=None):
        """Shows or hides the category & description fields based on type selection."""
        selected_type = self.type_combobox.get()

        if selected_type == "Expense":
            # Show description field with AI detection
            self.desc_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
            self.desc_entry.grid(row=3, column=1, padx=5, pady=5)
            self.ai_indicator_frame.grid(row=3, column=2, padx=5, pady=5, sticky="w")
            # Show category field
            self.category_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
            self.category_combobox.grid(row=4, column=1, padx=5, pady=5)
        else:
            self.desc_label.grid_remove()
            self.desc_entry.grid_remove()
            self.ai_indicator_frame.grid_remove()
            self.category_label.grid_remove()
            self.category_combobox.grid_remove()
            self.ai_badge.config(text="")

    def _on_desc_key(self, event=None):
        """Debounced handler for real-time AI classification as user types."""
        if self._classify_after_id:
            self.root.after_cancel(self._classify_after_id)
        self._classify_after_id = self.root.after(300, self._run_classification)

    def _run_classification(self):
        """Run AI classification on the current description text."""
        description = self.desc_entry.get().strip()
        if not description:
            self.ai_badge.config(text="", bg="lightblue")
            return

        result = self.classifier.classify(description)
        category = result["category"]
        confidence = result["confidence"]
        method = result["method"]

        # Auto-fill category dropdown
        self.category_combobox.set(category)

        # Update AI badge
        if confidence >= 80:
            badge_color = "#00C853"
            badge_text = f"🤖 {category} ({confidence:.0f}%) • {method}"
        elif confidence >= 50:
            badge_color = "#FF8F00"
            badge_text = f"🤖 {category} ({confidence:.0f}%) • {method}"
        else:
            badge_color = "#757575"
            badge_text = f"🤖 {category}? ({confidence:.0f}%)"

        self.ai_badge.config(text=badge_text, fg=badge_color)

    def add_transaction(self):
        """Handles adding a new transaction to the database."""
        type_ = self.type_combobox.get()
        category = self.category_combobox.get() if type_ == "Expense" else "N/A"
        amount = self.amount_entry.get()
        date = self.date_entry.get()
        payment_mode = self.payment_mode_combobox.get()
        description = self.desc_entry.get().strip() if type_ == "Expense" else ""

        if not (amount and type_ and date and payment_mode):
            messagebox.showwarning("Input Error", "All fields are required!")
            return

        try:
            amount = float(amount)
            self.cursor.execute(
                "INSERT INTO transactions (username, category, amount, type, payment_mode, date, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.username, category, amount, type_, payment_mode, date, description)
            )
            self.conn.commit()
            self.load_transactions()  # Refresh transactions immediately
            messagebox.showinfo("Success", "Transaction added successfully!")

            # Clear inputs properly
            self.category_combobox.set("")  
            self.amount_entry.delete(0, tk.END)
            self.type_combobox.set("")
            self.payment_mode_combobox.set("")
            self.desc_entry.delete(0, tk.END)
            self.ai_badge.config(text="")
            self.date_entry.set_date(datetime.today())  
            self.toggle_category_field()  # Hide description & category fields

        except ValueError:
            messagebox.showwarning("Input Error", "Amount must be a number!")

    def load_transactions(self):
        """Loads transactions for the logged-in user and displays them in the GUI."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.cursor.execute("SELECT id, COALESCE(description, ''), category, amount, type, payment_mode, date FROM transactions WHERE username = ?", (self.username,))
        
        for row in self.cursor.fetchall():
            self.tree.insert("", tk.END, values=row)

    def delete_selected_record(self):
        """Deletes the selected transaction from the Treeview and database."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a record to delete.")
            return

        # Get the selected record's ID
        record_id = self.tree.item(selected_item)["values"][0]

        # Confirm the deletion with the user
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete record {record_id}?"):
            try:
                self.cursor.execute("DELETE FROM transactions WHERE id = ?", (record_id,))
                self.conn.commit()
                self.load_transactions()  # Refresh the Treeview after deletion
                messagebox.showinfo("Success", f"Record {record_id} deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete record: {str(e)}")

    def show_spending_analysis(self):
        """Opens a comprehensive Spending Pattern Analysis window."""
        # Fetch all transactions for this user
        self.cursor.execute(
            "SELECT category, amount, type, payment_mode, date FROM transactions WHERE username = ?",
            (self.username,)
        )
        all_data = self.cursor.fetchall()

        if not all_data:
            messagebox.showinfo("No Data", "No transaction data available for analysis. Add some transactions first!")
            return

        # --- Compute Stats ---
        total_income = sum(r[1] for r in all_data if r[2] == "Income")
        total_expense = sum(r[1] for r in all_data if r[2] == "Expense")
        net_savings = total_income - total_expense
        expense_records = [r for r in all_data if r[2] == "Expense"]

        # Category breakdown
        category_totals = defaultdict(float)
        for r in expense_records:
            category_totals[r[0]] += r[1]

        # Payment mode breakdown
        payment_totals = defaultdict(float)
        for r in all_data:
            payment_totals[r[3]] += r[1]

        # Daily spending timeline
        daily_spending = defaultdict(float)
        daily_income = defaultdict(float)
        for r in all_data:
            try:
                date_str = r[4]
                if r[2] == "Expense":
                    daily_spending[date_str] += r[1]
                else:
                    daily_income[date_str] += r[1]
            except (ValueError, IndexError):
                pass

        # Top spending category
        top_category = max(category_totals, key=category_totals.get) if category_totals else "N/A"
        top_category_amount = category_totals.get(top_category, 0)

        # Number of unique days with transactions
        all_dates = set(r[4] for r in all_data)
        num_days = max(len(all_dates), 1)
        avg_daily_expense = total_expense / num_days

        # --- Build the Analysis Window ---
        analysis_win = tk.Toplevel(self.root)
        analysis_win.title(f"{self.username}'s Spending Pattern Analysis")
        analysis_win.geometry("1100x800")
        analysis_win.configure(bg="#0A192F")
        analysis_win.resizable(True, True)

        # Title
        tk.Label(analysis_win, text="📊 Spending Pattern Analysis",
                 font=("Montserrat", 20, "bold"), fg="white", bg="#0A192F").pack(pady=(15, 5))

        # === SUMMARY STATS BAR ===
        stats_frame = tk.Frame(analysis_win, bg="#112240", pady=10)
        stats_frame.pack(fill="x", padx=20, pady=(5, 10))

        stats = [
            ("💰 Total Income", f"₹{total_income:,.2f}", "#00E676"),
            ("💸 Total Expenses", f"₹{total_expense:,.2f}", "#FF5252"),
            ("🏦 Net Savings", f"₹{net_savings:,.2f}", "#64FFDA" if net_savings >= 0 else "#FF5252"),
            ("📅 Avg Daily Spend", f"₹{avg_daily_expense:,.2f}", "#FFD740"),
            ("🔥 Top Category", f"{top_category} (₹{top_category_amount:,.0f})", "#E040FB"),
        ]

        for i, (label, value, color) in enumerate(stats):
            card = tk.Frame(stats_frame, bg="#1E3A5F", padx=15, pady=8, relief="groove", bd=1)
            card.grid(row=0, column=i, padx=8, pady=5, sticky="nsew")
            stats_frame.columnconfigure(i, weight=1)
            tk.Label(card, text=label, font=("Arial", 9), fg="#8892B0", bg="#1E3A5F").pack()
            tk.Label(card, text=value, font=("Arial", 13, "bold"), fg=color, bg="#1E3A5F").pack()

        # === CHARTS AREA ===
        # Use matplotlib figure with 2x2 subplots
        fig = Figure(figsize=(11, 5.5), dpi=95, facecolor="#0A192F")

        # Color palette
        colors = ["#00E676", "#FF5252", "#FFD740", "#64FFDA", "#E040FB",
                  "#448AFF", "#FF6E40", "#B388FF", "#69F0AE", "#FF80AB"]

        # --- 1. Category Pie Chart (top-left) ---
        ax1 = fig.add_subplot(2, 2, 1)
        ax1.set_facecolor("#0A192F")
        if category_totals:
            cats = list(category_totals.keys())
            vals = list(category_totals.values())
            wedges, texts, autotexts = ax1.pie(
                vals, labels=cats, autopct="%1.1f%%", startangle=90,
                colors=colors[:len(cats)],
                textprops={"color": "white", "fontsize": 8}
            )
            for at in autotexts:
                at.set_fontsize(7)
                at.set_color("white")
            ax1.set_title("Expense by Category", color="white", fontsize=10, fontweight="bold")
        else:
            ax1.text(0.5, 0.5, "No expense data", ha="center", va="center", color="white")
            ax1.set_title("Expense by Category", color="white", fontsize=10)

        # --- 2. Category Bar Chart (top-right) ---
        ax2 = fig.add_subplot(2, 2, 2)
        ax2.set_facecolor("#112240")
        if category_totals:
            cats = list(category_totals.keys())
            vals = list(category_totals.values())
            bars = ax2.barh(cats, vals, color=colors[:len(cats)], edgecolor="#0A192F", height=0.6)
            ax2.set_xlabel("Amount (₹)", color="white", fontsize=8)
            ax2.set_title("Category-wise Spending", color="white", fontsize=10, fontweight="bold")
            ax2.tick_params(colors="white", labelsize=8)
            # Add value labels on bars
            for bar, val in zip(bars, vals):
                ax2.text(bar.get_width() + max(vals) * 0.02, bar.get_y() + bar.get_height() / 2,
                         f"₹{val:,.0f}", va="center", color="white", fontsize=7)
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            ax2.spines["bottom"].set_color("#233554")
            ax2.spines["left"].set_color("#233554")
        else:
            ax2.text(0.5, 0.5, "No expense data", ha="center", va="center", color="white")

        # --- 3. Spending Timeline (bottom-left) ---
        ax3 = fig.add_subplot(2, 2, 3)
        ax3.set_facecolor("#112240")
        if daily_spending or daily_income:
            all_date_keys = sorted(set(list(daily_spending.keys()) + list(daily_income.keys())))
            try:
                parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in all_date_keys]
            except ValueError:
                parsed_dates = list(range(len(all_date_keys)))

            exp_vals = [daily_spending.get(d, 0) for d in all_date_keys]
            inc_vals = [daily_income.get(d, 0) for d in all_date_keys]

            ax3.fill_between(parsed_dates, exp_vals, alpha=0.3, color="#FF5252")
            ax3.plot(parsed_dates, exp_vals, color="#FF5252", marker="o", markersize=4, linewidth=1.5, label="Expenses")
            ax3.fill_between(parsed_dates, inc_vals, alpha=0.3, color="#00E676")
            ax3.plot(parsed_dates, inc_vals, color="#00E676", marker="s", markersize=4, linewidth=1.5, label="Income")

            ax3.set_title("Income vs Expense Over Time", color="white", fontsize=10, fontweight="bold")
            ax3.set_xlabel("Date", color="white", fontsize=8)
            ax3.set_ylabel("Amount (₹)", color="white", fontsize=8)
            ax3.tick_params(colors="white", labelsize=7)
            ax3.legend(fontsize=7, facecolor="#112240", labelcolor="white", edgecolor="#233554")
            if isinstance(parsed_dates[0], datetime):
                ax3.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
                fig.autofmt_xdate(rotation=30)
            ax3.spines["top"].set_visible(False)
            ax3.spines["right"].set_visible(False)
            ax3.spines["bottom"].set_color("#233554")
            ax3.spines["left"].set_color("#233554")
        else:
            ax3.text(0.5, 0.5, "No timeline data", ha="center", va="center", color="white")

        # --- 4. Payment Mode Breakdown (bottom-right) ---
        ax4 = fig.add_subplot(2, 2, 4)
        ax4.set_facecolor("#112240")
        if payment_totals:
            modes = list(payment_totals.keys())
            mode_vals = list(payment_totals.values())
            bar_colors = ["#448AFF", "#FFD740", "#FF6E40", "#E040FB", "#64FFDA"]
            bars = ax4.bar(modes, mode_vals, color=bar_colors[:len(modes)], edgecolor="#0A192F", width=0.5)
            ax4.set_title("Spending by Payment Mode", color="white", fontsize=10, fontweight="bold")
            ax4.set_ylabel("Amount (₹)", color="white", fontsize=8)
            ax4.tick_params(colors="white", labelsize=7)
            # Add value labels on top of bars
            for bar, val in zip(bars, mode_vals):
                ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(mode_vals) * 0.02,
                         f"₹{val:,.0f}", ha="center", color="white", fontsize=7)
            ax4.spines["top"].set_visible(False)
            ax4.spines["right"].set_visible(False)
            ax4.spines["bottom"].set_color("#233554")
            ax4.spines["left"].set_color("#233554")
        else:
            ax4.text(0.5, 0.5, "No payment data", ha="center", va="center", color="white")

        fig.tight_layout(pad=2.0)

        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=analysis_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Close button
        tk.Button(analysis_win, text="Close", command=analysis_win.destroy,
                  bg="#FF5252", fg="white", font=("Arial", 10, "bold"), width=15).pack(pady=(0, 10))
    
    def load_test_data(self):
        """Seeds 5 months of sample data for testing the AI prediction feature."""
        if messagebox.askyesno("Load Test Data",
                               "This will REPLACE your current transactions with 5 months of sample data.\n\n"
                               "This is meant for testing the AI Prediction feature.\nContinue?"):
            count = seed_sample_data(self.username)
            self.load_transactions()
            messagebox.showinfo("Test Data Loaded",
                                f"✅ {count} sample transactions loaded across 5 months!\n\n"
                                f"Now click '🤖 AI Prediction' to see the ML prediction in action.")

    def show_budget_suggestions(self):
        """Opens the Smart Budget Suggestions dashboard."""
        advisor = BudgetAdvisor()
        report = advisor.generate_budget(self.username)

        if "error" in report:
            messagebox.showinfo("No Data", report["error"])
            return

        # --- Build Budget Window ---
        budget_win = tk.Toplevel(self.root)
        budget_win.title(f"💰 Smart Budget — {self.username}")
        budget_win.geometry("1000x780")
        budget_win.configure(bg="#0A192F")
        budget_win.resizable(True, True)

        # Scrollable canvas
        main_canvas = tk.Canvas(budget_win, bg="#0A192F", highlightthickness=0)
        scrollbar = ttk.Scrollbar(budget_win, orient="vertical", command=main_canvas.yview)
        scroll_frame = tk.Frame(main_canvas, bg="#0A192F")

        scroll_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # === HEADER ===
        tk.Label(scroll_frame, text="💰 Smart Budget Suggestions",
                 font=("Montserrat", 22, "bold"), fg="white", bg="#0A192F").pack(pady=(15, 3))
        tk.Label(scroll_frame, text=f"Based on {report['n_months_analyzed']} months of data • {report['framework']}",
                 font=("Arial", 10), fg="#8892B0", bg="#0A192F").pack(pady=(0, 10))

        # === OVERVIEW CARDS ===
        overview_frame = tk.Frame(scroll_frame, bg="#112240", pady=10)
        overview_frame.pack(fill="x", padx=25, pady=(5, 10))

        savings_color = "#00E676" if report['actual_savings_rate'] >= 20 else ("#FFD740" if report['actual_savings_rate'] >= 10 else "#FF5252")

        overview_stats = [
            ("💵 Avg Income", f"₹{report['avg_monthly_income']:,.0f}", "#00E676"),
            ("💸 Avg Expenses", f"₹{report['avg_monthly_expense']:,.0f}", "#FF5252"),
            ("🎯 Budget Target", f"₹{report['total_suggested_budget']:,.0f}", "#64FFDA"),
            ("📊 Savings Rate", f"{report['actual_savings_rate']}%", savings_color),
            ("🏦 Ideal Savings", f"₹{report['ideal_savings']:,.0f}/mo", "#448AFF"),
        ]

        for i, (label, value, color) in enumerate(overview_stats):
            card = tk.Frame(overview_frame, bg="#1E3A5F", padx=12, pady=8, relief="groove", bd=1)
            card.grid(row=0, column=i, padx=6, pady=5, sticky="nsew")
            overview_frame.columnconfigure(i, weight=1)
            tk.Label(card, text=label, font=("Arial", 8), fg="#8892B0", bg="#1E3A5F").pack()
            tk.Label(card, text=value, font=("Arial", 13, "bold"), fg=color, bg="#1E3A5F").pack()

        # === 50/30/20 ALLOCATION BAR ===
        alloc_frame = tk.Frame(scroll_frame, bg="#112240", padx=20, pady=12, relief="groove", bd=1)
        alloc_frame.pack(padx=25, pady=5, fill="x")

        tk.Label(alloc_frame, text="50/30/20 Budget Allocation",
                 font=("Arial", 11, "bold"), fg="white", bg="#112240").pack(anchor="w")

        # Visual allocation bar
        bar_frame = tk.Frame(alloc_frame, bg="#112240", height=30)
        bar_frame.pack(fill="x", pady=(8, 5))

        total_income = report['avg_monthly_income']
        if total_income > 0:
            needs_pct = report['needs_budget'] / total_income
            wants_pct = report['wants_budget'] / total_income
            savings_pct = 0.20
        else:
            needs_pct = 0.50
            wants_pct = 0.30
            savings_pct = 0.20

        # Create colored segments
        bar_canvas = tk.Canvas(bar_frame, height=28, bg="#112240", highlightthickness=0)
        bar_canvas.pack(fill="x")

        def draw_alloc_bar(event=None):
            bar_canvas.delete("all")
            w = bar_canvas.winfo_width()
            if w < 10:
                return
            x = 0
            segments = [
                (needs_pct, "#448AFF", f"Needs 50% (₹{report['needs_budget']:,.0f})"),
                (wants_pct, "#E040FB", f"Wants 30% (₹{report['wants_budget']:,.0f})"),
                (savings_pct, "#00E676", f"Save 20% (₹{report['ideal_savings']:,.0f})"),
            ]
            for pct, color, label in segments:
                seg_w = w * pct
                bar_canvas.create_rectangle(x, 0, x + seg_w, 28, fill=color, outline="")
                if seg_w > 60:
                    bar_canvas.create_text(x + seg_w / 2, 14, text=label, fill="white", font=("Arial", 7, "bold"))
                x += seg_w

        bar_canvas.bind("<Configure>", draw_alloc_bar)

        # === CATEGORY BUDGET CARDS WITH PROGRESS BARS ===
        tk.Label(scroll_frame, text="📊 Per-Category Budget Tracker",
                 font=("Arial", 13, "bold"), fg="white", bg="#0A192F").pack(anchor="w", padx=30, pady=(15, 5))

        category_budgets = report['category_budgets']
        # Sort: over-budget first, then by usage % descending
        sorted_cats = sorted(category_budgets.items(), key=lambda x: x[1]['usage_pct'], reverse=True)

        for cat, data in sorted_cats:
            cat_frame = tk.Frame(scroll_frame, bg="#112240", padx=20, pady=12, relief="groove", bd=1)
            cat_frame.pack(padx=25, pady=4, fill="x")

            # Top row: category name, type badge, status
            top_row = tk.Frame(cat_frame, bg="#112240")
            top_row.pack(fill="x")

            type_color = "#448AFF" if data['category_type'] == "Need" else "#E040FB"
            tk.Label(top_row, text=f"  {cat}  ", font=("Arial", 11, "bold"), fg="white", bg="#112240").pack(side="left")
            tk.Label(top_row, text=f" {data['category_type']} ", font=("Arial", 7, "bold"),
                     fg="white", bg=type_color).pack(side="left", padx=5)
            tk.Label(top_row, text=data['status'], font=("Arial", 10),
                     fg=data['status_color'], bg="#112240").pack(side="right")

            # Progress bar
            progress_frame = tk.Frame(cat_frame, bg="#0A192F", height=20)
            progress_frame.pack(fill="x", pady=(8, 4))

            progress_canvas = tk.Canvas(progress_frame, height=18, bg="#0A192F", highlightthickness=0)
            progress_canvas.pack(fill="x")

            usage = min(data['usage_pct'], 120)  # Cap at 120% for visual
            bar_color = data['status_color']

            def draw_progress(event=None, canvas=progress_canvas, pct=usage, color=bar_color):
                canvas.delete("all")
                w = canvas.winfo_width()
                if w < 10:
                    return
                # Background track
                canvas.create_rectangle(0, 2, w, 16, fill="#233554", outline="")
                # Filled portion
                fill_w = min(w * (pct / 100), w)
                canvas.create_rectangle(0, 2, fill_w, 16, fill=color, outline="")
                # 100% marker
                if pct > 5:
                    marker_x = w * (100 / max(pct, 100)) if pct > 100 else w
                    canvas.create_line(marker_x, 0, marker_x, 18, fill="white", width=1, dash=(3, 3))

            progress_canvas.bind("<Configure>", draw_progress)

            # Bottom row: amounts
            bottom_row = tk.Frame(cat_frame, bg="#112240")
            bottom_row.pack(fill="x")

            tk.Label(bottom_row, text=f"Spent: ₹{data['current_spent']:,.0f}",
                     font=("Arial", 9), fg="#CCD6F6", bg="#112240").pack(side="left")
            tk.Label(bottom_row, text=f"{data['usage_pct']:.0f}%",
                     font=("Arial", 9, "bold"), fg=data['status_color'], bg="#112240").pack(side="left", padx=10)
            tk.Label(bottom_row, text=f"Budget: ₹{data['suggested_budget']:,.0f}",
                     font=("Arial", 9), fg="#64FFDA", bg="#112240").pack(side="right")
            remaining_color = "#00E676" if data['remaining'] >= 0 else "#FF5252"
            remaining_text = f"Remaining: ₹{data['remaining']:,.0f}" if data['remaining'] >= 0 else f"Over by: ₹{abs(data['remaining']):,.0f}"
            tk.Label(bottom_row, text=remaining_text,
                     font=("Arial", 9), fg=remaining_color, bg="#112240").pack(side="right", padx=15)

        # === SMART SUGGESTIONS ===
        tk.Label(scroll_frame, text="💡 Smart Suggestions",
                 font=("Arial", 13, "bold"), fg="white", bg="#0A192F").pack(anchor="w", padx=30, pady=(15, 5))

        for suggestion in report['suggestions']:
            sug_frame = tk.Frame(scroll_frame, bg="#1A2A3A", padx=15, pady=10, relief="groove", bd=1)
            sug_frame.pack(padx=25, pady=3, fill="x")

            header_row = tk.Frame(sug_frame, bg="#1A2A3A")
            header_row.pack(fill="x")

            tk.Label(header_row, text=f"{suggestion['icon']} {suggestion['title']}",
                     font=("Arial", 10, "bold"), fg=suggestion['color'], bg="#1A2A3A").pack(side="left")

            severity_colors = {"HIGH": "#FF5252", "MEDIUM": "#FFD740", "LOW": "#00E676"}
            sev_color = severity_colors.get(suggestion['severity'], "#8892B0")
            tk.Label(header_row, text=f" {suggestion['severity']} ", font=("Arial", 7, "bold"),
                     fg="white", bg=sev_color).pack(side="right")

            tk.Label(sug_frame, text=suggestion['text'], font=("Arial", 9), fg="#CCD6F6",
                     bg="#1A2A3A", wraplength=880, justify="left").pack(anchor="w", pady=(5, 0))

        # Close button
        tk.Button(scroll_frame, text="Close", command=lambda: [main_canvas.unbind_all("<MouseWheel>"), budget_win.destroy()],
                  bg="#FF5252", fg="white", font=("Arial", 10, "bold"), width=15).pack(pady=15)
    def show_ai_forecast(self):
        """Opens the unified AI Forecast dashboard — combines prediction + forecast chart."""
        predictor = ExpensePredictor()
        data = predictor.get_monthly_data(self.username)

        if data is None or not data["monthly_expenses"]:
            messagebox.showinfo("No Data", "No expense data available. Add transactions or load test data first!")
            return

        # Also get the single-month prediction for the big card
        prediction_result = predictor.predict_next_month(self.username)
        if "error" in prediction_result:
            messagebox.showinfo("No Data", prediction_result["error"])
            return

        monthly_expenses = data["monthly_expenses"]
        monthly_category = data["monthly_category"]
        sorted_months = sorted(monthly_expenses.keys())
        expense_values = [monthly_expenses[m] for m in sorted_months]
        n_months = len(sorted_months)

        # --- Multi-month forecasting ---
        import numpy as np
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import PolynomialFeatures

        X = np.arange(n_months).reshape(-1, 1)
        y = np.array(expense_values)

        poly = PolynomialFeatures(degree=min(2, max(n_months - 1, 1)))
        X_poly = poly.fit_transform(X)

        model = LinearRegression()
        model.fit(X_poly, y)

        # Predict next 3 months
        forecast_months = 3
        predictions = []
        prediction_labels = []
        last_month_dt = datetime.strptime(sorted_months[-1] + "-01", "%Y-%m-%d")

        for i in range(1, forecast_months + 1):
            next_dt = last_month_dt
            for _ in range(i):
                next_dt = (next_dt.replace(day=28) + timedelta(days=4)).replace(day=1)
            X_next = poly.transform(np.array([[n_months - 1 + i]]))
            pred = max(0, model.predict(X_next)[0])
            predictions.append(pred)
            prediction_labels.append(next_dt.strftime("%b %Y"))

        residuals = y - model.predict(X_poly)
        std_error = np.std(residuals)
        upper_bound = [p + 1.5 * std_error for p in predictions]
        lower_bound = [max(0, p - 1.5 * std_error) for p in predictions]

        # Category forecast (proportional)
        recent_months = sorted_months[-min(3, n_months):]
        cat_proportions = defaultdict(float)
        cat_counts = defaultdict(int)
        for month in recent_months:
            total = monthly_expenses.get(month, 0)
            if total > 0 and month in monthly_category:
                for cat, amt in monthly_category[month].items():
                    cat_proportions[cat] += amt / total
                    cat_counts[cat] += 1
        for cat in cat_proportions:
            cat_proportions[cat] /= cat_counts[cat]

        # --- Build Unified Forecast Window ---
        forecast_win = tk.Toplevel(self.root)
        forecast_win.title(f"📈 AI Forecast — {self.username}")
        forecast_win.geometry("1050x800")
        forecast_win.configure(bg="#0A192F")

        main_canvas = tk.Canvas(forecast_win, bg="#0A192F", highlightthickness=0)
        scrollbar = ttk.Scrollbar(forecast_win, orient="vertical", command=main_canvas.yview)
        scroll_frame = tk.Frame(main_canvas, bg="#0A192F")
        scroll_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # === HEADER ===
        tk.Label(scroll_frame, text="📈 AI Expense Forecast",
                 font=("Montserrat", 22, "bold"), fg="white", bg="#0A192F").pack(pady=(15, 3))
        tk.Label(scroll_frame, text=f"ML-powered predictions based on {n_months} months of data • Polynomial Regression",
                 font=("Arial", 10), fg="#8892B0", bg="#0A192F").pack(pady=(0, 10))

        # === BIG PREDICTION CARD (from F2) ===
        pred_card = tk.Frame(scroll_frame, bg="#112240", padx=30, pady=20, relief="groove", bd=2)
        pred_card.pack(padx=25, pady=10, fill="x")

        tk.Label(pred_card, text=f"Predicted Spending — {prediction_result['next_month']}",
                 font=("Arial", 12), fg="#8892B0", bg="#112240").pack()
        tk.Label(pred_card, text=f"₹{predictions[0]:,.2f}",
                 font=("Montserrat", 36, "bold"), fg="#64FFDA", bg="#112240").pack(pady=(5, 10))

        # Trend, Confidence, Training Data row
        info_frame = tk.Frame(pred_card, bg="#112240")
        info_frame.pack(fill="x")

        # Trend card
        trend_card = tk.Frame(info_frame, bg="#1E3A5F", padx=15, pady=8)
        trend_card.grid(row=0, column=0, padx=10, sticky="nsew")
        info_frame.columnconfigure(0, weight=1)
        tk.Label(trend_card, text="Trend", font=("Arial", 9), fg="#8892B0", bg="#1E3A5F").pack()
        tk.Label(trend_card, text=prediction_result['trend'], font=("Arial", 14, "bold"),
                 fg=prediction_result['trend_color'], bg="#1E3A5F").pack()
        tk.Label(trend_card, text=f"{prediction_result['recent_change_pct']:+.1f}% vs last month",
                 font=("Arial", 8), fg="#8892B0", bg="#1E3A5F").pack()

        # Confidence card
        conf_card = tk.Frame(info_frame, bg="#1E3A5F", padx=15, pady=8)
        conf_card.grid(row=0, column=1, padx=10, sticky="nsew")
        info_frame.columnconfigure(1, weight=1)
        conf_color = "#00E676" if prediction_result['confidence'] > 60 else ("#FFD740" if prediction_result['confidence'] > 30 else "#FF5252")
        tk.Label(conf_card, text="Confidence", font=("Arial", 9), fg="#8892B0", bg="#1E3A5F").pack()
        tk.Label(conf_card, text=f"{prediction_result['confidence']}%", font=("Arial", 14, "bold"),
                 fg=conf_color, bg="#1E3A5F").pack()
        tk.Label(conf_card, text=prediction_result['method'], font=("Arial", 8), fg="#8892B0", bg="#1E3A5F").pack()

        # Uncertainty card
        unc_card = tk.Frame(info_frame, bg="#1E3A5F", padx=15, pady=8)
        unc_card.grid(row=0, column=2, padx=10, sticky="nsew")
        info_frame.columnconfigure(2, weight=1)
        tk.Label(unc_card, text="Uncertainty", font=("Arial", 9), fg="#8892B0", bg="#1E3A5F").pack()
        tk.Label(unc_card, text=f"±₹{std_error:,.0f}", font=("Arial", 14, "bold"),
                 fg="#FFD740", bg="#1E3A5F").pack()
        tk.Label(unc_card, text=f"{n_months} months training data",
                 font=("Arial", 8), fg="#8892B0", bg="#1E3A5F").pack()

        # === AI INSIGHT (from F2) ===
        advice_frame = tk.Frame(scroll_frame, bg="#1A3A2A", padx=20, pady=12, relief="groove", bd=1)
        advice_frame.pack(padx=25, pady=8, fill="x")
        tk.Label(advice_frame, text="💡 AI Insight", font=("Arial", 10, "bold"), fg="#69F0AE", bg="#1A3A2A").pack(anchor="w")
        tk.Label(advice_frame, text=prediction_result['trend_advice'], font=("Arial", 10), fg="white", bg="#1A3A2A",
                 wraplength=900, justify="left").pack(anchor="w", pady=(3, 0))

        # === FORECAST LINE CHART (from F5) ===
        fig = Figure(figsize=(10, 4.5), dpi=95, facecolor="#0A192F")
        colors = ["#00E676", "#FF5252", "#FFD740", "#64FFDA", "#E040FB",
                  "#448AFF", "#FF6E40", "#B388FF", "#69F0AE", "#FF80AB"]

        ax = fig.add_subplot(1, 1, 1)
        ax.set_facecolor("#112240")

        hist_labels = [m[-5:] for m in sorted_months]
        all_x = list(range(len(hist_labels) + len(prediction_labels)))
        all_labels = hist_labels + prediction_labels

        hist_x = list(range(len(hist_labels)))
        ax.plot(hist_x, expense_values, color="#448AFF", marker="o", markersize=6,
                linewidth=2.5, label="Actual Spending", zorder=5)
        ax.fill_between(hist_x, expense_values, alpha=0.15, color="#448AFF")

        forecast_x = list(range(len(hist_labels) - 1, len(hist_labels) + len(predictions)))
        forecast_y = [expense_values[-1]] + predictions
        ax.plot(forecast_x, forecast_y, color="#64FFDA", marker="D", markersize=6,
                linewidth=2.5, linestyle="--", label="Forecast", zorder=5)

        ci_x = list(range(len(hist_labels), len(hist_labels) + len(predictions)))
        ax.fill_between(ci_x, lower_bound, upper_bound, alpha=0.2, color="#64FFDA",
                        label="Confidence Interval")

        ax.axvline(x=len(hist_labels) - 0.5, color="white", linestyle=":", alpha=0.5, linewidth=1)
        ax.text(len(hist_labels) - 0.5, max(expense_values + predictions) * 1.05,
                "← Actual | Forecast →", ha="center", color="#8892B0", fontsize=8)

        for x, val in zip(hist_x, expense_values):
            ax.annotate(f"₹{val:,.0f}", (x, val), textcoords="offset points",
                        xytext=(0, 12), ha="center", color="white", fontsize=7)
        for x, val in zip(ci_x, predictions):
            ax.annotate(f"₹{val:,.0f}", (x, val), textcoords="offset points",
                        xytext=(0, 12), ha="center", color="#64FFDA", fontsize=7, fontweight="bold")

        ax.set_xticks(all_x)
        ax.set_xticklabels(all_labels, rotation=30)
        ax.set_title("Monthly Expense Forecast with Confidence Interval",
                      color="white", fontsize=12, fontweight="bold", pad=15)
        ax.set_ylabel("Amount (₹)", color="white", fontsize=9)
        ax.tick_params(colors="white", labelsize=8)

        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#448AFF", label="Actual"),
            Patch(facecolor="#64FFDA", label="Forecast"),
            Patch(facecolor="#64FFDA", alpha=0.3, label="Confidence Interval")
        ]
        ax.legend(handles=legend_elements, fontsize=7, facecolor="#112240",
                  labelcolor="white", edgecolor="#233554", loc="upper left")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color("#233554")
        ax.spines["left"].set_color("#233554")
        ax.set_ylim(bottom=0)
        fig.tight_layout(pad=2.0)

        canvas = FigureCanvasTkAgg(fig, master=scroll_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=20, pady=10)

        # === CATEGORY FORECAST + PIE (side by side concept, stacked here) ===
        # Predicted category pie chart (from F2)
        fig2 = Figure(figsize=(5, 3), dpi=95, facecolor="#0A192F")
        ax2 = fig2.add_subplot(1, 1, 1)
        ax2.set_facecolor("#0A192F")
        pred_cats = prediction_result.get('predicted_categories', {})
        if pred_cats:
            cats = list(pred_cats.keys())
            vals = list(pred_cats.values())
            wedges, texts, autotexts = ax2.pie(
                vals, labels=cats, autopct="%1.1f%%", startangle=90,
                colors=colors[:len(cats)],
                textprops={"color": "white", "fontsize": 9}
            )
            for at in autotexts:
                at.set_fontsize(8)
                at.set_color("white")
            ax2.set_title("Predicted Category Split", color="white", fontsize=11, fontweight="bold")
        fig2.tight_layout(pad=1.5)
        canvas2 = FigureCanvasTkAgg(fig2, master=scroll_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="x", padx=80, pady=5)

        # === 3-MONTH OUTLOOK TABLE (from F5) ===
        outlook_frame = tk.Frame(scroll_frame, bg="#112240", padx=20, pady=15, relief="groove", bd=1)
        outlook_frame.pack(padx=25, pady=10, fill="x")
        tk.Label(outlook_frame, text="🔮 3-Month Outlook",
                 font=("Arial", 12, "bold"), fg="white", bg="#112240").pack(anchor="w", pady=(0, 8))

        for i, (label, pred, low, high) in enumerate(zip(prediction_labels, predictions, lower_bound, upper_bound)):
            row_bg = "#1E3A5F" if i % 2 == 0 else "#172A45"
            row = tk.Frame(outlook_frame, bg=row_bg)
            row.pack(fill="x")
            tk.Label(row, text=f"📅 {label}", font=("Arial", 10, "bold"), fg="white",
                     bg=row_bg, width=15, anchor="w").pack(side="left", padx=10, pady=5)
            tk.Label(row, text=f"₹{pred:,.0f}", font=("Arial", 11, "bold"), fg="#64FFDA",
                     bg=row_bg, width=12).pack(side="left", padx=5, pady=5)
            tk.Label(row, text=f"Range: ₹{low:,.0f} — ₹{high:,.0f}", font=("Arial", 9),
                     fg="#8892B0", bg=row_bg).pack(side="left", padx=10, pady=5)

        # === CATEGORY BREAKDOWN TABLE ===
        table_frame = tk.Frame(scroll_frame, bg="#112240", padx=20, pady=15, relief="groove", bd=1)
        table_frame.pack(padx=25, pady=10, fill="x")
        tk.Label(table_frame, text="📋 Category-wise Forecast (Next Month)",
                 font=("Arial", 12, "bold"), fg="white", bg="#112240").pack(anchor="w", pady=(0, 10))

        header_frame = tk.Frame(table_frame, bg="#233554")
        header_frame.pack(fill="x")
        for col, w in [("Category", 15), ("Predicted", 15), ("Share", 10)]:
            tk.Label(header_frame, text=col, font=("Arial", 10, "bold"), fg="white",
                     bg="#233554", width=w).pack(side="left", padx=10, pady=5)

        sorted_cats = sorted(cat_proportions.items(), key=lambda x: x[1], reverse=True)
        for idx, (cat, prop) in enumerate(sorted_cats):
            row_bg = "#1E3A5F" if idx % 2 == 0 else "#172A45"
            row_frame = tk.Frame(table_frame, bg=row_bg)
            row_frame.pack(fill="x")
            pred_amt = predictions[0] * prop
            tk.Label(row_frame, text=cat, font=("Arial", 10), fg="white",
                     bg=row_bg, width=15, anchor="w").pack(side="left", padx=10, pady=4)
            tk.Label(row_frame, text=f"₹{pred_amt:,.0f}", font=("Arial", 10, "bold"),
                     fg="#64FFDA", bg=row_bg, width=15, anchor="w").pack(side="left", padx=10, pady=4)
            tk.Label(row_frame, text=f"{prop * 100:.1f}%", font=("Arial", 10),
                     fg="#8892B0", bg=row_bg, width=10, anchor="w").pack(side="left", padx=10, pady=4)

        tk.Button(scroll_frame, text="Close", command=lambda: [main_canvas.unbind_all("<MouseWheel>"), forecast_win.destroy()],
                  bg="#FF5252", fg="white", font=("Arial", 10, "bold"), width=15).pack(pady=15)

    def show_smart_alerts(self):
        """Opens the Smart Alerts dashboard."""
        engine = SmartAlerts()
        alerts = engine.generate_alerts(self.username)

        # --- Build Alerts Window ---
        alerts_win = tk.Toplevel(self.root)
        alerts_win.title(f"🔔 Smart Alerts — {self.username}")
        alerts_win.geometry("850x650")
        alerts_win.configure(bg="#0A192F")
        alerts_win.resizable(True, True)

        # Scrollable
        main_canvas = tk.Canvas(alerts_win, bg="#0A192F", highlightthickness=0)
        scrollbar = ttk.Scrollbar(alerts_win, orient="vertical", command=main_canvas.yview)
        scroll_frame = tk.Frame(main_canvas, bg="#0A192F")
        scroll_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Header
        tk.Label(scroll_frame, text="🔔 Smart Alerts",
                 font=("Montserrat", 22, "bold"), fg="white", bg="#0A192F").pack(pady=(15, 3))

        if not alerts:
            tk.Label(scroll_frame, text="No alerts to show. Add some transactions first!",
                     font=("Arial", 12), fg="#8892B0", bg="#0A192F").pack(pady=30)
            tk.Button(scroll_frame, text="Close", command=lambda: [main_canvas.unbind_all("<MouseWheel>"), alerts_win.destroy()],
                      bg="#FF5252", fg="white", font=("Arial", 10, "bold"), width=15).pack(pady=15)
            return

        # === ALERT SUMMARY BAR ===
        severity_counts = defaultdict(int)
        for a in alerts:
            severity_counts[a.get("severity", "LOW")] += 1

        summary_frame = tk.Frame(scroll_frame, bg="#112240", pady=10)
        summary_frame.pack(fill="x", padx=25, pady=(5, 10))

        total_alerts = len(alerts)
        critical_count = severity_counts.get("CRITICAL", 0)
        high_count = severity_counts.get("HIGH", 0)
        medium_count = severity_counts.get("MEDIUM", 0)
        ok_count = severity_counts.get("OK", 0)

        # Health score: lower is worse
        health_score = max(0, 100 - critical_count * 30 - high_count * 15 - medium_count * 5 + ok_count * 10)
        health_score = min(health_score, 100)
        health_color = "#00E676" if health_score >= 70 else ("#FFD740" if health_score >= 40 else "#FF5252")

        summary_stats = [
            ("🔔 Total Alerts", str(total_alerts), "#448AFF"),
            ("🚨 Critical", str(critical_count), "#D50000" if critical_count > 0 else "#555"),
            ("⚠️ High", str(high_count), "#FF5252" if high_count > 0 else "#555"),
            ("💡 Medium", str(medium_count), "#FFD740" if medium_count > 0 else "#555"),
            ("💚 Health Score", f"{health_score}/100", health_color),
        ]

        for i, (label, value, color) in enumerate(summary_stats):
            card = tk.Frame(summary_frame, bg="#1E3A5F", padx=12, pady=8, relief="groove", bd=1)
            card.grid(row=0, column=i, padx=6, pady=5, sticky="nsew")
            summary_frame.columnconfigure(i, weight=1)
            tk.Label(card, text=label, font=("Arial", 8), fg="#8892B0", bg="#1E3A5F").pack()
            tk.Label(card, text=value, font=("Arial", 14, "bold"), fg=color, bg="#1E3A5F").pack()

        # === HEALTH BAR ===
        health_bar_frame = tk.Frame(scroll_frame, bg="#112240", padx=20, pady=10, relief="groove", bd=1)
        health_bar_frame.pack(padx=25, pady=5, fill="x")

        tk.Label(health_bar_frame, text="Financial Health", font=("Arial", 10, "bold"),
                 fg="white", bg="#112240").pack(anchor="w")

        health_canvas = tk.Canvas(health_bar_frame, height=22, bg="#112240", highlightthickness=0)
        health_canvas.pack(fill="x", pady=(5, 3))

        def draw_health_bar(event=None):
            health_canvas.delete("all")
            w = health_canvas.winfo_width()
            if w < 10:
                return
            health_canvas.create_rectangle(0, 2, w, 20, fill="#233554", outline="")
            fill_w = w * (health_score / 100)
            health_canvas.create_rectangle(0, 2, fill_w, 20, fill=health_color, outline="")
            health_canvas.create_text(w / 2, 11, text=f"{health_score}%", fill="white",
                                       font=("Arial", 8, "bold"))
        health_canvas.bind("<Configure>", draw_health_bar)

        health_labels = {
            (80, 101): "Excellent — Your finances are in great shape!",
            (60, 80): "Good — A few areas need attention.",
            (40, 60): "Fair — Several warnings need your review.",
            (0, 40): "Needs Attention — Take action on the critical alerts below.",
        }
        health_msg = "Review your alerts below."
        for (lo, hi), msg in health_labels.items():
            if lo <= health_score < hi:
                health_msg = msg
                break
        tk.Label(health_bar_frame, text=health_msg, font=("Arial", 9),
                 fg=health_color, bg="#112240").pack(anchor="w")

        # === ALERT CARDS ===
        tk.Label(scroll_frame, text="📋 Alert Details",
                 font=("Arial", 13, "bold"), fg="white", bg="#0A192F").pack(anchor="w", padx=30, pady=(15, 5))

        severity_bg = {
            "CRITICAL": "#2D0000",
            "HIGH": "#1A0A0A",
            "MEDIUM": "#1A1A0A",
            "LOW": "#0A1A1A",
            "OK": "#0A1A0A",
        }
        severity_border = {
            "CRITICAL": "#D50000",
            "HIGH": "#FF5252",
            "MEDIUM": "#FFD740",
            "LOW": "#8892B0",
            "OK": "#00E676",
        }

        for alert in alerts:
            sev = alert.get("severity", "LOW")
            card_bg = severity_bg.get(sev, "#1A2A3A")
            border_color = severity_border.get(sev, "#555")

            alert_card = tk.Frame(scroll_frame, bg=card_bg, padx=18, pady=12, relief="groove", bd=1,
                                  highlightbackground=border_color, highlightthickness=2)
            alert_card.pack(padx=25, pady=5, fill="x")

            # Header row
            header = tk.Frame(alert_card, bg=card_bg)
            header.pack(fill="x")

            tk.Label(header, text=f"{alert['icon']} {alert['title']}",
                     font=("Arial", 11, "bold"), fg=alert["color"], bg=card_bg).pack(side="left")

            # Severity badge
            badge_colors = {"CRITICAL": "#D50000", "HIGH": "#FF5252", "MEDIUM": "#FF8F00", "LOW": "#555", "OK": "#00C853"}
            badge_bg = badge_colors.get(sev, "#555")
            tk.Label(header, text=f"  {sev}  ", font=("Arial", 7, "bold"),
                     fg="white", bg=badge_bg).pack(side="right")

            # Alert type tag
            tk.Label(header, text=f"  {alert['type']}  ", font=("Arial", 7),
                     fg="#8892B0", bg="#233554").pack(side="right", padx=5)

            # Message
            tk.Label(alert_card, text=alert["message"], font=("Arial", 9), fg="#CCD6F6",
                     bg=card_bg, wraplength=750, justify="left").pack(anchor="w", pady=(8, 0))

        # Close button
        tk.Button(scroll_frame, text="Close", command=lambda: [main_canvas.unbind_all("<MouseWheel>"), alerts_win.destroy()],
                  bg="#FF5252", fg="white", font=("Arial", 10, "bold"), width=15).pack(pady=15)

    def logout(self):
        """Logs out the user and returns to the login screen."""
        self.root.destroy()  # Close the finance tracker window
        restart_app()  # Call restart_app() correctly

if __name__ == "__main__":
        root = tk.Tk()

        # Start the login page first
        login = LoginPage(root, open_finance_tracker)
        root.mainloop()
