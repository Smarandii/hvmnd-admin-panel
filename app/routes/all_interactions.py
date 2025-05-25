from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
)

from app.repositories.all_interactions import AllInteractionRepository

bp = Blueprint("all_interactions_bp", __name__)
repo = AllInteractionRepository()


def _require_login():
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))
    return None


@bp.route("/all_interactions", methods=["GET"], endpoint="all_interactions")
def all_interactions_route():
    """
    Global chronological log of every Telegram interaction.
    Example:  /all_interactions?sort=username&order=asc&limit=1000
    """
    if (redir := _require_login()) is not None:
        return redir

    sort = request.args.get("sort", "timestamp")
    order = request.args.get("order", "desc")
    limit = request.args.get("limit", 500, type=int)

    interactions = repo.list_recent(limit=limit, sort_by=sort, order=order)
    return render_template(
        "all_interactions.html",
        interactions=interactions,
        sort=sort,
        order=order,
        limit=limit,
    )
