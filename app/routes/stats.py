# app/routes/stats.py
from __future__ import annotations

from flask import Blueprint, render_template, session, redirect, url_for
from app.db import get_conn
from app.repositories.user import UserRepository
from app.repositories.payments import PaymentRepository

bp = Blueprint("stats_bp", __name__)
users_repo = UserRepository()
payments_repo = PaymentRepository()


def _require_login():
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))
    return None


@bp.route("/dashboard", methods=["GET"], endpoint="dashboard")
def dashboard_route():
    """Show high-level statistics & charts."""
    if (redirect_resp := _require_login()) is not None:
        return redirect_resp

    # --- numeric figures -------------------------------------------------- #
    totals = users_repo.totals()
    total_successful = payments_repo.total_successful()

    with get_conn() as (_, cur):
        cur.execute("SELECT COUNT(*) FROM users")
        (user_count,) = cur.fetchone()  # int

    context = {
        "user_count": user_count,
        "total_balance": totals["total_balance"],
        "total_spent": totals["total_spent"],
        "total_paid": total_successful,
    }
    return render_template("dashboard.html", **context)
