import os

import pymongo
from dotenv import \
    load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.secret_key = os.getenv("FLASK_SECRET_KEY")
mongo = PyMongo(app)


@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        order = request.args.get('order', 'asc')
        sort_order = pymongo.ASCENDING if order == 'asc' else pymongo.DESCENDING
        sort_by = request.args.get('sort', '_id')  # Default sort by ID
        users = list(mongo.db.user_sessions.find().sort(sort_by, sort_order))

        pipeline = [
            {"$group": {
                "_id": None,
                "total_balance": {"$sum": "$balance"},
                "total_bonus": {"$sum": "$bonus"},
                "total_spent": {"$sum": "$total_spent"}
            }}
        ]
        totals = list(mongo.db.user_sessions.aggregate(pipeline))[0]

        for key in totals.keys():
            if key != "_id":
                totals[key] = round(totals[key], 2)

    except Exception as e:

        print(f"An error occurred: {e}")
        users = []
        totals = {"total_balance": 0.0, "total_bonus": 0.0, "total_spent": 0.0}

    return render_template('users.html', users=users, totals=totals)


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
    mongo.db.user_sessions.update_one({"user_telegram_id": int(user_telegram_id)},
                                      {"$set": {"balance": float(new_balance)}})

    return redirect(url_for('index'))


@app.route('/update_bonus/<user_telegram_id>', methods=['POST'])
def update_bonus(user_telegram_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    new_bonus = request.form['bonus']
    mongo.db.user_sessions.update_one({"user_telegram_id": int(user_telegram_id)},
                                      {"$set": {"bonus": float(new_bonus)}})

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
