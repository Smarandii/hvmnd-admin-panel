from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from app.repositories.user import UserRepository

bp = Blueprint("users", __name__)
repo = UserRepository()


@bp.get("/")
def list_users():
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))

    search = request.args.get("search", "")
    sort   = request.args.get("sort", "id")
    order  = request.args.get("order", "asc")

    users = repo.find_many(search=search, sort_by=sort, order=order)

    return render_template("users.html", users=users, search=search)


@bp.post("/update_balance/<int:user_id>", endpoint="update_balance")
def update_balance(user_id: int):
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))

    try:
        repo.update_balance(user_id, float(request.form["balance"]))
        flash("Balance updated")
    except Exception:
        flash("Could not update balance", "error")

    return redirect(url_for("index"))
