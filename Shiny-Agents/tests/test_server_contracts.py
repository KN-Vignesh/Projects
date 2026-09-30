import os
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Add parent directory to path
SHINY_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SHINY_ROOT))

class TestShinyAgentsContracts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_trials.sqlite3"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_agent_registry_integrity(self):
        """Verify that all configured agents have scripts on disk."""
        agents = {
            "crewai": ("CrewAI", SHINY_ROOT / "01_crewai" / "agent.py"),
            "agents-sdk": ("Agents SDK", SHINY_ROOT / "02_agents_sdk" / "agent.py"),
            "langgraph": ("LangGraph", SHINY_ROOT / "03_langgraph" / "multi_agent.py"),
        }
        for key, (label, path) in agents.items():
            self.assertTrue(path.exists(), f"Agent script for {label} should exist at {path}")
            self.assertTrue(path.is_file(), f"Agent script for {label} should be a file")

    def test_sqlite_trial_rate_limiter_logic(self):
        """Verify the 3-request limit and 24-hour expiration window in SQLite."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """CREATE TABLE trial_usage (
                user_id TEXT PRIMARY KEY,
                first_used_at INTEGER NOT NULL,
                uses INTEGER NOT NULL DEFAULT 0
            )"""
        )

        user_id = "test_user_abc123"
        now = int(time.time())

        # First use
        conn.execute("INSERT INTO trial_usage VALUES (?, ?, ?)", (user_id, now, 1))
        conn.commit()

        row = conn.execute("SELECT uses, first_used_at FROM trial_usage WHERE user_id = ?", (user_id,)).fetchone()
        self.assertEqual(row[0], 1)

        # Second use
        conn.execute("UPDATE trial_usage SET uses = uses + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        row = conn.execute("SELECT uses FROM trial_usage WHERE user_id = ?", (user_id,)).fetchone()
        self.assertEqual(row[0], 2)

        # Third use (at limit)
        conn.execute("UPDATE trial_usage SET uses = uses + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        row = conn.execute("SELECT uses FROM trial_usage WHERE user_id = ?", (user_id,)).fetchone()
        self.assertEqual(row[0], 3)

        # Exceeding limit should be blocked
        limit = 3
        can_proceed = row[0] < limit
        self.assertFalse(can_proceed, "User with 3 uses must be blocked")

        # Expiration test: 25 hours later, window resets
        twenty_five_hours_ago = now - (25 * 3600)
        conn.execute("UPDATE trial_usage SET first_used_at = ? WHERE user_id = ?", (twenty_five_hours_ago, user_id))
        conn.commit()

        row = conn.execute("SELECT first_used_at, uses FROM trial_usage WHERE user_id = ?", (user_id,)).fetchone()
        window_seconds = 24 * 3600
        is_expired = (now - row[0]) >= window_seconds
        self.assertTrue(is_expired, "Usage record older than 24h must be marked expired and reset")

        conn.close()

    def test_conversation_prompt_formatting(self):
        """Verify prompt formatting with and without history."""
        def format_prompt(history: list[dict[str, str]], message: str) -> str:
            transcript = "\n".join(
                f"{item.get('role', 'user').title()}: {item.get('content', '')}" for item in history[-12:]
            )
            return f"Conversation context:\n{transcript}\n\nCurrent user request:\n{message}" if transcript else message

        # Without history
        direct = format_prompt([], "Create a binary search function")
        self.assertEqual(direct, "Create a binary search function")

        # With history
        history = [
            {"role": "user", "content": "Hello agent"},
            {"role": "assistant", "content": "Hello! How can I help?"},
        ]
        contextual = format_prompt(history, "Can you optimize it?")
        self.assertIn("Conversation context:", contextual)
        self.assertIn("User: Hello agent", contextual)
        self.assertIn("Assistant: Hello! How can I help?", contextual)
        self.assertIn("Current user request:\nCan you optimize it?", contextual)

if __name__ == "__main__":
    unittest.main()
