"""Job listing scraper integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class JobListing:
    """Represents a job listing."""

    title: str
    company: str
    location: str
    description: str = ""
    url: str = ""
    source: str = ""

    salary: str | None = None
    posted_date: datetime | None = None

    requirements: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)

    def to_prompt_text(self) -> str:
        """Convert to text for AI matching."""
        return f"""
Title: {self.title}
Company: {self.company}
Location: {self.location}
Source: {self.source}
Description: {self.description[:500]}...
Requirements: {', '.join(self.requirements[:5])}
""".strip()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JobListing:
        """Create from dictionary."""
        return cls(
            title=data.get("title", ""),
            company=data.get("company", ""),
            location=data.get("location", ""),
            description=data.get("description", ""),
            url=data.get("url", ""),
            source=data.get("source", ""),
            salary=data.get("salary"),
            requirements=data.get("requirements", []),
            benefits=data.get("benefits", []),
        )


class JobScraper(ABC):
    """Abstract base class for job scrapers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs,
    ) -> list[JobListing]:
        """Search for jobs matching criteria."""

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None


class LinkedInScraper(JobScraper):
    """LinkedIn job scraper."""

    def __init__(self, email: str | None = None, password: str | None = None):
        super().__init__("linkedin")
        self.email = email
        self.password = password

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs,
    ) -> list[JobListing]:
        """Search LinkedIn for jobs."""
        # Placeholder - would implement actual API calls
        return []


class IndeedScraper(JobScraper):
    """Indeed job scraper."""

    def __init__(self):
        super().__init__("indeed")

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs,
    ) -> list[JobListing]:
        """Search Indeed for jobs."""
        # Placeholder - would implement actual API calls
        return []


class BaytScraper(JobScraper):
    """Bayt.com job scraper."""

    def __init__(self):
        super().__init__("bayt")

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs,
    ) -> list[JobListing]:
        """Search Bayt for jobs."""
        # Placeholder - would implement actual API calls
        return []


class NaukriGulfScraper(JobScraper):
    """Naukri Gulf job scraper."""

    def __init__(self):
        super().__init__("naukrigulf")

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs,
    ) -> list[JobListing]:
        """Search Naukri Gulf for jobs."""
        # Placeholder - would implement actual API calls
        return []


class MockScraper(JobScraper):
    """Mock scraper for testing/development."""

    def __init__(self):
        super().__init__("mock")

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs,
    ) -> list[JobListing]:
        """Return mock job listings for development."""
        mock_jobs = [
            JobListing(
                title="Financial Data Analyst",
                company="Dubai Holding",
                location="Dubai, UAE",
                description="Looking for experienced Financial Data Analyst to join our team. "
                "Must have experience with ETL pipelines, Power BI, and financial modeling. "
                "Knowledge of AML/KYC is a plus.",
                source="mock",
                requirements=[
                    "3+ years financial analysis",
                    "Power BI/DAX",
                    "ETL experience",
                    "SQL proficiency",
                    "AML knowledge preferred",
                ],
            ),
            JobListing(
                title="Senior Data Analyst - Finance",
                company="Emirates NBD",
                location="Dubai, UAE",
                description="Senior position for financial data analyst with banking experience. "
                "Will involve building dashboards, automated reports, and data pipelines.",
                source="mock",
                requirements=[
                    "5+ years in financial services",
                    "Power BI expert",
                    "Python/SQL required",
                    "VBA/Excel advanced",
                    "Banking AML experience",
                ],
            ),
            JobListing(
                title="BI Developer",
                company="Al Futtaim Group",
                location="Dubai, UAE",
                description="Build and maintain business intelligence solutions. "
                "Work with finance team to create automated reporting.",
                source="mock",
                requirements=[
                    "Power BI development",
                    "DAX expertise",
                    "SQL Server",
                    "Financial reporting",
                    "ETL pipelines",
                ],
            ),
        ]
        return mock_jobs[:max_results]


def get_scraper(name: str, **kwargs) -> JobScraper:
    """Get a scraper instance by name."""
    scrapers: dict[str, type[JobScraper]] = {
        "linkedin": LinkedInScraper,
        "indeed": IndeedScraper,
        "bayt": BaytScraper,
        "naukrigulf": NaukriGulfScraper,
        "mock": MockScraper,
    }

    if name not in scrapers:
        raise ValueError(f"Unknown scraper: {name}. Available: {list(scrapers.keys())}")

    return scrapers[name](**kwargs)


def get_all_scrapers(config: dict[str, Any] | None = None) -> list[JobScraper]:
    """Get all enabled scrapers."""
    scrapers = []
    config = config or {}

    for name in config.get("job_sources", ["mock"]):
        try:
            scrapers.append(get_scraper(name))
        except ValueError:
            pass

    return scrapers
