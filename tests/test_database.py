"""
test_database.py
----------------
Tests for the SQLite ticket storage in api/database.py.
Each test uses a fresh temporary database, so your real helpdesk.db is never touched.
"""

import pytest
import api.database as db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point the database at a throwaway file for every test."""
    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "test_helpdesk.db"))
    db.init_db()


def test_new_ticket_starts_open():
    ticket_id = db.create_ticket("My laptop won't turn on")
    ticket = db.get_ticket(ticket_id)
    assert ticket["status"] == "Open"
    assert ticket["description"] == "My laptop won't turn on"
    assert ticket["category"] is None


def test_update_ticket_fills_results():
    ticket_id = db.create_ticket("I forgot my password")
    db.update_ticket(ticket_id, "Password Reset", "Use the self-service portal.", "Resolved")
    ticket = db.get_ticket(ticket_id)
    assert ticket["category"] == "Password Reset"
    assert ticket["suggestion"] == "Use the self-service portal."
    assert ticket["status"] == "Resolved"


def test_get_missing_ticket_returns_none():
    assert db.get_ticket(99) is None


def test_get_all_tickets_newest_first():
    first_id = db.create_ticket("First ticket")
    second_id = db.create_ticket("Second ticket")
    tickets = db.get_all_tickets()
    assert [t["id"] for t in tickets] == [second_id, first_id]