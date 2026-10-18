"""Keyword retrieval over memory. No embeddings, no external service."""

from __future__ import annotations

import sqlite3
from typing import Any


def keyword_search(conn: sqlite3.Connection, query: str, limit: int = 8) -> list[dict[str, Any]]:
    terms = [t for t in query.lower().split() if t]
    if not terms:
        return []

    results: list[dict[str, Any]] = []

    rows = conn.execute(
        "SELECT id, category, content, provenance, created_at FROM observations "
        "ORDER BY created_at DESC LIMIT 200"
    ).fetchall()
    for r in rows:
        text = r["content"].lower()
        score = sum(text.count(t) for t in terms)
        if score:
            results.append(
                {
                    "kind": "observation",
                    "category": r["category"],
                    "content": r["content"],
                    "provenance": r["provenance"],
                    "created_at": r["created_at"],
                    "score": score,
                }
            )

    rows = conn.execute(
        "SELECT decision, rationale, created_at FROM decisions ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    for r in rows:
        text = (r["decision"] + " " + (r["rationale"] or "")).lower()
        score = sum(text.count(t) for t in terms) + 1  # decisions are high-signal
        if score > 1:
            results.append(
                {
                    "kind": "decision",
                    "category": "semantic",
                    "content": r["decision"],
                    "provenance": r["rationale"],
                    "created_at": r["created_at"],
                    "score": score,
                }
            )

    rows = conn.execute(
        "SELECT id, goal, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    for r in rows:
        text = r["goal"].lower()
        score = sum(text.count(t) for t in terms)
        if score:
            results.append(
                {
                    "kind": "task",
                    "category": "episodic",
                    "content": f"[{r['status']}] {r['goal']} ({r['id']})",
                    "provenance": "task history",
                    "created_at": r["created_at"],
                    "score": score,
                }
            )

    results.sort(key=lambda x: (x["score"], x["created_at"]), reverse=True)
    return results[:limit]
