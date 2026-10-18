"""Model-independent reasoning interface.

The operating environment never depends on a specific model or vendor.
Two interchangeable implementations live behind this interface:

* RuleBasedEngine  — deterministic intent routing + plan templates (baseline)
* (future) small local LLMs, custom classifiers, or hybrid reasoning

Nothing outside `models/` should import a concrete engine.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Intent:
    name: str
    confidence: float
    params: dict[str, Any] = field(default_factory=dict)
    clarify: str | None = None  # when ambiguous: what to ask the user


class ReasoningEngine(ABC):
    """The one interface the rest of the system talks to."""

    @abstractmethod
    def interpret(self, request: str, context: dict[str, Any]) -> Intent:
        """Understand a user request in its context."""

    @abstractmethod
    def propose_plan(self, goal: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Propose plan steps as plain dicts (validated by the planner)."""


PATH_RE = re.compile(r"(/[\w./\-]+|\./[\w./\-]+|~[\w./\-]*)")


class RuleBasedEngine(ReasoningEngine):
    """Deterministic baseline: keyword intents, exact tool selection,
    structured plan templates, explicit clarification for ambiguity."""

    INTENTS: list[tuple[str, list[str]]] = [
        ("diagnose_project", ["diagnos", "failing test", "test fail", "why.*fail", "fix the error", "traceback", "bug"]),
        ("verify_changes", ["verify", "check my change", "regression", "run the tests", "test suite"]),
        ("organize_files", ["organize", "sort files", "clean up files", "tidy"]),
        ("maintenance_report", ["maintenance", "disk space", "health report", "system report"]),
        ("system_status", ["system info", "status of the system", "memory usage", "disk usage"]),
        ("project_status", ["what is this project", "project overview", "project map", "structure of"]),
    ]

    def interpret(self, request: str, context: dict[str, Any]) -> Intent:
        text = request.lower().strip()
        for name, patterns in self.INTENTS:
            for pat in patterns:
                if re.search(pat, text):
                    params: dict[str, Any] = {}
                    candidates = [m.group(1) for m in PATH_RE.finditer(request)]
                    # bare trailing words may be directory names (e.g. "demo_project")
                    words = re.findall(r"[\w./\-]+", request)
                    if words:
                        candidates.append(words[-1])
                    params["path_candidates"] = candidates
                    if candidates:
                        params["path"] = candidates[0]
                    elif context.get("project_path"):
                        params["path"] = context["project_path"]
                    return Intent(name=name, confidence=0.9, params=params)

        if any(w in text for w in ("open ", "launch ", "start ")):
            m = re.search(r"\b(?:open|launch|start)\s+(\S+)", text)
            target = m.group(1) if m else ""
            if target.startswith(("http://", "https://")):
                return Intent("desktop_open_url", confidence=0.9, params={"url": target})
            if target:
                return Intent("desktop_launch", confidence=0.8, params={"app": target})

        return Intent(
            name="unknown",
            confidence=0.0,
            clarify=(
                "I could not map that request to a known workflow. "
                "Try: 'diagnose failing tests in <path>', 'verify changes', "
                "'maintenance report', or 'system status'."
            ),
        )

    def propose_plan(self, goal: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Plan templates per intent. The planner validates these against the
        registry before anything executes. Each step declares its expected
        result and verification method — not just commands."""
        intent = context.get("intent", "generic")
        path = context.get("path", ".")

        if intent == "diagnose_project":
            return [
                {
                    "objective": "Scan the project structure",
                    "action": {"tool": "project.scan", "arguments": {"path": path}},
                    "expected": "A map of files, entry points and test locations",
                    "verify": {"type": "result_ok"},
                    "retry_safe": True,
                },
                {
                    "objective": "Run the test suite and capture failures",
                    "action": {"tool": "project.run_tests", "arguments": {"path": path}},
                    "expected": "Test output with exit code and structured failures",
                    "verify": {"type": "result_ok"},
                    "retry_safe": False,  # test runs are side-effecting (time)
                },
                {
                    "objective": "Search the codebase for the failing symbol",
                    "action": {
                        "tool": "project.find_symbol",
                        "arguments": {"path": path, "name": "__FAILING_SYMBOL__"},
                    },
                    "expected": "Definitions and references for the failing code",
                    "verify": {"type": "result_ok"},
                    "retry_safe": True,
                },
                {
                    "objective": "Read the implicated source file",
                    "action": {
                        "tool": "filesystem.read_text",
                        "arguments": {"path": "__FAILING_FILE__"},
                    },
                    "expected": "Source excerpt as evidence",
                    "verify": {"type": "result_ok"},
                    "retry_safe": True,
                },
            ]

        if intent == "verify_changes":
            return [
                {
                    "objective": "Inspect repository state",
                    "action": {
                        "tool": "terminal.run",
                        "arguments": {"command": "git", "args": ["status", "--short"], "cwd": path},
                    },
                    "expected": "Git status listing changed files",
                    "verify": {"type": "exit_code", "value": 0},
                    "retry_safe": True,
                },
                {
                    "objective": "Run the test suite",
                    "action": {"tool": "project.run_tests", "arguments": {"path": path}},
                    "expected": "Pass/fail summary with captured output",
                    "verify": {"type": "result_ok"},
                    "retry_safe": False,
                },
            ]

        if intent == "maintenance_report":
            return [
                {
                    "objective": "Check disk usage",
                    "action": {"tool": "terminal.run", "arguments": {"command": "df", "args": [], "cwd": "."}},
                    "expected": "Disk usage report",
                    "verify": {"type": "exit_code", "value": 0},
                    "retry_safe": True,
                },
                {
                    "objective": "Check memory usage",
                    "action": {"tool": "terminal.run", "arguments": {"command": "free", "args": [], "cwd": "."}},
                    "expected": "Memory usage report",
                    "verify": {"type": "exit_code", "value": 0},
                    "retry_safe": True,
                },
                {
                    "objective": "Collect system information",
                    "action": {"tool": "system.info", "arguments": {}},
                    "expected": "Python version, platform, resources",
                    "verify": {"type": "result_ok"},
                    "retry_safe": True,
                },
            ]

        if intent == "system_status":
            return [
                {
                    "objective": "Collect system information",
                    "action": {"tool": "system.info", "arguments": {}},
                    "expected": "Resource snapshot",
                    "verify": {"type": "result_ok"},
                    "retry_safe": True,
                }
            ]

        if intent == "project_status":
            return [
                {
                    "objective": "Scan the project structure",
                    "action": {"tool": "project.scan", "arguments": {"path": path}},
                    "expected": "Project overview",
                    "verify": {"type": "result_ok"},
                    "retry_safe": True,
                }
            ]

        return []
