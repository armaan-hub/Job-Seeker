"""Test configuration and fixtures."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


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