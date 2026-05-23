"""Tests for scraper helpers and live integrations."""

from __future__ import annotations

from typing import Any

from jobscout.scraper import RemoteOKScraper, _build_generated_jobs, _search_url


class DummyResponse:
    """Simple response stub for RemoteOK API tests."""

    def __init__(self, payload: list[dict[str, Any]], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> list[dict[str, Any]]:
        """Return the configured JSON payload."""
        return self._payload


def test_search_url_builds_seek_deep_link() -> None:
    """Seek URLs should point to the real board search page."""
    assert (
        _search_url("seek", "Data Analyst", "Sydney, Australia")
        == "https://www.seek.com.au/data-analyst-jobs/in-Sydney-Australia"
    )


def test_build_generated_jobs_uses_board_search_urls() -> None:
    """Generated preview jobs should deep-link to the source board search."""
    jobs = _build_generated_jobs("seek", ["Data Analyst"], "Sydney, Australia", 3)

    assert len(jobs) == 3
    assert all(job.url.startswith("https://www.seek.com.au/") for job in jobs)
    assert all("example.com" not in job.url for job in jobs)


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
