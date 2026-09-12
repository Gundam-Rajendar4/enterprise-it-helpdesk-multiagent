"""
helpdesk_graph.py
------------------
UPDATED (Day 8): State now also carries `is_relevant` and `distance`,
so the Resolver node knows whether to actually generate advice or
return a "needs human review" message.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END

from agents.triage_agent import triage_ticket
from agents.resolver_agent import resolve_ticket
from agents.knowledge_agent import retrieve_relevant_knowledge


class HelpdeskState(TypedDict):
    ticket: str
    category: str
    knowledge: str
    is_relevant: bool      # NEW
    distance: float         # NEW
    suggestion: str


def triage_node(state: HelpdeskState) -> dict:
    category = triage_ticket(state["ticket"])
    return {"category": category}


def knowledge_node(state: HelpdeskState) -> dict:
    result = retrieve_relevant_knowledge(state["ticket"])
    return {
        "knowledge": result["content"],
        "is_relevant": result["is_relevant"],
        "distance": result["distance"]
    }


def resolver_node(state: HelpdeskState) -> dict:
    suggestion = resolve_ticket(
        state["ticket"],
        state["category"],
        state["knowledge"],
        state["is_relevant"]
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
        "What's the weather like today?",
    ]

    print("=== Full Pipeline with Confidence Threshold ===\n")
    for ticket in test_tickets:
        result = helpdesk_app.invoke({"ticket": ticket})
        print(f"Ticket: {result['ticket']}")
        print(f"Category: {result['category']}")
        print(f"Distance: {result['distance']:.3f}")
        print(f"Is Relevant: {result['is_relevant']}")
        print(f"Suggestion: {result['suggestion']}\n")