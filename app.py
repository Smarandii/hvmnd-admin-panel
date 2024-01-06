import os
from dotenv import \
    load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)


@app.route('/')
def index():
    try:
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

        users = list(mongo.db.user_sessions.find())
    except Exception as e:

        print(f"An error occurred: {e}")
        users = []
        totals = {"total_balance": 0.0, "total_bonus": 0.0, "total_spent": 0.0}

    return render_template('users.html', users=users, totals=totals)


@app.route('/update_balance/<user_telegram_id>', methods=['POST'])
def update_balance(user_telegram_id):
    new_balance = request.form['balance']
    mongo.db.user_sessions.update_one({"user_telegram_id": int(user_telegram_id)},
                                      {"$set": {"balance": float(new_balance)}})

    return redirect(url_for('index'))


@app.route('/update_bonus/<user_telegram_id>', methods=['POST'])
def update_bonus(user_telegram_id):
    new_bonus = request.form['bonus']
    mongo.db.user_sessions.update_one({"user_telegram_id": int(user_telegram_id)},
                                      {"$set": {"bonus": float(new_bonus)}})

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
