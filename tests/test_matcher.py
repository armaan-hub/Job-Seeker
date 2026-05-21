"""Tests for job scraper."""

from jobscout.scraper import JobListing, MockScraper, get_scraper


class TestMockScraper:
    """Test mock scraper functionality."""

    def test_get_scraper(self):
        """Test getting a scraper by name."""
        scraper = get_scraper("mock")
        assert scraper.name == "mock"

    def test_mock_search_returns_jobs(self):
        """Test mock scraper returns jobs."""
        scraper = MockScraper()
        jobs = scraper.search(
            roles=["Data Analyst"],
            location="Dubai",
            max_results=5,
        )

        assert len(jobs) > 0
        assert all(isinstance(j, JobListing) for j in jobs)
        assert all(j.source == "mock" for j in jobs)


class TestJobListing:
    """Test job listing functionality."""

    def test_job_to_prompt_text(self):
        """Test converting job to prompt text."""
        job = JobListing(
            title="Data Analyst",
            company="Tech Corp",
            location="Dubai, UAE",
            description="Great opportunity",
            requirements=["Python", "SQL"],
        )

        text = job.to_prompt_text()

        assert "Data Analyst" in text
        assert "Tech Corp" in text
        assert "Dubai" in text
