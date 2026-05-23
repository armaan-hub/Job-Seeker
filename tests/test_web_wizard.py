"""Tests for web wizard business logic."""

from __future__ import annotations

import json
from types import SimpleNamespace

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
