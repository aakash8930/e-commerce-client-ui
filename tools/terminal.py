"""Terminal tool — allowlisted commands only, never a raw shell string.

`terminal.run` names a registered command from permissions.toml; argv is the
fixed prefix plus user args. subprocess runs with shell=False and a timeout.
"""

from __future__ import annotations

import subprocess
from typing import Any

from core.action import ToolError
from core.policy_engine import PolicyEngine, PolicyViolation
from tools.registry import ToolSpec


def make_terminal_tool(
    policy: PolicyEngine,
    default_timeout_s: int = 30,
) -> ToolSpec:
    def run(args: dict[str, Any]) -> dict[str, Any]:
        name = args.get("command", "")
        extra: list[str] = args.get("args", [])
        cwd = args.get("cwd", ".")
        if not isinstance(extra, list) or not all(isinstance(a, str) for a in extra):
            raise ToolError("'args' must be a list of strings")

        try:
            spec = policy.check_command(name, cwd)
        except PolicyViolation as exc:
            raise ToolError(str(exc)) from exc

        argv = list(spec["argv"]) + list(extra)
        timeout = int(spec.get("timeout_s", default_timeout_s))
        try:
            proc = subprocess.run(
                argv,
                cwd=spec["cwd"],
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            raise ToolError(
                f"command {name!r} timed out after {timeout}s and was stopped"
            ) from None
        except FileNotFoundError:
            raise ToolError(f"command binary not found: {argv[0]!r}") from None

        return {
            "command": name,
            "argv": argv,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-20000:],
            "stderr": proc.stderr[-8000:],
            "timed_out": False,
        }

    return ToolSpec(
        name="terminal.run",
        description="Run an allowlisted command with timeout and captured output",
        handler=run,
        input_schema={
            "command": {"type": str, "required": True},
            "args": {"type": list, "required": False},
            "cwd": {"type": str, "required": False},
        },
    )
