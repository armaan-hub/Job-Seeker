"""Web wizard flow tests."""

from __future__ import annotations

import io
import json

import pytest

from web.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def sample_profile_json() -> str:
    return json.dumps(
        {
            "profile": {
                "name": "Flow User",
                "title": "Data Analyst",
                "contact": {"location": "Dubai, UAE"},
            },
            "skills": {"core": ["SQL", "Power BI"]},
            "target_roles": ["Data Analyst", "BI Developer"],
            "preferred_locations": ["Dubai, UAE"],
        }
    )


@pytest.fixture
def large_profile_json(sample_profile_json: str) -> str:
    payload = json.loads(sample_profile_json)
    payload["professional_summary"] = "x" * 4000
    return json.dumps(payload)


class TestUploadStep:
    def test_get_upload_page(self, client) -> None:
        response = client.get("/wizard/upload")
        assert response.status_code == 200
        assert b"Upload Your Profile" in response.data

    def test_valid_json_upload_redirects_to_configure(self, client, sample_profile_json: str) -> None:
        response = client.post(
            "/wizard/upload",
            data={"profile_json": (io.BytesIO(sample_profile_json.encode("utf-8")), "profile.json")},
            content_type="multipart/form-data",
        )

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/wizard/configure")

    def test_invalid_json_redirects_back_with_error(self, client) -> None:
        response = client.post(
            "/wizard/upload",
            data={"profile_json": (io.BytesIO(b"not-json"), "profile.json")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Invalid JSON file" in response.data

    def test_missing_file_shows_error(self, client) -> None:
        response = client.post("/wizard/upload", data={}, follow_redirects=True)

        assert response.status_code == 200
        assert b"Please select a JSON file" in response.data

    def test_large_profile_uses_disk_fallback(
        self, client, large_profile_json: str, monkeypatch, tmp_path
    ) -> None:
        from web import wizard

        monkeypatch.setattr(wizard.Path, "home", lambda: tmp_path)

        client.post(
            "/wizard/upload",
            data={"profile_json": (io.BytesIO(large_profile_json.encode("utf-8")), "profile.json")},
            content_type="multipart/form-data",
        )

        with client.session_transaction() as sess:
            assert sess["profile_data"]["profile_storage"] == "disk"


class TestConfigureStep:
    def test_get_configure_redirects_if_no_profile(self, client) -> None:
        response = client.get("/wizard/configure")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/wizard/upload")

    def test_get_configure_prefills_from_session(self, client) -> None:
        with client.session_transaction() as sess:
            sess["profile_data"] = {"profile_json": "{}"}
            sess["profile_preview"] = {
                "target_roles": ["Data Analyst"],
                "location": "Dubai, UAE",
            }

        response = client.get("/wizard/configure")

        assert response.status_code == 200
        assert b"Data Analyst" in response.data

    def test_post_configure_stores_config(self, client) -> None:
        with client.session_transaction() as sess:
            sess["profile_data"] = {"profile_json": "{}"}

        response = client.post(
            "/wizard/configure",
            data={
                "roles": "Data Analyst, BI Developer",
                "location": "Dubai, UAE",
                "sources": ["mock", "indeed"],
                "max_results": "10",
            },
        )

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/wizard/search")
        with client.session_transaction() as sess:
            assert sess["search_config"]["roles"] == ["Data Analyst", "BI Developer"]

    def test_post_configure_empty_roles_shows_error(self, client) -> None:
        with client.session_transaction() as sess:
            sess["profile_data"] = {"profile_json": "{}"}

        response = client.post(
            "/wizard/configure",
            data={"roles": "", "location": "Dubai", "sources": ["mock"], "max_results": "10"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Please enter at least one job role" in response.data

    def test_post_configure_empty_sources_shows_error(self, client) -> None:
        with client.session_transaction() as sess:
            sess["profile_data"] = {"profile_json": "{}"}

        response = client.post(
            "/wizard/configure",
            data={"roles": "Data Analyst", "location": "Dubai", "max_results": "10"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Please select at least one job source" in response.data


class TestSearchStep:
    def test_search_post_starts_worker(self, client, monkeypatch) -> None:
        from web import routes

        monkeypatch.setattr(routes, "start_search", lambda profile_data, search_config: "job-123")

        with client.session_transaction() as sess:
            sess["profile_data"] = {"profile_json": "{}"}
            sess["search_config"] = {
                "roles": ["Data Analyst"],
                "location": "Dubai",
                "sources": ["mock"],
                "max_results": 10,
            }

        response = client.post("/wizard/search")

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/wizard/searching")
        with client.session_transaction() as sess:
            assert sess["job_id"] == "job-123"

    def test_searching_page_renders(self, client) -> None:
        with client.session_transaction() as sess:
            sess["job_id"] = "job-123"

        response = client.get("/wizard/searching")

        assert response.status_code == 200
        assert b"Finding your matches" in response.data

    def test_search_status_done_returns_redirect_url(self, client, monkeypatch) -> None:
        from web import routes

        monkeypatch.setattr(routes, "get_search_status", lambda job_id: {"status": "done", "count": 2})

        with client.session_transaction() as sess:
            sess["job_id"] = "job-123"

        response = client.get("/wizard/search-status")

        assert response.status_code == 200
        body = response.get_json()
        assert body["status"] == "done"
        assert body["redirect"].endswith("/wizard/results")

    def test_search_status_error_returns_configure_url(self, client, monkeypatch) -> None:
        from web import routes

        monkeypatch.setattr(routes, "get_search_status", lambda job_id: {"status": "error"})

        with client.session_transaction() as sess:
            sess["job_id"] = "job-123"

        response = client.get("/wizard/search-status")

        assert response.status_code == 200
        body = response.get_json()
        assert body["status"] == "error"
        assert body["redirect"].endswith("/wizard/configure")

    def test_zero_results_worker_sets_error(self, monkeypatch, sample_profile_json: str) -> None:
        from web.wizard import JOB_REGISTRY, run_search_worker

        class EmptyScraper:
            def search(self, roles, location, max_results):
                return []

        from web import wizard

        monkeypatch.setattr(wizard, "get_scraper", lambda source: EmptyScraper())

        job_id = "job-zero"
        run_search_worker(
            profile_dict={"profile_json": sample_profile_json},
            search_config={
                "roles": ["Data Analyst"],
                "location": "Dubai",
                "sources": ["mock"],
                "max_results": 10,
            },
            job_id=job_id,
        )

        assert JOB_REGISTRY[job_id]["status"] == "error"


@pytest.fixture
def seeded_results() -> list[dict]:
    return [
        {
            "job": {
                "title": "Data Analyst",
                "company": "ACME Corp",
                "location": "Dubai, UAE",
                "url": "https://example.com/job/1",
                "source": "mock",
                "salary": "AED 15000",
                "description": "desc",
                "requirements": [],
                "benefits": [],
            },
            "score": 85.0,
            "reasoning": "Strong match due to Python and SQL skills.",
            "skill_match": {"Python": 0.9, "SQL": 0.8},
            "missing_skills": ["Tableau"],
            "strengths": ["Python", "SQL", "Excel"],
            "improvement_tips": ["Learn Tableau"],
        },
        {
            "job": {
                "title": "Junior Data Analyst",
                "company": "Beta LLC",
                "location": "Abu Dhabi, UAE",
                "url": "",
                "source": "linkedin",
                "salary": "",
                "description": "desc",
                "requirements": [],
                "benefits": [],
            },
            "score": 45.0,
            "reasoning": "Good baseline fit but needs dashboard tooling experience.",
            "skill_match": {"Python": 0.7, "SQL": 0.7},
            "missing_skills": ["Power BI", "Tableau"],
            "strengths": ["Python", "SQL"],
            "improvement_tips": ["Build BI portfolio"],
        },
    ]


class TestCoachingStep:
    def test_coaching_redirects_on_invalid_index(self, client):
        """GET /wizard/coaching/99 with no results redirects to results."""
        response = client.get("/wizard/coaching/99")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/wizard/results")

    def test_coaching_redirects_on_missing_profile(self, client, monkeypatch):
        """Coaching page redirects to upload if profile session expired."""
        from web import routes

        monkeypatch.setattr(
            routes,
            "get_job_at_index",
            lambda job_index: {
                "job": {
                    "title": "Data Analyst",
                    "company": "Acme Corp",
                    "location": "Dubai, UAE",
                    "source": "mock",
                    "salary": None,
                }
            },
        )
        monkeypatch.setattr(routes, "load_profile_from_session", lambda flask_session: None)

        response = client.get("/wizard/coaching/1")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/wizard/upload")

    def test_coaching_renders_with_mock_data(self, client, monkeypatch, seeded_results):
        """Coaching page renders with mocked advisor outputs."""
        from web import routes

        monkeypatch.setattr(routes, "get_job_at_index", lambda job_index: seeded_results[job_index - 1])
        monkeypatch.setattr(routes, "load_profile_from_session", lambda flask_session: object())
        monkeypatch.setattr(
            routes,
            "run_coaching",
            lambda profile, job_dict, include_plan: {
                "resume_edits": [
                    {
                        "section": "Summary",
                        "current_text": "Old text",
                        "suggested_text": "New text",
                        "reason": "Improve impact",
                    }
                ],
                "requirements": {
                    "requirements": [
                        {
                            "item": "Python",
                            "priority": "must-have",
                            "candidate_has": True,
                            "candidate_note": "5 years exp",
                        }
                    ],
                    "coverage_score": 80.0,
                    "critical_gaps": [],
                },
                "coaching": {
                    "quick_tips": ["Tailor your CV", "Research the company"],
                    "action_plan": None,
                },
                "errors": [],
            },
        )

        response = client.get("/wizard/coaching/1")
        assert response.status_code == 200
        assert b"Resume Edits" in response.data
        assert b"Requirements Analysis" in response.data
        assert b"Application Coaching" in response.data

    def test_coaching_shows_errors_gracefully(self, client, monkeypatch, seeded_results):
        """If run_coaching returns errors, page still renders 200 with warning."""
        from web import routes

        monkeypatch.setattr(routes, "get_job_at_index", lambda job_index: seeded_results[job_index - 1])
        monkeypatch.setattr(routes, "load_profile_from_session", lambda flask_session: object())
        monkeypatch.setattr(
            routes,
            "run_coaching",
            lambda profile, job_dict, include_plan: {
                "resume_edits": [],
                "requirements": {},
                "coaching": {},
                "errors": ["resume_edits: timeout"],
            },
        )

        response = client.get("/wizard/coaching/1")
        assert response.status_code == 200
        assert b"Some coaching sections could not be generated" in response.data
        assert b"resume_edits: timeout" in response.data

    def test_coaching_with_include_plan(self, client, monkeypatch, seeded_results):
        """?include_plan=true passes include_plan=True to run_coaching."""
        from web import routes

        tracker = {"include_plan": None}

        monkeypatch.setattr(routes, "get_job_at_index", lambda job_index: seeded_results[job_index - 1])
        monkeypatch.setattr(routes, "load_profile_from_session", lambda flask_session: object())

        def _fake_run_coaching(profile, job_dict, include_plan):
            tracker["include_plan"] = include_plan
            return {
                "resume_edits": [],
                "requirements": {"requirements": [], "coverage_score": 0, "critical_gaps": []},
                "coaching": {"quick_tips": [], "action_plan": None},
                "errors": [],
            }

        monkeypatch.setattr(routes, "run_coaching", _fake_run_coaching)

        response = client.get("/wizard/coaching/1?include_plan=true")
        assert response.status_code == 200
        assert tracker["include_plan"] is True


class TestResultsStep:
    def test_results_redirects_when_no_data(self, client, monkeypatch):
        """GET /wizard/results with no web_results.json redirects to configure."""
        from web import routes

        monkeypatch.setattr(routes, "load_web_results", lambda: [])

        response = client.get("/wizard/results")

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/wizard/configure")

    def test_results_renders_job_cards(self, client, seeded_results, monkeypatch):
        """GET /wizard/results with data renders job cards."""
        from web import routes

        monkeypatch.setattr(routes, "load_web_results", lambda: seeded_results)

        response = client.get("/wizard/results")

        assert response.status_code == 200
        assert b"Data Analyst" in response.data
        assert b"85" in response.data
        assert b"/wizard/coaching/1" in response.data
        assert b"Get Coaching" in response.data

    def test_results_score_colors(self, client, seeded_results, monkeypatch):
        """Score >= 70 gets score-green class, < 50 gets score-red."""
        from web import routes

        monkeypatch.setattr(routes, "load_web_results", lambda: seeded_results)

        response = client.get("/wizard/results")

        assert response.status_code == 200
        assert b"score-badge score-green" in response.data
        assert b"score-badge score-red" in response.data

    def test_results_export_returns_json(self, client, seeded_results, monkeypatch):
        """GET /wizard/results-export returns JSON attachment."""
        from web import routes

        monkeypatch.setattr(routes, "load_web_results", lambda: seeded_results)

        response = client.get("/wizard/results-export")

        assert response.status_code == 200
        assert response.mimetype == "application/json"
        assert response.headers["Content-Disposition"] == "attachment; filename=job_results.json"
        data = response.get_json()
        assert isinstance(data, list)
        assert data[0]["job"]["title"] == "Data Analyst"
