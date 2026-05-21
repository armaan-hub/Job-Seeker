"""Profile parser for CV/resume processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WorkExperience:
    """Work experience entry."""

    company: str
    role: str
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    bullets: list[str] = field(default_factory=list)
    key_achievement: str | None = None


@dataclass
class Education:
    """Education entry."""

    degree: str
    institution: str
    year: str | None = None
    status: str | None = None


@dataclass
class Certification:
    """Certification entry."""

    name: str
    issuer: str | None = None
    date: str | None = None
    skills: list[str] = field(default_factory=list)
    grade: str | None = None


@dataclass
class UserProfile:
    """Parsed user profile."""

    name: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    summary: str | None = None

    experience: list[WorkExperience] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    certifications: list[Certification] = field(default_factory=list)

    skills: dict[str, list[str]] = field(default_factory=dict)
    target_roles: list[str] = field(default_factory=list)
    preferred_locations: list[str] = field(default_factory=list)

    languages: list[str] = field(default_factory=list)
    years_experience: int | None = None
    visa_status: str | None = None
    availability: str | None = None

    def to_prompt_text(self) -> str:
        """Convert profile to text for AI consumption."""
        lines = [
            f"Name: {self.name}",
            f"Title: {self.title}",
            f"Location: {self.location}",
            f"Experience: {self.years_experience or 'N/A'} years",
            "",
            "Professional Summary:",
            self.summary or "N/A",
            "",
            "Key Skills:",
        ]

        for category, skill_list in self.skills.items():
            lines.append(f"  {category}: {', '.join(skill_list)}")

        lines.extend(["", "Target Roles:", *[f"  - {r}" for r in self.target_roles]])

        if self.experience:
            lines.extend(["", "Work Experience:"])
            for exp in self.experience:
                lines.append(f"  - {exp.role} at {exp.company} ({exp.start_date} - {exp.end_date})")
                for bullet in exp.bullets[:3]:
                    lines.append(f"    {bullet[:100]}...")

        return "\n".join(lines)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserProfile:
        """Create profile from dictionary (e.g., parsed JSON)."""
        profile = cls()

        # Basic info
        profile_data = data.get("profile", {})
        profile.name = profile_data.get("name")
        profile.email = profile_data.get("contact", {}).get("email")
        profile.phone = profile_data.get("contact", {}).get("phone")
        profile.location = profile_data.get("contact", {}).get("location")
        profile.linkedin = profile_data.get("contact", {}).get("linkedin")
        profile.visa_status = profile_data.get("contact", {}).get("visa")
        profile.availability = profile_data.get("contact", {}).get("availability")

        profile.title = profile_data.get("title") or data.get("title")
        profile.summary = data.get("professional_summary")

        # Experience
        for exp in data.get("experience", []):
            profile.experience.append(
                WorkExperience(
                    company=exp.get("company", ""),
                    role=exp.get("role", ""),
                    start_date=exp.get("start"),
                    end_date=exp.get("end"),
                    location=exp.get("location"),
                    bullets=exp.get("bullets", []),
                    key_achievement=exp.get("key_achievement"),
                )
            )

        # Skills
        profile.skills = data.get("skills", {})

        # Target roles
        profile.target_roles = data.get("target_roles", [])

        # Preferred locations
        profile.preferred_locations = data.get("preferred_locations", [])

        # Metrics
        metrics = data.get("key_metrics", {})
        profile.years_experience = metrics.get("years_experience")

        return profile


class ProfileParser:
    """Parse user profiles from various formats."""

    @staticmethod
    def parse_json_file(path: Path) -> UserProfile:
        """Parse profile from JSON file."""
        import json

        with open(path) as f:
            data = json.load(f)
        return UserProfile.from_dict(data)

    @staticmethod
    def parse_markdown_file(path: Path) -> UserProfile:
        """Parse profile from Markdown file (basic extraction)."""
        # For now, return an empty profile with just the path
        # Full markdown parsing would be implemented with more sophisticated parsing
        return UserProfile()

    @staticmethod
    def parse_cv_file(path: Path) -> UserProfile:
        """Parse CV/resume file based on extension."""
        suffix = path.suffix.lower()

        if suffix == ".json":
            return ProfileParser.parse_json_file(path)
        elif suffix in (".md", ".markdown"):
            return ProfileParser.parse_markdown_file(path)
        else:
            # For PDF/DOCX, we'd need additional libraries
            # For now, return empty profile
            return UserProfile()

    @staticmethod
    def load_profile(profile_path: Path | str | None) -> UserProfile | None:
        """Load a profile from path, supporting JSON and Markdown formats."""
        if not profile_path:
            return None

        path = Path(profile_path)
        if not path.exists():
            raise FileNotFoundError(f"Profile file not found: {path}")

        return ProfileParser.parse_cv_file(path)
