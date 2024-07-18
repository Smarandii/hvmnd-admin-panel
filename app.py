import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
DATABASE_URL = os.getenv("POSTGRES_URL")


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', "id")
    order = request.args.get('order', 'asc')
    sort_order = 'ASC' if order == 'asc' else 'DESC'

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = "SELECT id, telegram_id, total_spent, balance, first_name, last_name, username, language_code FROM users"
        if search_query:
            search_conditions = f"""
                WHERE username ILIKE '%{search_query}%'
                OR first_name ILIKE '%{search_query}%'
                OR last_name ILIKE '%{search_query}%'
                OR language_code ILIKE '%{search_query}%'
            """
            try:
                numeric_search = float(search_query)
                numeric_conditions = f"""
                    OR id = {numeric_search}
                    OR balance = {numeric_search}
                    OR total_spent = {numeric_search}
                """
                search_conditions += numeric_conditions
            except ValueError:
                pass
            query += search_conditions

        query += f" ORDER BY {sort_by} {sort_order}"

        cur.execute(query)
        users = cur.fetchall()

        cur.execute("""
            SELECT SUM(balance) as total_balance, SUM(total_spent) as total_spent FROM users
        """)
        totals = cur.fetchone()
        totals = {
            'total_balance': round(totals[0], 2),
            'total_spent': round(totals[1], 2)
        }

        cur.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")
        users = []
        totals = {"total_balance": 0.0, "total_spent": 0.0}

    return render_template('users.html', users=users, totals=totals, search=search_query)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == os.getenv("ADMIN_LOGIN") and password == os.getenv("ADMIN_PASSWORD"):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid Credentials. Please try again.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/update_balance/<int:user_id>', methods=['POST'])
def update_balance(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    new_balance = request.form['balance']

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE users SET balance = %s WHERE id = %s
        """, (float(new_balance), int(user_id)))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

    return redirect(url_for('index'))


@app.route('/payment_history/<int:user_id>/')
def payment_history(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    sort_by = request.args.get('sort', 'datetime')
    order = request.args.get('order', 'desc')
    sort_order = 'ASC' if order == 'asc' else 'DESC'

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = f"""
            SELECT id, user_id, amount, status, datetime FROM payments WHERE user_id = %s ORDER BY {sort_by} {sort_order}
        """
        cur.execute(query, (user_id,))
        payments = cur.fetchall()

        cur.execute("SELECT id, telegram_id, first_name, last_name, username FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        return render_template('payment_history.html', payments=payments, user=user)
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Error fetching payment history"


if __name__ == '__main__':
    app.run(debug=bool(os.getenv("IS_DEBUG", False)))
