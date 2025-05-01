from flask import Blueprint, request, render_template, redirect, url_for, session, flash

from app.repositories.payments import PaymentRepository
from app.repositories.user import UserRepository

bp = Blueprint("users", __name__)

repo = UserRepository()
payments_repo = PaymentRepository()


@bp.get("/")
def list_users():
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))
    search = request.args.get("search", "")
    sort = request.args.get("sort", "id")
    order = request.args.get("order", "asc")

    users = repo.find_many(search=search, sort_by=sort, order=order)
    totals = repo.totals()
    total_successful = payments_repo.total_successful()

    return render_template(
        template_name_or_list="users.html",
        users=users,
        totals=totals,
        total_paid=total_successful,
        search=search
    )


@bp.post("/update_balance/<int:user_id>", endpoint="update_balance")
def update_balance(user_id: int):
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))

    try:
        repo.update_balance(user_id, float(request.form["balance"]))
        flash("Balance updated")
    except Exception:  # pragma: no cover
        flash("Could not update balance", "error")

    # keep original redirect target
    return redirect(url_for("index"))
