# Job Advisor Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three AI-powered advisor features to the CLI: Resume Advisor, Requirements Analyzer, and Application Coach, accessible via a new `advise` command and inline summaries in `search`.

**Architecture:** New `advisor.py` module with three advisor classes (ResumeAdvisor, RequirementsAnalyzer, ApplicationCoach) and a `state.py` module for persisting last search results. The `search` command saves results to `~/.jobscout/last_results.json` and numbers them; `advise <N>` loads by index and runs all three advisors.

**Tech Stack:** Python 3.11+, click, rich, dataclasses, json, pathlib. No new dependencies. All three advisors take an AIProvider and return structured dataclasses parsed from AI JSON responses.

---

## Context

**Repo root:** `/Users/armaan/Job Finder/job-scout/`
**Run tests from repo root:** `cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/ -v`
**Lint:** `cd "/Users/armaan/Job Finder/job-scout" && ruff check src/`
**Existing passing tests:** 6 tests across `tests/test_profile.py` and `tests/test_matcher.py`
**DO NOT break existing tests.** Run full suite after every task.

**Key existing classes:**
- `src/jobscout/providers/base.py` — `AIProvider(ABC)` with `complete(prompt, system, **kwargs) -> AIResponse` and `AIResponse(content: str, model: str)`
- `src/jobscout/profile.py` — `UserProfile` with `to_prompt_text() -> str`
- `src/jobscout/scraper.py` — `JobListing(title, company, location, description, source, url, requirements)` with `to_prompt_text() -> str`
- `src/jobscout/matcher.py` — `MatchResult(job, score, reasoning, skill_match, missing_skills, strengths, improvement_tips)`
- `src/jobscout/main.py` — Click CLI with `search`, `analyze`, `providers` commands
- `tests/conftest.py` — `sample_profile` and `sample_job` fixtures

**Spec:** `docs/superpowers/specs/2026-05-21-job-advisor-features-design.md`

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/jobscout/advisor.py` | CREATE | Dataclasses + 3 advisor classes |
| `src/jobscout/state.py` | CREATE | Save/load last results to `~/.jobscout/last_results.json` |
| `src/jobscout/main.py` | MODIFY | Number results in search, save state, new `advise` command |
| `tests/test_advisor.py` | CREATE | TDD tests for all 3 advisors |
| `tests/test_state.py` | CREATE | TDD tests for state persistence |

---

## Task 1: Dataclasses and Test Infrastructure

**Files:**
- Create: `src/jobscout/advisor.py`
- Create: `tests/test_advisor.py`

- [ ] **Step 1: Write the failing import test**

Create `tests/test_advisor.py`:

```python
"""Tests for advisor module."""

from __future__ import annotations

from dataclasses import dataclass
from jobscout.providers.base import AIProvider, AIResponse, ProviderType


class MockProvider(AIProvider):
    """Mock AI provider for testing."""

    def __init__(self, response_content: str):
        super().__init__()
        self._response = response_content

    def complete(self, prompt: str, system: str | None = None, **kwargs) -> AIResponse:
        return AIResponse(content=self._response, model="mock")

    def provider_type(self) -> ProviderType:
        return ProviderType.OPENCODE


class TestDataclasses:
    """Test that all dataclasses are importable and constructible."""

    def test_resume_edit_importable(self):
        from jobscout.advisor import ResumeEdit
        edit = ResumeEdit(
            section="Experience",
            current_text="Managed data",
            suggested_text="Led ETL pipelines processing 6M+ records",
            reason="Quantifies impact",
        )
        assert edit.section == "Experience"

    def test_requirement_importable(self):
        from jobscout.advisor import Requirement
        req = Requirement(
            item="Power BI",
            priority="must-have",
            candidate_has=True,
            candidate_note="5 years Power BI",
        )
        assert req.priority == "must-have"

    def test_requirements_report_importable(self):
        from jobscout.advisor import Requirement, RequirementsReport
        report = RequirementsReport(
            requirements=[],
            coverage_score=75.0,
            critical_gaps=["Azure"],
        )
        assert report.coverage_score == 75.0

    def test_coach_advice_importable(self):
        from jobscout.advisor import CoachAdvice
        advice = CoachAdvice(
            quick_tips=["Apply via referral"],
            action_plan=None,
        )
        assert len(advice.quick_tips) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/test_advisor.py -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'jobscout.advisor'`

- [ ] **Step 3: Create `advisor.py` with dataclasses only**

Create `src/jobscout/advisor.py`:

```python
"""AI-powered job advisor module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResumeEdit:
    """A targeted CV edit suggestion for a specific job."""

    section: str
    current_text: str
    suggested_text: str
    reason: str


@dataclass
class Requirement:
    """A job requirement with candidate coverage info."""

    item: str
    priority: str  # "must-have" or "nice-to-have"
    candidate_has: bool
    candidate_note: str


@dataclass
class RequirementsReport:
    """Full requirements analysis for a job vs. a candidate."""

    requirements: list[Requirement]
    coverage_score: float
    critical_gaps: list[str]


@dataclass
class CoachAdvice:
    """Career coaching advice for landing a specific job."""

    quick_tips: list[str]
    action_plan: dict[str, list[str]] | None  # None if not requested
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/test_advisor.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Run full suite to confirm no regressions**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/ -v
```

Expected: `10 passed` (6 existing + 4 new)

- [ ] **Step 6: Commit**

```bash
cd "/Users/armaan/Job Finder/job-scout" && git add src/jobscout/advisor.py tests/test_advisor.py && git commit -m "feat: add advisor dataclasses and test infrastructure"
```

---

## Task 2: ResumeAdvisor

**Files:**
- Modify: `src/jobscout/advisor.py`
- Modify: `tests/test_advisor.py`

- [ ] **Step 1: Write failing tests for ResumeAdvisor**

Append to `tests/test_advisor.py`:

```python
class TestResumeAdvisor:
    """Tests for ResumeAdvisor."""

    def test_suggest_edits_returns_list(self, sample_profile, sample_job):
        """ResumeAdvisor returns a list of ResumeEdit objects."""
        from jobscout.advisor import ResumeAdvisor, ResumeEdit

        json_response = '''[
            {
                "section": "Experience",
                "current_text": "Managed data pipelines",
                "suggested_text": "Designed ETL pipelines processing 6M+ records daily",
                "reason": "Quantifies impact and matches job requirements"
            }
        ]'''
        provider = MockProvider(json_response)
        advisor = ResumeAdvisor(provider)

        edits = advisor.suggest_edits(sample_profile, sample_job)

        assert isinstance(edits, list)
        assert len(edits) == 1
        assert isinstance(edits[0], ResumeEdit)
        assert edits[0].section == "Experience"
        assert "ETL" in edits[0].suggested_text

    def test_suggest_edits_handles_json_with_markdown_fence(self, sample_profile, sample_job):
        """ResumeAdvisor parses JSON wrapped in markdown code fences."""
        from jobscout.advisor import ResumeAdvisor

        json_response = '''```json
[{"section": "Skills", "current_text": "Python", "suggested_text": "Python, SQL, Power BI", "reason": "ATS keywords"}]
```'''
        provider = MockProvider(json_response)
        advisor = ResumeAdvisor(provider)

        edits = advisor.suggest_edits(sample_profile, sample_job)

        assert len(edits) == 1
        assert edits[0].section == "Skills"

    def test_suggest_edits_returns_empty_list_on_ai_failure(self, sample_profile, sample_job):
        """ResumeAdvisor returns empty list when AI response is unparseable."""
        from jobscout.advisor import ResumeAdvisor

        provider = MockProvider("Sorry, I cannot help with that.")
        advisor = ResumeAdvisor(provider)

        edits = advisor.suggest_edits(sample_profile, sample_job)

        assert edits == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/test_advisor.py::TestResumeAdvisor -v
```

Expected: `FAILED` — `AttributeError: type object 'ResumeAdvisor' ... not found` or `ImportError`

- [ ] **Step 3: Implement ResumeAdvisor in `advisor.py`**

Add after the dataclasses in `src/jobscout/advisor.py`:

```python
import json

from jobscout.profile import UserProfile
from jobscout.providers.base import AIProvider
from jobscout.scraper import JobListing


_RESUME_PROMPT = """You are an expert CV coach. Given the candidate profile and job listing below, \
suggest exactly 3-5 targeted edits the candidate should make to their existing CV to maximize \
their match for this specific job. Focus on rewriting existing content to better reflect the \
job's requirements. Be specific about which section to change and why.

## Candidate Profile:
{profile}

## Job Listing:
{job}

Return a JSON array only, no other text:
[{{"section": "<section name>", "current_text": "<what's there now>", \
"suggested_text": "<improved version>", "reason": "<why this helps>"}}]
"""


class ResumeAdvisor:
    """Suggests targeted CV edits tailored to a specific job."""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    def suggest_edits(self, profile: UserProfile, job: JobListing) -> list[ResumeEdit]:
        """Return 3-5 targeted CV edit suggestions for this job."""
        prompt = _RESUME_PROMPT.format(
            profile=profile.to_prompt_text(),
            job=job.to_prompt_text(),
        )
        try:
            response = self.provider.complete(
                prompt=prompt,
                system="You are an expert CV coach. Return valid JSON only.",
                max_tokens=1024,
            )
            return self._parse(response.content)
        except Exception:
            return []

    def _parse(self, content: str) -> list[ResumeEdit]:
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "[" in content:
            start = content.find("[")
            end = content.rfind("]") + 1
            content = content[start:end]
        else:
            return []
        try:
            data = json.loads(content)
            return [
                ResumeEdit(
                    section=item.get("section", ""),
                    current_text=item.get("current_text", ""),
                    suggested_text=item.get("suggested_text", ""),
                    reason=item.get("reason", ""),
                )
                for item in data
            ]
        except (json.JSONDecodeError, AttributeError):
            return []
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/test_advisor.py::TestResumeAdvisor -v
```

Expected: `3 passed`

- [ ] **Step 5: Run full suite**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/ -v
```

Expected: `13 passed`

- [ ] **Step 6: Lint check**

```bash
cd "/Users/armaan/Job Finder/job-scout" && ruff check src/jobscout/advisor.py
```

Expected: no output (clean)

- [ ] **Step 7: Commit**

```bash
cd "/Users/armaan/Job Finder/job-scout" && git add src/jobscout/advisor.py tests/test_advisor.py && git commit -m "feat: implement ResumeAdvisor with TDD"
```

---

## Task 3: RequirementsAnalyzer

**Files:**
- Modify: `src/jobscout/advisor.py`
- Modify: `tests/test_advisor.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_advisor.py`:

```python
class TestRequirementsAnalyzer:
    """Tests for RequirementsAnalyzer."""

    def test_analyze_returns_report(self, sample_profile, sample_job):
        """RequirementsAnalyzer returns a RequirementsReport."""
        from jobscout.advisor import RequirementsAnalyzer, RequirementsReport

        json_response = '''{
            "requirements": [
                {"item": "Power BI", "priority": "must-have", "candidate_has": true, "candidate_note": "3 years"},
                {"item": "Azure", "priority": "must-have", "candidate_has": false, "candidate_note": "Not in CV"}
            ],
            "coverage_score": 65.0,
            "critical_gaps": ["Azure"]
        }'''
        provider = MockProvider(json_response)
        analyzer = RequirementsAnalyzer(provider)

        report = analyzer.analyze(sample_profile, sample_job)

        assert isinstance(report, RequirementsReport)
        assert len(report.requirements) == 2
        assert report.coverage_score == 65.0
        assert "Azure" in report.critical_gaps

    def test_analyze_requirement_fields(self, sample_profile, sample_job):
        """Each requirement has correct fields."""
        from jobscout.advisor import Requirement, RequirementsAnalyzer

        json_response = '''{
            "requirements": [
                {"item": "SQL", "priority": "must-have", "candidate_has": true, "candidate_note": "5 years SQL"}
            ],
            "coverage_score": 100.0,
            "critical_gaps": []
        }'''
        provider = MockProvider(json_response)
        analyzer = RequirementsAnalyzer(provider)

        report = analyzer.analyze(sample_profile, sample_job)
        req = report.requirements[0]

        assert isinstance(req, Requirement)
        assert req.item == "SQL"
        assert req.priority == "must-have"
        assert req.candidate_has is True
        assert req.candidate_note == "5 years SQL"

    def test_analyze_returns_empty_report_on_failure(self, sample_profile, sample_job):
        """Returns empty report when AI response is unparseable."""
        from jobscout.advisor import RequirementsAnalyzer

        provider = MockProvider("error")
        analyzer = RequirementsAnalyzer(provider)

        report = analyzer.analyze(sample_profile, sample_job)

        assert report.requirements == []
        assert report.coverage_score == 0.0
        assert report.critical_gaps == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/test_advisor.py::TestRequirementsAnalyzer -v
```

Expected: `FAILED` — `ImportError: cannot import name 'RequirementsAnalyzer'`

- [ ] **Step 3: Implement RequirementsAnalyzer in `advisor.py`**

Add after `ResumeAdvisor` class in `src/jobscout/advisor.py`:

```python
_REQUIREMENTS_PROMPT = """You are a hiring expert. Extract ALL requirements from the job listing \
below and assess whether the candidate meets each one. Label each as "must-have" or "nice-to-have". \
For each, state whether the candidate has it (true/false) and include a short note with evidence \
from the candidate's profile.

## Candidate Profile:
{profile}

## Job Listing:
{job}

Return JSON only, no other text:
{{"requirements": [{{"item": "<requirement>", "priority": "must-have|nice-to-have", \
"candidate_has": true|false, "candidate_note": "<evidence or Not in CV>"}}], \
"coverage_score": <0-100>, "critical_gaps": ["<must-have items candidate lacks>"]}}
"""


class RequirementsAnalyzer:
    """Compares job requirements against candidate profile."""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    def analyze(self, profile: UserProfile, job: JobListing) -> RequirementsReport:
        """Return side-by-side requirements analysis with coverage score."""
        prompt = _REQUIREMENTS_PROMPT.format(
            profile=profile.to_prompt_text(),
            job=job.to_prompt_text(),
        )
        try:
            response = self.provider.complete(
                prompt=prompt,
                system="You are a hiring expert. Return valid JSON only.",
                max_tokens=1024,
            )
            return self._parse(response.content)
        except Exception:
            return RequirementsReport(requirements=[], coverage_score=0.0, critical_gaps=[])

    def _parse(self, content: str) -> RequirementsReport:
        if "{" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            content = content[start:end]
        else:
            return RequirementsReport(requirements=[], coverage_score=0.0, critical_gaps=[])
        try:
            data = json.loads(content)
            requirements = [
                Requirement(
                    item=r.get("item", ""),
                    priority=r.get("priority", "nice-to-have"),
                    candidate_has=bool(r.get("candidate_has", False)),
                    candidate_note=r.get("candidate_note", ""),
                )
                for r in data.get("requirements", [])
            ]
            return RequirementsReport(
                requirements=requirements,
                coverage_score=float(data.get("coverage_score", 0.0)),
                critical_gaps=data.get("critical_gaps", []),
            )
        except (json.JSONDecodeError, AttributeError, TypeError):
            return RequirementsReport(requirements=[], coverage_score=0.0, critical_gaps=[])
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/test_advisor.py::TestRequirementsAnalyzer -v
```

Expected: `3 passed`

- [ ] **Step 5: Run full suite**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/ -v
```

Expected: `16 passed`

- [ ] **Step 6: Commit**

```bash
cd "/Users/armaan/Job Finder/job-scout" && git add src/jobscout/advisor.py tests/test_advisor.py && git commit -m "feat: implement RequirementsAnalyzer with TDD"
```

---

## Task 4: ApplicationCoach

**Files:**
- Modify: `src/jobscout/advisor.py`
- Modify: `tests/test_advisor.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_advisor.py`:

```python
class TestApplicationCoach:
    """Tests for ApplicationCoach."""

    def test_advise_returns_quick_tips(self, sample_profile, sample_job):
        """ApplicationCoach returns quick tips."""
        from jobscout.advisor import ApplicationCoach, CoachAdvice

        json_response = '''{
            "quick_tips": [
                "Highlight your AML experience in the cover letter",
                "Add quantified impact to your resume",
                "Apply via LinkedIn referral if possible"
            ],
            "action_plan": null
        }'''
        provider = MockProvider(json_response)
        coach = ApplicationCoach(provider)

        advice = coach.advise(sample_profile, sample_job, include_plan=False)

        assert isinstance(advice, CoachAdvice)
        assert len(advice.quick_tips) == 3
        assert advice.action_plan is None

    def test_advise_with_plan_returns_action_plan(self, sample_profile, sample_job):
        """ApplicationCoach returns action plan when include_plan=True."""
        from jobscout.advisor import ApplicationCoach

        json_response = '''{
            "quick_tips": ["Apply early"],
            "action_plan": {
                "before_applying": ["Update CV with ETL keywords", "Check LinkedIn connections"],
                "cover_letter": ["Open with AML background"],
                "interview_prep": ["Prepare 2 STAR stories"]
            }
        }'''
        provider = MockProvider(json_response)
        coach = ApplicationCoach(provider)

        advice = coach.advise(sample_profile, sample_job, include_plan=True)

        assert advice.action_plan is not None
        assert "before_applying" in advice.action_plan
        assert "cover_letter" in advice.action_plan
        assert "interview_prep" in advice.action_plan

    def test_advise_returns_empty_on_failure(self, sample_profile, sample_job):
        """ApplicationCoach returns empty advice when AI fails."""
        from jobscout.advisor import ApplicationCoach

        provider = MockProvider("unparseable garbage")
        coach = ApplicationCoach(provider)

        advice = coach.advise(sample_profile, sample_job)

        assert advice.quick_tips == []
        assert advice.action_plan is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/test_advisor.py::TestApplicationCoach -v
```

Expected: `FAILED` — `ImportError: cannot import name 'ApplicationCoach'`

- [ ] **Step 3: Implement ApplicationCoach in `advisor.py`**

Add after `RequirementsAnalyzer` class in `src/jobscout/advisor.py`:

```python
_COACH_PROMPT = """You are an expert career coach specializing in job applications. Given the \
candidate profile and job listing below, provide:
1. 3-5 high-impact quick tips the candidate should act on to maximize their chances
2. A detailed action plan {plan_instruction}

## Candidate Profile:
{profile}

## Job Listing:
{job}

Return JSON only, no other text:
{{"quick_tips": ["<tip1>", "<tip2>", ...], \
"action_plan": {{"before_applying": ["<step1>", ...], \
"cover_letter": ["<guidance>"], \
"interview_prep": ["<step1>", ...]}} }}

If no action plan was requested, set "action_plan" to null.
"""


class ApplicationCoach:
    """Provides quick tips and full action plans for landing a job."""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    def advise(
        self,
        profile: UserProfile,
        job: JobListing,
        include_plan: bool = False,
    ) -> CoachAdvice:
        """Return quick tips and optionally a full action plan."""
        plan_instruction = (
            "covering: before-applying steps, cover letter angle, and interview preparation"
            if include_plan
            else "(set action_plan to null — not requested)"
        )
        prompt = _COACH_PROMPT.format(
            profile=profile.to_prompt_text(),
            job=job.to_prompt_text(),
            plan_instruction=plan_instruction,
        )
        try:
            response = self.provider.complete(
                prompt=prompt,
                system="You are a career coach. Return valid JSON only.",
                max_tokens=2048 if include_plan else 1024,
            )
            return self._parse(response.content, include_plan)
        except Exception:
            return CoachAdvice(quick_tips=[], action_plan=None)

    def _parse(self, content: str, include_plan: bool) -> CoachAdvice:
        if "{" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            content = content[start:end]
        else:
            return CoachAdvice(quick_tips=[], action_plan=None)
        try:
            data = json.loads(content)
            action_plan = None
            if include_plan and isinstance(data.get("action_plan"), dict):
                action_plan = data["action_plan"]
            return CoachAdvice(
                quick_tips=data.get("quick_tips", []),
                action_plan=action_plan,
            )
        except (json.JSONDecodeError, AttributeError):
            return CoachAdvice(quick_tips=[], action_plan=None)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/test_advisor.py::TestApplicationCoach -v
```

Expected: `3 passed`

- [ ] **Step 5: Run full suite**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/ -v
```

Expected: `19 passed`

- [ ] **Step 6: Lint check**

```bash
cd "/Users/armaan/Job Finder/job-scout" && ruff check src/jobscout/advisor.py
```

Expected: no output (clean)

- [ ] **Step 7: Commit**

```bash
cd "/Users/armaan/Job Finder/job-scout" && git add src/jobscout/advisor.py tests/test_advisor.py && git commit -m "feat: implement ApplicationCoach with TDD"
```

---

## Task 5: State Persistence

**Files:**
- Create: `src/jobscout/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_state.py`:

```python
"""Tests for state persistence module."""

from __future__ import annotations

import json
import pytest
from pathlib import Path


class TestStatePersistence:
    """Tests for save_results and load_results."""

    def test_save_and_load_round_trip(self, tmp_path, monkeypatch, sample_job):
        """Save results then load them back successfully."""
        from jobscout.state import save_results, load_results
        from jobscout import state as state_module

        # Redirect state file to tmp_path
        monkeypatch.setattr(state_module, "STATE_DIR", tmp_path)
        monkeypatch.setattr(state_module, "LAST_RESULTS_FILE", tmp_path / "last_results.json")

        save_results([sample_job], [87.5])

        jobs = load_results()

        assert len(jobs) == 1
        assert jobs[0]["title"] == sample_job.title
        assert jobs[0]["company"] == sample_job.company
        assert jobs[0]["score"] == 87.5
        assert jobs[0]["index"] == 1

    def test_load_results_raises_when_no_file(self, tmp_path, monkeypatch):
        """load_results raises FileNotFoundError when no results file exists."""
        from jobscout.state import load_results
        from jobscout import state as state_module

        monkeypatch.setattr(state_module, "LAST_RESULTS_FILE", tmp_path / "nonexistent.json")

        with pytest.raises(FileNotFoundError, match="Run `job-scout search` first"):
            load_results()

    def test_load_job_at_index_returns_job_listing(self, tmp_path, monkeypatch, sample_job):
        """load_job_at_index returns a JobListing for a valid index."""
        from jobscout.state import save_results, load_job_at_index
        from jobscout.scraper import JobListing
        from jobscout import state as state_module

        monkeypatch.setattr(state_module, "STATE_DIR", tmp_path)
        monkeypatch.setattr(state_module, "LAST_RESULTS_FILE", tmp_path / "last_results.json")

        save_results([sample_job], [80.0])

        job = load_job_at_index(1)

        assert isinstance(job, JobListing)
        assert job.title == sample_job.title

    def test_load_job_at_index_raises_for_bad_index(self, tmp_path, monkeypatch, sample_job):
        """load_job_at_index raises IndexError for invalid index."""
        from jobscout.state import save_results, load_job_at_index
        from jobscout import state as state_module

        monkeypatch.setattr(state_module, "STATE_DIR", tmp_path)
        monkeypatch.setattr(state_module, "LAST_RESULTS_FILE", tmp_path / "last_results.json")

        save_results([sample_job], [80.0])

        with pytest.raises(IndexError, match="out of range"):
            load_job_at_index(99)

    def test_save_multiple_jobs_indexed_correctly(self, tmp_path, monkeypatch, sample_job):
        """Multiple jobs are saved with correct 1-based indices."""
        from jobscout.state import save_results, load_results
        from jobscout.scraper import JobListing
        from jobscout import state as state_module

        monkeypatch.setattr(state_module, "STATE_DIR", tmp_path)
        monkeypatch.setattr(state_module, "LAST_RESULTS_FILE", tmp_path / "last_results.json")

        job2 = JobListing(
            title="BI Developer",
            company="ADIB",
            location="Abu Dhabi",
            description="Power BI role",
            source="test",
        )
        save_results([sample_job, job2], [90.0, 75.0])

        jobs = load_results()

        assert jobs[0]["index"] == 1
        assert jobs[1]["index"] == 2
        assert jobs[1]["title"] == "BI Developer"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/test_state.py -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'jobscout.state'`

- [ ] **Step 3: Create `src/jobscout/state.py`**

```python
"""Persistence layer for last search results."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jobscout.scraper import JobListing

STATE_DIR = Path.home() / ".jobscout"
LAST_RESULTS_FILE = STATE_DIR / "last_results.json"


def save_results(jobs: list[JobListing], scores: list[float]) -> None:
    """Save search results to disk for use with the advise command."""
    STATE_DIR.mkdir(exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "jobs": [
            {
                "index": i + 1,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "description": j.description,
                "source": j.source,
                "url": j.url or "",
                "requirements": j.requirements,
                "score": scores[i] if i < len(scores) else 0.0,
            }
            for i, j in enumerate(jobs)
        ],
    }
    LAST_RESULTS_FILE.write_text(json.dumps(data, indent=2))


def load_results() -> list[dict[str, Any]]:
    """Load last search results. Raises FileNotFoundError if none saved."""
    if not LAST_RESULTS_FILE.exists():
        raise FileNotFoundError(
            "No saved results found. Run `job-scout search` first."
        )
    data = json.loads(LAST_RESULTS_FILE.read_text())
    return data["jobs"]


def load_job_at_index(index: int) -> JobListing:
    """Load a job by 1-based index from last search results."""
    jobs = load_results()
    matching = [j for j in jobs if j["index"] == index]
    if not matching:
        total = len(jobs)
        raise IndexError(
            f"Index {index} out of range. Last search had {total} result(s) (1–{total})."
        )
    d = matching[0]
    return JobListing(
        title=d["title"],
        company=d["company"],
        location=d["location"],
        description=d["description"],
        source=d["source"],
        url=d.get("url") or None,
        requirements=d.get("requirements", []),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/test_state.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Run full suite**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/ -v
```

Expected: `24 passed`

- [ ] **Step 6: Lint**

```bash
cd "/Users/armaan/Job Finder/job-scout" && ruff check src/jobscout/state.py
```

Expected: no output (clean)

- [ ] **Step 7: Commit**

```bash
cd "/Users/armaan/Job Finder/job-scout" && git add src/jobscout/state.py tests/test_state.py && git commit -m "feat: add state persistence for search results"
```

---

## Task 6: Update `search` Command

**Files:**
- Modify: `src/jobscout/main.py`

Changes: (1) import `save_results` from state module, (2) number results `[N]` in panel title, (3) save all results after display, (4) show inline quick tip from existing `improvement_tips` when `--detailed` flag is used, (5) print "Results saved" footer.

- [ ] **Step 1: Modify `format_match_result` to accept an index**

In `src/jobscout/main.py`, replace the `format_match_result` function:

```python
def format_match_result(result: MatchResult, index: int, detailed: bool = False) -> None:
    """Format and print a single match result."""
    score = result.score
    score_color = (
        "green" if score >= 70 else "yellow" if score >= 50 else "red"
    )

    panel_content = [
        f"[bold]Score:[/bold] [{score_color}]{score:.0f}%[/]"
    ]

    if detailed:
        panel_content.extend([
            f"[bold]Reasoning:[/bold] {result.reasoning}",
            "",
            f"[bold]Strengths:[/bold] {', '.join(result.strengths) if result.strengths else 'N/A'}",
        ])
        if result.missing_skills:
            panel_content.append(f"[bold]Missing Skills:[/bold] {', '.join(result.missing_skills)}")
        if result.improvement_tips:
            panel_content.append(
                f"[bold][yellow]💡 Tip:[/yellow][/bold] {result.improvement_tips[0]}"
            )

    console.print(Panel(
        "\n".join(panel_content),
        title=f"[bold][{index}] {result.job.title}[/bold] at {result.job.company}",
        subtitle=f"{result.job.location} | Source: {result.job.source}",
        border_style="blue",
    ))
```

- [ ] **Step 2: Add `save_results` import and update the `search` function to save and show footer**

In `src/jobscout/main.py`, add to the imports block at the top:

```python
from jobscout.state import save_results
```

In the `search` function, replace the result-display loop:

```python
        # Display top matches
        top_results = results[:max_results]
        console.print(f"\n[bold cyan]Top {len(top_results)} Matches:[/bold cyan]\n")

        for i, result in enumerate(top_results, start=1):
            format_match_result(result, index=i, detailed=detailed)

        # Save results for `advise` command
        save_results(
            [r.job for r in top_results],
            [r.score for r in top_results],
        )
        console.print(
            "\n[dim]✅ Results saved. Run [bold]job-scout advise <number>[/bold] "
            "for full advice on any job.[/dim]"
        )
```

- [ ] **Step 3: Run full test suite to verify no regressions**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/ -v
```

Expected: `24 passed`

- [ ] **Step 4: Lint check**

```bash
cd "/Users/armaan/Job Finder/job-scout" && ruff check src/jobscout/main.py
```

Expected: no output (clean)

- [ ] **Step 5: Commit**

```bash
cd "/Users/armaan/Job Finder/job-scout" && git add src/jobscout/main.py && git commit -m "feat: number search results and save state for advise command"
```

---

## Task 7: New `advise` Command

**Files:**
- Modify: `src/jobscout/main.py`

- [ ] **Step 1: Add display helper functions to `main.py`**

Add these three functions after `display_skill_analysis` in `src/jobscout/main.py`:

```python
def display_requirements_report(report) -> None:
    """Display requirements analysis table."""
    from jobscout.advisor import RequirementsReport

    console.print(
        f"\n[bold cyan]📋 JOB REQUIREMENTS ANALYSIS[/bold cyan]  "
        f"(Coverage: [bold]{report.coverage_score:.0f}%[/bold])\n"
    )

    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("Requirement", style="white", min_width=30)
    table.add_column("Priority", min_width=12)
    table.add_column("You Have?", min_width=20)

    for req in report.requirements:
        priority_style = "red" if req.priority == "must-have" else "yellow"
        has_icon = "✅" if req.candidate_has else "❌"
        table.add_row(
            req.item,
            f"[{priority_style}]{req.priority}[/]",
            f"{has_icon} {req.candidate_note}",
        )

    console.print(table)

    if report.critical_gaps:
        console.print(
            f"\n[bold red]🔴 Critical gaps:[/bold red] {', '.join(report.critical_gaps)}\n"
        )


def display_resume_edits(edits) -> None:
    """Display resume edit suggestions."""
    if not edits:
        console.print("\n[yellow]✍️  No resume edit suggestions generated.[/yellow]\n")
        return

    console.print(f"\n[bold cyan]✍️  RESUME EDITS[/bold cyan] ({len(edits)} targeted changes)\n")

    for i, edit in enumerate(edits, start=1):
        console.print(f"  [bold]{i}. {edit.section}[/bold]")
        console.print(f"     [dim]CURRENT:[/dim] {edit.current_text}")
        console.print(f"     [green]SUGGEST:[/green] {edit.suggested_text}")
        console.print(f"     [dim]WHY:[/dim] {edit.reason}")
        console.print()


def display_coach_advice(advice, include_plan: bool = False) -> None:
    """Display quick tips and optionally the full action plan."""
    if not advice.quick_tips:
        console.print("\n[yellow]🎯 No tips generated.[/yellow]\n")
        return

    console.print(
        f"\n[bold cyan]🎯 QUICK TIPS[/bold cyan] ({len(advice.quick_tips)} high-impact actions)\n"
    )
    for i, tip in enumerate(advice.quick_tips, start=1):
        console.print(f"  {i}. {tip}")

    if include_plan and advice.action_plan:
        console.print("\n[bold cyan]📅 FULL ACTION PLAN[/bold cyan]\n")

        before = advice.action_plan.get("before_applying", [])
        if before:
            console.print("  [bold]BEFORE APPLYING[/bold]")
            for step in before:
                console.print(f"  ☐ {step}")
            console.print()

        cover = advice.action_plan.get("cover_letter", [])
        if cover:
            console.print("  [bold]COVER LETTER ANGLE[/bold]")
            for line in cover:
                console.print(f"  {line}")
            console.print()

        interview = advice.action_plan.get("interview_prep", [])
        if interview:
            console.print("  [bold]INTERVIEW PREPARATION[/bold]")
            for step in interview:
                console.print(f"  ☐ {step}")
```

- [ ] **Step 2: Add the `advise` command to `main.py`**

Add this command after the `analyze` command (before the `providers` command) in `src/jobscout/main.py`:

```python
@main.command()
@click.argument("index", type=int, required=False)
@click.option("--plan", is_flag=True, help="Include full step-by-step action plan")
@click.option(
    "--desc-file",
    type=click.Path(exists=True, path_type=Path),
    help="Job description text file (alternative to index)",
)
def advise(index: int | None, plan: bool, desc_file: Path | None):
    """Get full advisor report for a specific job.

    Use INDEX to reference a job from the last `search` results (e.g. `advise 2`),
    or provide a job description file with --desc-file.
    """
    from jobscout.advisor import ApplicationCoach, RequirementsAnalyzer, ResumeAdvisor
    from jobscout.scraper import JobListing
    from jobscout.state import load_job_at_index

    config = get_config()

    # Resolve job
    if desc_file:
        job = JobListing(
            title="Job from file",
            company="Unknown",
            location="Unknown",
            description=desc_file.read_text(),
            source="file",
        )
    elif index is not None:
        try:
            job = load_job_at_index(index)
        except FileNotFoundError as e:
            console.print(f"[red]{e}[/red]")
            sys.exit(1)
        except IndexError as e:
            console.print(f"[red]{e}[/red]")
            sys.exit(1)
    else:
        console.print("[red]Provide a job index (e.g. `advise 2`) or --desc-file.[/red]")
        sys.exit(1)

    # Load profile
    default_profile = Path("My Instroduction/aniket_profile.json")
    if default_profile.exists():
        user_profile = ProfileParser.load_profile(default_profile)
    else:
        from jobscout.profile import UserProfile
        user_profile = UserProfile()

    console.print(f"\n[bold]{'━' * 60}[/bold]")
    console.print(f"[bold]📌 {job.title} at {job.company} | {job.location}[/bold]")
    console.print(f"[bold]{'━' * 60}[/bold]")

    try:
        provider = get_provider(config)

        # 1. Requirements Analysis
        with console.status("[bold green]Analyzing job requirements..."):
            analyzer = RequirementsAnalyzer(provider)
            report = analyzer.analyze(user_profile, job)
        display_requirements_report(report)

        # 2. Resume Edits
        with console.status("[bold green]Generating resume edit suggestions..."):
            resume_advisor = ResumeAdvisor(provider)
            edits = resume_advisor.suggest_edits(user_profile, job)
        display_resume_edits(edits)

        # 3. Application Coaching
        with console.status("[bold green]Generating application advice..."):
            coach = ApplicationCoach(provider)
            advice = coach.advise(user_profile, job, include_plan=plan)
        display_coach_advice(advice, include_plan=plan)

        if not plan:
            console.print("\n[dim]Run with --plan for a full step-by-step action plan.[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
```

- [ ] **Step 3: Run full test suite to verify no regressions**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/ -v
```

Expected: `24 passed`

- [ ] **Step 4: Smoke test CLI help to confirm new command registered**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m jobscout.main --help 2>&1 | grep advise
```

Expected: output contains `advise`

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m jobscout.main advise --help
```

Expected: Shows `Usage: main.py advise [OPTIONS] [INDEX]` with `--plan` and `--desc-file` options

- [ ] **Step 5: End-to-end smoke test with mock source**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m jobscout.main search --sources mock --max-results 3 --detailed 2>&1 | head -40
```

Expected: Shows numbered results `[1]`, `[2]`, `[3]` with score and tips, then "Results saved" footer

- [ ] **Step 6: Lint check**

```bash
cd "/Users/armaan/Job Finder/job-scout" && ruff check src/jobscout/main.py
```

Expected: no output (clean)

- [ ] **Step 7: Commit**

```bash
cd "/Users/armaan/Job Finder/job-scout" && git add src/jobscout/main.py && git commit -m "feat: add advise command with requirements, resume, and coaching output"
```

---

## Task 8: Final Verification

- [ ] **Step 1: Run complete test suite**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m pytest tests/ -v
```

Expected: `24 passed`, `0 failed`

- [ ] **Step 2: Run linter on all source**

```bash
cd "/Users/armaan/Job Finder/job-scout" && ruff check src/
```

Expected: no output (clean)

- [ ] **Step 3: Verify `advise --help` shows correctly**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m jobscout.main advise --help
```

Expected: Shows index argument, --plan flag, --desc-file option

- [ ] **Step 4: Verify `advise` gracefully handles missing state file**

```bash
cd "/Users/armaan/Job Finder/job-scout" && python3 -m jobscout.main advise 99 2>&1
```

Expected: Either "No saved results found. Run `job-scout search` first." OR index-out-of-range error (both acceptable depending on state)

- [ ] **Step 5: Push to GitHub**

```bash
cd "/Users/armaan/Job Finder/job-scout" && git push origin main
```

Expected: `main -> main` push success

- [ ] **Step 6: Update project journal**

Append to `/Users/armaan/Job Finder/project.md` (after last session entry):

```markdown
### Session 3 — 2026-05-21 (Job Advisor Features)

**Features implemented:**
- `ResumeAdvisor` — 3-5 targeted CV edit suggestions per job
- `RequirementsAnalyzer` — side-by-side requirements vs. profile table with coverage score
- `ApplicationCoach` — 3-5 quick tips + optional full action plan (before applying, cover letter, interview prep)
- `search` command updated: results now numbered [1][2]..., saved to `~/.jobscout/last_results.json`
- New `advise <N>` command: runs all 3 advisors on a selected job
- New `advise --desc-file f.txt` fallback: advise on a pasted job description

**Tests added:** 24 total (was 6, added 18 new)
**New files:** `src/jobscout/advisor.py`, `src/jobscout/state.py`, `tests/test_advisor.py`, `tests/test_state.py`
```

- [ ] **Step 7: Commit journal update**

```bash
cd "/Users/armaan/Job Finder" && git add "Job Finder/project.md" && git commit -m "docs: update project journal with session 3 advisor features" 2>/dev/null || \
cd "/Users/armaan/Job Finder" && git add project.md && git commit -m "docs: update project journal with session 3 advisor features"
```
