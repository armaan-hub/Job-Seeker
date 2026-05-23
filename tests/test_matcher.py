"""Tests for job scraper."""

from jobscout.scraper import BOARD_REGISTRY, REGION_BOARDS, JobListing, MockScraper, get_scraper


class TestMockScraper:
    """Test mock scraper functionality."""

    def test_get_scraper(self):
        """Test getting a scraper by name."""
        scraper = get_scraper("mock")
        assert scraper.name == "mock"

    def test_get_scraper_supports_international_boards(self):
        """Test international scrapers can be constructed via canonical and legacy IDs."""
        assert get_scraper("remoteok").name == "remoteok"
        assert get_scraper("gulftalent").name == "gulftalent"
        # seek is now seek_au; legacy alias still works
        assert get_scraper("seek_au").name == "seek_au"
        assert get_scraper("seek").name == "seek_au"  # legacy alias
        assert get_scraper("weworkremotely").name == "weworkremotely"
        # Spot-check new global regions
        assert get_scraper("indeed_us").name == "indeed_us"
        assert get_scraper("stepstone_de").name == "stepstone_de"
        assert get_scraper("naukri").name == "naukri"

    def test_board_registry_and_regions_cover_new_boards(self):
        """Test board metadata and regional mappings are exposed."""
        # Registry now has 70+ boards covering 16 regions globally
        assert len(BOARD_REGISTRY) >= 60
        assert BOARD_REGISTRY["remoteok"]["status"] == "live"
        # New global regions present
        assert "usa" in REGION_BOARDS
        assert "germany" in REGION_BOARDS
        assert "australia" in REGION_BOARDS
        assert "brazil" in REGION_BOARDS
        assert REGION_BOARDS["uae"]["boards"] == ["gulftalent", "bayt", "naukrigulf", "dubizzle"]
        assert "remoteok" in REGION_BOARDS["global_remote"]["boards"]
        assert "remotive" in REGION_BOARDS["global_remote"]["boards"]

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
