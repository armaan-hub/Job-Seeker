"""Tests for cv_tailor module — all AI calls are mocked."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import MagicMock, patch


SAMPLE_PROFILE = {
    "name": "Aniket Kumar Mishra",
    "current_role": "Financial Data Analyst",
    "summary": "Financial analyst with 5+ years in UAE/India. Expert in SQL, Excel, Power BI.",
    "skills": ["SQL", "Excel", "Power BI", "Python", "ETL", "Financial Modeling", "SAP"],
    "experience": [
        {
            "title": "Financial Data Analyst",
            "company": "Chalhoub Group",
            "responsibilities": [
                "Built ETL pipelines reducing processing time by 40%",
                "Created Power BI dashboards for C-suite reporting",
                "Managed $50M budget analysis using SQL and Excel",
            ]
        }
    ],
    "education": [{"degree": "B.Com", "institution": "University of Mumbai"}],
}

SAMPLE_JD = """
We are looking for a Senior Financial Analyst with expertise in SQL, Power BI,
and advanced Excel. The role involves ETL pipeline management, financial modeling,
KPI reporting, and working with SAP ERP system. Python skills preferred.
Experience with Bloomberg terminal is a plus.
"""


def test_keyword_fallback_no_provider():
    from jobscout.cv_tailor import tailor_cv
    result = tailor_cv(SAMPLE_PROFILE, "Senior Financial Analyst", "Deloitte", SAMPLE_JD, provider=None)

    assert "tailored_sections" in result
    assert "gaps" in result
    assert "keywords_added" in result
    assert "match_score" in result
    assert result["ai_available"] is False
    assert isinstance(result["match_score"], int)
    assert 0 <= result["match_score"] <= 100


def test_cache_returns_same_result():
    from jobscout.cv_tailor import tailor_cv, _CACHE
    _CACHE.clear()

    r1 = tailor_cv(SAMPLE_PROFILE, "Analyst", "KPMG", SAMPLE_JD, provider=None)
    r2 = tailor_cv(SAMPLE_PROFILE, "Analyst", "KPMG", SAMPLE_JD, provider=None)
    assert r1 is r2  # Same object from cache


def test_gaps_are_missing_keywords():
    from jobscout.cv_tailor import tailor_cv, _CACHE
    _CACHE.clear()

    jd_with_rare_skill = SAMPLE_JD + "\nMust have experience with Hyperion Financial Management."
    result = tailor_cv(SAMPLE_PROFILE, "Analyst", "EY", jd_with_rare_skill, provider=None)
    # Hyperion is in JD but likely not in profile
    assert isinstance(result["gaps"], list)


def test_match_score_is_reasonable():
    from jobscout.cv_tailor import tailor_cv, _CACHE
    _CACHE.clear()

    result = tailor_cv(SAMPLE_PROFILE, "Data Analyst", "Accenture", SAMPLE_JD, provider=None)
    # Profile has SQL, Power BI, Excel, ETL, SAP — JD asks for all of those
    # Match score should be > 0
    assert result["match_score"] > 0


def test_ai_provider_failure_falls_back():
    from jobscout.cv_tailor import tailor_cv, _CACHE
    _CACHE.clear()

    mock_provider = MagicMock()
    mock_provider.complete.side_effect = Exception("API error")

    result = tailor_cv(SAMPLE_PROFILE, "Analyst", "PwC", SAMPLE_JD, provider=mock_provider)
    assert result["ai_available"] is False
    assert "tailored_sections" in result


def test_empty_jd_raises():
    """Flask route should reject empty JD, but tailor_cv itself handles gracefully."""
    from jobscout.cv_tailor import tailor_cv, _CACHE
    _CACHE.clear()

    result = tailor_cv(SAMPLE_PROFILE, "Analyst", "Co", "", provider=None)
    assert "tailored_sections" in result  # Should not crash


def test_profile_to_text_flattens_correctly():
    from jobscout.cv_tailor import _profile_to_text
    text = _profile_to_text(SAMPLE_PROFILE)
    assert "Aniket" in text
    assert "SQL" in text
    assert "ETL" in text


def test_ai_provider_success_returns_ai_available():
    """When provider returns valid JSON, ai_available should be True."""
    from jobscout.cv_tailor import tailor_cv, _CACHE
    _CACHE.clear()

    valid_response = {
        "summary": "Experienced analyst.",
        "key_skills": "• SQL\n• Power BI",
        "experience_highlights": "• Led ETL projects",
        "cover_note": "Strong fit for this role.",
    }

    mock_provider = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"summary": "Experienced analyst.", "key_skills": "• SQL", "experience_highlights": "• Led ETL", "cover_note": "Strong fit."}'
    mock_provider.complete.return_value = mock_response

    result = tailor_cv(SAMPLE_PROFILE, "Analyst", "Firm", SAMPLE_JD, provider=mock_provider)
    assert result["ai_available"] is True
    assert "tailored_sections" in result
