"""
app.py
------
Streamlit UI for the Enterprise IT Helpdesk Multi-Agent System.

UPDATED: now handles errors gracefully -
1. Empty/blank ticket submissions
2. Ollama not running / LLM connection failures
3. Any unexpected pipeline failure

UPDATED (Day 11): tickets are saved to the SQLite database,
and a ticket history table is shown below the form.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from graphs.helpdesk_graph import helpdesk_app
from api.database import init_db, create_ticket, update_ticket, get_all_tickets

st.set_page_config(page_title="IT Helpdesk Multi-Agent System", page_icon="🎫")

init_db()

st.title("🎫 Enterprise IT Helpdesk Multi-Agent System")
st.write("Describe your IT issue below, and our AI agent team will triage, "
         "look up relevant knowledge, and suggest a resolution.")

ticket_input = st.text_area(
    "Describe your issue:",
    placeholder="e.g., I forgot my password and can't log into my laptop."
)

if st.button("Submit Ticket"):
    if ticket_input.strip() == "":
        st.warning("Please describe your issue before submitting.")
    else:
        try:
            ticket_id = create_ticket(ticket_input)

            with st.spinner("Agents are working on your ticket..."):
                result = helpdesk_app.invoke({"ticket": ticket_input})

            status = "Resolved" if result["is_relevant"] else "Escalated"
            update_ticket(ticket_id, result["category"], result["suggestion"], status)

            st.success(f"Done! Ticket #{ticket_id} is {status}. Here's what our agents found:")

            st.subheader("📁 Category")
            st.write(result["category"])

            st.subheader("📚 Relevant Knowledge Found")
            st.write(result["knowledge"])

            st.subheader("✅ Suggested Resolution Step")
            st.write(result["suggestion"])

        except Exception as e:
            error_text = str(e).lower()
            if "actively refused" in error_text or "connection" in error_text:
                st.error(
                    "⚠️ The AI service (Ollama) is currently unavailable. "
                    "Please make sure Ollama is running on your machine and try again."
                )
            else:
                st.error(f"⚠️ Something went wrong while processing your ticket: {e}")

st.divider()
st.subheader("📋 Ticket History")

tickets = get_all_tickets()
if tickets:
    st.dataframe(tickets)
else:
    st.info("No tickets yet.")