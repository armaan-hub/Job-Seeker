"""Tests for profile parsing."""

from pathlib import Path

from jobscout.profile import ProfileParser, UserProfile


class TestProfileParser:
    """Test profile parser functionality."""

    def test_load_json_profile(self):
        """Test loading a JSON profile."""
        profile_path = Path(__file__).parent.parent / "data" / "profile.json"

        if profile_path.exists():
            profile = ProfileParser.load_profile(profile_path)

            assert profile.name == "Aniket Kumar Mishra"
            assert "Financial Data Analyst" in profile.title
            assert profile.location == "Dubai, UAE"
            assert len(profile.experience) > 0
            assert len(profile.skills) > 0

    def test_profile_to_prompt(self):
        """Test converting profile to AI prompt text."""
        profile = UserProfile(
            name="Test User",
            title="Software Engineer",
            location="Dubai, UAE",
            years_experience=5,
            skills={"languages": ["Python", "JavaScript"]},
        )

        text = profile.to_prompt_text()

        assert "Test User" in text
        assert "Software Engineer" in text
        assert "Python" in text
        assert "Dubai, UAE" in text

    def test_profile_from_dict(self):
        """Test creating profile from dictionary."""
        data = {
            "profile": {
                "name": "John Doe",
                "contact": {
                    "email": "john@example.com",
                    "location": "Dubai",
                },
            },
            "title": "Data Analyst",
            "skills": {"languages": ["Python"]},
            "experience": [
                {
                    "company": "Tech Corp",
                    "role": "Junior Developer",
                    "start": "2020-01",
                    "end": "2023-01",
                    "bullets": ["Built things"],
                }
            ],
        }

        profile = UserProfile.from_dict(data)

        assert profile.name == "John Doe"
        assert profile.email == "john@example.com"
        assert profile.title == "Data Analyst"
        assert len(profile.experience) == 1
        assert profile.experience[0].company == "Tech Corp"
