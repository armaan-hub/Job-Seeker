"""Tests for web wizard business logic."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

from jobscout.scraper import JobListing
from web.wizard import (
    get_provider_health,
    load_profile_from_session,
    load_web_results,
    run_coaching,
    save_profile_to_session,
)


def _profile_json() -> str:
    return json.dumps(
        {
            "profile": {
                "name": "Test User",
                "title": "Data Analyst",
                "contact": {"location": "Dubai, UAE"},
            },
            "skills": {"core": ["SQL", "Power BI"]},
            "target_roles": ["Data Analyst", "BI Developer"],
            "preferred_locations": ["Dubai, UAE"],
        }
    )


def test_save_small_profile_uses_cookie() -> None:
    session: dict = {}
    payload = _profile_json()

    result = save_profile_to_session(session, payload)

    assert result["storage"] == "cookie"
    assert session["profile_data"]["profile_json"] == payload
    assert session["profile_preview"]["name"] == "Test User"


def test_save_large_profile_uses_disk(monkeypatch, tmp_path) -> None:
    from web import wizard

    monkeypatch.setattr(wizard.Path, "home", lambda: tmp_path)

    session: dict = {}
    profile = json.loads(_profile_json())
    profile["professional_summary"] = "x" * 4000

    result = save_profile_to_session(session, json.dumps(profile))

    assert result["storage"] == "disk"
    assert session["profile_data"]["profile_storage"] == "disk"
    assert (tmp_path / ".jobscout" / "session_profile.json").exists()


def test_load_profile_from_cookie() -> None:
    session: dict = {}
    payload = _profile_json()

    save_profile_to_session(session, payload)
    profile = load_profile_from_session(session)

    assert profile is not None
    assert profile.name == "Test User"


def test_load_profile_from_disk(monkeypatch, tmp_path) -> None:
    from web import wizard

    monkeypatch.setattr(wizard.Path, "home", lambda: tmp_path)

    session: dict = {}
    profile = json.loads(_profile_json())
    profile["professional_summary"] = "x" * 4000

    save_profile_to_session(session, json.dumps(profile))
    loaded = load_profile_from_session(session)

    assert loaded is not None
    assert loaded.name == "Test User"


def test_provider_health_missing_key(monkeypatch) -> None:
    from web import wizard

    fake_cfg = SimpleNamespace(
        active_provider="anthropic",
        anthropic=SimpleNamespace(api_key=""),
    )
    monkeypatch.setattr(wizard, "get_config", lambda: fake_cfg)

    health = get_provider_health()

    assert health["ok"] is False
    assert "not set" in health["message"]


def test_provider_health_returns_safe_fallback_on_exception(monkeypatch) -> None:
    from web import wizard

    monkeypatch.setattr(wizard, "get_config", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    assert get_provider_health() == {"ok": True, "provider": "unknown", "message": ""}


def test_run_coaching_returns_provider_configuration_error(monkeypatch, sample_profile) -> None:
    from web import wizard

    monkeypatch.setattr(wizard, "get_config", lambda: object())

    def _raise_provider_error(config):
        raise ValueError("missing API key")

    monkeypatch.setattr(wizard, "_get_provider", _raise_provider_error)

    result = run_coaching(
        sample_profile,
        {
            "job": {
                "title": "Data Analyst",
                "company": "Tech Corp",
                "location": "Dubai, UAE",
                "description": "Looking for a data analyst",
                "source": "remoteok",
                "requirements": ["SQL"],
            }
        },
        include_plan=False,
    )

    assert result == {
        "errors": ["Provider configuration error: missing API key"],
        "resume_edits": [],
        "requirements": {},
        "coaching": {},
    }


def test_load_web_results_missing_file(monkeypatch, tmp_path) -> None:
    from web import wizard

    monkeypatch.setattr(wizard.Path, "home", lambda: tmp_path)

    assert load_web_results() == []



def test_run_search_worker_persists_gateway_flag(monkeypatch) -> None:
    from web import wizard

    state_root = Path("/Users/armaan/Job Finder/job-scout/.test-state-web-wizard")
    if state_root.exists():
        shutil.rmtree(state_root)
    state_root.mkdir(parents=True)

    class GatewayScraper:
        def search(self, roles, location, max_results):
            return [
                JobListing(
                    title="Browse Data Analyst jobs →",
                    company="SEEK",
                    location="Sydney",
                    description="Gateway card",
                    url="https://www.seek.com.au/data-analyst-jobs/in-sydney",
                    source="seek_au",
                    is_gateway=True,
                )
            ]

    class FakeMatcher:
        def __init__(self, provider):
            self.provider = provider

        def match_profile_to_jobs(self, profile, jobs, detailed=True):
            return [
                SimpleNamespace(
                    job=jobs[0],
                    score=88.0,
                    reasoning="Gateway preserved",
                    skill_match={},
                    missing_skills=[],
                    strengths=[],
                    improvement_tips=[],
                )
            ]

    monkeypatch.setattr(wizard.Path, "home", lambda: state_root)
    monkeypatch.setattr(wizard, "get_scraper", lambda source: GatewayScraper())
    monkeypatch.setattr(wizard, "get_config", lambda: object())
    monkeypatch.setattr(wizard, "_get_provider", lambda config: object())
    monkeypatch.setattr(wizard, "JobMatcher", FakeMatcher)

    wizard.run_search_worker(
        profile_dict={"profile_json": _profile_json()},
        search_config={
            "roles": ["Data Analyst"],
            "location": "Sydney",
            "sources": ["seek_au"],
            "max_results": 1,
        },
        job_id="job-gateway",
    )

    payload = json.loads(wizard._web_results_path().read_text(encoding="utf-8"))

    assert payload[0]["job"]["is_gateway"] is True
    assert wizard.JOB_REGISTRY["job-gateway"] == {"status": "done", "count": 1}

    shutil.rmtree(state_root)
