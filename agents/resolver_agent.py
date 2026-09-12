"""
resolver_agent.py
------------------
UPDATED (Day 8): now handles the case where NO relevant knowledge was
found (is_relevant=False) by skipping the LLM call entirely and returning
a clear "needs manual review" message - instead of asking the LLM to
generate advice from irrelevant content.
"""

from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3.2")


def resolve_ticket(ticket_description: str, category: str, knowledge: str, is_relevant: bool = True) -> str:
    """
    Suggests a resolution step GROUNDED in retrieved knowledge.

    If is_relevant is False, we don't even call the LLM - we know upfront
    that we don't have good information, so there's no point asking the
    LLM to guess. This saves an unnecessary LLM call AND avoids a
    confidently-wrong answer.
    """
    if not is_relevant:
        return ("This ticket doesn't match any known issue in our knowledge "
                "base. Please escalate to a human support agent for review.")

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
    # Test case 1: relevant knowledge available
    suggestion1 = resolve_ticket(
        "I forgot my password.",
        "Password Reset",
        "Go to portal.company.com/reset to reset your password.",
        is_relevant=True
    )
    print(f"Relevant case: {suggestion1}")

    # Test case 2: no relevant knowledge found
    suggestion2 = resolve_ticket(
        "What's the weather today?",
        "Other",
        "",
        is_relevant=False
    )
    print(f"Irrelevant case: {suggestion2}")