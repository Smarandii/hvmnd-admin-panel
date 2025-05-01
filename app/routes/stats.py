# app/routes/stats.py
from __future__ import annotations

import json
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

    # ------------------------------------------------------------------ #
    # Numeric figures
    totals = users_repo.totals()
    total_successful = payments_repo.total_successful()

    with get_conn() as (_, cur):
        cur.execute("SELECT COUNT(*) FROM users")
        (user_count,) = cur.fetchone()

    # ------------------------------------------------------------------ #
    # User-level spending for pie chart                                  #
    # Grab all users ordered by spend, aggregate into Top-10 + Others
    with get_conn() as (_, cur):
        cur.execute("""
            SELECT
                COALESCE(NULLIF(username, ''), CONCAT('id_', id)) AS label,
                COALESCE(total_spent, 0)                         AS spent
            FROM   users
            ORDER  BY spent DESC
        """)
        rows = cur.fetchall()

    labels: list[str] = []
    data:   list[float] = []
    other_total = 0.0

    for idx, (label, spent) in enumerate(rows):
        spent_val = float(spent or 0)
        if idx < 10:
            labels.append(label)
            data.append(spent_val)
        else:
            other_total += spent_val

    if other_total:
        labels.append("Others")
        data.append(other_total)

    context = {
        # cards
        "user_count":    user_count,
        "total_balance": totals["total_balance"],
        "total_spent":   totals["total_spent"],
        "total_paid":    total_successful,
        # pie-chart data (serialised to JSON once for the template)
        "pie_labels": json.dumps(labels, ensure_ascii=False),
        "pie_values": json.dumps(data),
    }
    return render_template("dashboard.html", **context)
