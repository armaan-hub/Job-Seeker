"""Tests for scam_detector module."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from jobscout.scam_detector import score_job, QualityResult


def test_clean_job_scores_high():
    r = score_job(
        title="Senior Data Analyst",
        company="Accenture",
        description="We are looking for a Senior Data Analyst with 5+ years experience in SQL, Python, and Tableau. You will work with financial data and create dashboards.",
        url="https://www.seek.com.au/job/12345",
    )
    assert r.score >= 70
    assert not r.flags


def test_missing_company_penalised():
    r = score_job(
        title="Data Analyst",
        company="",
        description="Join our team for data analysis work using Excel and Python.",
        url="https://example.com/job",
    )
    assert "missing_company" in r.flags
    assert r.score < 60


def test_scam_keywords_detected():
    r = score_job(
        title="Work From Home Data Entry",
        company="EasyMoney Ltd",
        description="Unlimited earning potential! No experience needed make money from home. Commission only role.",
        url="https://jobs.example.com/scam",
    )
    assert any("scam_keywords" in f for f in r.flags)
    assert r.score < 50


def test_example_url_penalised():
    r = score_job(
        title="Analyst",
        company="KPMG",
        description="Detailed financial analysis role with Excel, Power BI required. Strong analytical skills needed.",
        url="https://example.com/job",
    )
    assert "no_apply_link" in r.flags


def test_duplicate_detection():
    seen: set[str] = set()
    r1 = score_job("Data Analyst", "Deloitte", "Full description here for analysis role needing SQL skills.", "https://seek.com.au/1", seen_keys=seen)
    r2 = score_job("Data Analyst", "Deloitte", "Full description here for analysis role needing SQL skills.", "https://seek.com.au/2", seen_keys=seen)
    assert "duplicate_listing" not in r1.flags
    assert "duplicate_listing" in r2.flags


def test_short_description_penalised():
    r = score_job(
        title="Analyst",
        company="ABC Corp",
        description="Great job.",
        url="https://jobs.abc.com/123",
    )
    assert "missing_description" in r.flags
