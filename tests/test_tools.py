"""Tool registry tests: structured results, controlled failures, timeouts."""

from pathlib import Path

import pytest

from core.action import Action, RiskLevel, ToolError
from core.policy_engine import PolicyEngine
from tools.filesystem import make_filesystem_tools
from tools.registry import ToolRegistry, ToolSpec
from tools.terminal import make_terminal_tool


@pytest.fixture()
def setup(tmp_path: Path):
    (tmp_path / "readme.md").write_text("project documentation", encoding="utf-8")
    policy = PolicyEngine(
        approved_roots=[str(tmp_path)],
        write_roots=[str(tmp_path)],
        blocked_names=[".env"],
        blocked_dirs=[],
        command_specs={
            "echo": {"argv": ["echo"], "risk": "low", "timeout_s": 5},
            "sleep": {"argv": ["sleep"], "risk": "low", "timeout_s": 1},
        },
        project_root=str(tmp_path),
    )
    registry = ToolRegistry()
    for spec in make_filesystem_tools(policy, max_read_bytes=1000, max_hits=20):
        registry.register(spec)
    registry.register(make_terminal_tool(policy, default_timeout_s=2))
    return registry, tmp_path


def test_read_file(setup):
    registry, tmp_path = setup
    result = registry.execute(Action(tool="filesystem.read_text", arguments={"path": str(tmp_path / "readme.md")}))
    assert result.ok
    assert result.data["content"] == "project documentation"


def test_missing_file_is_controlled_error(setup):
    registry, tmp_path = setup
    result = registry.execute(Action(tool="filesystem.read_text", arguments={"path": str(tmp_path / "nope.txt")}))
    assert not result.ok
    assert "not found" in result.error
    assert result.duration_ms >= 0


def test_unknown_tool_rejected(setup):
    registry, _ = setup
    result = registry.execute(Action(tool="nonsense.run", arguments={}))
    assert not result.ok
    assert "unknown tool" in result.error


def test_missing_required_argument(setup):
    registry, _ = setup
    result = registry.execute(Action(tool="filesystem.read_text", arguments={}))
    assert not result.ok
    assert "missing required argument" in result.error


def test_terminal_allowlisted_command(setup):
    registry, tmp_path = setup
    result = registry.execute(
        Action(tool="terminal.run", arguments={"command": "echo", "args": ["hello"], "cwd": str(tmp_path)})
    )
    assert result.ok
    assert result.data["exit_code"] == 0
    assert "hello" in result.data["stdout"]


def test_terminal_unlisted_command_refused(setup):
    registry, tmp_path = setup
    result = registry.execute(
        Action(tool="terminal.run", arguments={"command": "rm", "args": ["-rf", "/"], "cwd": str(tmp_path)})
    )
    assert not result.ok
    assert "not allowlisted" in result.error or "policy refused" in result.error


def test_terminal_timeout_is_controlled_error(setup):
    registry, tmp_path = setup
    result = registry.execute(
        Action(tool="terminal.run", arguments={"command": "sleep", "args": ["5"], "cwd": str(tmp_path)})
    )
    assert not result.ok
    assert "timed out" in result.error


def test_handler_exception_becomes_error_result():
    registry = ToolRegistry()

    def boom(_args):
        raise RuntimeError("kaput")

    registry.register(ToolSpec(name="x.boom", description="d", handler=boom))
    result = registry.execute(Action(tool="x.boom", arguments={}))
    assert not result.ok
    assert "kaput" in result.error


def test_duplicate_registration_rejected():
    registry = ToolRegistry()
    spec = ToolSpec(name="a.b", description="d", handler=lambda a: {})
    registry.register(spec)
    with pytest.raises(ValueError):
        registry.register(spec)
