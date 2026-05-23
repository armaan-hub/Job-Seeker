"""Tests for Flask app shell."""

from __future__ import annotations

from flask import Flask

from web.app import create_app


def test_create_app() -> None:
    app = create_app()
    assert isinstance(app, Flask)


def test_index_redirects_to_upload() -> None:
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/wizard/upload")


def test_500_renders_error_template() -> None:
    app = create_app()
    app.config["TESTING"] = False

    @app.route("/boom")
    def boom():
        raise RuntimeError("forced test error")

    with app.test_client() as client:
        response = client.get("/boom")

    assert response.status_code == 500
    assert b"Something went wrong" in response.data


def test_provider_health_in_context(monkeypatch) -> None:
    from web import wizard

    monkeypatch.setattr(
        wizard,
        "get_provider_health",
        lambda: {
            "ok": False,
            "provider": "anthropic",
            "message": "test warning",
        },
    )
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/wizard/upload")

    assert response.status_code == 200
    assert b"test warning" in response.data
