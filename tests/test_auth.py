"""
test_auth.py
------------
Tests for API key authentication on the FastAPI endpoints.
Uses FastAPI's TestClient, so no server needs to be running.
"""

import pytest
from fastapi.testclient import TestClient
import api.database as db
from api.main import app, API_KEY

client = TestClient(app)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Use a throwaway database so tests never touch the real helpdesk.db."""
    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "test_helpdesk.db"))
    db.init_db()


def test_wrong_api_key_is_rejected():
    response = client.get("/tickets", headers={"x-api-key": "definitely-wrong"})
    assert response.status_code == 401


def test_missing_api_key_is_rejected():
    response = client.get("/tickets")
    assert response.status_code == 422


def test_correct_api_key_is_accepted():
    response = client.get("/tickets", headers={"x-api-key": API_KEY})
    assert response.status_code == 200
    assert response.json() == []


def test_missing_ticket_returns_404():
    response = client.get("/tickets/99", headers={"x-api-key": API_KEY})
    assert response.status_code == 404