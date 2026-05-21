"""AI-powered job advisor module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResumeEdit:
    """A targeted CV edit suggestion for a specific job."""

    section: str
    current_text: str
    suggested_text: str
    reason: str


@dataclass
class Requirement:
    """A job requirement with candidate coverage info."""

    item: str
    priority: str  # "must-have" or "nice-to-have"
    candidate_has: bool
    candidate_note: str


@dataclass
class RequirementsReport:
    """Full requirements analysis for a job vs. a candidate."""

    requirements: list[Requirement]
    coverage_score: float
    critical_gaps: list[str]


@dataclass
class CoachAdvice:
    """Career coaching advice for landing a specific job."""

    quick_tips: list[str]
    action_plan: dict[str, list[str]] | None  # None if not requested

import json

from jobscout.profile import UserProfile
from jobscout.scraper import JobListing
from jobscout.providers.base import AIProvider


class ResumeAdvisor:
    """Suggests targeted CV edits for a specific job."""

    SYSTEM_PROMPT = (
        "You are an expert CV consultant and career coach specialising in the MENA job market. "
        "Return ONLY a valid JSON array of objects, no prose."
    )

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    def suggest_edits(self, profile: UserProfile, job: JobListing) -> list[ResumeEdit]:
        """Return a list of targeted CV edits for the given job."""
        prompt = (
            f"Candidate profile:\n{profile}\n\n"
            f"Job listing:\nTitle: {job.title}\nCompany: {job.company}\n"
            f"Description: {job.description}\n\n"
            "Return a JSON array of CV edits. Each object must have keys: "
            "section, current_text, suggested_text, reason."
        )
        response = self._provider.complete(prompt, system=self.SYSTEM_PROMPT)
        return self._parse(response.content)

    def _parse(self, content: str) -> list[ResumeEdit]:
        try:
            # Strip markdown code fences if present
            text = content.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            return [
                ResumeEdit(
                    section=item.get("section", ""),
                    current_text=item.get("current_text", ""),
                    suggested_text=item.get("suggested_text", ""),
                    reason=item.get("reason", ""),
                )
                for item in data
            ]
        except (json.JSONDecodeError, KeyError, TypeError):
            return [
                ResumeEdit(
                    section="General",
                    current_text="",
                    suggested_text=content,
                    reason="Raw AI response (JSON parsing failed)",
                )
            ]
