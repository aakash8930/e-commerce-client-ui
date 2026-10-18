"""Planner + reasoning tests: intent → validated plan, no execution."""

import pytest

from core.planner import PlanValidationError, Planner
from core.task import Task
from models.reasoning_interface import RuleBasedEngine
from tools.registry import ToolSpec, ToolRegistry


@pytest.fixture()
def planner() -> Planner:
    registry = ToolRegistry()
    for name in (
        "project.scan",
        "project.run_tests",
        "project.find_symbol",
        "filesystem.read_text",
        "terminal.run",
        "system.info",
    ):
        registry.register(ToolSpec(name=name, description="d", handler=lambda a: {}))
    return Planner(RuleBasedEngine(), registry)


def test_intent_diagnose(planner: Planner):
    intent = planner.understand("diagnose the failing tests in ./demo_project", {})
    assert intent.name == "diagnose_project"
    assert "demo_project" in intent.params.get("path", "")


def test_intent_unknown_asks_for_clarification(planner: Planner):
    intent = planner.understand("please do something mysterious", {})
    assert intent.name == "unknown"
    assert intent.clarify


def test_plan_steps_are_typed_and_verified(planner: Planner):
    task = Task(goal="diagnose failing tests")
    intent = planner.understand("diagnose failing tests", {})
    plan = planner.build_plan(task, intent, {"path": "demo_project"})
    assert task.state.value == "planned"
    assert len(plan.steps) >= 3
    for step in plan.steps:
        assert step.objective
        assert step.expected
        assert step.verify.get("type")
        assert step.action.tool


def test_plan_rejects_unregistered_tool(planner: Planner):
    engine = RuleBasedEngine()

    def bad_plan(goal, context):
        return [{"objective": "x", "action": {"tool": "does.not.exist", "arguments": {}}}]

    planner.engine.propose_plan = bad_plan  # type: ignore[method-assign]
    task = Task(goal="x")
    with pytest.raises(PlanValidationError):
        planner.build_plan(task, type("I", (), {"name": "generic"})(), {})
