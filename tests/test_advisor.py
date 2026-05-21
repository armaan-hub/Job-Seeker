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


class TestResumeAdvisor:
    """Test ResumeAdvisor.suggest_edits()."""

    def test_suggest_edits_returns_list(self, sample_profile, sample_job):
        from jobscout.advisor import ResumeAdvisor, ResumeEdit
        provider = MockProvider(
            '[{"section":"Experience","current_text":"Managed data","suggested_text":"Led ETL pipelines","reason":"Quantifies impact"}]'
        )
        advisor = ResumeAdvisor(provider)
        result = advisor.suggest_edits(sample_profile, sample_job)
        assert isinstance(result, list)
        assert len(result) >= 1
        assert isinstance(result[0], ResumeEdit)

    def test_suggest_edits_parses_fields(self, sample_profile, sample_job):
        from jobscout.advisor import ResumeAdvisor, ResumeEdit
        provider = MockProvider(
            '[{"section":"Summary","current_text":"Analyst","suggested_text":"Senior FP&A Analyst","reason":"Matches title"}]'
        )
        advisor = ResumeAdvisor(provider)
        result = advisor.suggest_edits(sample_profile, sample_job)
        assert result[0].section == "Summary"
        assert result[0].reason == "Matches title"

    def test_suggest_edits_fallback_on_bad_json(self, sample_profile, sample_job):
        from jobscout.advisor import ResumeAdvisor, ResumeEdit
        provider = MockProvider("This is not JSON at all")
        advisor = ResumeAdvisor(provider)
        result = advisor.suggest_edits(sample_profile, sample_job)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ResumeEdit)
        assert result[0].section == "General"


class TestRequirementsAnalyzer:
    """Test RequirementsAnalyzer.analyze()."""

    def test_analyze_returns_report(self, sample_profile, sample_job):
        from jobscout.advisor import RequirementsAnalyzer, RequirementsReport
        provider = MockProvider(
            '{"requirements":[{"item":"Python","priority":"must-have","candidate_has":true,"candidate_note":"5 years"}],'
            '"coverage_score":80.0,"critical_gaps":[]}'
        )
        analyzer = RequirementsAnalyzer(provider)
        result = analyzer.analyze(sample_profile, sample_job)
        assert isinstance(result, RequirementsReport)
        assert 0.0 <= result.coverage_score <= 100.0

    def test_analyze_parses_requirements(self, sample_profile, sample_job):
        from jobscout.advisor import Requirement, RequirementsAnalyzer
        provider = MockProvider(
            '{"requirements":[{"item":"SQL","priority":"must-have","candidate_has":true,"candidate_note":"Expert"}],'
            '"coverage_score":90.0,"critical_gaps":[]}'
        )
        analyzer = RequirementsAnalyzer(provider)
        result = analyzer.analyze(sample_profile, sample_job)
        assert len(result.requirements) >= 1
        req = result.requirements[0]
        assert isinstance(req, Requirement)
        assert req.item == "SQL"
        assert req.candidate_has is True

    def test_analyze_fallback_on_bad_json(self, sample_profile, sample_job):
        from jobscout.advisor import RequirementsAnalyzer, RequirementsReport
        provider = MockProvider("Not valid JSON")
        analyzer = RequirementsAnalyzer(provider)
        result = analyzer.analyze(sample_profile, sample_job)
        assert isinstance(result, RequirementsReport)
        assert result.coverage_score == 0.0
        assert len(result.critical_gaps) >= 1


class TestApplicationCoach:
    """Test ApplicationCoach.advise()."""

    def test_advise_returns_quick_tips(self, sample_profile, sample_job):
        from jobscout.advisor import ApplicationCoach, CoachAdvice
        provider = MockProvider(
            '{"quick_tips":["Apply via LinkedIn referral","Tailor cover letter to role"]}'
        )
        coach = ApplicationCoach(provider)
        result = coach.advise(sample_profile, sample_job, include_plan=False)
        assert isinstance(result, CoachAdvice)
        assert len(result.quick_tips) >= 1
        assert result.action_plan is None

    def test_advise_includes_action_plan_when_requested(self, sample_profile, sample_job):
        from jobscout.advisor import ApplicationCoach, CoachAdvice
        provider = MockProvider(
            '{"quick_tips":["Network first"],'
            '"action_plan":{"before_applying":["Research company"],'
            '"cover_letter":["Open with impact"],'
            '"interview_prep":["Practice STAR method"]}}'
        )
        coach = ApplicationCoach(provider)
        result = coach.advise(sample_profile, sample_job, include_plan=True)
        assert result.action_plan is not None
        assert "before_applying" in result.action_plan
        assert "cover_letter" in result.action_plan
        assert "interview_prep" in result.action_plan

    def test_advise_fallback_on_bad_json(self, sample_profile, sample_job):
        from jobscout.advisor import ApplicationCoach, CoachAdvice
        provider = MockProvider("Not valid JSON")
        coach = ApplicationCoach(provider)
        result = coach.advise(sample_profile, sample_job, include_plan=False)
        assert isinstance(result, CoachAdvice)
        assert len(result.quick_tips) >= 1
        assert result.action_plan is None
