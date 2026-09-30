# Shiny Agents

A comparative multi-agent engineering platform contrasting three production orchestration architectures—CrewAI, OpenAI Agents SDK, and LangGraph—powered by Google Gemini and a hybrid trial + BYOK gateway.

## Overview

Shiny Agents implements the same core coding assistant across three distinct agentic paradigms:
1. **Level 1 — Role-Based Team (CrewAI):** Declarative role, goal, and backstory definitions with linear task handoffs.
2. **Level 2 — Event-Driven Tool Loop with Guardrails (OpenAI Agents SDK):** Async function tool executions, conversational SQLite sessions, and input safety guardrails to block destructive commands.
3. **Level 3 — Stateful Cyclical Review Graph (LangGraph):** Explicit state graph featuring routing triage, specialist agents, and a code reviewer loop with iterative rework cycles (up to 2 revisions).

All three agent backends operate on top of Google Gemini (`gemini-2.5-flash`), unified by a responsive FastAPI web gateway that manages a 3-request rolling 24-hour trial quota and Bring-Your-Own-Key (BYOK) memory authentication.

## Problem

Building reliable AI agents requires answering fundamental system architecture questions:
- How much autonomy should the agent have versus deterministic control flow?
- How are destructive tool actions prevented before execution?
- Can an agent self-correct through review loops without infinite cycles?
- How do different agent frameworks (CrewAI vs OpenAI Agents SDK vs LangGraph) compare in structure, complexity, and observability?

## Motivation

Rather than treating AI agents as magical prompts, Shiny Agents was built to provide an objective, side-by-side engineering comparison of the three dominant agent orchestration design patterns using identical tool capabilities:
1. `list_files(path)`: Scans filesystem entries.
2. `read_file(path)`: Reads target source code.
3. `write_file(path, content)`: Creates or updates project files.
4. `run_command(command)`: Executes shell commands with optional user approval.

## Key Capabilities

- **Unified Web Interface:** Single-page dashboard allowing technical reviewers to switch between runtimes on the fly and inspect agent execution outputs.
- **Input Guardrail Defense:** Level 2 features a specialized pre-execution safety classifier (`SafetyCheck`) that screens prompts for destructive commands (e.g. `rm -rf`, dropping directories) and triggers a tripwire before the coding agent ever runs.
- **Cyclical Quality Control:** Level 3 implements a closed-loop review graph where a reviewer node evaluates the coder's output and can reject changes with specific feedback, looping execution back to the coder.
- **Fair-Use Trial & BYOK Gateway:** SQLite-backed rate limiter giving default visitors 3 free Gemini requests per 24 hours, with zero-persistence BYOK support for unlimited user runs.
- **Dual Execution Modes:** Fully functional as standalone CLI terminal agents and via the unified FastAPI web server.

## Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │                   User Request                         │
       │          (via Web UI or Terminal CLI)                  │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                 FastAPI Server Gateway                 │
       │       - Validates Gemini API Key                       │
       │       - Enforces 24-Hour 3-Request Trial (SQLite)      │
       │       - Formats conversation context history           │
       └───────┬───────────────────┼───────────────────┬────────┘
               │                   │                   │
               ▼                   ▼                   ▼
    ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
    │  Level 1: CrewAI   │ │Level 2: Agents SDK │ │Level 3: LangGraph  │
    ├────────────────────┤ ├────────────────────┤ ├────────────────────┤
    │  [Tech Lead]       │ │ [Safety Guardrail] │ │      [START]       │
    │  (Breaks task into │ │ (Blocks destruction)│ │         │          │
    │   numbered steps)  │ │         │          │ │         ▼          │
    │         │          │ │         ▼          │ │     [Triage]       │
    │         ▼          │ │     [Triage]       │ │    /        \      │
    │   [Senior Coder]   │ │    /        \      │ │   ▼          ▼     │
    │  (Applies 4 tools  │ │[Coder]   [Explainer│ │[Coder]    [Explain]│
    │   to build plan)   │ │ (Tools)   (Readonly│ │   │          │     │
    │                    │ │         │          │ │   ▼          ▼     │
    │                    │ │  [SQLite Session]  │ │[Reviewer]   [END]  │
    │                    │ │   (Thread memory)  │ │   │    ▲           │
    │                    │ │                    │ │   │    │ (Changes) │
    │                    │ │                    │ │   └───-┘           │
    │                    │ │                    │ │   (Approved)       │
    │                    │ │                    │ │         │          │
    │                    │ │                    │ │         ▼          │
    │                    │ │                    │ │       [END]        │
    └──────────┬─────────┘ └──────────┬─────────┘ └──────────┬─────────┘
               │                      │                      │
               └──────────────────────┼──────────────────────┘
                                      │
                                      ▼
       ┌────────────────────────────────────────────────────────┐
       │                     Gemini LLM                         │
       │           (gemini-2.5-flash via Google GenAI)          │
       └────────────────────────────────────────────────────────┘
```

## How It Works

### Paradigm 1: CrewAI (Linear Hierarchical Delegation)
- The user request enters `01_crewai/crew.py`.
- The **Tech Lead** agent uses `list_files` and `read_file` to draft a concise, numbered build plan.
- The **Coder** agent receives the plan as task context and executes file modifications and shell commands.
- Ideal for: Straightforward workflows where a clear sequence of steps can be pre-planned.

### Paradigm 2: OpenAI Agents SDK (Handoffs & Safety Tripwires)
- In `02_agents_sdk/handoff_guardrail.py`, every prompt first passes through `block_destructive`.
- A dedicated lightweight `guardrail_agent` evaluates whether the request is destructive. If triggered, execution halts immediately with `InputGuardrailTripwireTriggered`.
- If safe, the `Triage` agent routes requests to either `Coder` (read/write/run) or `Explainer` (read-only), maintaining conversational memory via `SQLiteSession`.

### Paradigm 3: LangGraph (Stateful Graph with Feedback Loops)
- In `03_langgraph/multi_agent.py`, a compiled `StateGraph` manages shared conversation state.
- `triage_node` selects between `coder` and `explainer` using function-calling structured output.
- When `coder` completes work, execution transitions to `reviewer_node`.
- The reviewer inspects files written and commands run. If defects are found, it generates structured feedback and transitions state back to `coder` (capped at `MAX_REVISIONS = 2` to prevent infinite oscillation).

## Technology Stack

### Models
- **Google Gemini 2.5 Flash:** Chosen for fast inference, generous context window, and native function calling capabilities.

### Frameworks & SDKs
- **FastAPI (>=0.115):** Asynchronous REST gateway serving static assets and API routes.
- **CrewAI (>=0.11.2):** Role-based multi-agent orchestration.
- **OpenAI Agents SDK (>=0.4) & OpenAI (>=1.60):** Agent loops, handoffs, and input guardrails using Gemini's OpenAI-compatible endpoint.
- **LangGraph (>=1.0) & LangChain (>=1.0):** State machines, conditional routing edges, and cycles.
- **LangChain Google GenAI (>=2.0):** Native Gemini integration for LangGraph nodes.

### Storage & Session Management
- **SQLite 3:** Lightweight local storage for fair-use trial quotas (`trials.sqlite3`) and agent conversation thread checkpoints.

## Engineering Decisions

1. **Why three distinct framework implementations?**  
   Developers often debate whether to use high-level frameworks (CrewAI), lightweight SDKs (Agents SDK), or explicit graph libraries (LangGraph). Building the exact same tools across all three allows an apples-to-apples comparison of code complexity, execution flow control, and debugging transparency.

2. **Why LangGraph for the reviewer loop?**  
   Review and refinement requires cycles. CrewAI tasks are largely DAG-based, whereas LangGraph natively supports cyclical graphs (`coder -> reviewer -> coder`) with explicit state termination conditions (`state['revisions'] >= MAX_REVISIONS`).

3. **Why SQLite cookies for the trial gateway?**  
   To prevent abuse without requiring user registration, the gateway issues a random `HttpOnly` session cookie mapped to a SQLite usage table (`user_id`, `first_used_at`, `uses`). Users get 3 free calls per 24-hour rolling window.

4. **Why zero-persistence BYOK?**  
   Personal Gemini API keys entered in the modal are stored strictly in browser memory for the current page session. They are passed directly via the POST payload header and never saved in the server's SQLite database or committed to logs.

## Project Structure

```text
Shiny-Agents/
├── README.md               # Architecture and comparative documentation
├── requirements.txt        # Python dependency manifest
├── .env.example            # Environment template for Gemini API key
├── 01_crewai/
│   ├── agent.py            # Level 1 single coding agent with 4 tools
│   └── crew.py             # Level 1 hierarchical crew (Tech Lead + Coder)
├── 02_agents_sdk/
│   ├── agent.py            # Level 2 tool loop agent with SQLite session
│   └── handoff_guardrail.py# Level 2 triage, specialists & safety guardrail
├── 03_langgraph/
│   ├── agent.py            # Level 3 single-agent graph with tool node
│   └── multi_agent.py      # Level 3 multi-agent cyclical graph with Reviewer
├── app/
│   ├── server.py           # FastAPI server, trial limiter & agent runner
│   ├── static/             # Responsive frontend dashboard
│   │   ├── app.js          # Client-side agent selection & BYOK modal
│   │   ├── index.html      # Workspace layout & chat thread
│   │   └── styles.css      # Dark-mode styling matching portfolio theme
│   └── trials.sqlite3      # (Created at runtime) Rolling 24h usage store
└── tests/
    └── test_server_contracts.py # Automated test suite for agent routing & trials
```

## Setup & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.10, 3.11, 3.12, 3.13)
- Google Gemini API Key

### Installation
From the repository root:
```bash
cd Shiny-Agents
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration
Create your local `.env` file:
```bash
cp .env.example .env
```
Add your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Usage

### 1. Launching the Web Workspace
```bash
uvicorn app.server:app --reload --port 8000
```
Open [http://localhost:8000](http://localhost:8000) to chat with the active agent, toggle between CrewAI, Agents SDK, and LangGraph, and manage your Gemini key.

### 2. Direct Terminal Execution
Each agent can be run standalone directly in your terminal:
```bash
# Level 1: CrewAI Team
AGENT_REQUEST="Create a helper function to format timestamps" python 01_crewai/crew.py

# Level 2: Agents SDK with Guardrail
python 02_agents_sdk/handoff_guardrail.py

# Level 3: LangGraph Cyclical Review Graph
AGENT_REQUEST="Refactor error handling in server.py" python 03_langgraph/multi_agent.py
```

### 3. Running Automated Tests
```bash
python -m unittest tests/test_server_contracts.py
```

## Comparative Framework Evaluation

| Dimension | Level 1: CrewAI | Level 2: Agents SDK | Level 3: LangGraph |
| :--- | :--- | :--- | :--- |
| **Orchestration Model** | Role & Task Declarative | Function Tools & Event Loop | Explicit Node-Edge State Machine |
| **Flow Control** | Sequential DAG | Routing Handoffs | Cyclical Graphs with Conditional Edges |
| **Error / Critique Loop** | Retries per task | Tool error recovery | Closed-loop Reviewer with revision limit |
| **Safety Guardrails** | Prompt instructions | Pre-execution Guardrail Agent | Dedicated Triage validation node |
| **State Persistence** | Transient memory | `SQLiteSession` | `InMemorySaver` / `SqliteSaver` |
| **Best Suited For** | Fast team prototyping | Lightweight CLI tools | Mission-critical apps needing deterministic review loops |

## Limitations

- **Subprocess Isolation:** The web server runs each agent execution in a subprocess with a 180-second timeout. While this isolates crashes, it incurs process startup overhead per web request.
- **Shell Command Safety:** Shell execution uses `AGENT_AUTO_APPROVE=1` in web mode. Destructive actions are screened by the guardrail in Level 2, but Level 1 relies on prompt discipline.
- **Process-Local Trial Store:** `trials.sqlite3` is stored on the local filesystem, which resets if deployed on ephemeral container runtimes without persistent volumes.

## Future Improvements

- Streaming SSE (Server-Sent Events) tokens directly from agent stdout to the web UI.
- Docker sandbox containerization for executing `run_command` in an isolated virtual filesystem.
- Adding a fourth paradigm using AutoGen or Semantic Kernel for multi-modal code review.

## License

MIT License. Developed by Vignesh K N.
