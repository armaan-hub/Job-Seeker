"""Wizard route handlers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from jobscout.config import get_config
from web.wizard import (
    get_job_at_index,
    get_search_status,
    load_profile_from_session,
    load_web_results,
    run_coaching,
    save_profile_to_session,
    start_search,
)

wizard_bp = Blueprint("wizard", __name__, url_prefix="/wizard")


@wizard_bp.route("/upload", methods=["GET"])
def upload_get():
    return render_template("step1_upload.html", step=1)


@wizard_bp.route("/upload", methods=["POST"])
def upload_post():
    f = request.files.get("profile_json")
    if not f or f.filename == "":
        flash("Please select a JSON file.", "error")
        return redirect(url_for("wizard.upload_get"))

    try:
        content = f.read().decode("utf-8")
        json.loads(content)
    except Exception:
        flash("Invalid JSON file. Please upload a valid profile JSON.", "error")
        return redirect(url_for("wizard.upload_get"))

    save_profile_to_session(session, content)
    session.pop("search_config", None)
    session.pop("job_id", None)
    flash(f"Profile loaded! ({session['profile_preview']['name']})", "success")
    return redirect(url_for("wizard.configure_get"))


@wizard_bp.route("/upload-sample", methods=["POST"])
def upload_sample_post():
    data_dir = Path(__file__).parent.parent / "data"
    sample_path = data_dir / "profile.json"
    if not sample_path.exists():
        candidates = sorted(data_dir.glob("*.json"))
        if not candidates:
            flash("No sample profile found under data/.", "error")
            return redirect(url_for("wizard.upload_get"))
        sample_path = candidates[0]

    content = sample_path.read_text(encoding="utf-8")
    save_profile_to_session(session, content)
    session.pop("search_config", None)
    session.pop("job_id", None)
    flash("Loaded sample profile.", "success")
    return redirect(url_for("wizard.configure_get"))


@wizard_bp.route("/configure", methods=["GET"])
def configure_get():
    if not session.get("profile_data"):
        flash("Please upload your profile first.", "error")
        return redirect(url_for("wizard.upload_get"))

    preview = session.get("profile_preview", {})
    search_config = session.get("search_config", {})
    defaults = get_config()
    return render_template(
        "step2_config.html",
        step=2,
        roles=search_config.get("roles", preview.get("target_roles", defaults.default_roles)),
        location=search_config.get("location", preview.get("location", defaults.default_location)),
        sources=search_config.get("sources", ["mock"]),
        max_results=search_config.get("max_results", 10),
    )


@wizard_bp.route("/configure", methods=["POST"])
def configure_post():
    roles_raw = request.form.get("roles", "")
    roles = [r.strip() for r in roles_raw.split(",") if r.strip()]
    location = request.form.get("location", "").strip()
    sources = request.form.getlist("sources")

    try:
        max_results = int(request.form.get("max_results", 10))
    except ValueError:
        max_results = 10

    if not roles:
        flash("Please enter at least one job role.", "error")
        return redirect(url_for("wizard.configure_get"))
    if not sources:
        flash("Please select at least one job source.", "error")
        return redirect(url_for("wizard.configure_get"))

    session["search_config"] = {
        "roles": roles,
        "location": location,
        "sources": sources,
        "max_results": max_results,
    }
    return redirect(url_for("wizard.search_get"))


@wizard_bp.route("/search", methods=["GET"])
def search_get():
    if not session.get("search_config") or not session.get("profile_data"):
        return redirect(url_for("wizard.upload_get"))
    return render_template("step3_search_start.html", step=3)


@wizard_bp.route("/search", methods=["POST"])
def search_post():
    if not session.get("search_config") or not session.get("profile_data"):
        return redirect(url_for("wizard.upload_get"))
    job_id = start_search(session["profile_data"], session["search_config"])
    session["job_id"] = job_id
    return redirect(url_for("wizard.searching_get"))


@wizard_bp.route("/searching", methods=["GET"])
def searching_get():
    job_id = session.get("job_id")
    if not job_id:
        return redirect(url_for("wizard.configure_get"))
    return render_template("step3_searching.html", step=3, job_id=job_id)


@wizard_bp.route("/search-status", methods=["GET"])
def search_status():
    job_id = session.get("job_id") or request.args.get("job_id")
    status = get_search_status(job_id)
    if status.get("status") == "done":
        status["redirect"] = url_for("wizard.results_get")
    elif status.get("status") == "error":
        status["redirect"] = url_for("wizard.configure_get")
    return jsonify(status)


@wizard_bp.route("/results", methods=["GET"])
def results_get():
    results = load_web_results()
    if not results:
        flash("No results found. Please run a search first.", "error")
        return redirect(url_for("wizard.configure_get"))
    return render_template("step4_results.html", step=4, results=results, enumerate=enumerate)


@wizard_bp.route("/results-export", methods=["GET"])
def results_export():
    import json as _json

    from flask import Response

    results = load_web_results()
    return Response(
        _json.dumps(results, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=job_results.json"},
    )


@wizard_bp.route("/coaching/<int:job_index>", methods=["GET"])
def coaching_get(job_index: int):
    job_dict = get_job_at_index(job_index)
    if job_dict is None:
        flash(f"Job #{job_index} not found. Please run a search first.", "error")
        return redirect(url_for("wizard.results_get"))

    profile = load_profile_from_session(session)
    if profile is None:
        flash("Profile session expired. Please upload your profile again.", "error")
        return redirect(url_for("wizard.upload_get"))

    include_plan = request.args.get("include_plan", "false").lower() == "true"
    coaching_data = run_coaching(profile, job_dict, include_plan)

    return render_template(
        "step5_coaching.html",
        step=5,
        job=job_dict["job"],
        job_index=job_index,
        coaching=coaching_data,
        include_plan=include_plan,
    )
