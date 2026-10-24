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

---

## Day 6 — Error Handling + Documentation

**README.md** — a public-facing doc explaining the project: architecture, tech stack, setup steps, usage, known limitations, and planned improvements. Different purpose from NOTES.md — README is for OTHERS (recruiters, interviewers, anyone visiting the repo); NOTES.md is for YOU (learning reference).

**Pydantic `field_validator`** — a way to add custom validation rules to a request model. Runs automatically BEFORE your endpoint code executes.
```python
class TicketRequest(BaseModel):
    ticket: str

    @field_validator("ticket")
    @classmethod
    def ticket_must_not_be_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Ticket description cannot be empty.")
        return value
```
Empty/blank input now gets rejected automatically with a clear 422 error, before the pipeline even runs.

**`try/except` around the pipeline call** — catches failures (e.g., Ollama not running) so the app returns a clean error message instead of crashing.
- FastAPI: raises `HTTPException(status_code=503, detail="...")` for service-unavailable, `500` for anything else unexpected.
- Streamlit: shows `st.error("...")` instead of letting the raw crash/traceback show.

**Important lesson learned:** don't assume a library raises Python's built-in exception classes (e.g., `ConnectionError`). Different libraries (Ollama's client, httpx, etc.) raise their OWN exception classes. When you don't know the exact class, catch broadly (`except Exception as e`) and check `str(e)` for known failure signatures instead of guessing the class name.

**HTTP status codes to remember:**
- `200` = success
- `422` = validation error (bad input shape/content, caught before your code runs)
- `500` = unexpected server-side error (something broke that we didn't specifically anticipate)
- `503` = service unavailable (a dependency, like Ollama, isn't reachable)

**Housekeeping:** always double check `git status` BEFORE `git add .` — caught a stray `README.md.pdf` file that snuck into a commit this way.

---

## Full pipeline journey (fill this in from memory before each new day)

User types ticket in ______ → clicks submit → data goes into ______ →
first agent (______) does ______ → result stored in ______ →
second agent (______) does ______ → third agent (______) does ______ →
final result shown back in ______.

(Answer key is in Day 2-5 sections above if you get stuck — but try from memory first!)

## Day 7: Automated Testing with pytest

**Problem:** Every time we changed code, we had to check by hand that nothing broke.

**Solution:** pytest runs checks automatically and reports pass or fail.

**Key concepts:**
- A test is a function whose name starts with `test_`, and it uses `assert` to state what must be true
- pytest finds files named `test_*.py` in the `tests/` folder automatically
- `pytest -v` runs everything and lists each test with PASSED or FAILED
- Tests give confidence to change code later, because a break shows up immediately

**Our tests:**
- `tests/test_agents.py`: triage (password reset, hardware), knowledge retrieval, resolver output
- `tests/test_pipeline.py`: the full Triage → Knowledge → Resolver flow

**Lesson learned:** Tests that call the LLM are slower and can vary slightly between runs, so we assert on stable things (the category, a non-empty answer) and not exact wording.

## Day 8: RAG Confidence Threshold

**Problem:** ChromaDB always returns its closest match, even when that match is far from the question. A ticket about lunch would still get some KB document, and the Resolver would write a confident but wrong answer.

**Solution:** Added a distance check in `agents/knowledge_agent.py`.

**Key concepts:**
- Embeddings turn text into numbers, and ChromaDB measures the distance between them. Lower distance means a closer match
- `DISTANCE_THRESHOLD = 1.0`, defined in `knowledge_agent.py`, not in the graph
- Distance at or below 1.0: `is_relevant = True`. Distance above 1.0: `is_relevant = False`
- Measured on real data: a relevant ticket scored about 0.697, and an irrelevant one about 1.881
- `retrieve_relevant_knowledge()` now returns a dictionary: `content`, `is_relevant`, `distance`
- When `is_relevant` is False, the Resolver skips the LLM call and returns an escalation message

**Grounded:** the Resolver only builds answers from the knowledge base content, not from the model's general knowledge. The threshold protects this, because there is nothing to ground on when no good match exists.

**Lesson learned:** Changing a return type (string to dictionary) broke an old test. After changing a function's output, re-run the tests.

## Day 9: Logging

**Problem:** When something failed, there was no record of what happened or when. The error message disappeared as soon as the screen closed.

**Solution:** Added Python's built-in `logging` module, which writes records to a file called `helpdesk.log`.

**Key concepts:**
- `logging.basicConfig(filename="helpdesk.log", level=logging.INFO, format=...)` sets up the log file and the line format, once per program
- `logging.info(...)` records routine activity. We use it in `helpdesk_graph.py`, one line per node (triage, knowledge, resolver)
- `logging.error(...)` records something that actually failed. We use it in the `except` blocks of `api/main.py` (Ollama unavailable, unexpected error)
- Log levels in order of seriousness: DEBUG, INFO, WARNING, ERROR, CRITICAL. Setting the level to INFO hides DEBUG lines
- `logging.getLogger("httpx").setLevel(logging.WARNING)` silences a noisy library that was filling the log
- `helpdesk.log` is generated data, not source code, so it is in `.gitignore`
- Read the log in PowerShell with `type helpdesk.log`

**Why it matters:** In a real system you can't watch the screen all day. The log lets you check what happened later, such as which ticket failed and why.

**Lesson learned:** Write the ticket text and the error into the log line, not just "error occurred." A log line is only useful if it tells you which request failed and why.

## Day 10: API Key Authentication

**Problem:** Anyone who knew the API's URL could call `/submit-ticket` for free. There was no protection.

**Solution:** An API key check using FastAPI's `Header` and `Depends`.

**Key concepts:**
- `.env` is a plain text file for secrets (`API_KEY=...`). It is in `.gitignore`, so it never reaches GitHub
- `.env` and `venv` are different things: `.env` is the secrets file, `venv` is the Python environment folder
- `load_dotenv()` (from `python-dotenv`) reads `.env`, and `os.getenv("API_KEY")` gets the value in Python
- `Header(...)` tells FastAPI to expect a header, here `x-api-key`
- `Depends(verify_api_key)` runs the check before the endpoint's own code. If the check raises an error, the endpoint never runs

**The check:**
```python
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
```

**Applied to an endpoint:**
```python
@app.post("/submit-ticket")
def submit_ticket(request: TicketRequest, authorized: None = Depends(verify_api_key)):
```

**Results:**
- Wrong key: 401 Unauthorized
- Correct key: 200 OK
- Header missing completely: 422, because `Header(...)` rejects it before our code runs (found while writing the tests)

**Git gotcha:** Don't paste the `(venv) PS C:\...>` prompt along with a command. PowerShell tries to run the whole line and gives a parser error.

## Day 11: Ticketing with SQLite

**Problem:** The pipeline processed a ticket once and forgot it. A real helpdesk stores tickets and tracks their status.

**Solution:** A local SQLite database, plus new endpoints and a ticket history table in the UI.

**Key concepts:**
- SQLite is a full database stored in one file (`helpdesk.db`). It needs no server, no install and no cost, because Python includes `sqlite3`
- Source code is what you type by hand. Generated data is what the program creates while running. Generated data (`helpdesk.db`, `chroma_db/`, `helpdesk.log`) goes in `.gitignore`
- `api/database.py` holds the helpers: `init_db`, `create_ticket`, `update_ticket`, `get_all_tickets`, `get_ticket`
- `?` placeholders in SQL protect against SQL injection
- Query it directly with SQL: `SELECT * FROM tickets ORDER BY id DESC`

**Ticket flow in `POST /tickets` (and the Streamlit UI):**
1. Save the ticket first with status Open, so it survives even if Ollama is down
2. Run the AI pipeline
3. Update the same row with category, suggestion and final status

**Statuses:**
- Open: saved, not yet processed, or the AI step failed
- Resolved: the Knowledge agent found relevant content (`is_relevant` True)
- Escalated: no relevant content (`is_relevant` False), so a human takes over

**Endpoints (all need the API key):**
- `POST /tickets`: create and process
- `GET /tickets`: list all, newest first
- `GET /tickets/{ticket_id}`: one ticket, or 404 if it doesn't exist

**New HTTP status code:** 404 means "that thing doesn't exist."

**UI:** `ui/app.py` saves each ticket, shows "Ticket #N is Resolved/Escalated", and ends with `st.dataframe(get_all_tickets())`. Streamlit reruns the whole file after each click, so the table refreshes by itself.

**Tests added (15 total now):**
- `tests/test_database.py`: 4 tests on a temporary database, using the `tmp_path` and `monkeypatch` fixtures, so the real `helpdesk.db` is never touched
- `tests/test_auth.py`: 4 tests with FastAPI's `TestClient` (wrong key 401, missing key 422, correct key 200, missing ticket 404)
- `pytest.ini` with `pythonpath = .` fixes "No module named 'api'" when running plain `pytest`

**Lesson learned:** `python -m pytest` and `pytest` can behave differently, because only the first adds the current folder to Python's search path. A `pytest.ini` makes both work.