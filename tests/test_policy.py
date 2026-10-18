"""Safety tests: the assistant must not escape approved roots or touch secrets."""

import os
from pathlib import Path

import pytest

from core.action import Action, RiskLevel
from core.policy_engine import PolicyEngine, PolicyViolation


@pytest.fixture()
def policy(tmp_path: Path) -> PolicyEngine:
    safe = tmp_path / "safe"
    safe.mkdir()
    (safe / "notes.txt").write_text("hello", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("top secret", encoding="utf-8")
    (safe / ".env").write_text("API_KEY=abc", encoding="utf-8")
    (safe / "sub").mkdir()
    os.symlink(outside / "secret.txt", safe / "sub" / "escape_link.txt")

    return PolicyEngine(
        approved_roots=[str(safe)],
        write_roots=[str(safe / "sub")],
        blocked_names=[".env", "*.pem", "id_rsa"],
        blocked_dirs=[".ssh", ".aws"],
        command_specs={"df": {"argv": ["df", "-h"], "risk": "low"}},
        project_root=str(tmp_path),
    )


def test_read_inside_root_ok(policy: PolicyEngine, tmp_path: Path):
    safe = tmp_path / "safe"
    assert policy.check_path(safe / "notes.txt").name == "notes.txt"


def test_traversal_rejected(policy: PolicyEngine, tmp_path: Path):
    safe = tmp_path / "safe"
    with pytest.raises(PolicyViolation):
        policy.check_path(safe / ".." / "outside" / "secret.txt")


def test_symlink_escape_rejected(policy: PolicyEngine, tmp_path: Path):
    safe = tmp_path / "safe"
    # resolves to outside/secret.txt → must be refused
    with pytest.raises(PolicyViolation):
        policy.check_path(safe / "sub" / "escape_link.txt")


def test_secret_file_blocked(policy: PolicyEngine, tmp_path: Path):
    safe = tmp_path / "safe"
    with pytest.raises(PolicyViolation):
        policy.check_path(safe / ".env")


def test_secret_dir_blocked(policy: PolicyEngine, tmp_path: Path):
    safe = tmp_path / "safe"
    (safe / ".ssh").mkdir()
    (safe / ".ssh" / "config").write_text("x", encoding="utf-8")
    with pytest.raises(PolicyViolation):
        policy.check_path(safe / ".ssh" / "config")


def test_write_outside_write_roots_rejected(policy: PolicyEngine, tmp_path: Path):
    safe = tmp_path / "safe"
    # notes.txt is inside read root but outside write roots
    with pytest.raises(PolicyViolation):
        policy.check_path(safe / "notes.txt", write=True)


def test_write_inside_write_roots_ok(policy: PolicyEngine, tmp_path: Path):
    safe = tmp_path / "safe"
    assert policy.check_path(safe / "sub" / "out.txt", write=True)


def test_action_blocked_tool_family(policy: PolicyEngine):
    decision = policy.check_action(Action(tool="evil.destroy", arguments={}))
    assert not decision.allowed


def test_unlisted_command_refused(policy: PolicyEngine):
    decision = policy.check_action(
        Action(tool="terminal.run", arguments={"command": "rm", "args": ["-rf", "/"], "cwd": "."})
    )
    assert not decision.allowed
    assert "not allowlisted" in decision.reason


def test_high_risk_requires_approval(policy: PolicyEngine, tmp_path: Path):
    safe = tmp_path / "safe"
    (safe / "sub" / "new.txt").parent.mkdir(exist_ok=True)
    decision = policy.check_action(
        Action(tool="filesystem.write_text", arguments={"path": str(safe / "sub" / "new.txt"), "content": "x"})
    )
    assert decision.allowed
    assert decision.risk == RiskLevel.MODERATE
    assert not decision.requires_approval
