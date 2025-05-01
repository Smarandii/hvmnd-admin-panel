from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.repositories.payments import PaymentRepository

bp = Blueprint("payments_bp", __name__)
repo = PaymentRepository()


def _require_login():
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))
    return None


@bp.route(
    "/payment_history/<int:user_id>/",
    methods=["GET"],
    endpoint="payment_history",
)
def payment_history_route(user_id: int):
    if (redirect_resp := _require_login()) is not None:
        return redirect_resp

    sort_by = request.args.get("sort", "datetime")
    order = request.args.get("order", "desc")

    payments = repo.list_for_user(user_id, sort_by=sort_by, order=order)
    user = repo.fetch_user_brief(user_id)

    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("users.list_users"))  # fallback

    return render_template(
        "payment_history.html",
        payments=payments,
        user=user,
        sort=sort_by,
        order=order,
    )
