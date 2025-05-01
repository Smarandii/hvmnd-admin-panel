from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from app.repositories.webapp_user import WebAppUserRepository
from app.repositories.webapp_payments import WebAppPaymentRepository

bp = Blueprint("webapp_users", __name__)
users_repo = WebAppUserRepository()
payments_repo = WebAppPaymentRepository()


def _require_login():
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))
    return None


@bp.get("/webapp_users")
def list_webapp_users():
    if (redir := _require_login()) is not None:
        return redir

    search = request.args.get("search", "")
    sort = request.args.get("sort", "id")
    order = request.args.get("order", "asc")

    users = users_repo.find_many(search=search, sort_by=sort, order=order)
    return render_template(
        "webapp_users.html", users=users, search=search, sort=sort, order=order
    )


@bp.post("/webapp_users/update_balance/<int:user_id>", endpoint="update_balance_wa")
def update_balance(user_id: int):
    if (redir := _require_login()) is not None:
        return redir

    try:
        users_repo.update_balance(user_id, float(request.form["balance"]))
        flash("Balance updated")
    except Exception:
        flash("Could not update balance", "error")

    return redirect(url_for("webapp_users.list_webapp_users"))


@bp.route(
    "/webapp_payment_history/<int:user_id>/",
    methods=["GET"],
    endpoint="payment_history_wa",
)
def payment_history(user_id: int):
    if (redir := _require_login()) is not None:
        return redir

    sort_by = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")

    payments = payments_repo.list_for_user(user_id, sort_by=sort_by, order=order)
    user = payments_repo.fetch_user_brief(user_id)

    if user is None:
        flash("Web-app user not found.", "error")
        return redirect(url_for("webapp_users.list_webapp_users"))

    return render_template(
        "webapp_payment_history.html",
        payments=payments,
        user=user,
        sort=sort_by,
        order=order,
    )
