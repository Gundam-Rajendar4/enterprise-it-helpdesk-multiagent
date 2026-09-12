"""
main.py
-------
FastAPI backend for the Enterprise IT Helpdesk Multi-Agent System.

Includes:
- Empty/blank ticket validation
- Graceful handling of Ollama connection failures (and other errors)
- Logging of every error to helpdesk.log for later review
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from graphs.helpdesk_graph import helpdesk_app

logging.basicConfig(
    filename="helpdesk.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(
    title="IT Helpdesk Multi-Agent API",
    description="Submit an IT ticket and get AI-generated triage, knowledge, and resolution.",
    version="1.0"
)


class TicketRequest(BaseModel):
    ticket: str

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
    unreachable, or if anything else goes wrong in the pipeline. Every
    error is also logged to helpdesk.log for later review.
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
        error_text = str(e).lower()

        if "actively refused" in error_text or "connection" in error_text:
            logging.error(f"OLLAMA UNAVAILABLE | Ticket: '{request.ticket}' | Error: {e}")
            raise HTTPException(
                status_code=503,
                detail="The AI service (Ollama) is currently unavailable. "
                       "Please make sure Ollama is running and try again."
            )
        else:
            logging.error(f"UNEXPECTED ERROR | Ticket: '{request.ticket}' | Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred while processing the ticket: {str(e)}"
            )


@app.get("/")
def root():
    return {"message": "IT Helpdesk Multi-Agent API is running. Visit /docs to test it."}