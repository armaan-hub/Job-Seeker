"""Tests for matcher fallback behavior."""

import jobscout.matcher as matcher
from jobscout.matcher import JobMatcher
from jobscout.providers.base import AIProvider, AIResponse, ProviderType
from jobscout.scraper import JobListing


class RaisingProvider(AIProvider):
    """Provider test double that always raises."""

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def complete(self, prompt: str, system: str | None = None, **kwargs) -> AIResponse:
        raise RuntimeError(self.message)

    def provider_type(self) -> ProviderType:
        return ProviderType.OPENCODE


def _make_job() -> JobListing:
    return JobListing(
        title="Data Analyst",
        company="Test",
        location="Sydney",
        description="SQL Python Excel data analysis financial reporting",
        requirements=["SQL", "Python", "Excel"],
    )


def test_keyword_fallback_score_reflects_overlap() -> None:
    """Keyword fallback should reward matching profile keywords."""
    assert hasattr(matcher, "_keyword_fallback_score")

    score = matcher._keyword_fallback_score(
        "Financial Data Analyst with SQL Python Excel Power BI skills and 5 years experience",
        _make_job(),
    )

    assert score == 80.0


def test_match_single_sanitizes_html_errors_and_uses_keyword_score() -> None:
    """HTML provider errors should not leak raw markup into reasoning."""
    result = JobMatcher(RaisingProvider("<!DOCTYPE html><html><body>Login</body></html>"))._match_single(
        "Financial Data Analyst with SQL Python Excel Power BI skills and 5 years experience",
        _make_job(),
    )

    assert result.reasoning == (
        "AI analysis unavailable — provider returned an unexpected response. "
        "Check your API key or provider settings."
    )
    assert result.score == 80.0
    assert result.skill_match == {}
    assert result.missing_skills == []
    assert result.strengths == ["Role at Test in Sydney — manual review recommended"]
    assert result.improvement_tips == [
        "AI analysis is temporarily unavailable. Review the job description directly."
    ]
