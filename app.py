from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secretkeyfor2users'

USERS = {
    'Basharahmed': 'Bashar455',
    'Zikranahmed': 'ZikranCR7'
}

# -------- DB INIT --------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        amount REAL,
        description TEXT,
        date TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS balances (
        username TEXT PRIMARY KEY,
        balance REAL
    )''')
    
    # Add users to balance table if not present
    for user in USERS:
        c.execute("SELECT * FROM balances WHERE username = ?", (user,))
        if not c.fetchone():
            c.execute("INSERT INTO balances (username, balance) VALUES (?, ?)", (user, 0))
    
    conn.commit()
    conn.close()

# -------- ROUTES --------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if USERS.get(username) == password:
            session['user'] = username
            return redirect('/dashboard')
        return "Invalid login"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE username = ?", (session['user'],))
    transactions = c.fetchall()

    c.execute("SELECT balance FROM balances WHERE username = ?", (session['user'],))
    balance = c.fetchone()[0]

    conn.close()
    return render_template('dashboard.html', user=session['user'], transactions=transactions, balance=balance)

@app.route('/add', methods=['POST'])
def add():
    if 'user' not in session:
        return redirect('/')
    
    action = request.form['action']  # deposit or withdraw
    amount = float(request.form['amount'])
    description = request.form['description']
    date = request.form['date']
    
    if action == 'withdraw':
        amount = -abs(amount)  # make it negative

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Update balance
    c.execute("SELECT balance FROM balances WHERE username = ?", (session['user'],))
    current = c.fetchone()[0]
    new_balance = current + amount

    if new_balance < 0:
        conn.close()
        return "Insufficient funds"

    c.execute("UPDATE balances SET balance = ? WHERE username = ?", (new_balance, session['user']))
    c.execute("INSERT INTO transactions (username, amount, description, date) VALUES (?, ?, ?, ?)",
              (session['user'], amount, description, date))
    conn.commit()
    conn.close()
    return redirect('/dashboard')


@app.route('/delete/<int:id>')
def delete(id):
    if 'user' not in session:
        return redirect('/')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id = ? AND username = ?", (id, session['user']))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    init_db()  # 👈 This line is CRUCIAL
    app.run(debug=True)
