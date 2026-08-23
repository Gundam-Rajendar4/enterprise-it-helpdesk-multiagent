"""
resolver_agent.py
------------------
UPDATED for Day 3: Now uses retrieved knowledge (RAG) instead of relying
purely on the LLM's raw training. This makes suggestions grounded in
OUR company's actual documented procedures, not generic guesses.
"""

from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3.2")


def resolve_ticket(ticket_description: str, category: str, knowledge: str) -> str:
    """
    Takes the ticket, category, AND retrieved knowledge (from ChromaDB),
    and suggests a resolution step GROUNDED in that knowledge - not just
    the LLM guessing from memory.
    """

    prompt = f"""You are an IT Helpdesk resolution assistant.
Use ONLY the knowledge base content below to suggest ONE clear first
troubleshooting step. Do not invent steps that aren't supported by the
knowledge base.

Category: {category}
Ticket: "{ticket_description}"

Knowledge Base Content:
{knowledge}

Respond in ONE short sentence only. No explanations, no extra text."""

    response = llm.invoke(prompt)
    suggestion = response.strip()

    return suggestion


if __name__ == "__main__":
    sample_knowledge = """Password Reset Knowledge Base
To reset a forgotten password, go to portal.company.com/reset and
enter your registered work email. Never attempt repeated logins -
accounts lock after 5 failed attempts."""

    suggestion = resolve_ticket(
        "I forgot my password and can't log into my laptop.",
        "Password Reset",
        sample_knowledge
    )
    print(f"Suggested Step: {suggestion}")