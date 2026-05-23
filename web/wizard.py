"""Business logic layer for the Job Scout web wizard."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
import threading
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any

from jobscout.advisor import ApplicationCoach, RequirementsAnalyzer, ResumeAdvisor
from jobscout.config import JobScoutConfig, get_config
from jobscout.matcher import JobMatcher
from jobscout.profile import ProfileParser, UserProfile
from jobscout.providers.anthropic import AnthropicProvider
from jobscout.providers.openai import OpenAIProvider
from jobscout.providers.opencode import OpenCodeProvider
from jobscout.scraper import JobListing, get_scraper

JOB_REGISTRY: dict[str, dict[str, Any]] = {}


def _state_dir() -> Path:
    return Path.home() / ".jobscout"


def _profile_cache_path() -> Path:
    return _state_dir() / "session_profile.json"


def _web_results_path() -> Path:
    return _state_dir() / "web_results.json"


def _profile_from_json(profile_json_str: str) -> UserProfile:
    state_dir = _state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    temp_path = state_dir / f"profile_parse_{uuid.uuid4().hex}.json"
    temp_path.write_text(profile_json_str, encoding="utf-8")
    try:
        profile = ProfileParser.load_profile(temp_path)
        if profile is None:
            raise ValueError("Unable to parse profile JSON")
        return profile
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _get_provider(config: JobScoutConfig):
    if config.active_provider == "anthropic":
        return AnthropicProvider(config.anthropic.api_key)
    if config.active_provider == "openai":
        return OpenAIProvider(config.openai.api_key)
    if config.active_provider == "opencode":
        return OpenCodeProvider(
            base_url=config.opencode.base_url,
            api_key=config.opencode.api_key,
        )
    raise ValueError(f"Unknown provider: {config.active_provider}")


def save_profile_to_session(session, profile_json_str: str) -> dict[str, str]:
    """Persist uploaded profile payload to session cookie or disk fallback."""
    json.loads(profile_json_str)
    profile = _profile_from_json(profile_json_str)

    preview = {
        "name": profile.name,
        "title": profile.title,
        "skills_count": len(profile.skills),
        "target_roles": profile.target_roles[:3],
        "location": profile.location,
    }
    session["profile_preview"] = preview

    if len(profile_json_str.encode("utf-8")) < 3000:
        session["profile_data"] = {
            "profile_json": profile_json_str,
            "storage": "cookie",
        }
        return {"storage": "cookie"}

    state_dir = _state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    _profile_cache_path().write_text(profile_json_str, encoding="utf-8")
    session["profile_data"] = {
        "profile_storage": "disk",
        "storage": "disk",
    }
    return {"storage": "disk"}


def load_profile_from_session(session) -> UserProfile | None:
    """Rehydrate a user profile from session-backed storage."""
    profile_data = session.get("profile_data", {})
    profile_json = profile_data.get("profile_json")
    if profile_json:
        return _profile_from_json(profile_json)

    if profile_data.get("profile_storage") == "disk" or profile_data.get("storage") == "disk":
        path = _profile_cache_path()
        if path.exists():
            return _profile_from_json(path.read_text(encoding="utf-8"))

    return None


def get_provider_health() -> dict[str, Any]:
    """Return active provider configuration health for UI banner."""
    config = get_config()
    provider_name = config.active_provider
    provider_cfg = (
        config.get_active_provider_config()
        if hasattr(config, "get_active_provider_config")
        else getattr(config, provider_name)
    )
    key_name = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "opencode": "OPENCODE_API_KEY",
    }[provider_name]

    if provider_cfg.api_key:
        return {
            "ok": True,
            "provider": provider_name,
            "message": f"{provider_name.capitalize()} configured ✓",
        }

    return {
        "ok": False,
        "provider": provider_name,
        "message": f"{key_name} not set in .env",
    }


def run_search_worker(profile_dict: dict, search_config: dict, job_id: str) -> None:
    """Background worker that scrapes, matches, and persists web results."""
    try:
        profile_json = profile_dict.get("profile_json")
        if profile_json:
            profile = _profile_from_json(profile_json)
        elif profile_dict.get("storage") == "disk" or profile_dict.get("profile_storage") == "disk":
            profile_path = _profile_cache_path()
            if not profile_path.exists():
                JOB_REGISTRY[job_id] = {
                    "status": "error",
                    "message": "Profile session expired. Please upload again.",
                    "redirect": "upload",
                }
                return
            profile = _profile_from_json(profile_path.read_text(encoding="utf-8"))
        else:
            JOB_REGISTRY[job_id] = {
                "status": "error",
                "message": "Missing profile data. Please upload again.",
                "redirect": "upload",
            }
            return

        roles = search_config.get("roles", [])
        location = search_config.get("location")
        sources = search_config.get("sources", [])
        max_results = int(search_config.get("max_results", 10))

        if not sources:
            JOB_REGISTRY[job_id] = {
                "status": "error",
                "message": "No job sources selected.",
                "redirect": "configure",
            }
            return

        per_source = max(1, max_results // len(sources))
        all_jobs: list[JobListing] = []

        for source in sources:
            try:
                scraper = get_scraper(source)
                all_jobs.extend(scraper.search(roles, location, per_source))
            except Exception:
                continue

        if len(all_jobs) == 0:
            JOB_REGISTRY[job_id] = {
                "status": "error",
                "message": "No jobs found. Try selecting 'Mock' source for demonstration.",
                "redirect": "configure",
            }
            return

        config = get_config()
        provider = _get_provider(config)

        try:
            matcher = JobMatcher(provider)
            results = matcher.match_profile_to_jobs(profile, all_jobs, detailed=True)
        except Exception as exc:
            JOB_REGISTRY[job_id] = {
                "status": "error",
                "message": f"Matching failed: {exc}",
                "redirect": "configure",
            }
            return

        payload = []
        for result in results:
            posted_date = result.job.posted_date
            payload.append(
                {
                    "job": {
                        "title": result.job.title,
                        "company": result.job.company,
                        "location": result.job.location,
                        "description": result.job.description,
                        "url": result.job.url,
                        "source": result.job.source,
                        "salary": result.job.salary,
                        "posted_date": posted_date.isoformat() if isinstance(posted_date, datetime) else None,
                        "requirements": result.job.requirements,
                        "benefits": result.job.benefits,
                    },
                    "score": result.score,
                    "reasoning": result.reasoning,
                    "skill_match": result.skill_match,
                    "missing_skills": result.missing_skills,
                    "strengths": result.strengths,
                    "improvement_tips": result.improvement_tips,
                }
            )

        state_dir = _state_dir()
        state_dir.mkdir(parents=True, exist_ok=True)
        _web_results_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")
        JOB_REGISTRY[job_id] = {"status": "done", "count": len(results)}
    except Exception as exc:
        JOB_REGISTRY[job_id] = {
            "status": "error",
            "message": f"Search failed: {exc}",
            "redirect": "configure",
        }


def start_search(profile_data: dict, search_config: dict) -> str:
    """Start async search thread and return pollable job ID."""
    job_id = str(uuid.uuid4())
    JOB_REGISTRY[job_id] = {"status": "running"}
    thread = threading.Thread(
        target=run_search_worker,
        args=(profile_data, search_config, job_id),
        daemon=True,
    )
    thread.start()
    return job_id


def get_search_status(job_id: str) -> dict[str, Any]:
    """Return current state for a search job."""
    return JOB_REGISTRY.get(job_id, {"status": "unknown"})


def load_web_results() -> list[dict[str, Any]]:
    """Load web search results persisted by the worker."""
    path = _web_results_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def get_job_at_index(index: int) -> dict[str, Any] | None:
    """Get a 1-based result item from persisted web results."""
    results = load_web_results()
    idx = index - 1
    if idx < 0 or idx >= len(results):
        return None
    return results[idx]


def run_coaching(profile: UserProfile, job_dict: dict, include_plan: bool) -> dict[str, Any]:
    """Run all advisor modules and serialize for web templates."""
    job_payload = job_dict.get("job", job_dict)
    job = JobListing.from_dict(job_payload)
    config = get_config()
    provider = _get_provider(config)

    output: dict[str, Any] = {
        "resume_edits": [],
        "requirements": {},
        "coaching": {},
        "errors": [],
    }

    try:
        resume_advisor = ResumeAdvisor(provider)
        edits = resume_advisor.suggest_edits(profile, job)
        output["resume_edits"] = [asdict(item) for item in edits]
    except Exception as exc:
        output["errors"].append(f"resume_edits: {exc}")

    try:
        req_analyzer = RequirementsAnalyzer(provider)
        report = req_analyzer.analyze(profile, job)
        output["requirements"] = {
            "requirements": [asdict(item) for item in report.requirements],
            "coverage_score": report.coverage_score,
            "critical_gaps": report.critical_gaps,
        }
    except Exception as exc:
        output["errors"].append(f"requirements: {exc}")

    try:
        coach = ApplicationCoach(provider)
        advice = coach.advise(profile, job, include_plan=include_plan)
        output["coaching"] = {
            "quick_tips": advice.quick_tips,
            "action_plan": advice.action_plan,
        }
    except Exception as exc:
        output["errors"].append(f"coaching: {exc}")

    return output
