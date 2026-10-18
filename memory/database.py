"""SQLite memory: tasks, steps, tool runs, observations, projects.

Designed per the roadmap schema. One connection per MemoryDB instance,
WAL mode, and explicit transactions. Nothing here plans tasks — it only
persists and answers queries.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  root_path TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  goal TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  completed_at TEXT
);
CREATE TABLE IF NOT EXISTS task_steps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT NOT NULL REFERENCES tasks(id),
  sequence INTEGER NOT NULL,
  objective TEXT NOT NULL,
  action TEXT NOT NULL,
  status TEXT NOT NULL,
  detail TEXT
);
CREATE TABLE IF NOT EXISTS observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER REFERENCES projects(id),
  category TEXT NOT NULL,
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  provenance TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER REFERENCES projects(id),
  decision TEXT NOT NULL,
  rationale TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS tool_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT,
  tool_name TEXT NOT NULL,
  status TEXT NOT NULL,
  duration_ms INTEGER,
  detail TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_obs_hash ON observations(content_hash);
CREATE INDEX IF NOT EXISTS idx_obs_project ON observations(project_id);
CREATE INDEX IF NOT EXISTS idx_tool_runs_task ON tool_runs(task_id);
"""


class MemoryDBError(Exception):
    """A core state write failed (e.g. the database is locked)."""


class MemoryDB:
    def __init__(self, db_path: str | Path) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), timeout=5.0)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self.conn.executescript(SCHEMA)
        # lightweight migration for DBs created before the error column existed
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(tasks)")]
        if "error" not in cols:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN error TEXT")
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ------------------------------------------------------------- projects

    def register_project(self, root_path: str, name: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO projects (root_path, name) VALUES (?, ?) "
            "ON CONFLICT(root_path) DO UPDATE SET name=excluded.name",
            (root_path, name),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM projects WHERE root_path = ?", (root_path,)
        ).fetchone()
        return int(row["id"])

    def list_projects(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def find_project(self, query: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM projects WHERE root_path LIKE ? OR name LIKE ?",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
        return [dict(r) for r in rows]

    # ---------------------------------------------------------------- tasks

    def create_task(self, task_id: str, goal: str) -> None:
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO tasks (id, goal, status, created_at) VALUES (?, ?, ?, datetime('now'))",
                (task_id, goal, "created"),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise MemoryDBError(f"cannot record task {task_id}: {exc}") from exc

    def set_task_state(self, task_id: str, status: str, error: str | None = None) -> None:
        completed = "datetime('now')" if status in {"succeeded", "failed", "cancelled"} else "NULL"
        try:
            self.conn.execute(
                f"UPDATE tasks SET status = ?, error = ?, completed_at = {completed} WHERE id = ?",
                (status, error, task_id),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise MemoryDBError(f"cannot update task {task_id}: {exc}") from exc

    def log_step(self, task_id: str, sequence: int, objective: str, action: dict, status: str, detail: str = "") -> None:
        try:
            self.conn.execute(
                "INSERT INTO task_steps (task_id, sequence, objective, action, status, detail) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, sequence, objective, json.dumps(action), status, detail),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise MemoryDBError(f"cannot record step for task {task_id}: {exc}") from exc

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            return None
        steps = self.conn.execute(
            "SELECT * FROM task_steps WHERE task_id = ? ORDER BY sequence", (task_id,)
        ).fetchall()
        out = dict(row)
        out["steps"] = [dict(s) for s in steps]
        return out

    def list_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # --------------------------------------------------- observations etc.

    def add_observation(
        self,
        content: str,
        category: str = "episodic",
        project_id: int | None = None,
        provenance: str | None = None,
    ) -> int | None:
        """Store a memory fact. Deduplicates on content hash.

        Never raises: observation logging must not take down a running task.
        """
        import hashlib

        try:
            h = hashlib.sha256(content.encode("utf-8")).hexdigest()
            existing = self.conn.execute(
                "SELECT id FROM observations WHERE content_hash = ?", (h,)
            ).fetchone()
            if existing:
                return None  # duplicate — do not store twice
            cur = self.conn.execute(
                "INSERT INTO observations (project_id, category, content, content_hash, provenance) "
                "VALUES (?, ?, ?, ?, ?)",
                (project_id, category, content, h, provenance),
            )
            self.conn.commit()
            return int(cur.lastrowid)
        except sqlite3.Error:
            return None

    def add_decision(self, decision: str, rationale: str = "", project_id: int | None = None) -> None:
        try:
            self.conn.execute(
                "INSERT INTO decisions (project_id, decision, rationale) VALUES (?, ?, ?)",
                (project_id, decision, rationale),
            )
            self.conn.commit()
        except sqlite3.Error:
            pass

    def log_tool_run(self, task_id: str | None, tool_name: str, status: str, duration_ms: int, detail: str = "") -> None:
        try:
            self.conn.execute(
                "INSERT INTO tool_runs (task_id, tool_name, status, duration_ms, detail) "
                "VALUES (?, ?, ?, ?, ?)",
                (task_id, tool_name, status, duration_ms, detail),
            )
            self.conn.commit()
        except sqlite3.Error:
            pass  # audit logging must never crash execution

    def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        """Keyword search across observations and decisions, ranked by
        match count and recency."""
        from memory import retrieval

        return retrieval.keyword_search(self.conn, query, limit=limit)
