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
