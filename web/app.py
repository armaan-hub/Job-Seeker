"""Flask web app for AI Job Scout."""

import os
import sys
import warnings
from pathlib import Path

# Add project root (for `web.*` imports) and src/ (for `jobscout.*` imports)
_project_root = str(Path(__file__).parent.parent)
_src_dir = str(Path(__file__).parent.parent / "src")
for _p in (_project_root, _src_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from flask import Flask, redirect, url_for  # noqa: E402


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    secret_key = os.environ.get("SECRET_KEY", "")
    if not secret_key:
        warnings.warn(
            "SECRET_KEY env var not set; using insecure default. "
            "Set SECRET_KEY in your .env file before sharing access.",
            stacklevel=1,
        )
        secret_key = "dev-only-insecure-default-change-me"
    app.secret_key = secret_key

    from web.wizard import get_provider_health

    @app.context_processor
    def inject_health():
        return {"provider_health": get_provider_health()}

    @app.route("/")
    def index():
        return redirect(url_for("wizard.upload_get"))

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template

        return render_template("error.html", error=str(e)), 500

    @app.errorhandler(404)
    def not_found(e):
        from flask import redirect, url_for

        return redirect(url_for("wizard.upload_get"))

    from web.routes import wizard_bp

    app.register_blueprint(wizard_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="127.0.0.1", port=port, debug=True)
