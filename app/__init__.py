from flask import Flask
from app.config import Config
from app.db import init_pool
from app.routes import auth, users, nodes, payments  # noqa: E402 (after Flask import)


def create_app() -> Flask:
    app = Flask(__name__,
                template_folder=Config.TEMPLATE_FOLDER,
                static_folder=Config.STATIC_FOLDER)
    app.config.from_object(Config)
    init_pool(Config.DB_DSN)

    app.register_blueprint(auth.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(nodes.bp)
    app.register_blueprint(payments.bp)

    app.add_url_rule(
        "/", endpoint="index",
        view_func=app.view_functions["users.list_users"],
        methods=["GET"],
    )
    app.add_url_rule(
        "/login", endpoint="login",
        view_func=app.view_functions["auth.login"],
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/logout", endpoint="logout",
        view_func=app.view_functions["auth.logout"],
        methods=["GET"],
    )

    return app
