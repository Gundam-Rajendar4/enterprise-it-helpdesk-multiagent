"""
database.py
-----------
SQLite helper for the IT Helpdesk ticketing system.
Creates helpdesk.db (a local file) and the tickets table on first run.
"""

import sqlite3
from datetime import datetime

DB_FILE = "helpdesk.db"


def get_connection():
    """Open a connection to the database file."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # lets us read rows like dictionaries
    return conn


def init_db():
    """Create the tickets table if it doesn't exist yet."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            category TEXT,
            suggestion TEXT,
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def create_ticket(description):
    """Save a new ticket as 'Open' and return its new id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO tickets (description, status, created_at) VALUES (?, ?, ?)",
        (description, "Open", datetime.now().isoformat(timespec="seconds"))
    )
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id


def update_ticket(ticket_id, category, suggestion, status):
    """Fill in the AI results on an existing ticket."""
    conn = get_connection()
    conn.execute(
        "UPDATE tickets SET category = ?, suggestion = ?, status = ? WHERE id = ?",
        (category, suggestion, status, ticket_id)
    )
    conn.commit()
    conn.close()