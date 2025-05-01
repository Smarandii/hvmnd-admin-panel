# app/routes/interactions.py
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from app.repositories.tg_interactions import InteractionRepository

bp = Blueprint("interactions_bp", __name__)  # own namespace
repo = InteractionRepository()


def _require_login():
    """Simple session-check identical to other blueprints."""
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))
    return None


@bp.route(
    "/interaction_history/<int:user_id>/",
    methods=["GET"],
    endpoint="interaction_history",
)
def interaction_history_route(user_id: int):
    """Chronological view of Telegram-user interactions."""
    if (redir := _require_login()) is not None:
        return redir

    sort_by = request.args.get("sort", "timestamp")
    order = request.args.get("order", "desc")

    interactions = repo.list_for_user(user_id, sort_by=sort_by, order=order)
    user = repo.fetch_user_brief(user_id)

    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("users.list_users"))

    return render_template(
        "interaction_history.html",
        interactions=interactions,
        user=user,
        sort=sort_by,
        order=order,
    )
