# Shiny Agents

Three implementations of the same coding-agent idea, available through one small web UI:

- **CrewAI**: role-based single agent
- **Agents SDK**: tool loop with session support
- **LangGraph**: triage, specialist, and reviewer graph

All three use Google Gemini. The original terminal demos remain runnable, and the web gateway drives each one request at a time through `AGENT_REQUEST`.

## Setup

```bash
cd Shiny-Agents
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put the server's Gemini key in `.env` as `GEMINI_API_KEY`. The key is read only by the backend and is never sent to the browser. Start the unified UI with:

```bash
uvicorn app.server:app --reload
```

Open `http://127.0.0.1:8000`.

## Usage limits and BYOK

Users without a personal key receive three default-key requests in a rolling 24-hour window. The first request starts the window. Usage is tracked in `app/trials.sqlite3`, keyed by a random `HttpOnly` browser cookie. This is appropriate for a small single-instance app; a multi-instance deployment should replace the SQLite store with a shared database or Redis.

The optional Personal Gemini key field is kept in browser memory for the current page session and sent only over the server request. It is not persisted by this app or written to the trial database. A personal key bypasses the trial counter.

## Direct demos

```bash
GEMINI_API_KEY=... python 01_crewai/agent.py
GEMINI_API_KEY=... python 02_agents_sdk/agent.py
GEMINI_API_KEY=... python 03_langgraph/multi_agent.py
```
