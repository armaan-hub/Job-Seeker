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


class RequirementsAnalyzer:
    """Analyzes job requirements against a candidate's profile."""

    SYSTEM_PROMPT = (
        "You are an expert recruiter and talent assessor specialising in the MENA market. "
        "Return ONLY a valid JSON object, no prose."
    )

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    def analyze(self, profile: UserProfile, job: JobListing) -> RequirementsReport:
        """Return a requirements coverage report for the given job."""
        prompt = (
            f"Candidate profile:\n{profile}\n\n"
            f"Job listing:\nTitle: {job.title}\nCompany: {job.company}\n"
            f"Description: {job.description}\n\n"
            "Analyze the job requirements against the candidate's profile. "
            "Return a JSON object with keys: requirements (array of objects with "
            "item, priority, candidate_has, candidate_note), coverage_score (0-100), "
            "critical_gaps (array of strings)."
        )
        response = self._provider.complete(prompt, system=self.SYSTEM_PROMPT)
        return self._parse(response.content)

    def _parse(self, content: str) -> RequirementsReport:
        try:
            text = content.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            requirements = [
                Requirement(
                    item=r.get("item", ""),
                    priority=r.get("priority", "nice-to-have"),
                    candidate_has=bool(r.get("candidate_has", False)),
                    candidate_note=r.get("candidate_note", ""),
                )
                for r in data.get("requirements", [])
            ]
            return RequirementsReport(
                requirements=requirements,
                coverage_score=float(data.get("coverage_score", 0.0)),
                critical_gaps=list(data.get("critical_gaps", [])),
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return RequirementsReport(
                requirements=[],
                coverage_score=0.0,
                critical_gaps=["Unable to parse AI response"],
            )


class ApplicationCoach:
    """Provides coaching advice for landing a specific job."""

    SYSTEM_PROMPT = (
        "You are an expert career coach and interview trainer specialising in the MENA job market. "
        "Return ONLY a valid JSON object, no prose."
    )

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    def advise(
        self,
        profile: UserProfile,
        job: JobListing,
        include_plan: bool = False,
    ) -> CoachAdvice:
        """Return coaching advice; include_plan=True adds a full action plan."""
        plan_instruction = (
            " Also include an 'action_plan' object with keys before_applying, "
            "cover_letter, interview_prep (each an array of strings)."
            if include_plan
            else ""
        )
        prompt = (
            f"Candidate profile:\n{profile}\n\n"
            f"Job listing:\nTitle: {job.title}\nCompany: {job.company}\n"
            f"Description: {job.description}\n\n"
            "Provide career coaching for this application. "
            f"Return a JSON object with key 'quick_tips' (array of strings).{plan_instruction}"
        )
        response = self._provider.complete(prompt, system=self.SYSTEM_PROMPT)
        return self._parse(response.content, include_plan)

    def _parse(self, content: str, include_plan: bool) -> CoachAdvice:
        try:
            text = content.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            action_plan: dict[str, list[str]] | None = None
            if include_plan and "action_plan" in data:
                action_plan = {
                    k: list(v) for k, v in data["action_plan"].items()
                }
            return CoachAdvice(
                quick_tips=list(data.get("quick_tips", [])),
                action_plan=action_plan,
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            return CoachAdvice(
                quick_tips=[content],
                action_plan=None,
            )
