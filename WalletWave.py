from flask import Flask, render_template, request, jsonify
import csv
from datetime import datetime

app = Flask(__name__)

# Core data structures and files
users = {}
expenses = []
user_id_counter = 1

currency = "USD"
conversion_rates = {
    "USD": 1.0,
    "INR": 75.0,
    "EUR": 0.9,
}

USER_FILE = "users.csv"
EXPENSE_FILE = "expenses.csv"

# Loaders and savers for persistence
def load_users():
    global user_id_counter
    try:
        with open(USER_FILE, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                user_id = int(row['user_id'])
                users[user_id] = {
                    'username': row['username'],
                    'email': row['email'],
                    'balance': float(row['balance'])
                }
                user_id_counter = max(user_id_counter, user_id + 1)
    except FileNotFoundError:
        pass

def save_users():
    with open(USER_FILE, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=['user_id', 'username', 'email', 'balance'])
        writer.writeheader()
        for user_id, user_info in users.items():
            writer.writerow({
                'user_id': user_id,
                'username': user_info['username'],
                'email': user_info['email'],
                'balance': user_info['balance']
            })

def load_expenses():
    try:
        with open(EXPENSE_FILE, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                expense = {
                    'amount': float(row['amount']),
                    'description': row['description'],
                    'paid_by': int(row['paid_by']),
                    'participants': list(map(int, row['participants'].split(','))),
                    'date': row.get('date', None)
                }
                expenses.append(expense)
    except FileNotFoundError:
        pass

def save_expenses():
    with open(EXPENSE_FILE, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=['amount', 'description', 'paid_by', 'participants', 'date'])
        writer.writeheader()
        for expense in expenses:
            writer.writerow({
                'amount': expense['amount'],
                'description': expense['description'],
                'paid_by': expense['paid_by'],
                'participants': ','.join(map(str, expense['participants'])),
                'date': expense.get('date', '')
            })

# Flask routes for functionality
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    global user_id_counter
    data = request.get_json()
    username = data['username']
    email = data['email']
    users[user_id_counter] = {'username': username, 'email': email, 'balance': 0}
    user_id_counter += 1
    save_users()
    return jsonify({"message": "User registered successfully!", "user_id": user_id_counter - 1})

@app.route("/add_expense", methods=["POST"])
def add_expense_route():
    data = request.get_json()
    amount = float(data['amount'])
    description = data['description']
    paid_by = int(data['paid_by'])
    participants = list(map(int, data['participants']))
    expense_date = data.get('date', datetime.now().strftime("%Y-%m-%d"))

    if paid_by not in participants:
        participants.append(paid_by)

    # Calculate shares
    exact_share = amount / len(participants)
    rounded_shares = [round(exact_share, 2) for _ in participants]
    total_rounded = sum(rounded_shares)
    if total_rounded != amount:
        diff = amount - total_rounded
        rounded_shares[0] += diff

    # Add expense
    expense = {
        'amount': amount,
        'description': description,
        'paid_by': paid_by,
        'participants': participants,
        'date': expense_date
    }
    expenses.append(expense)

    # Update balances
    for i, participant_id in enumerate(participants):
        if participant_id != paid_by:
            users[participant_id]['balance'] -= rounded_shares[i]
    users[paid_by]['balance'] += amount - sum(rounded_shares)

    save_expenses()
    save_users()
    return jsonify({"message": "Expense added successfully!"})

@app.route("/balances", methods=["GET"])
def balances():
    user_balances = {
        user_info['username']: user_info['balance']
        for user_id, user_info in users.items()
    }
    return jsonify(user_balances)

@app.route("/track_monthly_expenses", methods=["GET"])
def track_monthly_expenses_route():
    monthly_totals = {}
    for expense in expenses:
        expense_date = expense.get('date', None)
        if not expense_date:
            continue
        month_year = datetime.strptime(expense_date, "%Y-%m-%d").strftime("%Y-%m")
        monthly_totals[month_year] = monthly_totals.get(month_year, 0) + expense['amount']
    return jsonify(monthly_totals)

@app.route("/set_goal", methods=["POST"])
def set_goal_route():
    data = request.get_json()
    target_amount = float(data['target_amount'])
    target_date_str = data['target_date']
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    today = datetime.today()
    days_left = (target_date - today).days
    if days_left <= 0:
        return jsonify({"error": "Target date must be in the future."}), 400
    daily_savings = target_amount / days_left
    return jsonify({
        "message": f"To reach your goal of {target_amount:.2f} {currency} by {target_date_str}, you need to save {daily_savings:.2f} {currency} every day."
    })

# App initialization
if __name__ == "__main__":
    load_users()
    load_expenses()
    app.run(debug=True)
