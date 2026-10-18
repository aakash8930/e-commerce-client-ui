"""Workflow A — Project diagnosis.

Input: a project path (and optional error hint).
Output: an evidence-driven report — actual files and actual test output,
never invented architecture. Inter-step analysis is deterministic and
rule-based; every file/test operation goes through the orchestrator.

Flow:
  scan project → run tests → extract failure evidence → locate symbols →
  read implicated sources → compose report → save report + memory.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.action import Action
from core.orchestrator import Orchestrator
from core.task import Plan, PlanStep


def _extract_symbol_and_file(failures: list[dict[str, Any]], project_path: str) -> tuple[str | None, str | None]:
    """From structured failures, find the failing test symbol and its file."""
    for f in failures:
        test = f.get("test") or ""
        # pytest node id: tests/test_x.py::test_y
        m = re.search(r"([\w./-]+\.py)::(\w+)", test)
        if m:
            fp, sym = m.group(1), m.group(2)
            full = fp if fp.startswith("/") else str(Path(project_path) / fp)
            return sym, full
        if f.get("file"):
            sym = (test.split("::")[-1] if "::" in test else test) or None
            fp = f["file"]
            full = fp if str(fp).startswith("/") else str(Path(project_path) / fp)
            return sym, full
    return None, None


def _error_evidence(failures: list[dict[str, Any]], output: str) -> list[str]:
    lines = []
    for f in failures[:3]:
        if f.get("error"):
            lines.append(f"{f['test']}: {f['error']}")
    for line in output.splitlines():
        if re.match(r"^E\s+", line) and len(lines) < 8:
            lines.append(line.strip())
    return lines


def diagnose(
    orchestrator: Orchestrator,
    project_path: str,
    reports_dir: str,
    error_hint: str | None = None,
    task_id: str = "adhoc",
) -> dict[str, Any]:
    """Run the diagnosis workflow end-to-end and return the report dict."""
    steps_out: list[dict[str, Any]] = []

    def do(action: Action) -> dict[str, Any]:
        result, refusal = orchestrator.run_action(action, task_id=task_id)
        steps_out.append(
            {"tool": action.tool, "ok": result.ok, "error": result.error, "data_keys": list(result.data)}
        )
        if not result.ok:
            raise RuntimeError(f"diagnosis step failed: {result.error}")
        return result.data

    # 1. project map
    scan = do(Action(tool="project.scan", arguments={"path": project_path}, reason="Map the project"))

    # 2. test evidence
    tests = do(
        Action(
            tool="project.run_tests",
            arguments={"path": project_path},
            reason="Run tests to capture real failure evidence",
        )
    )
    failures = tests.get("failures", [])
    output = tests.get("output", "")

    symbol, failing_file = _extract_symbol_and_file(failures, project_path)
    if error_hint and not symbol:
        # use the hint to search for a symbol
        m = re.search(r"\b(\w+)\b", error_hint)
        symbol = m.group(1) if m else None

    # 3. locate the failing code
    symbol_info: dict[str, Any] = {}
    if symbol:
        symbol_info = do(
            Action(
                tool="project.find_symbol",
                arguments={"path": project_path, "name": symbol},
                reason=f"Locate code for failing symbol {symbol!r}",
            )
        )
        if not failing_file and symbol_info.get("definitions"):
            failing_file = symbol_info["definitions"][0]["path"]

    # 4. read the implicated source as evidence
    source_excerpt = ""
    if failing_file:
        try:
            src = do(
                Action(
                    tool="filesystem.read_text",
                    arguments={"path": failing_file},
                    reason="Read the implicated source file as evidence",
                )
            )
            source_excerpt = src.get("content", "")[:4000]
        except RuntimeError:
            source_excerpt = ""

    # 5. compose an evidence-based report (rule-based synthesis)
    passed = tests.get("passed", False)
    evidence = _error_evidence(failures, output)

    if passed:
        cause = "The test suite currently passes — no failing test to diagnose."
    elif evidence:
        cause = (
            f"The failing evidence points to: {evidence[0] if evidence else 'see test output'}. "
            f"{'Failing file: ' + failing_file if failing_file else ''}"
        )
    else:
        cause = "Tests failed but no structured failure was extracted — see raw output."

    report = {
        "project": scan.get("root", project_path),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "test_passed": passed,
        "exit_code": tests.get("exit_code"),
        "failing_tests": failures,
        "evidence": evidence,
        "failing_symbol": symbol,
        "failing_file": failing_file,
        "cause_analysis": cause,
        "source_excerpt": source_excerpt[:2000],
        "proposal": (
            "Minimal fix: correct the logic at the failing location above, "
            "then re-run `python3 -m pytest` to verify. No file has been modified."
        )
        if not passed
        else "No change needed.",
        "steps": steps_out,
    }

    # 6. persist report
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report_path = reports / f"{stamp}-diagnosis.md"
    report_path.write_text(_render_markdown(report), encoding="utf-8")
    report["report_path"] = str(report_path)

    # 7. remember the outcome
    orchestrator.memory.add_observation(
        content=(
            f"Diagnosed project {scan.get('root', project_path)}: "
            f"tests {'passed' if passed else 'failed'}"
            + (f", failing symbol {symbol}" if symbol else "")
            + (f", file {failing_file}" if failing_file else "")
        ),
        category="episodic",
        provenance=f"workflow:project_diagnosis:{task_id}",
    )
    return report


def _render_markdown(r: dict[str, Any]) -> str:
    lines = [
        f"# Project diagnosis — {r['project']}",
        "",
        f"Generated: {r['generated_at']}",
        "",
        "## Result",
        f"- Tests passing: **{r['test_passed']}** (exit code {r['exit_code']})",
        f"- Failing symbol: `{r.get('failing_symbol') or 'n/a'}`",
        f"- Implicated file: `{r.get('failing_file') or 'n/a'}`",
        "",
        "## Cause analysis (evidence-based)",
        r["cause_analysis"],
        "",
        "## Evidence",
    ]
    for e in r["evidence"] or ["(none captured)"]:
        lines.append(f"- `{e}`")
    if r.get("failing_tests"):
        lines += ["", "## Failing tests"]
        for f in r["failing_tests"][:5]:
            lines.append(f"- `{f.get('test')}` — {f.get('error', '')[:200]}")
    if r.get("source_excerpt"):
        lines += ["", "## Implicated source (excerpt)", "```python", r["source_excerpt"][:1500], "```"]
    lines += ["", "## Proposed next step", r["proposal"], ""]
    return "\n".join(lines)
