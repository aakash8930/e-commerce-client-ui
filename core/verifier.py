"""Verifier: did the action achieve its intended result?

Success is never assumed just because a command returned. Each plan step
declares how to verify its outcome; the verifier inspects the actual result.
"""

from __future__ import annotations

from typing import Any

from core.action import ToolResult
from core.task import PlanStep


def verify(step: PlanStep, result: ToolResult) -> tuple[bool, str]:
    if not result.ok:
        return False, f"tool failed: {result.error}"

    check = step.verify or {"type": "result_ok"}
    kind = check.get("type", "result_ok")

    if kind == "result_ok":
        return True, "tool returned ok"

    if kind == "exit_code":
        expected = check.get("value", 0)
        actual = result.data.get("exit_code")
        if actual == expected:
            return True, f"exit code {actual} as expected"
        return False, f"expected exit code {expected}, got {actual}"

    if kind == "output_contains":
        needle = check.get("value", "")
        haystack = str(result.data.get("stdout", "")) + str(result.data.get("content", ""))
        if needle in haystack:
            return True, f"output contains {needle!r}"
        return False, f"output does not contain {needle!r}"

    if kind == "file_exists":
        import os

        path = result.data.get("path") or step.action.arguments.get("path")
        if path and os.path.exists(path):
            return True, f"file exists: {path}"
        return False, f"expected file missing: {path}"

    return False, f"unknown verification type: {kind!r}"
