"""Test configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add project root and src to path for imports
_root = str(Path(__file__).parent.parent)
_src = str(Path(__file__).parent.parent / "src")
for _p in (_root, _src):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Silence SECRET_KEY warning in all web tests
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")


@pytest.fixture
def sample_profile():
    """Sample user profile for testing."""
    from jobscout.profile import UserProfile

    return UserProfile(
        name="Test User",
        title="Data Analyst",
        location="Dubai, UAE",
        years_experience=5,
        summary="Experienced data analyst with ETL skills",
        skills={
            "data_engineering": ["ETL", "Power BI", "SQL"],
            "languages": ["Python", "English"],
        },
        target_roles=["Data Analyst", "BI Developer"],
        preferred_locations=["Dubai, UAE"],
    )


@pytest.fixture
def sample_job():
    """Sample job listing for testing."""
    from jobscout.scraper import JobListing

    return JobListing(
        title="Data Analyst",
        company="Tech Corp",
        location="Dubai, UAE",
        description="Looking for a data analyst with ETL experience",
        source="test",
        requirements=["Python", "SQL", "Power BI"],
    )
