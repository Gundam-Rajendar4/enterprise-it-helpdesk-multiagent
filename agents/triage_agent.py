"""
triage_agent.py
----------------
This is our FIRST agent in the Enterprise IT Helpdesk Multi-Agent System.

Job of this agent: Read an incoming IT ticket description, and classify it
into a category. This is the "front door" of a real helpdesk — before any
ticket gets routed to a specialist team, someone (or something) has to
read it and decide what kind of issue it is.

We're using Ollama (running llama3.2 locally) as the "brain" of this agent.
LangChain gives us a clean way to talk to that brain.
"""

#from langchain_community.llms import Ollama
from langchain_ollama import OllamaLLM

# Step 1: Connect to our local LLM running via Ollama.
#llm = Ollama(model="llama3.2")
llm = OllamaLLM(model="llama3.2")


def triage_ticket(ticket_description: str) -> str:
    """
    Takes a raw IT ticket description and returns a category classification.
    """

    prompt = f"""You are an IT Helpdesk triage assistant.
Classify the following IT support ticket into EXACTLY ONE of these categories:
- Password Reset
- Hardware Issue
- Software Bug
- Network Issue
- Access Request
- Other

Ticket: "{ticket_description}"

Respond with ONLY the category name, nothing else."""

    response = llm.invoke(prompt)
    category = response.strip()
    return category


if __name__ == "__main__":
    test_tickets = [
        "I forgot my password and can't log into my laptop.",
        "My monitor won't turn on even though it's plugged in.",
        "The CRM app crashes every time I click 'Save'.",
        "I can't access the shared drive for the finance team.",
    ]

    print("=== IT Helpdesk Triage Agent — Test Run ===\n")
    for ticket in test_tickets:
        category = triage_ticket(ticket)
        print(f"Ticket: {ticket}")
        print(f"→ Category: {category}\n")