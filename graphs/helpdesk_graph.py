"""
helpdesk_graph.py
------------------
UPDATED for Day 3: Now a 3-agent pipeline.

Triage -> Knowledge Retrieval -> Resolver

Each node reads what previous nodes wrote into State, and adds its own
piece before passing along.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END

from agents.triage_agent import triage_ticket
from agents.resolver_agent import resolve_ticket
from agents.knowledge_agent import retrieve_relevant_knowledge


class HelpdeskState(TypedDict):
    ticket: str
    category: str
    knowledge: str      # NEW - retrieved knowledge base content
    suggestion: str


def triage_node(state: HelpdeskState) -> dict:
    category = triage_ticket(state["ticket"])
    return {"category": category}


def knowledge_node(state: HelpdeskState) -> dict:
    knowledge = retrieve_relevant_knowledge(state["ticket"])
    return {"knowledge": knowledge}


def resolver_node(state: HelpdeskState) -> dict:
    suggestion = resolve_ticket(
        state["ticket"],
        state["category"],
        state["knowledge"]
    )
    return {"suggestion": suggestion}


graph_builder = StateGraph(HelpdeskState)

graph_builder.add_node("triage", triage_node)
graph_builder.add_node("knowledge", knowledge_node)
graph_builder.add_node("resolver", resolver_node)

graph_builder.set_entry_point("triage")
graph_builder.add_edge("triage", "knowledge")
graph_builder.add_edge("knowledge", "resolver")
graph_builder.add_edge("resolver", END)

helpdesk_app = graph_builder.compile()


if __name__ == "__main__":
    test_tickets = [
        "I forgot my password and can't log into my laptop.",
        "My monitor won't turn on even though it's plugged in.",
        "The CRM app crashes every time I click 'Save'.",
    ]

    print("=== Full 3-Agent Helpdesk Pipeline ===\n")
    for ticket in test_tickets:
        result = helpdesk_app.invoke({"ticket": ticket})
        print(f"Ticket: {result['ticket']}")
        print(f"Category: {result['category']}")
        print(f"Suggested Step: {result['suggestion']}\n")