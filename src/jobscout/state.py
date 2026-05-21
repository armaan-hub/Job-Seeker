"""Session state: persist last search results to disk."""

from __future__ import annotations

import json
from pathlib import Path

from jobscout.scraper import JobListing

STATE_DIR: Path = Path.home() / ".jobscout"
LAST_RESULTS_FILE: Path = STATE_DIR / "last_results.json"


def save_results(jobs: list[JobListing], scores: list[float]) -> None:
    """Persist jobs and scores to ~/.jobscout/last_results.json."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "jobs": [
            {
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "url": j.url,
                "description": j.description,
                "source": j.source,
                "salary": j.salary,
                "requirements": j.requirements,
                "benefits": j.benefits,
            }
            for j in jobs
        ],
        "scores": scores,
    }
    LAST_RESULTS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_results() -> tuple[list[JobListing], list[float]]:
    """Load persisted jobs and scores. Returns ([], []) if no file."""
    if not LAST_RESULTS_FILE.exists():
        return [], []
    try:
        data = json.loads(LAST_RESULTS_FILE.read_text(encoding="utf-8"))
        jobs = [
            JobListing(
                title=j["title"],
                company=j["company"],
                location=j["location"],
                url=j.get("url", ""),
                description=j.get("description", ""),
                source=j.get("source", ""),
                salary=j.get("salary"),
                requirements=j.get("requirements", []),
                benefits=j.get("benefits", []),
            )
            for j in data.get("jobs", [])
        ]
        scores = [float(s) for s in data.get("scores", [])]
        return jobs, scores
    except (json.JSONDecodeError, KeyError):
        return [], []


def load_job_at_index(index: int) -> JobListing | None:
    """Return the 1-based indexed job from last results, or None."""
    jobs, _ = load_results()
    if not jobs:
        return None
    idx = index - 1  # convert 1-based to 0-based
    if idx < 0 or idx >= len(jobs):
        return None
    return jobs[idx]
