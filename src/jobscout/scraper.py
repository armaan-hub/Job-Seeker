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
    # Australia (new canonical IDs)
    "seek_au": {
        "label": "SEEK",
        "description": "Australia's largest job board with 100k+ live listings.",
        "quality": "verified",
        "status": "preview",
    },
    "indeed_au": {
        "label": "Indeed AU",
        "description": "Indeed's dedicated Australian portal with broad coverage.",
        "quality": "verified",
        "status": "preview",
    },
    "jora_au": {
        "label": "Jora AU",
        "description": "Aggregated job search for Australian opportunities.",
        "quality": "good",
        "status": "preview",
    },
    "adzuna_au": {
        "label": "Adzuna AU",
        "description": "Smart job search with salary insights for Australia.",
        "quality": "good",
        "status": "preview",
    },
    "careerone": {
        "label": "CareerOne",
        "description": "Australian job board with strong employer network.",
        "quality": "good",
        "status": "preview",
    },
    # New Zealand
    "seek_nz": {
        "label": "SEEK NZ",
        "description": "New Zealand's top job marketplace with nationwide listings.",
        "quality": "verified",
        "status": "preview",
    },
    "trademe_jobs": {
        "label": "Trade Me Jobs",
        "description": "NZ's most popular classifieds platform including jobs.",
        "quality": "verified",
        "status": "preview",
    },
    "jora_nz": {
        "label": "Jora NZ",
        "description": "Aggregated job search across New Zealand boards.",
        "quality": "good",
        "status": "preview",
    },
    # UK (new canonical IDs)
    "totaljobs": {
        "label": "Totaljobs",
        "description": "One of the UK's largest job boards with strong professional coverage.",
        "quality": "verified",
        "status": "preview",
    },
    "cv_library": {
        "label": "CV-Library",
        "description": "Leading UK job board with 1M+ registered candidates.",
        "quality": "verified",
        "status": "preview",
    },
    "indeed_uk": {
        "label": "Indeed UK",
        "description": "UK's top general job search engine.",
        "quality": "verified",
        "status": "preview",
    },
    "adzuna_uk": {
        "label": "Adzuna UK",
        "description": "UK aggregator with real-time salary benchmarks.",
        "quality": "good",
        "status": "preview",
    },
    # USA
    "indeed_us": {
        "label": "Indeed US",
        "description": "America's #1 job site with millions of listings.",
        "quality": "verified",
        "status": "preview",
    },
    "ziprecruiter": {
        "label": "ZipRecruiter",
        "description": "AI-powered job matching used by 1M+ employers.",
        "quality": "verified",
        "status": "preview",
    },
    "dice": {
        "label": "Dice",
        "description": "Premier US tech and IT job board.",
        "quality": "verified",
        "status": "preview",
    },
    "simplyhired": {
        "label": "SimplyHired",
        "description": "Broad US aggregator with salary estimator.",
        "quality": "good",
        "status": "preview",
    },
    # Canada
    "indeed_ca": {
        "label": "Indeed CA",
        "description": "Canada's leading job search engine.",
        "quality": "verified",
        "status": "preview",
    },
    "jobbank": {
        "label": "Job Bank",
        "description": "Government of Canada's official job board.",
        "quality": "verified",
        "status": "preview",
    },
    "workopolis": {
        "label": "Workopolis",
        "description": "Major Canadian job board with strong corporate listings.",
        "quality": "good",
        "status": "preview",
    },
    # Germany
    "stepstone_de": {
        "label": "StepStone DE",
        "description": "Germany's most-visited job portal with 60k+ listings.",
        "quality": "verified",
        "status": "preview",
    },
    "xing_jobs": {
        "label": "XING Jobs",
        "description": "German professional network job board (strong in DACH region).",
        "quality": "verified",
        "status": "preview",
    },
    "indeed_de": {
        "label": "Indeed DE",
        "description": "Indeed's German portal for nationwide roles.",
        "quality": "verified",
        "status": "preview",
    },
    "arbeitsagentur": {
        "label": "Arbeitsagentur",
        "description": "Official German Federal Employment Agency job board.",
        "quality": "verified",
        "status": "preview",
    },
    # France
    "indeed_fr": {
        "label": "Indeed FR",
        "description": "France's top job search with broad sector coverage.",
        "quality": "verified",
        "status": "preview",
    },
    "france_travail": {
        "label": "France Travail",
        "description": "Official French national employment service.",
        "quality": "verified",
        "status": "preview",
    },
    "apec": {
        "label": "APEC",
        "description": "French executive and manager career portal.",
        "quality": "verified",
        "status": "preview",
    },
    "cadremploi": {
        "label": "Cadremploi",
        "description": "Leading French board for cadres and senior professionals.",
        "quality": "good",
        "status": "preview",
    },
    # Netherlands
    "indeed_nl": {
        "label": "Indeed NL",
        "description": "Netherlands' most-used job search engine.",
        "quality": "verified",
        "status": "preview",
    },
    "nationalevacaturebank": {
        "label": "Nationale Vacaturebank",
        "description": "The Netherlands' largest job board.",
        "quality": "verified",
        "status": "preview",
    },
    "intermediair": {
        "label": "Intermediair",
        "description": "Dutch academic and professional career platform.",
        "quality": "good",
        "status": "preview",
    },
    # Saudi Arabia
    "bayt_sa": {
        "label": "Bayt KSA",
        "description": "Bayt's dedicated Saudi Arabia job listings.",
        "quality": "verified",
        "status": "preview",
    },
    "naukrigulf_sa": {
        "label": "NaukriGulf KSA",
        "description": "Saudi Arabia-focused NaukriGulf listings.",
        "quality": "good",
        "status": "preview",
    },
    "jadarat": {
        "label": "Jadarat",
        "description": "Saudi national job portal linked to government hiring.",
        "quality": "verified",
        "status": "preview",
    },
    # India (add to existing)
    "naukri": {
        "label": "Naukri",
        "description": "India's #1 job portal with 1M+ listings.",
        "quality": "verified",
        "status": "preview",
    },
    "indeed_in": {
        "label": "Indeed IN",
        "description": "Indeed's India portal with national and MNC roles.",
        "quality": "verified",
        "status": "preview",
    },
    "shine": {
        "label": "Shine",
        "description": "Indian job board by HT Media with strong analytics roles.",
        "quality": "good",
        "status": "preview",
    },
    "timesjobs": {
        "label": "TimesJobs",
        "description": "Times Group-owned Indian job portal with diverse listings.",
        "quality": "good",
        "status": "preview",
    },
    # Singapore
    "jobstreet_sg": {
        "label": "JobStreet SG",
        "description": "Singapore's leading job marketplace (SEEK-owned).",
        "quality": "verified",
        "status": "preview",
    },
    "mycareersfuture": {
        "label": "MyCareersFuture",
        "description": "Singapore government's official career portal.",
        "quality": "verified",
        "status": "preview",
    },
    "indeed_sg": {
        "label": "Indeed SG",
        "description": "Indeed's Singapore portal with local and MNC roles.",
        "quality": "verified",
        "status": "preview",
    },
    "glints_sg": {
        "label": "Glints SG",
        "description": "Tech-focused Southeast Asian job platform.",
        "quality": "good",
        "status": "preview",
    },
    # Southeast Asia
    "jobstreet_sea": {
        "label": "JobStreet SEA",
        "description": "Dominant job board across Malaysia, Philippines, Indonesia.",
        "quality": "verified",
        "status": "preview",
    },
    "jobsdb_sea": {
        "label": "JobsDB SEA",
        "description": "Major job board for Hong Kong and Southeast Asia.",
        "quality": "verified",
        "status": "preview",
    },
    "kalibrr": {
        "label": "Kalibrr",
        "description": "Tech-enabled job board for Philippines and Southeast Asia.",
        "quality": "good",
        "status": "preview",
    },
    "glints_sea": {
        "label": "Glints SEA",
        "description": "Southeast Asia's startup and tech job platform.",
        "quality": "good",
        "status": "preview",
    },
    # South Africa
    "careers24": {
        "label": "Careers24",
        "description": "South Africa's leading job board.",
        "quality": "verified",
        "status": "preview",
    },
    "pnet": {
        "label": "PNet",
        "description": "Major South African professional job portal.",
        "quality": "verified",
        "status": "preview",
    },
    "indeed_za": {
        "label": "Indeed ZA",
        "description": "Indeed's South Africa portal.",
        "quality": "verified",
        "status": "preview",
    },
    "adzuna_za": {
        "label": "Adzuna ZA",
        "description": "SA aggregator with salary data.",
        "quality": "good",
        "status": "preview",
    },
    # Brazil
    "catho": {
        "label": "Catho",
        "description": "Brazil's largest job portal with 5M+ candidates.",
        "quality": "verified",
        "status": "preview",
    },
    "vagas": {
        "label": "Vagas",
        "description": "Leading Brazilian job board for professional roles.",
        "quality": "verified",
        "status": "preview",
    },
    "indeed_br": {
        "label": "Indeed BR",
        "description": "Indeed's Brazil portal.",
        "quality": "verified",
        "status": "preview",
    },
    "gupy": {
        "label": "Gupy",
        "description": "Modern Brazilian HR platform used by major employers.",
        "quality": "good",
        "status": "preview",
    },
    # Global Remote (add to existing)
    "remotive": {
        "label": "Remotive",
        "description": "Curated remote job board for tech and digital professionals.",
        "quality": "verified",
        "status": "live",
        "tier": "free_api",
        "regions": ["global"],
    },
    "arbeitnow": {
        "label": "Arbeitnow",
        "description": "European and global remote job board with free public API.",
        "quality": "verified",
        "status": "live",
        "tier": "free_api",
        "regions": ["europe", "global"],
    },
    "themuse": {
        "label": "The Muse",
        "description": "US and global job board with company culture insights.",
        "quality": "verified",
        "status": "live",
        "tier": "free_api",
        "regions": ["usa", "global"],
    },
    "jobicy": {
        "label": "Jobicy",
        "description": "Remote-focused job board with free public API.",
        "quality": "good",
        "status": "live",
        "tier": "free_api",
        "regions": ["global"],
    },
    "wellfound": {
        "label": "Wellfound",
        "description": "AngelList Talent — startup and tech remote jobs.",
        "quality": "verified",
        "status": "preview",
    },
    "himalayas": {
        "label": "Himalayas",
        "description": "Fully remote jobs with transparent salaries and timezones.",
        "quality": "good",
        "status": "preview",
    },
}

REGION_BOARDS: dict[str, dict[str, Any]] = {
    "uae": {
        "name": "UAE / Middle East",
        "icon": "🇦🇪",
        "default_location": "Dubai, UAE",
        "boards": ["gulftalent", "bayt", "naukrigulf", "dubizzle"],
    },
    "saudi": {
        "name": "Saudi Arabia",
        "icon": "🇸🇦",
        "default_location": "Riyadh, Saudi Arabia",
        "boards": ["bayt_sa", "naukrigulf_sa", "jadarat", "gulftalent"],
    },
    "australia": {
        "name": "Australia",
        "icon": "🇦🇺",
        "default_location": "Sydney, Australia",
        "boards": ["seek_au", "indeed_au", "jora_au", "adzuna_au", "careerone"],
    },
    "new_zealand": {
        "name": "New Zealand",
        "icon": "🇳🇿",
        "default_location": "Auckland, New Zealand",
        "boards": ["seek_nz", "trademe_jobs", "jora_nz"],
    },
    "uk": {
        "name": "United Kingdom",
        "icon": "🇬🇧",
        "default_location": "London, UK",
        "boards": ["reed", "totaljobs", "cv_library", "indeed_uk", "adzuna_uk"],
    },
    "usa": {
        "name": "United States",
        "icon": "🇺🇸",
        "default_location": "New York, USA",
        "boards": ["indeed_us", "ziprecruiter", "dice", "simplyhired"],
    },
    "canada": {
        "name": "Canada",
        "icon": "🇨🇦",
        "default_location": "Toronto, Canada",
        "boards": ["indeed_ca", "jobbank", "workopolis"],
    },
    "germany": {
        "name": "Germany",
        "icon": "🇩🇪",
        "default_location": "Berlin, Germany",
        "boards": ["stepstone_de", "xing_jobs", "indeed_de", "arbeitsagentur"],
    },
    "france": {
        "name": "France",
        "icon": "🇫🇷",
        "default_location": "Paris, France",
        "boards": ["indeed_fr", "france_travail", "apec", "cadremploi"],
    },
    "netherlands": {
        "name": "Netherlands",
        "icon": "🇳🇱",
        "default_location": "Amsterdam, Netherlands",
        "boards": ["indeed_nl", "nationalevacaturebank", "intermediair"],
    },
    "india": {
        "name": "India",
        "icon": "🇮🇳",
        "default_location": "Bangalore, India",
        "boards": ["naukri", "indeed_in", "foundit", "shine", "timesjobs"],
    },
    "singapore": {
        "name": "Singapore",
        "icon": "🇸🇬",
        "default_location": "Singapore",
        "boards": ["jobstreet_sg", "mycareersfuture", "indeed_sg", "glints_sg"],
    },
    "sea": {
        "name": "Southeast Asia",
        "icon": "🌏",
        "default_location": "Kuala Lumpur, Malaysia",
        "boards": ["jobstreet_sea", "jobsdb_sea", "kalibrr", "glints_sea"],
    },
    "south_africa": {
        "name": "South Africa",
        "icon": "🇿🇦",
        "default_location": "Johannesburg, South Africa",
        "boards": ["careers24", "pnet", "indeed_za", "adzuna_za"],
    },
    "brazil": {
        "name": "Brazil",
        "icon": "🇧🇷",
        "default_location": "São Paulo, Brazil",
        "boards": ["catho", "vagas", "indeed_br", "gupy"],
    },
    "global_remote": {
        "name": "Remote / Global",
        "icon": "🌐",
        "default_location": "Remote",
        "boards": [
            "remoteok",
            "weworkremotely",
            "arbeitnow",
            "themuse",
            "jobicy",
            "remotive",
            "wellfound",
            "himalayas",
        ],
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
    "weworkremotely": "Remote",
    "seek": "Sydney, Australia",
    "glassdoor": "London, UK",
    "reed": "London, UK",
    "jobstreet": "Singapore",
    "foundit": "Bangalore, India",
    "seek_au": "Sydney, Australia",
    "indeed_au": "Sydney, Australia",
    "jora_au": "Sydney, Australia",
    "adzuna_au": "Sydney, Australia",
    "careerone": "Sydney, Australia",
    "seek_nz": "Auckland, New Zealand",
    "trademe_jobs": "Auckland, New Zealand",
    "jora_nz": "Auckland, New Zealand",
    "totaljobs": "London, UK",
    "cv_library": "London, UK",
    "indeed_uk": "London, UK",
    "adzuna_uk": "London, UK",
    "indeed_us": "New York, USA",
    "ziprecruiter": "New York, USA",
    "dice": "New York, USA",
    "simplyhired": "New York, USA",
    "indeed_ca": "Toronto, Canada",
    "jobbank": "Toronto, Canada",
    "workopolis": "Toronto, Canada",
    "stepstone_de": "Berlin, Germany",
    "xing_jobs": "Berlin, Germany",
    "indeed_de": "Berlin, Germany",
    "arbeitsagentur": "Berlin, Germany",
    "indeed_fr": "Paris, France",
    "france_travail": "Paris, France",
    "apec": "Paris, France",
    "cadremploi": "Paris, France",
    "indeed_nl": "Amsterdam, Netherlands",
    "nationalevacaturebank": "Amsterdam, Netherlands",
    "intermediair": "Amsterdam, Netherlands",
    "bayt_sa": "Riyadh, Saudi Arabia",
    "naukrigulf_sa": "Riyadh, Saudi Arabia",
    "jadarat": "Riyadh, Saudi Arabia",
    "naukri": "Bangalore, India",
    "indeed_in": "Bangalore, India",
    "shine": "Bangalore, India",
    "timesjobs": "Bangalore, India",
    "jobstreet_sg": "Singapore",
    "mycareersfuture": "Singapore",
    "indeed_sg": "Singapore",
    "glints_sg": "Singapore",
    "jobstreet_sea": "Kuala Lumpur, Malaysia",
    "jobsdb_sea": "Kuala Lumpur, Malaysia",
    "kalibrr": "Manila, Philippines",
    "glints_sea": "Kuala Lumpur, Malaysia",
    "careers24": "Johannesburg, South Africa",
    "pnet": "Johannesburg, South Africa",
    "indeed_za": "Johannesburg, South Africa",
    "adzuna_za": "Johannesburg, South Africa",
    "catho": "São Paulo, Brazil",
    "vagas": "São Paulo, Brazil",
    "indeed_br": "São Paulo, Brazil",
    "gupy": "São Paulo, Brazil",
    "remotive": "Remote",
    "arbeitnow": "Remote",
    "themuse": "Remote",
    "jobicy": "Remote",
    "wellfound": "Remote",
    "himalayas": "Remote",
}

_REMOTE_BOARDS = {"mock", "remoteok", "weworkremotely", "remotive", "arbeitnow", "themuse", "jobicy", "wellfound", "himalayas"}

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
    is_gateway: bool = False
    quality_score: int = 100
    scam_flags: list[str] = field(default_factory=list)

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
            is_gateway=data.get("is_gateway", False),
            quality_score=data.get("quality_score", 100),
            scam_flags=data.get("scam_flags", []),
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


class RemoteOKScraper(JobScraper):
    """Remote OK scraper – uses the public RemoteOK JSON API."""

    def __init__(self) -> None:
        super().__init__("remoteok")

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs: Any,
    ) -> list[JobListing]:
        """Fetch live remote jobs from remoteok.com/api."""
        import re
        import time

        try:
            import requests
        except ImportError:
            return _build_generated_jobs(self.name, roles, location, max_results)

        all_results: list[JobListing] = []
        seen_ids: set[str] = set()

        for role in roles[:2]:
            if len(all_results) >= max_results:
                break
            tag = role.lower().replace(" ", "-")
            try:
                resp = requests.get(
                    f"https://remoteok.com/api?tags={tag}",
                    headers={"User-Agent": "Mozilla/5.0 (AI Job Scout)"},
                    timeout=12,
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                jobs = [job for job in data if isinstance(job, dict) and "position" in job]
                for job in jobs:
                    job_id = str(job.get("id", ""))
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    url = job.get("url") or (
                        f"https://remoteok.com/l/{job_id}" if job_id else ""
                    )
                    tags = job.get("tags") or []
                    description = job.get("description") or ""
                    description = re.sub(r"<[^>]+>", " ", description).strip()
                    all_results.append(
                        JobListing(
                            title=job.get("position", role),
                            company=job.get("company", "Unknown"),
                            location="Remote",
                            description=(
                                description[:800]
                                if description
                                else (
                                    f"Remote {role} role at "
                                    f"{job.get('company', 'a distributed team')}."
                                )
                            ),
                            url=url,
                            source="remoteok",
                            salary=job.get("salary"),
                            requirements=tags[:6] if tags else [],
                        )
                    )
                    if len(all_results) >= max_results:
                        break
                time.sleep(0.5)
            except Exception:
                continue

        if not all_results:
            return _build_generated_jobs(self.name, roles, location, max_results)

        return all_results[:max_results]


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


class SeekAUScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("seek_au")


class IndeedAUScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("indeed_au")


class JoraAUScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("jora_au")


class AdzunaAUScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("adzuna_au")


class CareerOneScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("careerone")


class SeekNZScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("seek_nz")


class TradeMeJobsScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("trademe_jobs")


class JoraNZScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("jora_nz")


class TotalJobsScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("totaljobs")


class CVLibraryScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("cv_library")


class IndeedUKScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("indeed_uk")


class AdzunaUKScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("adzuna_uk")


class IndeedUSScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("indeed_us")


class ZipRecruiterScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("ziprecruiter")


class DiceScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("dice")


class SimplyHiredScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("simplyhired")


class IndeedCAScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("indeed_ca")


class JobBankScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("jobbank")


class WorkopolisScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("workopolis")


class StepStoneDEScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("stepstone_de")


class XingJobsScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("xing_jobs")


class IndeedDEScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("indeed_de")


class ArbeitsagenturScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("arbeitsagentur")


class IndeedFRScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("indeed_fr")


class FranceTravailScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("france_travail")


class APECScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("apec")


class CadremploiScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("cadremploi")


class IndeedNLScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("indeed_nl")


class NationaleVacaturebankScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("nationalevacaturebank")


class IntermediairScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("intermediair")


class BaytSAScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("bayt_sa")


class NaukriGulfSAScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("naukrigulf_sa")


class JadaratScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("jadarat")


class NaukriScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("naukri")


class IndeedINScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("indeed_in")


class ShineScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("shine")


class TimesJobsScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("timesjobs")


class JobStreetSGScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("jobstreet_sg")


class MyCareersFutureScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("mycareersfuture")


class IndeedSGScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("indeed_sg")


class GlintsSGScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("glints_sg")


class JobStreetSEAScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("jobstreet_sea")


class JobsDBSEAScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("jobsdb_sea")


class KalibrrScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("kalibrr")


class GlintsSEAScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("glints_sea")


class Careers24Scraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("careers24")


class PNetScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("pnet")


class IndeedZAScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("indeed_za")


class AdzunaZAScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("adzuna_za")


class CathoScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("catho")


class VagasScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("vagas")


class IndeedBRScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("indeed_br")


class GupyScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("gupy")


def _role_matches(role: str, title: str, tags: list[str] | None = None, description: str = "") -> bool:
    """Loose keyword match — any meaningful word from `role` found in title/tags/description."""
    _STOP = {"and", "or", "in", "the", "a", "an", "of", "at", "for", "with", "to", "senior", "junior"}
    words = [w for w in role.lower().split() if w not in _STOP and len(w) >= 3]
    if not words:
        return True  # no meaningful words → accept all
    haystack = (title + " " + " ".join(tags or []) + " " + description[:300]).lower()
    return any(w in haystack for w in words)


class RemotiveScraper(JobScraper):
    """Remotive scraper – uses the public Remotive JSON API."""

    def __init__(self) -> None:
        super().__init__("remotive")

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs: Any,
    ) -> list[JobListing]:
        """Fetch live remote jobs from remotive.com/api/remote-jobs."""
        import re
        import time

        try:
            import requests
        except ImportError:
            return _build_generated_jobs(self.name, roles, location, max_results)

        all_results: list[JobListing] = []
        seen_ids: set[str] = set()

        for role in roles[:2]:
            if len(all_results) >= max_results:
                break
            try:
                resp = requests.get(
                    "https://remotive.com/api/remote-jobs",
                    params={"search": role, "limit": 20},
                    headers={"User-Agent": "Mozilla/5.0 (AI Job Scout)"},
                    timeout=12,
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                jobs = data.get("jobs", [])
                for job in jobs:
                    job_id = str(job.get("id", ""))
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    title = job.get("title", role)
                    if not _role_matches(role, title, job.get("tags", [])):
                        continue
                    description = re.sub(r"<[^>]+>", " ", job.get("description", "")).strip()
                    all_results.append(
                        JobListing(
                            title=title,
                            company=job.get("company_name", "Unknown"),
                            location=job.get("candidate_required_location") or "Remote",
                            description=description[:800] if description else f"Remote {role} role.",
                            url=job.get("url", ""),
                            source="remotive",
                            salary=job.get("salary") or None,
                            posted_date=self._parse_date(job.get("publication_date")),
                            requirements=job.get("tags", [])[:6],
                            is_gateway=False,
                        )
                    )
                    if len(all_results) >= max_results:
                        break
                time.sleep(0.3)
            except Exception:
                continue

        if not all_results:
            return _build_generated_jobs(self.name, roles, location, max_results)

        return all_results[:max_results]


class ArbeitnowScraper(JobScraper):
    """Arbeitnow scraper – uses the public Arbeitnow job-board API."""

    def __init__(self) -> None:
        super().__init__("arbeitnow")

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs: Any,
    ) -> list[JobListing]:
        """Fetch live jobs from arbeitnow.com/api/job-board-api."""
        import time

        try:
            import requests
        except ImportError:
            return _build_generated_jobs(self.name, roles, location, max_results)

        all_results: list[JobListing] = []
        seen_slugs: set[str] = set()

        for role in roles[:2]:
            if len(all_results) >= max_results:
                break
            try:
                resp = requests.get(
                    "https://arbeitnow.com/api/job-board-api",
                    params={"q": role},
                    headers={"User-Agent": "Mozilla/5.0 (AI Job Scout)"},
                    timeout=12,
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                jobs = data.get("data", [])
                for job in jobs:
                    slug = job.get("slug", "")
                    if slug in seen_slugs:
                        continue
                    seen_slugs.add(slug)
                    title = job.get("title", role)
                    if not _role_matches(role, title, job.get("tags", [])):
                        continue
                    all_results.append(
                        JobListing(
                            title=title,
                            company=job.get("company_name", "Unknown"),
                            location=job.get("location") or "Remote",
                            description=(job.get("description") or f"Remote {role} role.")[:800],
                            url=job.get("url", ""),
                            source="arbeitnow",
                            posted_date=self._parse_date(job.get("created_at")),
                            requirements=job.get("tags", [])[:6],
                            is_gateway=False,
                        )
                    )
                    if len(all_results) >= max_results:
                        break
                time.sleep(0.3)
            except Exception:
                continue

        if not all_results:
            return _build_generated_jobs(self.name, roles, location, max_results)

        return all_results[:max_results]


class TheMuseScraper(JobScraper):
    """The Muse scraper – uses the public Muse jobs API."""

    def __init__(self) -> None:
        super().__init__("themuse")

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs: Any,
    ) -> list[JobListing]:
        """Fetch live jobs from themuse.com/api/public/jobs."""
        import time

        try:
            import requests
        except ImportError:
            return _build_generated_jobs(self.name, roles, location, max_results)

        all_results: list[JobListing] = []
        seen_ids: set[str] = set()

        try:
            resp = requests.get(
                "https://www.themuse.com/api/public/jobs",
                params={"page": 0, "category": "Data & Analysis", "level": ["Senior Level", "Mid Level"]},
                headers={"User-Agent": "Mozilla/5.0 (AI Job Scout)"},
                timeout=12,
            )
            if resp.status_code == 200:
                data = resp.json()
                jobs = data.get("results", [])
                for role in roles[:2]:
                    for job in jobs:
                        job_id = str(job.get("id", ""))
                        if job_id in seen_ids:
                            continue
                        title = job.get("name", "")
                        if not _role_matches(role, title):
                            continue
                        seen_ids.add(job_id)
                        levels = [lv.get("name", "") for lv in job.get("levels", [])]
                        locs = [lo.get("name", "") for lo in job.get("locations", [])]
                        refs = job.get("refs", {})
                        url = refs.get("landing_page", "")
                        all_results.append(
                            JobListing(
                                title=title,
                                company=job.get("company", {}).get("name", "Unknown"),
                                location=", ".join(locs) if locs else "Remote",
                                description=f"{title} at {job.get('company', {}).get('name', 'a company')}. Level: {', '.join(levels)}.",
                                url=url,
                                source="themuse",
                                posted_date=self._parse_date(job.get("published_on")),
                                requirements=levels[:3],
                                is_gateway=False,
                            )
                        )
                        if len(all_results) >= max_results:
                            break
                    if len(all_results) >= max_results:
                        break
            time.sleep(0.3)
        except Exception:
            pass

        if not all_results:
            # Fallback: broader search without category filter
            try:
                resp = requests.get(
                    "https://www.themuse.com/api/public/jobs",
                    params={"page": 0},
                    headers={"User-Agent": "Mozilla/5.0 (AI Job Scout)"},
                    timeout=12,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    jobs = data.get("results", [])
                    for role in roles[:2]:
                        for job in jobs:
                            job_id = str(job.get("id", ""))
                            if job_id in seen_ids:
                                continue
                            title = job.get("name", "")
                            if not _role_matches(role, title):
                                continue
                            seen_ids.add(job_id)
                            levels = [lv.get("name", "") for lv in job.get("levels", [])]
                            locs = [lo.get("name", "") for lo in job.get("locations", [])]
                            refs = job.get("refs", {})
                            url = refs.get("landing_page", "")
                            all_results.append(
                                JobListing(
                                    title=title,
                                    company=job.get("company", {}).get("name", "Unknown"),
                                    location=", ".join(locs) if locs else "Remote",
                                    description=f"{title} at {job.get('company', {}).get('name', 'a company')}. Level: {', '.join(levels)}.",
                                    url=url,
                                    source="themuse",
                                    posted_date=self._parse_date(job.get("published_on")),
                                    requirements=levels[:3],
                                    is_gateway=False,
                                )
                            )
                            if len(all_results) >= max_results:
                                break
                        if len(all_results) >= max_results:
                            break
            except Exception:
                pass

        if not all_results:
            return _build_generated_jobs(self.name, roles, location, max_results)

        return all_results[:max_results]


class JobicyScraper(JobScraper):
    """Jobicy scraper – uses the public Jobicy remote-jobs API."""

    def __init__(self) -> None:
        super().__init__("jobicy")

    def search(
        self,
        roles: list[str],
        location: str | None = None,
        max_results: int = 20,
        **kwargs: Any,
    ) -> list[JobListing]:
        """Fetch live remote jobs from jobicy.com/api/v2/remote-jobs."""
        import time

        try:
            import requests
        except ImportError:
            return _build_generated_jobs(self.name, roles, location, max_results)

        all_results: list[JobListing] = []
        seen_ids: set[str] = set()

        try:
            resp = requests.get(
                "https://jobicy.com/api/v2/remote-jobs",
                params={"count": 20, "industry": "data-analysis"},
                headers={"User-Agent": "Mozilla/5.0 (AI Job Scout)"},
                timeout=12,
            )
            if resp.status_code == 200:
                data = resp.json()
                jobs = data.get("jobs", [])
                for role in roles[:2]:
                    for job in jobs:
                        job_id = str(job.get("id", ""))
                        if job_id in seen_ids:
                            continue
                        title = job.get("jobTitle", role)
                        if not _role_matches(role, title, description=job.get("jobExcerpt", "")):
                            continue
                        seen_ids.add(job_id)
                        sal_min = job.get("annualSalaryMin")
                        sal_max = job.get("annualSalaryMax")
                        salary = None
                        if sal_min and sal_max:
                            salary = f"${sal_min:,}–${sal_max:,}"
                        elif sal_min:
                            salary = f"${sal_min:,}+"
                        all_results.append(
                            JobListing(
                                title=title,
                                company=job.get("companyName", "Unknown"),
                                location=job.get("jobGeo") or "Remote",
                                description=(job.get("jobExcerpt") or f"Remote {role} role.")[:800],
                                url=job.get("url", ""),
                                source="jobicy",
                                salary=salary,
                                posted_date=self._parse_date(job.get("pubDate")),
                                is_gateway=False,
                            )
                        )
                        if len(all_results) >= max_results:
                            break
                    if len(all_results) >= max_results:
                        break
            time.sleep(0.3)
        except Exception:
            pass

        if not all_results:
            return _build_generated_jobs(self.name, roles, location, max_results)

        return all_results[:max_results]


class WellfoundScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("wellfound")


class HimalayasScraper(GeneratedScraper):
    def __init__(self) -> None:
        super().__init__("himalayas")


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


def _search_url(source: str, role: str, location: str) -> str:
    """Generate a real job board search URL for a given source, role, and location."""
    import urllib.parse

    role_enc = urllib.parse.quote_plus(role)
    location_enc = urllib.parse.quote_plus(location)
    role_slug = urllib.parse.quote(role.lower().replace(" ", "-"), safe="-")
    location_slug = urllib.parse.quote(
        location.lower().replace(" ", "-").replace(",", "").strip(), safe="-"
    )

    templates: dict[str, str] = {
        # Australia — Seek uses slug+location path format
        "seek_au": f"https://www.seek.com.au/{role_slug}-jobs/in-{location_slug}",
        "seek": f"https://www.seek.com.au/jobs?keywords={role_enc}&where={location_enc}",  # legacy alias
        "indeed_au": f"https://au.indeed.com/jobs?q={role_enc}&l={location_enc}",
        "jora_au": f"https://au.jora.com/jobs?q={role_enc}&l={location_enc}",
        "adzuna_au": f"https://www.adzuna.com.au/jobs/search?q={role_enc}&where={location_enc}",
        "careerone": f"https://www.careerone.com.au/jobs?q={role_enc}&where={location_enc}",
        # New Zealand
        "seek_nz": f"https://www.seek.co.nz/jobs?keywords={role_enc}&where={location_enc}",
        "trademe_jobs": f"https://www.trademe.co.nz/a/jobs/search?search_string={role_enc}",
        "jora_nz": f"https://nz.jora.com/jobs?q={role_enc}&l={location_enc}",
        # UK — slug-only (no location in path avoids 404s on unknown city slugs)
        "reed": f"https://www.reed.co.uk/jobs/{role_slug}-jobs",
        "totaljobs": f"https://www.totaljobs.com/jobs/{role_slug}",
        "cv_library": f"https://www.cv-library.co.uk/search-jobs?q={role_enc}&geo={location_enc}&us=1",
        "indeed_uk": f"https://uk.indeed.com/jobs?q={role_enc}&l={location_enc}",
        "adzuna_uk": f"https://www.adzuna.co.uk/jobs/search?q={role_enc}&where={location_enc}",
        "guardian_jobs": f"https://jobs.theguardian.com/search/?q={role_enc}",
        # USA
        "indeed_us": f"https://www.indeed.com/jobs?q={role_enc}&l={location_enc}",
        "ziprecruiter": f"https://www.ziprecruiter.com/jobs-search?search={role_enc}&location={location_enc}",
        "dice": f"https://www.dice.com/jobs?q={role_enc}&location={location_enc}",
        "simplyhired": f"https://www.simplyhired.com/search?q={role_enc}&l={location_enc}",
        # Canada
        "indeed_ca": f"https://ca.indeed.com/jobs?q={role_enc}&l={location_enc}",
        "jobbank": f"https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={role_enc}&locationstring={location_enc}",
        "workopolis": f"https://www.workopolis.com/jobsearch/find-jobs?ak={role_enc}&l={location_enc}",
        # Germany
        "stepstone_de": f"https://www.stepstone.de/jobs/{role_slug}",
        "xing_jobs": f"https://www.xing.com/jobs/search?keywords={role_enc}&location={location_enc}",
        "indeed_de": f"https://de.indeed.com/jobs?q={role_enc}&l={location_enc}",
        "arbeitsagentur": f"https://www.arbeitsagentur.de/jobsuche/suche?was={role_enc}&wo={location_enc}",
        # France
        "indeed_fr": f"https://fr.indeed.com/jobs?q={role_enc}&l={location_enc}",
        "france_travail": f"https://www.france.travail.fr/offres-emploi/recherche/result.html?motsCles={role_enc}",
        "apec": f"https://www.apec.fr/candidat/recherche-emploi.html/emploi?motsCles={role_enc}",
        "cadremploi": f"https://www.cadremploi.fr/emploi/recherche?q={role_enc}&l={location_enc}",
        # Netherlands
        "indeed_nl": f"https://nl.indeed.com/jobs?q={role_enc}&l={location_enc}",
        "nationalevacaturebank": f"https://www.nationalevacaturebank.nl/vacature/zoeken?query={role_enc}&location={location_enc}",
        "intermediair": f"https://www.intermediair.nl/vacatures/{role_slug}",
        # UAE/Gulf (existing)
        "bayt": f"https://www.bayt.com/en/international/jobs/?q={role_enc}",
        "naukrigulf": f"https://www.naukrigulf.com/{role_slug}-jobs",
        "gulftalent": f"https://www.gulftalent.com/jobs?q={role_enc}&l={location_enc}",
        "dubizzle": f"https://uae.dubizzle.com/jobs/?q={role_enc}",
        # Saudi Arabia
        "bayt_sa": f"https://www.bayt.com/en/saudi-arabia/jobs/?q={role_enc}",
        "naukrigulf_sa": f"https://www.naukrigulf.com/{role_slug}-jobs-in-saudi-arabia",
        "jadarat": f"https://jadarat.sa/Search/{role_enc}",
        # India
        "naukri": f"https://www.naukri.com/{role_slug}-jobs",
        "indeed_in": f"https://www.indeed.co.in/jobs?q={role_enc}&l={location_enc}",
        "foundit": f"https://www.foundit.in/srp/results?query={role_enc}&location={location_enc}",
        "shine": f"https://www.shine.com/job-search/{role_slug}-jobs",
        "timesjobs": f"https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={role_enc}&txtLocation={location_enc}",
        # Singapore
        "jobstreet_sg": f"https://www.jobstreet.com.sg/en/job-search/find-jobs.php?q={role_enc}&l={location_enc}",
        "mycareersfuture": f"https://www.mycareersfuture.gov.sg/search?search={role_enc}&sortBy=new_posting_date",
        "indeed_sg": f"https://sg.indeed.com/jobs?q={role_enc}&l={location_enc}",
        "glints_sg": f"https://glints.com/sg/opportunities/jobs/explore?keyword={role_enc}&country=SG",
        # SEA
        "jobstreet_sea": f"https://www.jobstreet.com.my/en/job-search/find-jobs.php?q={role_enc}",
        "jobstreet": f"https://www.jobstreet.com.sg/en/job-search/find-jobs.php?q={role_enc}&l={location_enc}",  # legacy
        "jobsdb_sea": f"https://hk.jobsdb.com/hk/search-jobs/{role_slug}/1",
        "kalibrr": f"https://www.kalibrr.com/job-board/te/{role_slug}",
        "glints_sea": f"https://glints.com/opportunities/jobs/explore?keyword={role_enc}",
        # South Africa
        "careers24": f"https://www.careers24.com/jobs/?search={role_enc}&location={location_enc}",
        "pnet": f"https://www.pnet.co.za/jobs/?search={role_enc}&location={location_enc}",
        "indeed_za": f"https://za.indeed.com/jobs?q={role_enc}&l={location_enc}",
        "adzuna_za": f"https://www.adzuna.co.za/jobs/search?q={role_enc}",
        # Brazil
        "catho": f"https://www.catho.com.br/vagas/{role_slug}/",
        "vagas": f"https://www.vagas.com.br/vagas-de-{role_slug}",
        "indeed_br": f"https://br.indeed.com/jobs?q={role_enc}&l={location_enc}",
        "gupy": f"https://portal.gupy.io/job-search/term={role_enc}",
        # Global
        "linkedin": f"https://www.linkedin.com/jobs/search/?keywords={role_enc}&location={location_enc}",
        "indeed": f"https://www.indeed.com/jobs?q={role_enc}&l={location_enc}",
        "glassdoor": f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={role_enc}&locKeyword={location_enc}",
        "remoteok": f"https://remoteok.com/remote-{role_slug}-jobs",
        "weworkremotely": f"https://weworkremotely.com/remote-jobs/search?term={role_enc}",
        "remotive": f"https://remotive.com/remote-jobs?query={role_enc}",
        "wellfound": f"https://wellfound.com/jobs?q={role_enc}",
        "himalayas": f"https://himalayas.app/jobs/remote?q={role_enc}",
        "mock": "",
    }
    return templates.get(source, f"https://www.google.com/search?q={role_enc}+jobs+{location_enc}")


def _build_generated_jobs(
    source: str,
    roles: list[str],
    location: str | None,
    max_results: int,
) -> list[JobListing]:
    """Return one gateway search card per board (not fake multi-listings)."""
    if max_results <= 0:
        return []

    board_info = BOARD_REGISTRY.get(source, {})
    board_label = board_info.get("label", source.title())
    board_desc = board_info.get("description", f"Search {board_label} for job listings.")

    role = roles[0] if roles else "Data Analyst"
    default_location = _DEFAULT_LOCATIONS.get(source, location or "your area")
    requested_location = (location or "").strip() or default_location

    search_url = _search_url(source, role, requested_location)

    return [
        JobListing(
            title=f"Browse {role} jobs →",
            company=board_label,
            location=requested_location,
            description=f"{board_desc} Click to search real {role} openings on {board_label}.",
            url=search_url,
            source=source,
            requirements=[],
            is_gateway=True,
        )
    ]


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
        "seek": SeekAUScraper,
        "seek_au": SeekAUScraper,
        "indeed_au": IndeedAUScraper,
        "jora_au": JoraAUScraper,
        "adzuna_au": AdzunaAUScraper,
        "careerone": CareerOneScraper,
        "seek_nz": SeekNZScraper,
        "trademe_jobs": TradeMeJobsScraper,
        "jora_nz": JoraNZScraper,
        "glassdoor": GlassdoorScraper,
        "reed": ReedScraper,
        "totaljobs": TotalJobsScraper,
        "cv_library": CVLibraryScraper,
        "indeed_uk": IndeedUKScraper,
        "adzuna_uk": AdzunaUKScraper,
        "indeed_us": IndeedUSScraper,
        "ziprecruiter": ZipRecruiterScraper,
        "dice": DiceScraper,
        "simplyhired": SimplyHiredScraper,
        "indeed_ca": IndeedCAScraper,
        "jobbank": JobBankScraper,
        "workopolis": WorkopolisScraper,
        "stepstone_de": StepStoneDEScraper,
        "xing_jobs": XingJobsScraper,
        "indeed_de": IndeedDEScraper,
        "arbeitsagentur": ArbeitsagenturScraper,
        "indeed_fr": IndeedFRScraper,
        "france_travail": FranceTravailScraper,
        "apec": APECScraper,
        "cadremploi": CadremploiScraper,
        "indeed_nl": IndeedNLScraper,
        "nationalevacaturebank": NationaleVacaturebankScraper,
        "intermediair": IntermediairScraper,
        "bayt_sa": BaytSAScraper,
        "naukrigulf_sa": NaukriGulfSAScraper,
        "jadarat": JadaratScraper,
        "jobstreet": JobStreetScraper,
        "foundit": FoundItScraper,
        "naukri": NaukriScraper,
        "indeed_in": IndeedINScraper,
        "shine": ShineScraper,
        "timesjobs": TimesJobsScraper,
        "jobstreet_sg": JobStreetSGScraper,
        "mycareersfuture": MyCareersFutureScraper,
        "indeed_sg": IndeedSGScraper,
        "glints_sg": GlintsSGScraper,
        "jobstreet_sea": JobStreetSEAScraper,
        "jobsdb_sea": JobsDBSEAScraper,
        "kalibrr": KalibrrScraper,
        "glints_sea": GlintsSEAScraper,
        "careers24": Careers24Scraper,
        "pnet": PNetScraper,
        "indeed_za": IndeedZAScraper,
        "adzuna_za": AdzunaZAScraper,
        "catho": CathoScraper,
        "vagas": VagasScraper,
        "indeed_br": IndeedBRScraper,
        "gupy": GupyScraper,
        "remotive": RemotiveScraper,
        "wellfound": WellfoundScraper,
        "himalayas": HimalayasScraper,
        "arbeitnow": ArbeitnowScraper,
        "themuse": TheMuseScraper,
        "jobicy": JobicyScraper,
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
