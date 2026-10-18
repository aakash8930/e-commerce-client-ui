"""Workflow B — Code change verification.

Inspect git status, run the test suite, capture failures, summarize
potential regressions. Generates a report only — never commits or pushes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.action import Action
from core.orchestrator import Orchestrator


def verify_changes(orchestrator: Orchestrator, project_path: str, reports_dir: str, task_id: str = "adhoc") -> dict:
    result, _ = orchestrator.run_action(
        Action(
            tool="terminal.run",
            arguments={"command": "git", "args": ["status", "--short"], "cwd": project_path},
            reason="Inspect repository state",
        ),
        task_id=task_id,
    )
    changed = result.data.get("stdout", "") if result.ok else f"(git status failed: {result.error})"

    tests, _ = orchestrator.run_action(
        Action(tool="project.run_tests", arguments={"path": project_path}, reason="Run tests"),
        task_id=task_id,
    )

    report = {
        "project": project_path,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "changed_files": changed.strip().splitlines(),
        "tests_passed": tests.data.get("passed") if tests.ok else False,
        "failures": tests.data.get("failures", []) if tests.ok else [],
        "note": "Verification only — nothing was committed or pushed.",
    }

    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = reports / f"{stamp}-verification.md"
    path.write_text(
        "# Change verification\n\n"
        f"Generated: {report['generated_at']}\n\n"
        f"## Changed files\n{changed or '(clean)'}\n\n"
        f"## Tests passing: {report['tests_passed']}\n\n"
        "## Failures\n"
        + "\n".join(f"- `{f.get('test')}`: {f.get('error', '')[:200]}" for f in report["failures"])
        + f"\n\n{report['note']}\n",
        encoding="utf-8",
    )
    report["report_path"] = str(path)
    orchestrator.memory.add_observation(
        content=f"Verified changes in {project_path}: tests {'passed' if report['tests_passed'] else 'failed'}",
        category="episodic",
        provenance=f"workflow:code_verification:{task_id}",
    )
    return report
