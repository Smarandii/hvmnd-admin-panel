import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
DATABASE_URL = os.getenv("POSTGRES_URL")

# Create a connection pool
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1,  # Minimum number of connections
    1,  # Maximum number of connections
    DATABASE_URL
)


def get_db_connection():
    try:
        conn = connection_pool.getconn()
        if conn:
            print("Successfully received connection from connection pool")
            return conn
    except Exception as e:
        print(f"Error: {e}")


def release_db_connection(conn):
    try:
        connection_pool.putconn(conn)
        print("Successfully returned connection to connection pool")
    except Exception as e:
        print(f"Error: {e}")


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
        release_db_connection(conn)
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
        release_db_connection(conn)
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
        release_db_connection(conn)

        return render_template('payment_history.html', payments=payments, user=user)
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Error fetching payment history"


@app.route('/edit_nodes')
def edit_nodes():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, old_id, any_desk_address, any_desk_password, status, software, price, renter, 
            rent_start_time, last_balance_update_timestamp, cpu, gpu, other_specs, licenses, machine_id 
            FROM nodes
        """)
        nodes = cur.fetchall()

        cur.close()
        release_db_connection(conn)
    except Exception as e:
        print(f"An error occurred: {e}")
        nodes = []

    return render_template('edit_nodes.html', nodes=nodes)


@app.route('/update_node/<int:node_id>', methods=['POST'])
def update_node(node_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    old_id = request.form['old_id']
    status = request.form['status']
    software = request.form['software']
    price = request.form['price']
    cpu = request.form['cpu']
    gpu = request.form['gpu']
    other_specs = request.form['other_specs']
    licenses = request.form['licenses']

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE nodes
            SET old_id = %s, status = %s, software = %s, price = %s, cpu = %s, gpu = %s, other_specs = %s, licenses = %s
            WHERE id = %s
        """, (old_id, status, software, price, cpu, gpu, other_specs, licenses, node_id))
        conn.commit()
        cur.close()
        release_db_connection(conn)
    except Exception as e:
        print(f"An error occurred: {e}")

    return redirect(url_for('edit_nodes'))


@app.route('/deactivate_node/<int:node_id>', methods=['POST'])
def deactivate_node(node_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE nodes SET status = 'unavailable' WHERE id = %s", (node_id,))
        conn.commit()
        cur.close()
        release_db_connection(conn)
    except Exception as e:
        print(f"An error occurred: {e}")

    return redirect(url_for('edit_nodes'))


@app.route('/edit_node/<int:node_id>', methods=['GET', 'POST'])
def edit_node(node_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        old_id = request.form['old_id']
        status = request.form['status']
        software = request.form['software']
        price = request.form['price']
        cpu = request.form['cpu']
        gpu = request.form['gpu']
        other_specs = request.form['other_specs']
        licenses = request.form['licenses']

        try:
            # Serialize the JSON fields
            software_json = json.dumps(software)
            licenses_json = json.dumps(licenses)

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE nodes
                SET old_id = %s, status = %s, software = %s, price = %s, cpu = %s, gpu = %s, other_specs = %s, licenses = %s
                WHERE id = %s
            """, (old_id, status, software_json, price, cpu, gpu, other_specs, licenses_json, node_id))
            conn.commit()
            cur.close()
            release_db_connection(conn)
        except Exception as e:
            print(f"An error occurred: {e}")

        return redirect(url_for('edit_nodes'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, old_id, any_desk_address, any_desk_password, status, software, price, cpu, gpu, other_specs, licenses, machine_id
            FROM nodes WHERE id = %s
        """, (node_id,))
        node = cur.fetchone()
        cur.close()
        release_db_connection(conn)
    except Exception as e:
        print(f"An error occurred: {e}")
        node = None

    return render_template('edit_node.html', node=node)


if __name__ == '__main__':
    app.run(debug=bool(os.getenv("IS_DEBUG", False)))
