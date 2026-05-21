"""Tests for state persistence module."""

from __future__ import annotations

import json
from pathlib import Path


class TestStatePersistence:
    """Test save/load of search results."""

    def test_save_and_load_results(self, tmp_path, monkeypatch, sample_job):
        import jobscout.state as state_mod
        monkeypatch.setattr(state_mod, "STATE_DIR", tmp_path)
        monkeypatch.setattr(state_mod, "LAST_RESULTS_FILE", tmp_path / "last_results.json")

        from jobscout.state import load_results, save_results
        save_results([sample_job], [0.85])
        jobs, scores = load_results()
        assert len(jobs) == 1
        assert jobs[0].title == sample_job.title
        assert abs(scores[0] - 0.85) < 0.001

    def test_load_results_empty_when_no_file(self, tmp_path, monkeypatch):
        import jobscout.state as state_mod
        monkeypatch.setattr(state_mod, "STATE_DIR", tmp_path)
        monkeypatch.setattr(state_mod, "LAST_RESULTS_FILE", tmp_path / "last_results.json")

        from jobscout.state import load_results
        jobs, scores = load_results()
        assert jobs == []
        assert scores == []

    def test_load_job_at_index(self, tmp_path, monkeypatch, sample_job):
        import jobscout.state as state_mod
        monkeypatch.setattr(state_mod, "STATE_DIR", tmp_path)
        monkeypatch.setattr(state_mod, "LAST_RESULTS_FILE", tmp_path / "last_results.json")

        from jobscout.state import load_job_at_index, save_results
        save_results([sample_job], [0.9])
        job = load_job_at_index(1)
        assert job is not None
        assert job.title == sample_job.title

    def test_load_job_at_index_out_of_range(self, tmp_path, monkeypatch, sample_job):
        import jobscout.state as state_mod
        monkeypatch.setattr(state_mod, "STATE_DIR", tmp_path)
        monkeypatch.setattr(state_mod, "LAST_RESULTS_FILE", tmp_path / "last_results.json")

        from jobscout.state import load_job_at_index, save_results
        save_results([sample_job], [0.9])
        job = load_job_at_index(99)
        assert job is None

    def test_load_job_at_index_no_results(self, tmp_path, monkeypatch):
        import jobscout.state as state_mod
        monkeypatch.setattr(state_mod, "STATE_DIR", tmp_path)
        monkeypatch.setattr(state_mod, "LAST_RESULTS_FILE", tmp_path / "last_results.json")

        from jobscout.state import load_job_at_index
        job = load_job_at_index(1)
        assert job is None
