"""Standard action and result contracts for every tool invocation.

The planner never issues free-form shell strings. It requests a structured
Action from the orchestrator, which checks policy and calls a registered tool.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Action:
    """A structured request for one tool invocation."""

    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    risk: RiskLevel | None = None  # None → derive from the tool spec

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "arguments": self.arguments,
            "reason": self.reason,
            "risk": (self.risk or RiskLevel.LOW).value,
        }


@dataclass
class ToolResult:
    """Standardized tool result. Failures are values, not crashes."""

    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "data": self.data,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


class PolicyViolation(Exception):
    """Raised when an action is refused by the policy engine."""


class ToolError(Exception):
    """Raised by a tool handler; converted to ToolResult(ok=False)."""


def timed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)
