"""
resolver_agent.py
------------------
This is our SECOND agent in the Enterprise IT Helpdesk Multi-Agent System.

Job of this agent: Given a ticket description AND its category (decided by
the triage agent), suggest a first-line resolution step. This mimics a real
helpdesk workflow — once a ticket is categorized, the next person (or agent)
suggests what to actually do about it.
"""

from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3.2")


def resolve_ticket(ticket_description: str, category: str) -> str:
    """
    Takes the ticket description AND the category (from the triage agent)
    and returns a suggested first resolution step.

    Notice: this function needs TWO inputs, not one. That's because it
    depends on the triage agent's output — this is the "handoff" in action.
    """

    prompt = f"""You are an IT Helpdesk resolution assistant.
A ticket has already been categorized. Suggest ONE clear, short first
troubleshooting step a support agent should try.

Category: {category}
Ticket: "{ticket_description}"

Respond in ONE short sentence only. No explanations, no extra text."""

    response = llm.invoke(prompt)
    suggestion = response.strip()

    return suggestion


# Quick standalone test — only runs if this file is executed directly
if __name__ == "__main__":
    test_cases = [
        ("I forgot my password and can't log into my laptop.", "Password Reset"),
        ("My monitor won't turn on even though it's plugged in.", "Hardware Issue"),
    ]

    print("=== Resolver Agent — Test Run ===\n")
    for ticket, category in test_cases:
        suggestion = resolve_ticket(ticket, category)
        print(f"Ticket: {ticket}")
        print(f"Category: {category}")
        print(f"→ Suggested Step: {suggestion}\n")