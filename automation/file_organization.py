"""Workflow C — Document and file organization.

Roadmap flow:
  scan an approved directory → identify files by extension/size/metadata →
  propose a folder structure → preview planned moves → apply approved
  changes → verify files exist at their destinations.

Nothing is moved without explicit approval. Moves go through the
filesystem.move tool (high risk → policy-enforced approval), and every
move is verified afterwards. No file is ever deleted.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.action import Action
from core.orchestrator import Orchestrator

CATEGORY_RULES: dict[str, list[str]] = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".md", ".odt", ".rtf"],
    "Images": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico"],
    "Archives": [".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".tgz"],
    "Code": [".py", ".js", ".ts", ".sh", ".c", ".cpp", ".h", ".java", ".html", ".css", ".go", ".rs"],
    "Data": [".csv", ".json", ".xml", ".sql", ".xlsx", ".xls", ".toml", ".yaml", ".yml"],
    "Audio-Video": [".mp3", ".wav", ".flac", ".mp4", ".mkv", ".avi", ".mov", ".webm"],
}

CATEGORY_ORDER = list(CATEGORY_RULES) + ["Other"]


def categorize(ext: str) -> str:
    ext = ext.lower()
    for category, exts in CATEGORY_RULES.items():
        if ext in exts:
            return category
    return "Other"


def build_plan(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Propose moves for top-level files (already-organized dirs untouched)."""
    plan = []
    for f in files:
        category = categorize(f.get("ext", ""))
        plan.append(
            {
                "name": f["name"],
                "category": category,
                "dest": f"{category}/{f['name']}",
                "size": f.get("size", 0),
            }
        )
    return plan


def organize_files(
    orchestrator: Orchestrator,
    target_dir: str,
    reports_dir: str,
    approve: Callable[[list[dict[str, Any]]], bool],
    task_id: str = "adhoc",
) -> dict[str, Any]:
    """Run Workflow C. `approve` receives the move plan and returns whether
    to apply it (False → preview-only report)."""

    # 1. scan (tool action — policy-checked)
    catalog_result, _ = orchestrator.run_action(
        Action(tool="filesystem.catalog", arguments={"path": target_dir}, reason="Inventory the directory"),
        task_id=task_id,
    )
    if not catalog_result.ok:
        raise RuntimeError(f"cannot scan directory: {catalog_result.error}")
    files = catalog_result.data.get("files", [])
    dirs = catalog_result.data.get("dirs", [])

    # 2. propose
    plan = build_plan(files)

    # 3. consent (single decision for the batch)
    apply_changes = bool(plan) and approve(plan)

    moves_applied: list[dict[str, Any]] = []
    moves_failed: list[dict[str, Any]] = []
    verified = 0

    if apply_changes:
        root = Path(target_dir)
        for item in plan:
            source = str(root / item["name"])
            dest = str(root / item["dest"])
            result, refusal = orchestrator.run_action(
                Action(
                    tool="filesystem.move",
                    arguments={"source": source, "dest": dest},
                    reason=f"Organize {item['name']} into {item['category']}/",
                ),
                task_id=task_id,
            )
            if result.ok:
                # 4. verify the file exists at its destination
                dest_exists = Path(dest).exists()
                source_gone = not Path(source).exists()
                if dest_exists and source_gone:
                    verified += 1
                    moves_applied.append(item)
                else:
                    moves_failed.append({**item, "error": "post-move verification failed"})
            else:
                moves_failed.append({**item, "error": result.error or refusal or "refused"})

    report = {
        "target": str(target_dir),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "existing_dirs": dirs,
        "planned_moves": plan,
        "applied": apply_changes,
        "moves_applied": moves_applied,
        "moves_failed": moves_failed,
        "verified": verified,
        "note": "No files were deleted. Preview only — nothing moved."
        if not apply_changes
        else f"{verified}/{len(plan)} moves verified at their destinations.",
    }

    # 5. report + memory
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = reports / f"{stamp}-organization.md"
    path.write_text(_render(report), encoding="utf-8")
    report["report_path"] = str(path)

    orchestrator.memory.add_observation(
        content=(
            f"Organized {target_dir}: {'applied' if apply_changes else 'preview only'}, "
            f"{len(plan)} files planned, {verified} moves verified"
        ),
        category="procedural",
        provenance=f"workflow:file_organization:{task_id}",
    )
    return report


def _render(r: dict[str, Any]) -> str:
    lines = [
        f"# File organization — {r['target']}",
        "",
        f"Generated: {r['generated_at']}",
        f"Mode: {'APPLIED' if r['applied'] else 'PREVIEW ONLY'}",
        "",
        "## Planned moves",
    ]
    for m in r["planned_moves"]:
        status = "moved" if m in r["moves_applied"] else ("failed: " + m.get("error", "?") if m in r["moves_failed"] else "pending")
        lines.append(f"- `{m['name']}` → `{m['dest']}` ({m['category']}, {m['size']} B) [{status}]")
    lines += ["", f"## Result: {r['note']}", ""]
    return "\n".join(lines)
