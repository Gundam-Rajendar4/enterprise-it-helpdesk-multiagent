"""
test_agents.py
---------------
Automated tests for our individual agents (Triage, Knowledge, Resolver).

Run all tests with: pytest tests/

Each test function name MUST start with "test_" - that's how pytest
finds and runs them automatically.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.triage_agent import triage_ticket
from agents.knowledge_agent import load_knowledge_base, retrieve_relevant_knowledge
from agents.resolver_agent import resolve_ticket


def test_triage_password_reset():
    """A password-related ticket should be classified as Password Reset."""
    result = triage_ticket("I forgot my password and can't log in.")
    assert result == "Password Reset"


def test_triage_hardware_issue():
    """A monitor-related ticket should be classified as Hardware Issue."""
    result = triage_ticket("My monitor won't turn on.")
    assert result == "Hardware Issue"


def test_knowledge_retrieval_returns_relevant_content():
    """Retrieving knowledge for a password ticket should mention 'password'
    and be correctly flagged as relevant."""
    load_knowledge_base()
    result = retrieve_relevant_knowledge("I forgot my password")
    assert "password" in result["content"].lower()
    assert result["is_relevant"] == True


def test_resolver_returns_non_empty_suggestion():
    """The resolver should always return SOME suggestion text, not blank."""
    knowledge = "Password Reset Knowledge Base: go to portal.company.com/reset"
    result = resolve_ticket("I forgot my password", "Password Reset", knowledge)
    assert result.strip() != ""