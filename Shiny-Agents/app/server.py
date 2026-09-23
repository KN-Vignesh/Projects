import json
import os
import secrets
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DEFAULT_KEY = os.getenv("GEMINI_API_KEY")
TRIAL_LIMIT = 3
WINDOW_SECONDS = 24 * 60 * 60
DB_PATH = Path(os.getenv("TRIAL_DB_PATH", ROOT / "app" / "trials.sqlite3"))

AGENTS = {
    "crewai": ("CrewAI", ROOT / "01_crewai" / "agent.py"),
    "agents-sdk": ("Agents SDK", ROOT / "02_agents_sdk" / "agent.py"),
    "langgraph": ("LangGraph", ROOT / "03_langgraph" / "multi_agent.py"),
}

app = FastAPI(title="Shiny Agents")
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")


class ChatRequest(BaseModel):
    agent: str
    message: str
    history: list[dict[str, str]] = Field(default_factory=list)
    api_key: str | None = None


class KeyRequest(BaseModel):
    api_key: str


def db_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute(
        """CREATE TABLE IF NOT EXISTS trial_usage (
            user_id TEXT PRIMARY KEY,
            first_used_at INTEGER NOT NULL,
            uses INTEGER NOT NULL DEFAULT 0
        )"""
    )
    return connection


def user_id_for(request: Request) -> tuple[str, bool]:
    user_id = request.cookies.get("shiny_agents_user")
    if user_id:
        return user_id, False
    return secrets.token_urlsafe(32), True


def trial_status(user_id: str) -> tuple[int, int | None]:
    now = int(time.time())
    with db_connection() as connection:
        row = connection.execute(
            "SELECT first_used_at, uses FROM trial_usage WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row or now - row[0] >= WINDOW_SECONDS:
        return 0, None
    return row[1], row[0]


def consume_trial(user_id: str) -> tuple[int, int]:
    now = int(time.time())
    connection = db_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT first_used_at, uses FROM trial_usage WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row or now - row[0] >= WINDOW_SECONDS:
            uses = 1
            connection.execute(
                "INSERT INTO trial_usage(user_id, first_used_at, uses) VALUES (?, ?, ?)",
                (user_id, now, uses),
            )
            connection.commit()
            return uses, now
        if row[1] >= TRIAL_LIMIT:
            connection.rollback()
            raise HTTPException(status_code=429, detail="Trial limit reached. Connect your Gemini API key to continue.")
        uses = row[1] + 1
        connection.execute("UPDATE trial_usage SET uses = ? WHERE user_id = ?", (uses, user_id))
        connection.commit()
        return uses, row[0]
    finally:
        connection.close()


def validate_gemini_key(api_key: str) -> bool:
    key = (api_key or "").strip()
    if not key:
        return False
    body = json.dumps({"contents": [{"parts": [{"text": "ping"}]}]}).encode("utf-8")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        f"?key={urllib.parse.quote(key)}"
    )
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            return response.status in (200, 201)
    except (HTTPError, URLError, ValueError):
        return False
    except Exception:
        return False


def conversation_prompt(history: list[dict[str, str]], message: str) -> str:
    transcript = "\n".join(
        f"{item.get('role', 'user').title()}: {item.get('content', '')}" for item in history[-12:]
    )
    return f"Conversation context:\n{transcript}\n\nCurrent user request:\n{message}" if transcript else message


def run_agent(agent: str, prompt: str, api_key: str) -> str:
    _, script = AGENTS[agent]
    environment = os.environ.copy()
    # The subprocess runs from the selected agent folder, so a relative PYTHONPATH
    # would stop resolving the shared runtime dependencies after cwd changes.
    runtime_path = ROOT / ".runtime"
    if runtime_path.is_dir():
        existing_pythonpath = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = os.pathsep.join(
            path for path in (str(runtime_path), existing_pythonpath) if path
        )
    environment["GEMINI_API_KEY"] = api_key
    environment["AGENT_REQUEST"] = prompt
    environment["AGENT_AUTO_APPROVE"] = "1"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=script.parent,
        env=environment,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        if "ModuleNotFoundError" in detail or "ImportError" in detail:
            raise HTTPException(
                status_code=503,
                detail="This agent runtime is not installed on the server. Install requirements.txt and restart the app.",
            )
        raise HTTPException(status_code=502, detail="The selected agent could not complete the request. Please try again.")
    return result.stdout.strip()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "app" / "static" / "index.html")


@app.get("/api/usage")
def usage(request: Request, response: Response) -> dict[str, int | bool | str]:
    user_id, is_new = user_id_for(request)
    uses, _ = trial_status(user_id)
    remaining = max(TRIAL_LIMIT - uses, 0)
    payload = {
        "uses": uses,
        "limit": TRIAL_LIMIT,
        "remaining": remaining,
        "has_default_key": bool(DEFAULT_KEY),
        "status": "trial_active" if DEFAULT_KEY and remaining > 0 else "trial_exhausted" if DEFAULT_KEY else "default_key_missing",
    }
    if is_new:
        response.set_cookie("shiny_agents_user", user_id, httponly=True, samesite="lax", secure=False, max_age=WINDOW_SECONDS)
    return payload


@app.post("/api/validate-key")
def validate_key(payload: KeyRequest) -> dict[str, bool | str]:
    api_key = (payload.api_key or "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API key is required.")
    if not validate_gemini_key(api_key):
        raise HTTPException(status_code=400, detail="Gemini key couldn't be validated. Check the key and try again.")
    return {"valid": True, "message": "Gemini key validated."}


@app.post("/api/chat")
def chat(payload: ChatRequest, request: Request, response: Response) -> dict[str, int | str | bool]:
    if payload.agent not in AGENTS:
        raise HTTPException(status_code=400, detail="Unknown agent")
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    user_id, is_new = user_id_for(request)
    personal_key = (payload.api_key or "").strip() or None
    if personal_key:
        if not validate_gemini_key(personal_key):
            raise HTTPException(status_code=400, detail="Gemini key couldn't be validated. Check the key and try again.")
        api_key = personal_key
        uses, _ = trial_status(user_id)
    else:
        if not DEFAULT_KEY:
            raise HTTPException(status_code=503, detail="Gemini connection required. Add a server-side key or connect your personal Gemini key.")
        uses, _ = trial_status(user_id)
        if uses >= TRIAL_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="You have used your 3 sponsored requests. Connect your Gemini API key to continue.",
            )
        uses, _ = consume_trial(user_id)
        api_key = DEFAULT_KEY

    if is_new:
        response.set_cookie("shiny_agents_user", user_id, httponly=True, samesite="lax", secure=False, max_age=WINDOW_SECONDS)

    output = run_agent(payload.agent, conversation_prompt(payload.history, payload.message), api_key)
    remaining = max(TRIAL_LIMIT - uses, 0)
    return {
        "agent": AGENTS[payload.agent][0],
        "output": output,
        "uses": uses,
        "limit": TRIAL_LIMIT,
        "remaining": remaining,
        "byok": bool(personal_key),
    }
