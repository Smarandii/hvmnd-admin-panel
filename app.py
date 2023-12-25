from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://admin:WIyniFnVBpcbG1pJ@ac-czkatd4-shard-00-01.aaaafpm.mongodb.net:27017,ac-czkatd4-shard-00-00.aaaafpm.mongodb.net:27017,ac-czkatd4-shard-00-02.aaaafpm.mongodb.net:27017/hvmnd_db?ssl=true&retryWrites=true&replicaSet=atlas-zqt5j0-shard-0&readPreference=primary&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1"
mongo = PyMongo(app)


@app.route('/')
def index():
    data = mongo.db.user_sessions.find()
    data = [doc for doc in data]
    return render_template('users.html', users=data)


@app.route('/update_balance/<user_telegram_id>', methods=['POST'])
def update_balance(user_telegram_id):
    new_balance = request.form['balance']
    # Update user balance
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
