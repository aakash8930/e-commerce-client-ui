"""Task model: explicit plan steps and a persisted state machine.

CREATED → PLANNED → WAITING_FOR_APPROVAL → RUNNING → VERIFYING
        → SUCCEEDED / FAILED / CANCELLED
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.action import Action


class TaskState(str, Enum):
    CREATED = "created"
    PLANNED = "planned"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    RUNNING = "running"
    VERIFYING = "verifying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATES = {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED}

TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.CREATED: {TaskState.PLANNED, TaskState.CANCELLED},
    TaskState.PLANNED: {
        TaskState.WAITING_FOR_APPROVAL,
        TaskState.RUNNING,
        TaskState.CANCELLED,
    },
    TaskState.WAITING_FOR_APPROVAL: {TaskState.RUNNING, TaskState.CANCELLED},
    TaskState.RUNNING: {TaskState.VERIFYING, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.VERIFYING: {
        TaskState.SUCCEEDED,
        TaskState.FAILED,
        TaskState.RUNNING,  # bounded repair: back to running for a retry
        TaskState.CANCELLED,
    },
    TaskState.SUCCEEDED: set(),
    TaskState.FAILED: set(),
    TaskState.CANCELLED: set(),
}


def can_transition(src: TaskState, dst: TaskState) -> bool:
    return dst in TRANSITIONS.get(src, set())


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class PlanStep:
    """One step of a plan: an action, its intent, and how to verify it."""

    sequence: int
    objective: str
    action: Action
    expected: str = ""
    verify: dict[str, Any] = field(default_factory=dict)
    depends_on: list[int] = field(default_factory=list)
    # retry only when the operation is safe to repeat (reads, searches, scans)
    retry_safe: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "objective": self.objective,
            "action": self.action.to_dict(),
            "expected": self.expected,
            "verify": self.verify,
            "depends_on": self.depends_on,
            "retry_safe": self.retry_safe,
        }


@dataclass
class Plan:
    goal: str
    steps: list[PlanStep]
    intent: str = "generic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "intent": self.intent,
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass
class Task:
    """A unit of work with a persisted lifecycle."""

    goal: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    state: TaskState = TaskState.CREATED
    plan: Plan | None = None
    created_at: str = field(default_factory=utcnow)
    completed_at: str | None = None
    error: str | None = None

    def transition(self, dst: TaskState) -> None:
        if not can_transition(self.state, dst):
            raise ValueError(f"illegal transition {self.state.value} → {dst.value}")
        self.state = dst
        if dst in TERMINAL_STATES:
            self.completed_at = utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "state": self.state.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "plan": self.plan.to_dict() if self.plan else None,
        }
