# Enterprise IT Helpdesk Multi-Agent System

A multi-agent AI system that automates the first line of IT helpdesk triage: classifying incoming tickets, retrieving relevant knowledge base documentation, suggesting a grounded first troubleshooting step, and storing every ticket with a tracked status. Built as a hands-on learning project to explore agentic AI architecture patterns used in real enterprise systems.

## Architecture

The system uses a **3-agent pipeline** orchestrated with LangGraph, where each agent reads from and writes to a shared state object as the ticket flows through the system:

```
                    ┌──────────────┐      ┌───────────────┐      ┌────────────────┐
   User Ticket ───▶ │ Triage Agent │ ───▶ │ Knowledge      │ ───▶ │ Resolver Agent  │ ───▶ Final Answer
                    │ (classifies) │      │ Agent (RAG)    │      │ (suggests fix)  │
                    └──────────────┘      └───────────────┘      └────────────────┘
```

1. **Triage Agent** reads the raw ticket description and classifies it into one of six categories (Password Reset, Hardware Issue, Software Bug, Network Issue, Access Request, Other).
2. **Knowledge Agent** performs Retrieval Augmented Generation (RAG): it converts the ticket into a vector embedding and searches a ChromaDB vector store for the most relevant internal knowledge base document. A **confidence threshold** (distance score above 1.0) flags matches that are too far away to trust.
3. **Resolver Agent** combines the ticket, its category, and the retrieved knowledge to suggest one concrete, grounded first troubleshooting step. When the Knowledge Agent finds nothing relevant, the Resolver skips the LLM call and returns an escalation message instead of guessing.

### Ticket lifecycle

Every ticket submitted through the UI or `POST /tickets` is saved to a local SQLite database **before** the AI pipeline runs, then updated with the results:

| Status | Meaning |
|---|---|
| Open | Ticket saved, not yet processed (or the AI step failed, for example Ollama was down) |
| Resolved | Relevant knowledge was found and a grounded suggestion was produced |
| Escalated | No relevant knowledge was found, so a human agent should take over |

The pipeline is exposed two ways:
- **Streamlit UI** (`ui/app.py`): a browser-based form to submit a ticket, see the results, and view a ticket history table.
- **FastAPI backend** (`api/main.py`): REST endpoints so other systems (a ticketing tool, a chatbot, Copilot Studio, etc.) can call the pipeline programmatically. All endpoints are protected by an API key.

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Ollama (llama3.2), running locally |
| LLM orchestration | LangChain |
| Multi-agent workflow | LangGraph |
| Vector database / RAG | ChromaDB |
| Ticket storage | SQLite (local file, no server needed) |
| Web UI | Streamlit |
| REST API | FastAPI + Uvicorn + Pydantic |
| Authentication | API key via `x-api-key` header (python-dotenv for secrets) |
| Testing | pytest |
| Language | Python 3.12+ |

## Project Structure

```
enterprise-it-helpdesk-multiagent/
├── agents/              # Individual agent logic
│   ├── triage_agent.py
│   ├── knowledge_agent.py
│   └── resolver_agent.py
├── graphs/
│   └── helpdesk_graph.py   # LangGraph pipeline wiring the 3 agents together
├── data/                # Sample IT knowledge base documents (.txt)
├── ui/
│   └── app.py           # Streamlit web interface
├── api/
│   ├── main.py          # FastAPI endpoints
│   └── database.py      # SQLite ticket storage helpers
├── tests/
│   ├── test_agents.py   # Agent-level tests
│   ├── test_pipeline.py # Full pipeline tests
│   ├── test_database.py # Ticket database tests
│   └── test_auth.py     # API key authentication tests
├── pytest.ini
├── requirements.txt
└── NOTES.md             # Personal learning notes / concept cheat-sheet
```

Files created at runtime and excluded from Git: `helpdesk.db` (tickets), `chroma_db/` (vector store), `helpdesk.log` (logs), `.env` (secrets).

## Setup & Installation

**Prerequisites:** Python 3.12+, Git, [Ollama](https://ollama.com) installed with the `llama3.2` model pulled (`ollama pull llama3.2`).

```bash
# Clone the repo
git clone https://github.com/Gundam-Rajendar4/enterprise-it-helpdesk-multiagent.git
cd enterprise-it-helpdesk-multiagent

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

**Create a `.env` file** in the project root with an API key of your choice:
```
API_KEY=your-own-secret-key
```
This file is gitignored and never committed.

## Usage

**Run the Streamlit UI:**
```bash
streamlit run ui/app.py
```
Opens at `http://localhost:8501`. Type a ticket description and click Submit. The ticket history table appears below the form.

**Run the FastAPI backend:**
```bash
uvicorn api.main:app --reload
```
Interactive API docs are available at `http://127.0.0.1:8000/docs`. Enter your API key in the `x-api-key` field before executing a request.

| Endpoint | Purpose |
|---|---|
| `POST /submit-ticket` | Run the pipeline and return the result (no storage) |
| `POST /tickets` | Save a ticket, run the pipeline, update it with the status |
| `GET /tickets` | List all tickets, newest first |
| `GET /tickets/{ticket_id}` | Get one ticket, or 404 if it doesn't exist |

Example request:
```bash
curl -X POST http://127.0.0.1:8000/tickets \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-own-secret-key" \
  -d '{"ticket": "I forgot my password and cannot log into my laptop."}'
```

**Run the pipeline directly from the terminal:**
```bash
python -m graphs.helpdesk_graph
```

**Run the tests:**
```bash
pytest -v
```
The agent and pipeline tests call the local LLM, so Ollama must be running. The authentication tests read `API_KEY` from your `.env` file.

## Error Handling & Logging

- Empty or blank tickets are rejected (HTTP 422 from the API, a warning in the UI).
- If Ollama is unavailable, the API returns 503 and the UI shows a friendly message. A ticket saved through `POST /tickets` stays as Open.
- Other failures return 500 with a clear message.
- Requests with a wrong API key get 401, and a missing key is rejected with 422.
- Pipeline activity and errors are written to `helpdesk.log`.

## Known Limitations

This is a learning-stage project, not a production system. Current gaps:
- Knowledge base is a small set of 4 sample documents, not representative of a real enterprise KB.
- Authentication is a single shared API key. There are no user accounts, roles, rate limiting, or HTTPS.
- Ticketing is a local mock (SQLite) and is not integrated with a real system such as ServiceNow or Jira.
- The confidence threshold (1.0) was tuned on a small set of examples and would need re-tuning on a real knowledge base.
- Error handling does not yet cover ChromaDB failures or oversized input.
- Runs locally only. It needs Ollama, so it is not yet deployed anywhere publicly accessible.

## Planned Improvements

- Deploy a public demo
- Expand the knowledge base and add a document-ingestion pipeline
- Add conditional routing in LangGraph (for example, route "Access Request" tickets differently from "Hardware Issue")
- Extend error handling to cover ChromaDB failures and oversized input
- Integrate with a real ticketing system

## Author

Built by Rajendar Gundam as a hands-on project to learn agentic AI system design: LangGraph orchestration, RAG, and multi-agent architecture patterns applicable to enterprise AI platforms.