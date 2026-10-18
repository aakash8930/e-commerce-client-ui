"""Orchestrator: the only component that executes actions.

Rules of the road:
* Every action passes the policy engine first (structured actions only).
* Risky actions wait for explicit approval via the injected `approver`.
* Failures are classified; retries are bounded (max_repair_attempts) and
  only for retry-safe operations.
* Every tool run is logged to memory and the audit trail.
* Task state is checkpointed after each step, so a crash leaves a record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from core.action import Action, ToolResult
from core.policy_engine import PolicyEngine
from core.task import PlanStep, Task, TaskState
from core.verifier import verify
from memory.database import MemoryDB
from memory.logger import Logger
from tools.registry import ToolRegistry

# Approver: called when an action needs confirmation. Returns True to proceed.
Approver = Callable[[Action, str], bool]

FAILURE_CLASSES = {
    "missing_file": ("file not found", "no such file", "not found"),
    "permission_denied": ("outside approved", "blocked", "refused", "protected"),
    "timeout": ("timed out", "timeout"),
    "command_failed": ("exit code", "returned non-zero"),
    "invalid_input": ("missing required argument", "must be", "unknown tool"),
}


def classify_failure(error: str) -> str:
    lowered = error.lower()
    for cls, needles in FAILURE_CLASSES.items():
        if any(n in lowered for n in needles):
            return cls
    return "unexpected"


@dataclass
class StepOutcome:
    sequence: int
    objective: str
    ok: bool
    result: ToolResult
    verified: bool
    verify_detail: str
    attempts: int = 1
    failure_class: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "objective": self.objective,
            "ok": self.ok,
            "verified": self.verified,
            "verify_detail": self.verify_detail,
            "attempts": self.attempts,
            "failure_class": self.failure_class,
            "error": self.result.error,
            "duration_ms": self.result.duration_ms,
        }


@dataclass
class TaskOutcome:
    task: Task
    steps: list[StepOutcome] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.task.state == TaskState.SUCCEEDED

    def summary(self) -> dict[str, Any]:
        return {
            "task_id": self.task.id,
            "goal": self.task.goal,
            "state": self.task.state.value,
            "steps": [s.to_dict() for s in self.steps],
        }


class Orchestrator:
    def __init__(
        self,
        registry: ToolRegistry,
        policy: PolicyEngine,
        memory: MemoryDB,
        logger: Logger,
        approver: Approver | None = None,
        max_repair_attempts: int = 2,
    ) -> None:
        self.registry = registry
        self.policy = policy
        self.memory = memory
        self.logger = logger
        self.approver = approver or (lambda action, reason: False)
        self.max_repair_attempts = max(1, max_repair_attempts)

    # ------------------------------------------------------------ single action

    def run_action(self, action: Action, task_id: str | None = None) -> tuple[ToolResult, str | None]:
        """Policy → approval → execute → log. Returns (result, refusal_reason)."""
        decision = self.policy.check_action(action)
        self.logger.audit(
            "action_policy_check",
            task_id=task_id,
            tool=action.tool,
            decision=decision.to_dict(),
        )

        if not decision.allowed:
            self.memory.log_tool_run(task_id, action.tool, "blocked", 0, decision.reason)
            return (
                ToolResult(ok=False, error=f"policy refused: {decision.reason}"),
                decision.reason,
            )

        if decision.requires_approval:
            approved = self.approver(action, decision.reason)
            self.logger.audit(
                "action_approval",
                task_id=task_id,
                tool=action.tool,
                approved=bool(approved),
            )
            if not approved:
                self.memory.log_tool_run(task_id, action.tool, "cancelled", 0, "user declined")
                return (
                    ToolResult(ok=False, error="user declined approval"),
                    "user declined approval",
                )

        result = self.registry.execute(action)
        self.memory.log_tool_run(
            task_id,
            action.tool,
            "ok" if result.ok else "error",
            result.duration_ms,
            result.error or "",
        )
        self.logger.audit(
            "action_executed",
            task_id=task_id,
            tool=action.tool,
            ok=result.ok,
            duration_ms=result.duration_ms,
            error=result.error,
        )
        return result, None

    # ------------------------------------------------------------ plan execution

    def run_plan(self, task: Task) -> TaskOutcome:
        if task.plan is None:
            raise ValueError("task has no plan")
        outcome = TaskOutcome(task=task)

        if task.state == TaskState.CREATED:
            task.transition(TaskState.PLANNED)  # a plan exists → planned
        task.transition(TaskState.RUNNING)
        self.memory.set_task_state(task.id, task.state.value)
        self.memory.create_task(task.id, task.goal)

        for step in task.plan.steps:
            step_outcome = self._run_step(task, step)
            outcome.steps.append(step_outcome)

            self.memory.log_step(
                task.id,
                step.sequence,
                step.objective,
                step.action.to_dict(),
                "ok" if step_outcome.verified else "failed",
                step_outcome.verify_detail,
            )

            if not step_outcome.verified:
                task.error = (
                    f"step {step.sequence} failed ({step_outcome.failure_class}): "
                    f"{step_outcome.result.error or step_outcome.verify_detail}"
                )
                task.transition(TaskState.FAILED)
                self.memory.set_task_state(task.id, task.state.value, task.error)
                self.logger.error("task_failed", task_id=task.id, error=task.error)
                return outcome

        task.transition(TaskState.VERIFYING)
        self.memory.set_task_state(task.id, task.state.value)
        task.transition(TaskState.SUCCEEDED)
        self.memory.set_task_state(task.id, task.state.value)
        self.logger.info("task_succeeded", task_id=task.id)
        return outcome

    def _run_step(self, task: Task, step: PlanStep) -> StepOutcome:
        attempts = 0
        last_result: ToolResult | None = None
        last_detail = ""
        verified = False

        while attempts < self.max_repair_attempts:
            attempts += 1
            result, refusal = self.run_action(step.action, task_id=task.id)
            last_result = result
            ok, detail = verify(step, result)
            last_detail = detail
            verified = ok
            self.logger.info(
                "step_result",
                task_id=task.id,
                step=step.sequence,
                attempt=attempts,
                ok=ok,
                detail=detail,
            )
            if ok:
                break
            # bounded repair: retry only when the operation is safe to repeat
            if not step.retry_safe:
                break
            if refusal:  # policy/approval refusals are not retryable
                break

        assert last_result is not None
        return StepOutcome(
            sequence=step.sequence,
            objective=step.objective,
            ok=last_result.ok,
            result=last_result,
            verified=verified,
            verify_detail=last_detail,
            attempts=attempts,
            failure_class=None if verified else classify_failure(last_result.error or last_detail),
        )
