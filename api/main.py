"""
main.py
-------
FastAPI backend for the Enterprise IT Helpdesk Multi-Agent System.

UPDATED: now includes error handling for:
1. Empty/blank ticket submissions
2. Ollama not running / LLM connection failures
3. Any unexpected pipeline failure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from graphs.helpdesk_graph import helpdesk_app

app = FastAPI(
    title="IT Helpdesk Multi-Agent API",
    description="Submit an IT ticket and get AI-generated triage, knowledge, and resolution.",
    version="1.0"
)


class TicketRequest(BaseModel):
    ticket: str

    # This runs automatically whenever a request comes in, BEFORE our
    # endpoint code even executes. If the ticket is blank/whitespace-only,
    # we reject it here with a clear message.
    @field_validator("ticket")
    @classmethod
    def ticket_must_not_be_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Ticket description cannot be empty.")
        return value


@app.post("/submit-ticket")
def submit_ticket(request: TicketRequest):
    """
    Accepts a ticket description, runs it through the full agent pipeline,
    and returns category, retrieved knowledge, and suggested resolution.

    Returns a clear HTTP error instead of crashing if the LLM (Ollama) is
    unreachable, or if anything else goes wrong in the pipeline.
    """
    try:
        result = helpdesk_app.invoke({"ticket": request.ticket})

        return {
            "ticket": result["ticket"],
            "category": result["category"],
            "knowledge": result["knowledge"],
            "suggestion": result["suggestion"]
        }

    except Exception as e:
        # We catch broadly here because different libraries (Ollama's
        # client, httpx, etc.) raise their OWN connection-error classes,
        # not Python's built-in ConnectionError. Instead of guessing the
        # exact class, we check the error MESSAGE for known connection
        # failure signatures.
        error_text = str(e).lower()
        if "actively refused" in error_text or "connection" in error_text:
            raise HTTPException(
                status_code=503,
                detail="The AI service (Ollama) is currently unavailable. "
                       "Please make sure Ollama is running and try again."
            )

        # Catch-all for anything else unexpected, so we NEVER crash silently
        # or return a confusing raw Python traceback to the caller.
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while processing the ticket: {str(e)}"
        )


@app.get("/")
def root():
    return {"message": "IT Helpdesk Multi-Agent API is running. Visit /docs to test it."}

