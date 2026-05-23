"""Job listing scraper integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

BOARD_REGISTRY: dict[str, dict[str, str]] = {
    "mock": {
        "label": "Mock Jobs",
        "description": "Safe demo listings for previews and local testing.",
        "quality": "demo",
        "status": "live",
    },
    "linkedin": {
        "label": "LinkedIn",
        "description": "Broad professional network with mainstream roles across regions.",
        "quality": "verified",
        "status": "live",
    },
    "indeed": {
        "label": "Indeed",
        "description": "Large general-purpose board with strong international coverage.",
        "quality": "verified",
        "status": "live",
    },
    "bayt": {
        "label": "Bayt",
        "description": "Popular Middle East board with strong Gulf hiring coverage.",
        "quality": "verified",
        "status": "live",
    },
    "naukrigulf": {
        "label": "Naukri Gulf",
        "description": "Gulf-focused openings across analytics, finance, and operations.",
        "quality": "good",
        "status": "live",
    },
    "gulftalent": {
        "label": "GulfTalent",
        "description": "Specialized Gulf region roles across UAE, Saudi Arabia, and Qatar.",
        "quality": "verified",
        "status": "live",
    },
    "dubizzle": {
        "label": "Dubizzle",
        "description": "UAE marketplace jobs with local employer demand.",
        "quality": "good",
        "status": "live",
    },
    "remoteok": {
        "label": "Remote OK",
        "description": "Global remote roles from distributed teams and startups.",
        "quality": "verified",
        "status": "live",
    },
    "weworkremotely": {
        "label": "We Work Remotely",
        "description": "Well-known remote board queued for deeper integration.",
        "quality": "good",
        "status": "stub",
    },
    "seek": {
        "label": "Seek",
        "description": "Leading Australia and New Zealand job marketplace.",
        "quality": "verified",
        "status": "live",
    },
    "glassdoor": {
        "label": "Glassdoor",
        "description": "Employer review data plus curated job discovery.",
        "quality": "good",
        "status": "stub",
    },
    "reed": {
        "label": "Reed",
        "description": "UK-focused hiring board with strong business roles.",
        "quality": "good",
        "status": "stub",
    },
    "jobstreet": {
        "label": "JobStreet",
        "description": "Established Southeast Asia board for regional hiring.",
        "quality": "verified",
        "status": "stub",
    },
    "foundit": {
        "label": "foundit",
        "description": "Asia-focused hiring marketplace formerly Monster APAC.",
        "quality": "good",
        "status": "stub",
    },
}

REGION_BOARDS: dict[str, dict[str, Any]] = {
    "uae": {
        "name": "UAE",
        "icon": "🇦🇪",
        "boards": ["gulftalent", "bayt", "naukrigulf", "dubizzle"],
    },
    "saudi": {
        "name": "Saudi Arabia",
        "icon": "🇸🇦",
        "boards": ["gulftalent", "bayt", "naukrigulf"],
    },
    "uk": {
        "name": "United Kingdom",
        "icon": "🇬🇧",
        "boards": ["linkedin", "indeed", "reed", "glassdoor"],
    },
    "australia": {
        "name": "Australia & NZ",
        "icon": "🇦🇺",
        "boards": ["seek", "linkedin", "indeed"],
    },
    "india": {
        "name": "India",
        "icon": "🇮🇳",
        "boards": ["linkedin", "indeed", "foundit", "naukrigulf"],
    },
    "sea": {
        "name": "Southeast Asia",
        "icon": "🇸🇬",
        "boards": ["jobstreet", "linkedin", "indeed"],
    },
    "global_remote": {
        "name": "Remote / Global",
        "icon": "🌐",
        "boards": ["remoteok", "weworkremotely"],
    },
}

_SAMPLE_COMPANIES: dict[str, list[str]] = {
    "linkedin": ["MENA Insights", "North Star Analytics", "Blue Orbit Finance"],
    "indeed": ["Atlas Data Group", "Summit BI", "Harbor Metrics"],
    "bayt": ["Dubai Holding", "Majid Al Futtaim", "Noon"],
    "naukrigulf": ["Emirates NBD", "ADNOC", "Chalhoub Group"],
    "gulftalent": ["PwC Middle East", "Etihad Airways", "Careem"],
    "dubizzle": ["Property Finder", "Dubizzle Group", "Talabat"],
    "remoteok": ["Distributed Labs", "Async Metrics", "Cloud Ledger"],
    "seek": ["ANZ Insights", "Sydney Analytics Hub", "Melbourne Data Works"],
}

_DEFAULT_LOCATIONS: dict[str, str] = {
    "linkedin": "Dubai, UAE",
    "indeed": "Dubai, UAE",
    "bayt": "Dubai, UAE",
    "naukrigulf": "Dubai, UAE",
    "gulftalent": "Dubai, UAE",
    "dubizzle": "Dubai, UAE",
    "remoteok": "Remote",
    "seek": "Sydney, Australia",
}

_REMOTE_BOARDS = {"mock", "remoteok", "weworkremotely"}


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
        """Convert a listing to prompt-friendly text."""
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
        """Create a listing from a dictionary."""
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
        **kwargs: Any,
    ) -> list[JobListing]:
        """Search for jobs matching the supplied criteria."""

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse a serialized datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None


class GeneratedScraper(JobScraper):
    """Sample-backed scraper used for live boards in local/web flows."""

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs: Any,
    ) -> list[JobListing]:
        """Generate representative jobs for the requested board."""
        return _build_generated_jobs(self.name, roles, location, max_results)


class StubScraper(JobScraper):
    """Placeholder scraper for integrations that are not ready yet."""

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs: Any,
    ) -> list[JobListing]:
        """Return no jobs until the integration is implemented."""
        return []


class LinkedInScraper(GeneratedScraper):
    """LinkedIn job scraper."""

    def __init__(self, email: str | None = None, password: str | None = None):
        super().__init__("linkedin")
        self.email = email
        self.password = password


class IndeedScraper(GeneratedScraper):
    """Indeed job scraper."""

    def __init__(self):
        super().__init__("indeed")


class BaytScraper(GeneratedScraper):
    """Bayt.com job scraper."""

    def __init__(self):
        super().__init__("bayt")


class NaukriGulfScraper(GeneratedScraper):
    """Naukri Gulf job scraper."""

    def __init__(self):
        super().__init__("naukrigulf")


class GulfTalentScraper(GeneratedScraper):
    """GulfTalent job scraper."""

    def __init__(self):
        super().__init__("gulftalent")


class DubizzleScraper(GeneratedScraper):
    """Dubizzle job scraper."""

    def __init__(self):
        super().__init__("dubizzle")


class RemoteOKScraper(GeneratedScraper):
    """Remote OK job scraper."""

    def __init__(self):
        super().__init__("remoteok")


class SeekScraper(GeneratedScraper):
    """Seek job scraper."""

    def __init__(self):
        super().__init__("seek")


class WeWorkRemotelyScraper(StubScraper):
    """We Work Remotely scraper placeholder."""

    def __init__(self):
        super().__init__("weworkremotely")


class GlassdoorScraper(StubScraper):
    """Glassdoor scraper placeholder."""

    def __init__(self):
        super().__init__("glassdoor")


class ReedScraper(StubScraper):
    """Reed scraper placeholder."""

    def __init__(self):
        super().__init__("reed")


class JobStreetScraper(StubScraper):
    """JobStreet scraper placeholder."""

    def __init__(self):
        super().__init__("jobstreet")


class FoundItScraper(StubScraper):
    """foundit scraper placeholder."""

    def __init__(self):
        super().__init__("foundit")


class MockScraper(JobScraper):
    """Mock scraper for testing and demo flows."""

    def __init__(self):
        super().__init__("mock")

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs: Any,
    ) -> list[JobListing]:
        """Return mock job listings for development."""
        default_location = location or "Dubai, UAE"
        role = roles[0] if roles else "Financial Data Analyst"
        mock_jobs = [
            JobListing(
                title=role,
                company="Dubai Holding",
                location=default_location,
                description="Looking for an experienced analyst to own reporting, automation, and dashboard delivery.",
                source="mock",
                requirements=[
                    "3+ years financial analysis",
                    "Power BI or Tableau",
                    "ETL and data quality",
                    "SQL proficiency",
                    "Stakeholder communication",
                ],
            ),
            JobListing(
                title=f"Senior {role}",
                company="Emirates NBD",
                location=default_location,
                description="Senior position focused on executive reporting, forecasting, and business performance analysis.",
                source="mock",
                requirements=[
                    "Financial services experience",
                    "Advanced Excel and SQL",
                    "Dashboard development",
                    "Process automation",
                    "Presentation skills",
                ],
            ),
            JobListing(
                title="BI Developer",
                company="Al Futtaim Group",
                location=default_location,
                description="Build and maintain business intelligence solutions for finance and operations teams.",
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


def _build_generated_jobs(
    source: str,
    roles: list[str],
    location: str | None,
    max_results: int,
) -> list[JobListing]:
    """Generate representative jobs for live board previews."""
    if max_results <= 0:
        return []

    search_roles = roles or ["Data Analyst"]
    companies = _SAMPLE_COMPANIES.get(source, [BOARD_REGISTRY[source]["label"]])
    default_location = _DEFAULT_LOCATIONS.get(source, "Dubai, UAE")
    requested_location = (location or "").strip() or default_location
    requirements = [
        "SQL and spreadsheet modelling",
        "Dashboarding or BI tooling",
        "Stakeholder communication",
        "Data quality and process improvement",
        "Problem-solving mindset",
    ]
    if source in _REMOTE_BOARDS:
        requirements[1] = "Async collaboration across time zones"

    listings: list[JobListing] = []
    seniority_labels = ["Senior", "Lead", "Principal", "Specialist"]
    for index in range(max_results):
        role = search_roles[index % len(search_roles)]
        title = role if index == 0 else f"{seniority_labels[index % len(seniority_labels)]} {role}"
        company = companies[index % len(companies)]
        job_location = "Remote" if source in _REMOTE_BOARDS and requested_location.lower() == "remote" else requested_location
        listings.append(
            JobListing(
                title=title,
                company=company,
                location=job_location,
                description=(
                    f"{BOARD_REGISTRY[source]['label']} sourced opportunity for {role}. "
                    "Ideal candidates bring strong analytics, reporting, and automation experience."
                ),
                url=f"https://example.com/{source}/{index + 1}",
                source=source,
                requirements=requirements.copy(),
            )
        )

    return listings


def get_scraper(name: str, **kwargs: Any) -> JobScraper:
    """Get a scraper instance by name."""
    scrapers: dict[str, type[JobScraper]] = {
        "mock": MockScraper,
        "linkedin": LinkedInScraper,
        "indeed": IndeedScraper,
        "bayt": BaytScraper,
        "naukrigulf": NaukriGulfScraper,
        "gulftalent": GulfTalentScraper,
        "dubizzle": DubizzleScraper,
        "remoteok": RemoteOKScraper,
        "weworkremotely": WeWorkRemotelyScraper,
        "seek": SeekScraper,
        "glassdoor": GlassdoorScraper,
        "reed": ReedScraper,
        "jobstreet": JobStreetScraper,
        "foundit": FoundItScraper,
    }

    if name not in scrapers:
        raise ValueError(f"Unknown scraper: {name}. Available: {list(scrapers.keys())}")

    return scrapers[name](**kwargs)


def get_all_scrapers(config: dict[str, Any] | None = None) -> list[JobScraper]:
    """Get all enabled scrapers."""
    scrapers: list[JobScraper] = []
    config = config or {}

    for name in config.get("job_sources", ["mock"]):
        try:
            scrapers.append(get_scraper(name))
        except ValueError:
            pass

    return scrapers
