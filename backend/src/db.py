import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "kisan_sahay.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_name TEXT NOT NULL,
            reason_category TEXT NOT NULL,
            summary TEXT NOT NULL,
            urgency TEXT NOT NULL,
            language TEXT,
            follow_up_method TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL,
            farmer_name TEXT,
            outcome TEXT NOT NULL DEFAULT 'in_progress',
            reason TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def normalize_user_id(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def get_user(user_id: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "language_preference": row["language_preference"],
        "facts": json.loads(row["facts"]) if row["facts"] else {},
        "last_interaction": row["last_interaction"],
    }


def save_user(user_id: str, name: str, language_preference: str, facts: dict):
    conn = get_connection()
    existing = conn.execute(
        "SELECT facts FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()

    merged_facts = {}
    if existing and existing["facts"]:
        merged_facts = json.loads(existing["facts"])
    merged_facts.update(facts)

    conn.execute(
        """
        INSERT INTO users (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name,
            language_preference = excluded.language_preference,
            facts = excluded.facts,
            last_interaction = excluded.last_interaction
        """,
        (
            user_id,
            name,
            language_preference,
            json.dumps(merged_facts),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def delete_user(user_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def create_escalation(
    farmer_name: str,
    reason_category: str,
    summary: str,
    urgency: str,
    language: str = "",
    follow_up_method: str = "",
) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO escalations
            (farmer_name, reason_category, summary, urgency, language, follow_up_method, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'open', ?)
        """,
        (
            farmer_name,
            reason_category,
            summary,
            urgency,
            language,
            follow_up_method,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    escalation_id = cursor.lastrowid
    conn.close()
    return escalation_id


def get_open_escalations():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM escalations WHERE status = 'open' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_escalations():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM escalations ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def resolve_escalation(escalation_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE escalations SET status = 'resolved' WHERE id = ?", (escalation_id,)
    )
    conn.commit()
    conn.close()


def start_call(channel: str, farmer_name: str = "") -> int:
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO calls (channel, farmer_name, outcome, started_at)
        VALUES (?, ?, 'in_progress', ?)
        """,
        (channel, farmer_name, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    call_id = cursor.lastrowid
    conn.close()
    return call_id


def finish_call(call_id: int, outcome: str, reason: str = "", farmer_name: str = ""):
    conn = get_connection()
    if farmer_name:
        conn.execute(
            """
            UPDATE calls SET outcome = ?, reason = ?, ended_at = ?, farmer_name = ?
            WHERE id = ?
            """,
            (outcome, reason, datetime.now(timezone.utc).isoformat(), farmer_name, call_id),
        )
    else:
        conn.execute(
            """
            UPDATE calls SET outcome = ?, reason = ?, ended_at = ?
            WHERE id = ?
            """,
            (outcome, reason, datetime.now(timezone.utc).isoformat(), call_id),
        )
    conn.commit()
    conn.close()


def get_call_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM calls").fetchone()[0]
    success = conn.execute("SELECT COUNT(*) FROM calls WHERE outcome = 'success'").fetchone()[0]
    failed = conn.execute("SELECT COUNT(*) FROM calls WHERE outcome = 'failure'").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM calls WHERE outcome = 'in_progress'").fetchone()[0]
    conn.close()
    return {"total": total, "success": success, "failed": failed, "in_progress": in_progress}


def get_recent_calls(limit: int = 25):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM calls ORDER BY started_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]