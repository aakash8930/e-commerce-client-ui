"""Reliability & failure-injection tests (roadmap Phase 11).

Simulates: missing files, inaccessible directories, corrupted config,
command timeouts, locked databases, interrupted tasks after restart,
invalid tool responses — and proves the system works fully offline.
"""

import os
import socket
import sqlite3
from pathlib import Path

import pytest

from core.action import Action
from core.app import JarvisApp
from core.config import ConfigError, load_config
from core.request_manager import RequestManager
from memory.database import MemoryDB, MemoryDBError
from tools.registry import ToolRegistry, ToolSpec

ROOT = str(Path(__file__).resolve().parent.parent)


def _app(tmp_path: Path) -> JarvisApp:
    return JarvisApp(
        project_root=ROOT,
        approver=lambda a, r: True,
        memory_db=str(tmp_path / "m.db"),
        reports_dir=str(tmp_path / "reports"),
    )


# ------------------------------------------------------------- missing files

def test_missing_file_is_controlled(tmp_path: Path):
    app = _app(tmp_path)
    app.policy.approved_roots.append(tmp_path.resolve())
    result, _ = app.orchestrator.run_action(
        Action(tool="filesystem.read_text", arguments={"path": str(tmp_path / "ghost.txt")})
    )
    assert not result.ok
    assert "not found" in result.error
    # the assistant is still alive afterwards
    assert app.orchestrator.registry.get("system.info") is not None


# ------------------------------------------------------ inaccessible directory

def test_inaccessible_directory_is_controlled(tmp_path: Path):
    app = _app(tmp_path)
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "x.txt").write_text("x", encoding="utf-8")
    app.policy.approved_roots.append(locked.resolve())
    os.chmod(locked, 0o000)
    try:
        result, _ = app.orchestrator.run_action(
            Action(tool="filesystem.list_dir", arguments={"path": str(locked)})
        )
        assert not result.ok  # controlled error, not a crash
    finally:
        os.chmod(locked, 0o755)


# ------------------------------------------------------------ corrupted config

def test_corrupted_config_raises_config_error(tmp_path: Path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "settings.toml").write_text(
        "this is [not valid toml", encoding="utf-8"
    )
    with pytest.raises(ConfigError) as exc:
        load_config(tmp_path)
    assert "settings.toml" in str(exc.value)


def test_cli_reports_config_error_cleanly(tmp_path: Path, monkeypatch, capsys):
    import interfaces.cli as cli

    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "settings.toml").write_text("= broken =", encoding="utf-8")
    monkeypatch.setattr(cli, "ROOT", str(tmp_path))
    exit_code = cli.main(["doctor"])
    assert exit_code == 2
    out = capsys.readouterr().out
    assert "configuration error" in out
    assert "settings.toml" in out


# ------------------------------------------------------------- locked database

def test_locked_database_state_write_raises_clear_error(tmp_path: Path):
    db = MemoryDB(tmp_path / "m.db")
    db.conn.execute("PRAGMA busy_timeout=100")  # keep the test fast

    blocker = sqlite3.connect(str(tmp_path / "m.db"))
    blocker.execute("BEGIN EXCLUSIVE")
    try:
        with pytest.raises(MemoryDBError) as exc:
            db.create_task("t1", "goal")
        assert "cannot record task" in str(exc.value)
    finally:
        blocker.rollback()
        blocker.close()
    db.close()


def test_locked_database_logging_never_raises(tmp_path: Path):
    db = MemoryDB(tmp_path / "m.db")
    db.conn.execute("PRAGMA busy_timeout=100")

    blocker = sqlite3.connect(str(tmp_path / "m.db"))
    blocker.execute("BEGIN EXCLUSIVE")
    try:
        db.log_tool_run("t1", "x.y", "ok", 1)      # must not raise
        assert db.add_observation("hello") is None  # must not raise
        db.add_decision("d", "r")                   # must not raise
    finally:
        blocker.rollback()
        blocker.close()
    db.close()


# ------------------------------------------------------ interrupted task restart

def test_interrupted_tasks_recovered_at_startup(tmp_path: Path):
    db = MemoryDB(tmp_path / "m.db")
    db.create_task("was-running", "a task that crashed mid-run")
    db.set_task_state("was-running", "running")
    db.create_task("done-task", "already finished")
    db.set_task_state("done-task", "succeeded")
    db.close()

    # "restart"
    db2 = MemoryDB(tmp_path / "m.db")
    recovered = RequestManager(db2).recover_interrupted()
    assert recovered == ["was-running"]
    task = db2.get_task("was-running")
    assert task["status"] == "failed"
    assert "interrupted" in (task["error"] or "")
    # completed tasks are untouched
    assert db2.get_task("done-task")["status"] == "succeeded"
    db2.close()


# ---------------------------------------------------------- invalid tool response

def test_invalid_tool_response_is_rejected():
    registry = ToolRegistry()
    registry.register(ToolSpec(name="x.garbage", description="d", handler=lambda a: "not a dict"))
    registry.register(ToolSpec(name="x.none", description="d", handler=lambda a: None))
    bad = registry.execute(Action(tool="x.garbage", arguments={}))
    assert not bad.ok
    assert "invalid tool response" in bad.error
    ok = registry.execute(Action(tool="x.none", arguments={}))
    assert ok.ok  # None is normalized to {}


# ----------------------------------------------------------------- timeout

def test_timeout_kills_the_child_process(tmp_path: Path):
    app = _app(tmp_path)
    # temporarily allowlist a long-running command with a 1s timeout
    app.policy.command_specs["sleep"] = {"argv": ["sleep"], "risk": "low", "timeout_s": 1}
    result, _ = app.orchestrator.run_action(
        Action(tool="terminal.run", arguments={"command": "sleep", "args": ["30"], "cwd": "."})
    )
    assert not result.ok
    assert "timed out" in result.error
    # and the next action still works — a timeout never wedges the assistant
    after, _ = app.orchestrator.run_action(Action(tool="system.info", arguments={}))
    assert after.ok


# ------------------------------------------------------------------ offline

def test_full_workflow_runs_offline(tmp_path: Path, monkeypatch):
    """No network sockets may be needed for any core feature."""

    def no_network(*args, **kwargs):
        raise OSError("network disabled by test")

    monkeypatch.setattr(socket, "socket", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)

    from automation.project_diagnosis import diagnose

    app = _app(tmp_path)

    # startup diagnostics
    assert app.doctor()["ok"]

    # local file reads + search
    result, _ = app.orchestrator.run_action(
        Action(tool="filesystem.read_text", arguments={"path": str(Path(ROOT) / "demo_project" / "calculator.py")})
    )
    assert result.ok

    # full diagnosis workflow (includes running the local test suite)
    report = diagnose(
        app.orchestrator,
        project_path=str(Path(ROOT) / "demo_project"),
        reports_dir=str(tmp_path / "reports"),
        task_id="offline",
    )
    assert Path(report["report_path"]).exists()

    # memory retrieval
    assert app.memory.search("diagnosed calculator") is not None

    # maintenance report (uses allowlisted local commands)
    from automation.maintenance import maintenance_report

    m = maintenance_report(
        app.orchestrator, project_path=str(Path(ROOT) / "demo_project"),
        reports_dir=str(tmp_path / "reports"), task_id="offline-m",
    )
    assert Path(m["report_path"]).exists()


# -------------------------------------------------------------- performance

def test_perf_report_is_reproducible(tmp_path: Path):
    from core.performance import run_benchmark

    app = _app(tmp_path)
    report = run_benchmark(app, project_root=ROOT)
    for key in (
        "startup_ms", "scan_ms", "fs_search_ms", "memory_search_ms",
        "system_info_ms", "rss_peak_mib",
    ):
        assert key in report
        assert report[key] >= 0
    assert report["rss_peak_mib"] > 0
    assert Path(report["report_path"]).exists()
    content = Path(report["report_path"]).read_text(encoding="utf-8")
    assert "Performance report" in content
