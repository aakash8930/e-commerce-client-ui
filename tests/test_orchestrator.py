"""Orchestrator tests: state machine, policy gate, bounded repair, checkpoints."""

from pathlib import Path

import pytest

from core.action import Action
from core.orchestrator import Orchestrator
from core.policy_engine import PolicyEngine
from core.task import Plan, PlanStep, Task
from memory.database import MemoryDB
from memory.logger import Logger
from tools.registry import ToolRegistry, ToolSpec


@pytest.fixture()
def setup(tmp_path: Path):
    policy = PolicyEngine(
        approved_roots=[str(tmp_path)],
        write_roots=[str(tmp_path)],
        blocked_names=[],
        blocked_dirs=[],
        command_specs={},
        project_root=str(tmp_path),
    )
    registry = ToolRegistry()
    calls = {"n": 0}

    def flaky(_args):
        calls["n"] += 1
        if calls["n"] < 2:
            from core.action import ToolError

            raise ToolError("transient failure")
        return {"value": "ok"}

    registry.register(ToolSpec(name="t.ok", description="always ok", handler=lambda a: {"done": True}))
    registry.register(ToolSpec(name="t.fail", description="always fail", handler=lambda a: (_ for _ in ()).throw(RuntimeError("broken"))))
    registry.register(ToolSpec(name="t.flaky", description="fails once", handler=flaky))
    policy.set_known_tools(registry.describe())
    memory = MemoryDB(tmp_path / "m.db")
    logger = Logger(tmp_path / "logs")
    return registry, policy, memory, logger, calls


def _orchestrator(setup, approver=None, attempts=2):
    registry, policy, memory, logger, calls = setup
    return Orchestrator(registry, policy, memory, logger, approver=approver, max_repair_attempts=attempts)


def test_successful_plan(setup):
    orch = _orchestrator(setup)
    task = Task(goal="do a safe thing")
    task.plan = Plan(
        goal=task.goal,
        steps=[
            PlanStep(1, "do it", Action(tool="t.ok", arguments={}), verify={"type": "result_ok"})
        ],
    )
    outcome = orch.run_plan(task)
    assert outcome.succeeded
    assert outcome.steps[0].verified
    assert task.state.value == "succeeded"
    # checkpointed
    record = setup[2].get_task(task.id)
    assert record["status"] == "succeeded"


def test_failed_step_stops_plan_with_classified_error(setup):
    orch = _orchestrator(setup)
    task = Task(goal="do a doomed thing")
    task.plan = Plan(
        goal=task.goal,
        steps=[
            PlanStep(1, "boom", Action(tool="t.fail", arguments={}), verify={"type": "result_ok"}, retry_safe=False),
            PlanStep(2, "never runs", Action(tool="t.ok", arguments={}), verify={"type": "result_ok"}),
        ],
    )
    outcome = orch.run_plan(task)
    assert not outcome.succeeded
    assert task.state.value == "failed"
    assert len(outcome.steps) == 1  # second step never executed
    assert outcome.steps[0].failure_class is not None


def test_bounded_repair_retries_safe_steps(setup):
    orch = _orchestrator(setup, attempts=2)
    task = Task(goal="retry a safe step")
    task.plan = Plan(
        goal=task.goal,
        steps=[
            PlanStep(1, "flaky", Action(tool="t.flaky", arguments={}), verify={"type": "result_ok"}, retry_safe=True),
        ],
    )
    outcome = orch.run_plan(task)
    assert outcome.succeeded
    assert outcome.steps[0].attempts == 2  # one failure + one retry


def test_unsafe_steps_are_not_retried(setup):
    orch = _orchestrator(setup, attempts=3)
    setup[4]["n"] = 0
    task = Task(goal="no blind retries")
    task.plan = Plan(
        goal=task.goal,
        steps=[
            PlanStep(1, "flaky", Action(tool="t.flaky", arguments={}), verify={"type": "result_ok"}, retry_safe=False),
        ],
    )
    outcome = orch.run_plan(task)
    assert not outcome.succeeded
    assert outcome.steps[0].attempts == 1


def test_approval_denial_cancels_action(setup):
    orch = _orchestrator(setup, approver=lambda a, r: False)
    result, refusal = orch.run_action(Action(tool="t.ok", arguments={}, reason="risky"))
    # t.ok is low risk → no approval needed → executes
    assert result.ok

    policy = setup[1]
    policy.command_specs["yes"] = {"argv": ["yes"], "risk": "high"}
    result, refusal = orch.run_action(
        Action(tool="terminal.run", arguments={"command": "yes", "args": [], "cwd": "."}, reason="risky")
    )
    assert not result.ok
    assert refusal is not None or result.error


def test_policy_blocked_action_recorded(setup):
    orch = _orchestrator(setup)
    result, refusal = orch.run_action(Action(tool="filesystem.read_text", arguments={"path": "/etc/passwd"}))
    assert not result.ok
    assert refusal is not None
