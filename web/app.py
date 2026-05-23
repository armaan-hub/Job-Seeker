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

    @app.route("/api/tailor", methods=["POST"])
    def api_tailor():
        """Tailor the user's CV for a specific job listing."""
        from flask import jsonify, request, session

        data = request.get_json(force=True, silent=True) or {}
        job_title = data.get("job_title", "")
        job_company = data.get("job_company", "")
        job_description = data.get("job_description", "")

        if not job_description or len(job_description.strip()) < 20:
            return jsonify({"error": "job_description is required (min 20 chars)"}), 400

        profile = _load_profile_dict(session)
        if not profile:
            return jsonify({"error": "No profile loaded. Please upload your CV first."}), 400

        try:
            from jobscout.config import get_config
            from web.wizard import _get_provider
            cfg = get_config()
            provider = _get_provider(cfg)
        except Exception:
            provider = None

        from jobscout.cv_tailor import tailor_cv
        result = tailor_cv(
            profile=profile,
            job_title=job_title,
            job_company=job_company,
            job_description=job_description,
            provider=provider,
        )
        return jsonify(result)

    @app.route("/tailor")
    def tailor_page():
        """CV tailoring page — receives job details via query params."""
        from flask import render_template, request
        job_title = request.args.get("title", "")
        job_company = request.args.get("company", "")
        job_description = request.args.get("description", "")
        job_url = request.args.get("url", "")
        return render_template(
            "step5_tailor.html",
            job_title=job_title,
            job_company=job_company,
            job_description=job_description,
            job_url=job_url,
        )

    return app


def _load_profile_dict(session) -> dict | None:
    """Load raw profile dict from session-backed storage."""
    import json as _json
    from pathlib import Path

    profile_data = session.get("profile_data", {})
    profile_json = profile_data.get("profile_json")
    if profile_json:
        try:
            return _json.loads(profile_json)
        except Exception:
            return None

    if profile_data.get("profile_storage") == "disk" or profile_data.get("storage") == "disk":
        path = Path.home() / ".jobscout" / "session_profile.json"
        if path.exists():
            try:
                return _json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return None

    return None


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="127.0.0.1", port=port, debug=True)
