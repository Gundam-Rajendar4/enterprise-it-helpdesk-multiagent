"""
app.py
------
Streamlit UI for the Enterprise IT Helpdesk Multi-Agent System.

This gives a simple web page where a user can type a ticket description
and see our full 3-agent pipeline (Triage -> Knowledge -> Resolver) run
live, with results displayed clearly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from graphs.helpdesk_graph import helpdesk_app

# Page setup
st.set_page_config(page_title="IT Helpdesk Multi-Agent System", page_icon="🎫")

st.title("🎫 Enterprise IT Helpdesk Multi-Agent System")
st.write("Describe your IT issue below, and our AI agent team will triage, "
         "look up relevant knowledge, and suggest a resolution.")

# Input box for the ticket
ticket_input = st.text_area(
    "Describe your issue:",
    placeholder="e.g., I forgot my password and can't log into my laptop."
)

# Button to trigger the pipeline
if st.button("Submit Ticket"):
    if ticket_input.strip() == "":
        st.warning("Please describe your issue before submitting.")
    else:
        # Show a spinner while the pipeline runs (agents take a few seconds)
        with st.spinner("Agents are working on your ticket..."):
            result = helpdesk_app.invoke({"ticket": ticket_input})

        st.success("Done! Here's what our agents found:")

        st.subheader("📁 Category")
        st.write(result["category"])

        st.subheader("📚 Relevant Knowledge Found")
        st.write(result["knowledge"])

        st.subheader("✅ Suggested Resolution Step")
        st.write(result["suggestion"])