"""Tests for advisor module."""

from __future__ import annotations

from dataclasses import dataclass
from jobscout.providers.base import AIProvider, AIResponse, ProviderType


class MockProvider(AIProvider):
    """Mock AI provider for testing."""

    def __init__(self, response_content: str):
        super().__init__()
        self._response = response_content

    def complete(self, prompt: str, system: str | None = None, **kwargs) -> AIResponse:
        return AIResponse(content=self._response, model="mock")

    def provider_type(self) -> ProviderType:
        return ProviderType.OPENCODE


class TestDataclasses:
    """Test that all dataclasses are importable and constructible."""

    def test_resume_edit_importable(self):
        from jobscout.advisor import ResumeEdit
        edit = ResumeEdit(
            section="Experience",
            current_text="Managed data",
            suggested_text="Led ETL pipelines processing 6M+ records",
            reason="Quantifies impact",
        )
        assert edit.section == "Experience"

    def test_requirement_importable(self):
        from jobscout.advisor import Requirement
        req = Requirement(
            item="Power BI",
            priority="must-have",
            candidate_has=True,
            candidate_note="5 years Power BI",
        )
        assert req.priority == "must-have"

    def test_requirements_report_importable(self):
        from jobscout.advisor import Requirement, RequirementsReport
        report = RequirementsReport(
            requirements=[],
            coverage_score=75.0,
            critical_gaps=["Azure"],
        )
        assert report.coverage_score == 75.0

    def test_coach_advice_importable(self):
        from jobscout.advisor import CoachAdvice
        advice = CoachAdvice(
            quick_tips=["Apply via referral"],
            action_plan=None,
        )
        assert len(advice.quick_tips) == 1
