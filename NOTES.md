# Enterprise IT Helpdesk Multi-Agent System — My Notes

A living cheat-sheet. Re-read this before starting each new day.

---

## Day 1 — Setup

**venv (Virtual Environment)**
- Problem it solves: different projects need different library versions; venv keeps each project's libraries isolated ("private kitchen" per project).
- Create ONCE per project: `python -m venv venv`
- Activate EVERY TIME you reopen the project: `venv\Scripts\activate`
- You know it's active when you see `(venv)` at the start of the terminal line.

**Git — 3 core commands**
- `git add .` → stage changes (mark files ready to be saved)
- `git commit -m "message"` → save a snapshot LOCALLY on your laptop
- `git push` → upload that snapshot to GitHub (online)
- Telugu: add = సిద్ధం చేయడం, commit = save చేయడం (local), push = GitHub కి పంపడం

**.gitignore**
- A file listing folders/files Git should NOT track (e.g., `venv/`, `__pycache__/`, `chroma_db/`)
- Must be named EXACTLY `.gitignore` — not `.gitignore.txt`. Create via VS Code "New File", not PowerShell `echo`, to avoid encoding bugs.
- Check if it's working: `git check-ignore -v <foldername>` — should show a match.

**LangChain**
- Framework to connect Python code to an LLM. Handles the "how do I talk to this AI model" plumbing.
- `llm.invoke(prompt)` → sends the prompt text to the LLM, returns the LLM's text response.
- Telugu: LangChain = LLM తో మాట్లాడటానికి ఉపయోగించే connector/bridge (phone line to the AI expert).

**Ollama**
- Runs an LLM (llama3.2) locally on your laptop — free, private, no data leaves your machine.
- One-time: `ollama pull llama3.2` (downloads the model)
- Every use: `OllamaLLM(model="llama3.2")` then `.invoke(prompt)` to actually ask it something.

**Running Python files with imports across folders**
- `python -m graphs.helpdesk_graph` (the `-m` + dotted path) tells Python to treat the project root as the import base — needed because our files import from other folders (e.g., `agents`).

---

## Day 2 — LangGraph (Multi-Agent Orchestration)

**LangGraph = the "manager's whiteboard" that decides which agent runs after which, and passes shared data between them.**

3 core building blocks:
- **State** — shared "clipboard" (a dictionary-like object) that flows through every agent. Ours: `HelpdeskState` with keys `ticket`, `category`, `knowledge`, `suggestion`.
- **Node** — one agent's logic as a function. Takes current State, does its job, returns ONLY the piece(s) it updated (as a dict) — not the whole State. LangGraph merges it automatically.
- **Edge** — defines execution order (`add_edge("triage", "resolver")` = after triage runs, go to resolver).

Build steps:
```python
graph_builder = StateGraph(HelpdeskState)
graph_builder.add_node("triage", triage_node)
graph_builder.set_entry_point("triage")
graph_builder.add_edge("triage", "resolver")
graph_builder.add_edge("resolver", END)
helpdesk_app = graph_builder.compile()   # makes it runnable
helpdesk_app.invoke({"ticket": "..."})    # actually runs it
```

**LangChain vs LangGraph — the one-liner**
"LangChain handles talking TO an LLM. LangGraph handles orchestrating MULTIPLE LLM-powered steps into a workflow with shared state."
Analogy: LangChain = one employee's phone line to the AI expert. LangGraph = the manager's whiteboard deciding the order employees work in and passing the folder (State) between them.

**Housekeeping habit learned:** `__pycache__` folders (auto-generated Python bytecode) should never be committed to Git — add to `.gitignore`.

---

## Day 3 — RAG (Retrieval Augmented Generation) + ChromaDB

**Problem it solves:** without RAG, the LLM only "guesses" from its training — it doesn't know OUR company's actual documented procedures. RAG makes it look up real documents first, then answer based on those.

**Embedding** = converting text into a list of numbers that represents MEANING (not exact words). Similar meanings → numbers land close together. This is what allows searching by intent/synonyms instead of exact keyword matching.

**Keyword search vs Vector search**
- Keyword search: exact word matches only — fails on synonyms, paraphrasing, typos.
- Vector/embedding search: matches by meaning/intent — "reset my password" and "can't log in" land close together even though the words differ.

**ChromaDB** = a vector database. Stores documents as embeddings; given a new query, finds the closest-meaning documents.
```python
collection.upsert(documents=[content], ids=[filename])   # store
collection.query(query_texts=[ticket], n_results=1)      # retrieve
```
- Persists to disk in a `chroma_db/` folder — don't need to re-embed every run, only when source docs change.
- IMPORTANT LIMITATION: ChromaDB always returns the "closest" match, even if nothing is truly relevant. It can't say "I don't know." (e.g., asking about weather would still retrieve one of our IT docs, just a bad match.) Real systems add a similarity-score threshold to catch this — we haven't built that yet.

**Housekeeping:** `chroma_db/` is generated/regenerable data — add to `.gitignore`, never commit.

---

## Day 4 — Streamlit UI

**What it does:** turns a plain Python script into an interactive web page, no HTML/CSS/JS needed.

Key functions used:
- `st.title()`, `st.text_area()`, `st.button()`, `st.write()`, `st.success()`, `st.spinner()`

**Critical behavior to remember:** Streamlit re-runs the ENTIRE script top to bottom on every single user interaction (any click, any typing that triggers a rerun). This is why we wrap expensive operations (like calling the LLM pipeline) inside `if st.button("Submit Ticket"):` — so it only runs when the button is actually clicked, not on every rerun.

**Run command (different from normal Python):**
```
streamlit run ui/app.py
```
NOT `python ui/app.py` — that wouldn't render anything as a web page.

**Import fix needed:** same root-import problem as Day 1, different fix this time since Streamlit doesn't support `-m`:
```python
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```
Add this before importing from `graphs/agents` folders.

---

## Day 5 — FastAPI (REST API)

**What it does:** exposes our pipeline so OTHER SOFTWARE (not just a human via browser) can call it — e.g., Copilot Studio, ServiceNow, a Slack bot.

**GET vs POST**
- GET = ask the server for data, nothing changes ("give me something") — e.g., our `/` root endpoint just confirms the API is alive.
- POST = send data TO the server to be processed ("here's something, do something with it") — e.g., `/submit-ticket` sends the ticket text so the pipeline can run.

**Pydantic BaseModel** — defines the expected SHAPE of incoming data:
```python
class TicketRequest(BaseModel):
    ticket: str
```
FastAPI uses this to automatically validate incoming requests — rejects bad data (wrong type, missing field) BEFORE our code even runs.

**Endpoint definition:**
```python
@app.post("/submit-ticket")
def submit_ticket(request: TicketRequest):
    result = helpdesk_app.invoke({"ticket": request.ticket})
    return {...}
```

**Run command:**
```
uvicorn api.main:app --reload
```
- `api.main` = the file `api/main.py`
- `:app` = the FastAPI instance named `app` inside that file
- `--reload` = auto-restart server when code changes
- uvicorn is what actually RUNS/SERVES the FastAPI app (FastAPI just defines the logic).

**`/docs`** — FastAPI auto-generates an interactive documentation page at `http://127.0.0.1:8000/docs` where you can test endpoints directly in the browser (click endpoint → "Try it out" → edit JSON → "Execute" → see response) — no separate tool (like Postman) needed.

**Stop the server:** `Ctrl + C` in the terminal where it's running.

---

## Full pipeline journey (fill this in from memory before each new day)

User types ticket in ______ → clicks submit → data goes into ______ →
first agent (______) does ______ → result stored in ______ →
second agent (______) does ______ → third agent (______) does ______ →
final result shown back in ______.

(Answer key is in Day 2-5 sections above if you get stuck — but try from memory first!)
