"""Tests for job scraper."""

from jobscout.scraper import BOARD_REGISTRY, REGION_BOARDS, JobListing, MockScraper, get_scraper


class TestMockScraper:
    """Test mock scraper functionality."""

    def test_get_scraper(self):
        """Test getting a scraper by name."""
        scraper = get_scraper("mock")
        assert scraper.name == "mock"

    def test_get_scraper_supports_international_boards(self):
        """Test new international scrapers can be constructed."""
        assert get_scraper("remoteok").name == "remoteok"
        assert get_scraper("gulftalent").name == "gulftalent"
        assert get_scraper("seek").name == "seek"
        assert get_scraper("weworkremotely").name == "weworkremotely"

    def test_board_registry_and_regions_cover_new_boards(self):
        """Test board metadata and regional mappings are exposed."""
        assert len(BOARD_REGISTRY) == 14
        assert BOARD_REGISTRY["remoteok"]["status"] == "live"
        assert BOARD_REGISTRY["weworkremotely"]["status"] == "stub"
        assert REGION_BOARDS["uae"]["boards"] == ["gulftalent", "bayt", "naukrigulf", "dubizzle"]
        assert REGION_BOARDS["global_remote"]["boards"] == ["remoteok", "weworkremotely"]

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
