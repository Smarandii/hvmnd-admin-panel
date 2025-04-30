from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import os

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        if (request.form["username"] == os.getenv("ADMIN_LOGIN") and
                request.form["password"] == os.getenv("ADMIN_PASSWORD")):
            session["logged_in"] = True
            return redirect(url_for("users.list_users"))
        flash("Invalid credentials")
    return render_template("login.html")


@bp.get("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("auth.login"))
