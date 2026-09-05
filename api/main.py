"""
main.py
-------
FastAPI backend for the Enterprise IT Helpdesk Multi-Agent System.

This exposes our LangGraph pipeline (Triage -> Knowledge -> Resolver) as
a REST API endpoint, so any external system (a ticketing tool, Copilot
Studio, a mobile app, etc.) can submit a ticket and get back structured
results - no browser UI required.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from pydantic import BaseModel
from graphs.helpdesk_graph import helpdesk_app

# Create the FastAPI application instance
app = FastAPI(
    title="IT Helpdesk Multi-Agent API",
    description="Submit an IT ticket and get AI-generated triage, knowledge, and resolution.",
    version="1.0"
)


# Pydantic model defines the SHAPE of data we expect in a request.
# FastAPI uses this to automatically validate incoming requests -
# if someone sends the wrong data type, FastAPI rejects it automatically
# with a clear error, before our code even runs.
class TicketRequest(BaseModel):
    ticket: str


# This defines an endpoint: a URL path + HTTP method combination.
# POST /submit-ticket means: send data TO this URL to create/process something.
@app.post("/submit-ticket")
def submit_ticket(request: TicketRequest):
    """
    Accepts a ticket description, runs it through the full agent pipeline,
    and returns category, retrieved knowledge, and suggested resolution.
    """
    result = helpdesk_app.invoke({"ticket": request.ticket})

    return {
        "ticket": result["ticket"],
        "category": result["category"],
        "knowledge": result["knowledge"],
        "suggestion": result["suggestion"]
    }


# A simple root endpoint just to confirm the API is alive
@app.get("/")
def root():
    return {"message": "IT Helpdesk Multi-Agent API is running. Visit /docs to test it."}