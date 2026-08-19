"""
helpdesk_graph.py
------------------
This file connects our TWO agents (Triage + Resolver) into a single
LangGraph workflow. This is where "multi-agent" actually becomes real —
instead of running each agent manually and passing data by hand, LangGraph
manages the handoff automatically.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END

from agents.triage_agent import triage_ticket
from agents.resolver_agent import resolve_ticket


# Step 1: Define the State — the shared "clipboard" that flows between nodes.
# TypedDict just means: a dictionary with a fixed, known set of keys.
class HelpdeskState(TypedDict):
    ticket: str        # original ticket text (input)
    category: str       # filled in by triage node
    suggestion: str     # filled in by resolver node


# Step 2: Define each Node — a function that takes the State, does its job,
# and returns the piece of State it updated.

def triage_node(state: HelpdeskState) -> dict:
    category = triage_ticket(state["ticket"])
    return {"category": category}


def resolver_node(state: HelpdeskState) -> dict:
    suggestion = resolve_ticket(state["ticket"], state["category"])
    return {"suggestion": suggestion}


# Step 3: Build the Graph — wire nodes together with edges.
graph_builder = StateGraph(HelpdeskState)

graph_builder.add_node("triage", triage_node)
graph_builder.add_node("resolver", resolver_node)

graph_builder.set_entry_point("triage")     # graph starts at triage
graph_builder.add_edge("triage", "resolver")  # after triage, go to resolver
graph_builder.add_edge("resolver", END)       # after resolver, we're done

# Compile it into a runnable app
helpdesk_app = graph_builder.compile()


# Step 4: Quick test — run the full pipeline end-to-end
if __name__ == "__main__":
    test_ticket = "I forgot my password and can't log into my laptop."

    result = helpdesk_app.invoke({"ticket": test_ticket})

    print("=== Full Helpdesk Pipeline ===\n")
    print(f"Ticket: {result['ticket']}")
    print(f"Category: {result['category']}")
    print(f"Suggested Step: {result['suggestion']}")