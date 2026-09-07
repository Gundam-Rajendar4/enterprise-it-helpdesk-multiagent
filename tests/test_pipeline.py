"""
test_pipeline.py
------------------
Tests the FULL LangGraph pipeline end-to-end (Triage -> Knowledge -> Resolver),
not just individual agents in isolation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graphs.helpdesk_graph import helpdesk_app


def test_full_pipeline_returns_all_expected_fields():
    """
    Running a ticket through the full pipeline should return a result
    containing all 4 expected keys, each with non-empty content.
    """
    result = helpdesk_app.invoke({"ticket": "My monitor won't turn on."})

    assert "category" in result
    assert "knowledge" in result
    assert "suggestion" in result

    assert result["category"].strip() != ""
    assert result["knowledge"].strip() != ""
    assert result["suggestion"].strip() != ""


def test_full_pipeline_hardware_category():
    """A hardware-related ticket should end up categorized correctly
    after flowing through the whole pipeline."""
    result = helpdesk_app.invoke({"ticket": "My laptop screen is cracked."})
    assert result["category"] == "Hardware Issue"