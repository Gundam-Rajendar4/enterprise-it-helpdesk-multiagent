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
from api.database import init_db, create_ticket, update_ticket, get_all_tickets, get_ticket
from fastapi import Header, Depends
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

logging.basicConfig(
    filename="helpdesk.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

init_db()

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
def submit_ticket(request: TicketRequest, authorized: None = Depends(verify_api_key)):
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

@app.post("/tickets")
def create_new_ticket(request: TicketRequest, authorized: None = Depends(verify_api_key)):
    """
    Creates a ticket (status 'Open'), runs it through the AI pipeline,
    then updates the same ticket with the category, suggestion and final status.
    """
    ticket_id = create_ticket(request.ticket)

    try:
        result = helpdesk_app.invoke({"ticket": request.ticket})

        status = "Resolved" if result["is_relevant"] else "Escalated"
        update_ticket(ticket_id, result["category"], result["suggestion"], status)

        return {
            "id": ticket_id,
            "status": status,
            "ticket": result["ticket"],
            "category": result["category"],
            "suggestion": result["suggestion"]
        }

    except Exception as e:
        error_text = str(e).lower()

        if "actively refused" in error_text or "connection" in error_text:
            logging.error(f"OLLAMA UNAVAILABLE | Ticket #{ticket_id}: '{request.ticket}' | Error: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Ticket #{ticket_id} was saved as 'Open', but the AI service (Ollama) is unavailable."
            )
        else:
            logging.error(f"UNEXPECTED ERROR | Ticket #{ticket_id}: '{request.ticket}' | Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ticket #{ticket_id} was saved as 'Open', but an unexpected error occurred: {str(e)}"
            )

@app.get("/tickets")
def list_tickets(authorized: None = Depends(verify_api_key)):
    """Return all tickets, newest first."""
    return get_all_tickets()


@app.get("/tickets/{ticket_id}")
def read_ticket(ticket_id: int, authorized: None = Depends(verify_api_key)):
    """Return one ticket by id, or 404 if it doesn't exist."""
    ticket = get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found")
    return ticket