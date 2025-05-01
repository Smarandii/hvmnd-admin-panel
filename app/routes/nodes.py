from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
    flash,
)

from app.repositories.nodes import NodeRepository

bp = Blueprint("nodes_bp", __name__)  # blueprint name – endpoints stay original
repo = NodeRepository()


def _require_login():
    if not session.get("logged_in"):
        return redirect(url_for("auth.login"))
    return None


@bp.route("/edit_nodes", methods=["GET"], endpoint="edit_nodes")
def edit_nodes_route():
    if (redirect_resp := _require_login()) is not None:
        return redirect_resp

    nodes = repo.list()
    return render_template("edit_nodes.html", nodes=nodes)


@bp.route("/edit_node/<int:node_id>", methods=["GET", "POST"], endpoint="edit_node")
def edit_single_node(node_id: int):
    if (redirect_resp := _require_login()) is not None:
        return redirect_resp

    if request.method == "POST":
        _save_node_from_form(node_id, request.form)
        flash("Node updated.")
        return redirect(url_for("nodes_bp.edit_nodes"))

    node = repo.get(node_id)
    if node is None:
        flash("Node not found.", "error")
        return redirect(url_for("nodes_bp.edit_nodes"))
    return render_template("edit_node.html", node=node)


@bp.route("/update_node/<int:node_id>", methods=["POST"], endpoint="update_node")
def update_node_route(node_id: int):
    if (redirect_resp := _require_login()) is not None:
        return redirect_resp

    _save_node_from_form(node_id, request.form)
    flash("Node updated.")
    return redirect(url_for("nodes_bp.edit_nodes"))


@bp.route(
    "/deactivate_node/<int:node_id>", methods=["POST"], endpoint="deactivate_node"
)
def deactivate_node_route(node_id: int):
    if (redirect_resp := _require_login()) is not None:
        return redirect_resp

    repo.deactivate(node_id)
    flash("Node deactivated.")
    return redirect(url_for("nodes_bp.edit_nodes"))


# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #
def _save_node_from_form(node_id: int, form) -> None:
    """Extracts fields from a Flask form dict and saves them."""
    repo.update(
        node_id,
        old_id=_to_int_or_none(form.get("old_id")),
        status=form.get("status"),
        software=form.get("software"),
        price=_to_float_or_none(form.get("price")),
        cpu=form.get("cpu"),
        gpu=form.get("gpu"),
        other_specs=form.get("other_specs"),
        licenses=form.get("licenses"),
    )


def _to_int_or_none(value: str | None):
    try:
        return int(value) if value not in (None, "") else None
    except (ValueError, TypeError):
        return None


def _to_float_or_none(value: str | None):
    try:
        return float(value) if value not in (None, "") else None
    except (ValueError, TypeError):
        return None
