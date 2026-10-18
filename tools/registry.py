"""Tool registry: typed, named capabilities with structured results.

Every tool has a unique name, an input schema, a risk level, a timeout and a
handler that returns a plain dict. The registry wraps handlers so failures
become ToolResult(ok=False) values instead of crashes.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from core.action import Action, RiskLevel, ToolError, ToolResult, timed_ms

Handler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class ToolSpec:
    name: str
    description: str
    handler: Handler
    risk: RiskLevel = RiskLevel.LOW
    timeout_s: int = 30
    input_schema: dict[str, Any] = field(default_factory=dict)

    def validate_arguments(self, arguments: dict[str, Any]) -> str | None:
        """Returns an error message, or None when arguments are acceptable."""
        for key, meta in self.input_schema.items():
            required = meta.get("required", False) if isinstance(meta, dict) else bool(meta)
            if required and key not in arguments:
                return f"missing required argument {key!r} for tool {self.name!r}"
            if key in arguments:
                expected = meta.get("type") if isinstance(meta, dict) else meta
                if expected and not isinstance(arguments[key], expected):
                    return (
                        f"argument {key!r} of tool {self.name!r} must be "
                        f"{getattr(expected, '__name__', expected)}"
                    )
        return None


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"tool already registered: {spec.name}")
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def describe(self) -> list[dict[str, Any]]:
        return [
            {
                "name": s.name,
                "description": s.description,
                "risk": s.risk.value,
                "timeout_s": s.timeout_s,
                "input_schema": s.input_schema,
            }
            for s in self._tools.values()
        ]

    def execute(self, action: Action) -> ToolResult:
        """Execute a validated action. Never raises for tool failures."""
        start = time.monotonic()
        spec = self.get(action.tool)
        if spec is None:
            return ToolResult(
                ok=False,
                error=f"unknown tool: {action.tool!r}",
                duration_ms=timed_ms(start),
            )

        error = spec.validate_arguments(action.arguments)
        if error:
            return ToolResult(ok=False, error=error, duration_ms=timed_ms(start))

        try:
            data = spec.handler(dict(action.arguments))
            return ToolResult(ok=True, data=data or {}, duration_ms=timed_ms(start))
        except ToolError as exc:
            return ToolResult(ok=False, error=str(exc), duration_ms=timed_ms(start))
        except Exception as exc:  # controlled error, never crash the assistant
            return ToolResult(
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                duration_ms=timed_ms(start),
            )
