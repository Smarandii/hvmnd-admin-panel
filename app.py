import os

import pymongo
from dotenv import \
    load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo

load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://admin:WIyniFnVBpcbG1pJ@cluster0.aaaafpm.mongodb.net/new_database?retryWrites=true&w=majority"
app.secret_key = os.getenv("FLASK_SECRET_KEY")
mongo = PyMongo(app)


@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', "id")
    order = request.args.get('order', 'asc')
    sort_order = pymongo.ASCENDING if order == 'asc' else pymongo.DESCENDING

    try:
        query = {}
        if search_query:
            search_regex = {'$regex': search_query, '$options': 'i'}
            query['$or'] = [
                {'username': search_regex},
                {'firstname': search_regex},
                {'lastname': search_regex},
                {'language_code': search_regex},
            ]

            try:
                numeric_search = float(search_query)
                numeric_conditions = [
                    {"id": numeric_search},
                    {'balance': numeric_search},
                    {'total_spent': numeric_search},
                    {'price_multiplier': numeric_search},
                ]
                query['$or'].extend(numeric_conditions)
            except ValueError:
                # If conversion fails, skip adding numeric fields to the query
                pass

        users = list(mongo.db.users.find(query).sort(sort_by, sort_order))

        pipeline = [
            {"$group": {
                "_id": None,
                "total_balance": {"$sum": "$balance"},
                "total_spent": {"$sum": "$total_spent"}
            }}
        ]
        totals = list(mongo.db.users.aggregate(pipeline))[0]

        for key in totals.keys():
            if key != "_id":
                totals[key] = round(totals[key], 2)

    except Exception as e:

        print(f"An error occurred: {e}")
        users = []
        totals = {"total_balance": 0.0, "total_bonus": 0.0, "total_spent": 0.0}

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


@app.route('/update_balance/<user_telegram_id>', methods=['POST'])
def update_balance(user_telegram_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    new_balance = request.form['balance']
    mongo.db.users.update_one({"id": int(user_telegram_id)},
                              {"$set": {"balance": float(new_balance)}})

    return redirect(url_for('index'))


@app.route('/payment_history/<int:telegram_id>/')
def payment_history(telegram_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    sort_by = request.args.get('sort', 'datetime')
    order = request.args.get('order', 'desc')
    sort_order = pymongo.ASCENDING if order == 'asc' else pymongo.DESCENDING

    try:
        payments = mongo.db.payments.find({"user_id": telegram_id}).sort(sort_by, sort_order)
        user = mongo.db.users.find_one({"id": telegram_id})
        return render_template('payment_history.html', payments=payments, user=user)
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Error fetching payment history"


if __name__ == '__main__':
    app.run(debug=bool(os.getenv("IS_DEBUG", False)))
