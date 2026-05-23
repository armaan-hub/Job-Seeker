"""Tests for scraper helpers and live integrations."""

from __future__ import annotations

from typing import Any

from jobscout.scraper import (
    BOARD_REGISTRY,
    REGION_BOARDS,
    JobListing,
    RemoteOKScraper,
    _build_generated_jobs,
    _search_url,
    get_scraper,
)


class DummyResponse:
    """Simple response stub for RemoteOK API tests."""

    def __init__(self, payload: list[dict[str, Any]], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> list[dict[str, Any]]:
        """Return the configured JSON payload."""
        return self._payload


def test_job_listing_from_dict_preserves_gateway_flag() -> None:
    """Gateway cards should survive JSON round-trips."""
    job = JobListing.from_dict(
        {
            "title": "Browse Data Analyst jobs →",
            "company": "SEEK",
            "location": "Sydney, Australia",
            "source": "seek_au",
            "is_gateway": True,
        }
    )

    assert job.is_gateway is True


def test_search_url_builds_seek_au_deep_link() -> None:
    """Seek AU URLs should use query params (slug path returns no results for unknown city slugs)."""
    url = _search_url("seek_au", "Data Analyst", "Sydney, Australia")
    assert url.startswith("https://www.seek.com.au/jobs?keywords=")
    assert "Data+Analyst" in url or "Data%20Analyst" in url


def test_build_generated_jobs_returns_single_gateway_card() -> None:
    """Generated boards should return one gateway card, not fake listings."""
    jobs = _build_generated_jobs("seek_au", ["Data Analyst"], "Sydney, Australia", 3)

    assert len(jobs) == 1
    assert jobs[0].title == "Browse Data Analyst jobs →"
    assert jobs[0].company == "SEEK"
    assert jobs[0].is_gateway is True
    # URL should be the correct seek.com.au query-param format
    assert jobs[0].url.startswith("https://www.seek.com.au/jobs?keywords=")



def test_registry_and_scrapers_include_new_gateway_boards() -> None:
    """Expanded regional boards should be registered and constructible."""
    assert "seek_au" in BOARD_REGISTRY
    assert "remotive" in BOARD_REGISTRY
    assert REGION_BOARDS["global_remote"]["boards"][-3:] == ["remotive", "wellfound", "himalayas"]

    gateway_job = get_scraper("seek_au").search(["Data Analyst"], "Sydney", 1)[0]
    legacy_job = get_scraper("seek").search(["Data Analyst"], "Sydney", 1)[0]

    assert gateway_job.is_gateway is True
    assert gateway_job.source == "seek_au"
    assert legacy_job.source == "seek_au"


def test_remoteok_scraper_parses_live_api_results(monkeypatch: Any) -> None:
    """RemoteOK should build listings from the public JSON API payload."""
    payload = [
        {"legal": "metadata"},
        {
            "id": 123,
            "position": "Data Analyst",
            "company": "Acme Remote",
            "url": "https://remoteok.com/remote-jobs/123",
            "tags": ["SQL", "Python", "BI"],
            "description": "<p>Work with dashboards</p>",
            "salary": "$100k",
        },
    ]

    def fake_get(url: str, headers: dict[str, str], timeout: int) -> DummyResponse:
        assert url == "https://remoteok.com/api?tags=data-analyst"
        assert headers["User-Agent"] == "Mozilla/5.0 (AI Job Scout)"
        assert timeout == 12
        return DummyResponse(payload)

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    jobs = RemoteOKScraper().search(["Data Analyst"], "Remote", max_results=5)

    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Data Analyst"
    assert job.company == "Acme Remote"
    assert job.location == "Remote"
    assert job.url == "https://remoteok.com/remote-jobs/123"
    assert "dashboards" in job.description
    assert "<p>" not in job.description
    assert job.salary == "$100k"
    assert job.requirements == ["SQL", "Python", "BI"]
