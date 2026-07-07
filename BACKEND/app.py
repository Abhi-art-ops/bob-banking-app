"""
app.py - Flask application factory and entry point.

Running the app:
    cd Banking_app/BACKEND
    python app.py

The server listens on http://127.0.0.1:5000 by default.
"""

import os

from flask import Flask, redirect, render_template, url_for

import config
from routes.auth import auth_bp
from routes.account import account_bp


def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder=config.TEMPLATE_FOLDER,
    )

    if test_config is None:
        app.config["SECRET_KEY"] = config.SECRET_KEY
        app.config["DEBUG"] = config.DEBUG
        app.config["DATABASE_PATH"] = config.DATABASE_PATH
    else:
        app.config.update(test_config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(account_bp)

    @app.route("/")
    def index():
        return redirect(url_for("auth.login_get"))

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("500.html"), 500

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host="127.0.0.1",
        port=5000,
        debug=config.DEBUG,
    )
