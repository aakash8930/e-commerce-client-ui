"""Planner: turns reasoning output into a validated, executable plan.

The planner never executes anything. It validates that every proposed step
references a registered tool with acceptable arguments, and produces a Plan
with explicit task states.
"""

from __future__ import annotations

from typing import Any

from core.action import Action, RiskLevel
from core.task import Plan, PlanStep, Task, TaskState
from models.reasoning_interface import Intent, ReasoningEngine
from tools.registry import ToolRegistry


class PlanValidationError(Exception):
    pass


class Planner:
    def __init__(self, engine: ReasoningEngine, registry: ToolRegistry) -> None:
        self.engine = engine
        self.registry = registry

    def understand(self, request: str, context: dict[str, Any]) -> Intent:
        return self.engine.interpret(request, context)

    def build_plan(self, task: Task, intent: Intent, context: dict[str, Any]) -> Plan:
        raw_steps = self.engine.propose_plan(task.goal, {**context, "intent": intent.name})
        if not raw_steps:
            raise PlanValidationError(
                f"no plan template for intent {intent.name!r}"
            )

        steps: list[PlanStep] = []
        for i, raw in enumerate(raw_steps, start=1):
            action_raw = raw.get("action", {})
            tool_name = action_raw.get("tool", "")
            spec = self.registry.get(tool_name)
            if spec is None:
                raise PlanValidationError(
                    f"step {i} references unregistered tool {tool_name!r}"
                )
            arguments = dict(action_raw.get("arguments", {}))
            error = spec.validate_arguments(arguments)
            if error:
                raise PlanValidationError(f"step {i}: {error}")

            action = Action(
                tool=tool_name,
                arguments=arguments,
                reason=raw.get("objective", ""),
                risk=RiskLevel(raw["risk"]) if raw.get("risk") else None,
            )
            steps.append(
                PlanStep(
                    sequence=i,
                    objective=raw.get("objective", f"step {i}"),
                    action=action,
                    expected=raw.get("expected", ""),
                    verify=raw.get("verify", {"type": "result_ok"}),
                    depends_on=raw.get("depends_on", []),
                    retry_safe=bool(raw.get("retry_safe", False)),
                )
            )

        plan = Plan(goal=task.goal, steps=steps, intent=intent.name)
        task.plan = plan
        task.transition(TaskState.PLANNED)
        return plan
