from flask import Blueprint, request, render_template, redirect, url_for, session
from app.repositories.user import UserRepository

bp = Blueprint("users", __name__)

repo = UserRepository()


@bp.get("/")
def list_users():
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))
    search = request.args.get("search", "")
    sort = request.args.get("sort", "id")
    order = request.args.get("order", "asc")

    users = repo.find_many(search=search, sort_by=sort, order=order)
    totals = repo.totals()
    return render_template("users.html", users=users, totals=totals, search=search)
