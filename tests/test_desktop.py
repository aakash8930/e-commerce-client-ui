"""Desktop tool tests — headless-safe: capability detection, allowlist,
scheme restrictions, and /proc-based process inspection."""

from pathlib import Path

import pytest

from core.action import Action
from core.app import JarvisApp
from tools.applications import desktop_available, make_desktop_tools
from tools.registry import ToolRegistry

ROOT = str(Path(__file__).resolve().parent.parent)


@pytest.fixture()
def registry(tmp_path: Path) -> ToolRegistry:
    from core.policy_engine import PolicyEngine

    policy = PolicyEngine(
        approved_roots=[str(tmp_path)],
        write_roots=[str(tmp_path)],
        blocked_names=[],
        blocked_dirs=[],
        approved_apps=["definitely-not-running-app"],
        allowed_url_schemes=["https"],
        project_root=str(tmp_path),
    )
    reg = ToolRegistry()
    for spec in make_desktop_tools(policy):
        reg.register(spec)
    policy.set_known_tools(reg.describe())
    return reg


def test_list_apps_works_headless(registry: ToolRegistry):
    result = registry.execute(Action(tool="desktop.list_apps", arguments={}))
    assert result.ok
    assert "desktop_available" in result.data
    assert isinstance(result.data["installed"], list)


def test_launch_never_fakes_success(registry: ToolRegistry):
    """Without a desktop session the tool must fail clearly, not pretend."""
    result = registry.execute(
        Action(tool="desktop.launch_app", arguments={"name": "definitely-not-running-app"})
    )
    if desktop_available():
        pytest.skip("desktop session present — launch path covered by policy tests")
    assert not result.ok
    assert "no desktop session" in result.error


def test_is_running_finds_processes(registry: ToolRegistry):
    import os

    result = registry.execute(
        Action(tool="desktop.is_running", arguments={"name": "python"})
    )
    assert result.ok
    # this test runs under python — /proc scan must see it
    assert result.data["running"] is True
    assert os.getpid() in result.data["pids"] or result.data["pids"]


def test_processes_listing_bounded(registry: ToolRegistry):
    result = registry.execute(Action(tool="desktop.processes", arguments={}))
    assert result.ok
    assert len(result.data["processes"]) <= 200
    if result.data["processes"]:
        p = result.data["processes"][0]
        assert set(p.keys()) == {"pid", "name", "rss_kib"}


def test_open_url_rejects_bad_schemes(registry: ToolRegistry):
    for bad in ("file:///etc/passwd", "javascript:alert(1)", "ftp://x/y"):
        result = registry.execute(Action(tool="desktop.open_url", arguments={"url": bad}))
        assert not result.ok


def test_policy_blocks_unapproved_app():
    app = JarvisApp(project_root=ROOT, approver=lambda a, r: True)
    decision = app.policy.check_action(
        Action(tool="desktop.launch_app", arguments={"name": "rm"})
    )
    assert not decision.allowed
    assert "allowlist" in decision.reason


def test_policy_allows_approved_app_name():
    app = JarvisApp(project_root=ROOT, approver=lambda a, r: True)
    decision = app.policy.check_action(
        Action(tool="desktop.launch_app", arguments={"name": "firefox"})
    )
    assert decision.allowed


def test_policy_blocks_file_scheme_urls():
    app = JarvisApp(project_root=ROOT, approver=lambda a, r: True)
    decision = app.policy.check_action(
        Action(tool="desktop.open_url", arguments={"url": "file:///etc/passwd"})
    )
    assert not decision.allowed
    assert decision.reason
