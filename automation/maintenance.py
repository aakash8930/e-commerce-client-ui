"""Workflow D — Recurring local maintenance report.

Checks disk space, memory and project folders; identifies stale temporary
files WITHOUT deleting anything. Reports only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.action import Action
from core.orchestrator import Orchestrator


def maintenance_report(orchestrator: Orchestrator, project_path: str, reports_dir: str, task_id: str = "adhoc") -> dict:
    df, _ = orchestrator.run_action(
        Action(tool="terminal.run", arguments={"command": "df", "args": [], "cwd": "."}, reason="Disk usage"),
        task_id=task_id,
    )
    free, _ = orchestrator.run_action(
        Action(tool="terminal.run", arguments={"command": "free", "args": [], "cwd": "."}, reason="Memory usage"),
        task_id=task_id,
    )
    sysinfo, _ = orchestrator.run_action(
        Action(tool="system.info", arguments={}, reason="System snapshot"),
        task_id=task_id,
    )

    stale: list[str] = []
    root = Path(project_path)
    if root.is_dir():
        for pattern in ("__pycache__", ".pytest_cache", "*.tmp", "*.log", ".DS_Store"):
            for fp in root.rglob(pattern):
                if fp.is_file() or fp.is_dir():
                    stale.append(str(fp))
                if len(stale) >= 40:
                    break

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "disk": df.data.get("stdout", "") if df.ok else "unavailable",
        "memory": free.data.get("stdout", "") if free.ok else "unavailable",
        "system": sysinfo.data if sysinfo.ok else {},
        "stale_candidates": stale,
        "note": "Identified only — nothing was deleted.",
    }

    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = reports / f"{stamp}-maintenance.md"
    path.write_text(
        "# Maintenance report\n\n"
        f"Generated: {report['generated_at']}\n\n"
        f"## Disk\n```\n{report['disk']}\n```\n\n"
        f"## Memory\n```\n{report['memory']}\n```\n\n"
        f"## Stale candidates (not deleted)\n"
        + "\n".join(f"- `{s}`" for s in report["stale_candidates"][:40] or ["(none found)"])
        + f"\n\n{report['note']}\n",
        encoding="utf-8",
    )
    report["report_path"] = str(path)
    return report
