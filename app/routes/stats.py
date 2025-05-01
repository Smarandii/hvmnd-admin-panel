import json
from flask import Blueprint, render_template, session, redirect, url_for
from app.db import get_conn
from app.repositories.user import UserRepository
from app.repositories.payments import PaymentRepository
from app.repositories.webapp_user import WebAppUserRepository

bp = Blueprint("stats_bp", __name__)

tg_users_repo = UserRepository()
tg_pay_repo = PaymentRepository()
wa_users_repo = WebAppUserRepository()


def _require_login():
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))
    return None


@bp.route("/dashboard", methods=["GET"], endpoint="dashboard")
def dashboard_route():
    """Show high-level statistics & charts (Telegram + Web-app + Crypto)."""
    if (redir := _require_login()) is not None:
        return redir

    # ------------------------------------------------------------------ #
    # 1. numeric figures (Telegram)
    tg_totals = tg_users_repo.totals()
    tg_total_paid = tg_pay_repo.total_successful()
    tg_user_count = tg_users_repo.find_many().__len__()  # small (<2k) – fine

    # 2. numeric figures (Web-app)
    wa_totals = wa_users_repo.totals()
    wa_user_count = wa_users_repo.count()

    # 3. total confirmed crypto received
    with get_conn() as (_, cur):
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM   crypto_payment_transactions
            WHERE  LOWER(status) = 'confirmed'
        """)
        (crypto_received,) = cur.fetchone()
    crypto_received = float(crypto_received)

    # ------------------------------------------------------------------ #
    # 4. pie – spending by Telegram users (Top-10 already-paid)
    with get_conn() as (_, cur):
        cur.execute("""
            SELECT
                COALESCE(NULLIF(username, ''), CONCAT('id_', id)) AS label,
                COALESCE(total_spent, 0)                         AS spent
            FROM   users
            ORDER  BY spent DESC
        """)
        tg_rows = cur.fetchall()

    tg_labels, tg_values, other = [], [], 0.0
    for idx, (lbl, val) in enumerate(tg_rows):
        if idx < 10:
            tg_labels.append(lbl)
            tg_values.append(float(val or 0))
        else:
            other += float(val or 0)
    if other:
        tg_labels.append("Others")
        tg_values.append(other)

    # ------------------------------------------------------------------ #
    # 5. pie – spending by Web-app users (Top-10)
    with get_conn() as (_, cur):
        cur.execute("""
            SELECT
                email                              AS label,
                COALESCE(total_spent, 0)           AS spent
            FROM   webapp_users
            ORDER  BY spent DESC
        """)
        wa_rows = cur.fetchall()

    wa_labels, wa_values, other_wa = [], [], 0.0
    for idx, (lbl, val) in enumerate(wa_rows):
        if idx < 10:
            wa_labels.append(lbl)
            wa_values.append(float(val or 0))
        else:
            other_wa += float(val or 0)
    if other_wa:
        wa_labels.append("Others")
        wa_values.append(other_wa)

    # ------------------------------------------------------------------ #
    # 6. pie – confirmed crypto by network
    with get_conn() as (_, cur):
        cur.execute("""
            SELECT n.name, SUM(t.amount) AS total
            FROM   crypto_payment_transactions t
            JOIN   crypto_networks n ON n.id = t.network_id
            WHERE  LOWER(t.status) = 'confirmed'
            GROUP  BY n.name
            ORDER  BY total DESC
        """)
        net_rows = cur.fetchall()

    net_labels = [lbl for lbl, _ in net_rows]
    net_values = [float(val) for _, val in net_rows]

    with get_conn() as (_, cur):
        cur.execute("SELECT DISTINCT address FROM crypto_deposit_addresses "
                    "WHERE address IS NOT NULL")
        addrs = [row[0] for row in cur.fetchall()]

    from app.services.tron import total_usdt
    live_usdt = total_usdt(addrs)

    # ------------------------------------------------------------------ #
    context = {
        # Telegram cards
        "tg_user_count": tg_user_count,
        "tg_total_balance": tg_totals["total_balance"],
        "tg_total_spent": tg_totals["total_spent"],
        "tg_total_paid": tg_total_paid,

        # Web-app cards
        "wa_user_count": wa_user_count,
        "wa_total_balance": wa_totals["total_balance"],
        "wa_total_spent": wa_totals["total_spent"],

        # crypto card
        "crypto_received": crypto_received,

        # chart data (serialised once per chart)
        "tg_pie_labels": json.dumps(tg_labels, ensure_ascii=False),
        "tg_pie_values": json.dumps(tg_values),

        "wa_pie_labels": json.dumps(wa_labels, ensure_ascii=False),
        "wa_pie_values": json.dumps(wa_values),

        "net_labels": json.dumps(net_labels, ensure_ascii=False),
        "net_values": json.dumps(net_values),

        "live_usdt": live_usdt,
    }
    return render_template("dashboard.html", **context)
