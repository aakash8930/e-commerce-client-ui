"""Desktop tools — controlled interaction with the Linux desktop.

Design rules (roadmap Phase 7):
* Capability detection at runtime — no DISPLAY/WAYLAND means clear errors,
  never silent pretence.
* Only allowlisted applications may launch (enforced in the policy engine,
  not just a confirmation prompt).
* URLs are restricted to approved schemes.
* Process inspection exposes only benign fields (pid, name, memory).
* No continuous screenshot analysis; no unrestricted input automation.
"""

from __future__ import annotations

import configparser
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from core.action import ToolError
from core.policy_engine import PolicyEngine, PolicyViolation
from tools.registry import ToolSpec

APP_DIRS = [
    "/usr/share/applications",
    os.path.expanduser("~/.local/share/applications"),
]


def desktop_available() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _iter_desktop_entries() -> list[dict[str, Any]]:
    """Enumerate installed applications from .desktop files (best effort)."""
    apps: list[dict[str, Any]] = []
    for d in APP_DIRS:
        base = Path(d)
        if not base.is_dir():
            continue
        for fp in sorted(base.glob("*.desktop")):
            try:
                cp = configparser.ConfigParser(interpolation=None)
                cp.read(fp, encoding="utf-8")
                if not cp.has_section("Desktop Entry"):
                    continue
                entry = cp["Desktop Entry"]
                if entry.get("Type", "Application") != "Application":
                    continue
                if entry.get("NoDisplay", "").lower() == "true":
                    continue
                apps.append(
                    {
                        "id": fp.stem,
                        "name": entry.get("Name", fp.stem),
                    }
                )
            except (configparser.Error, OSError):
                continue
    return apps


def _find_desktop_entry(name: str) -> dict[str, Any] | None:
    want = name.lower().replace(" ", "-")
    for app in _iter_desktop_entries():
        if app["id"].lower() == want or app["name"].lower() == name.lower():
            return app
    return None


def _guard(policy: PolicyEngine, path: Any) -> Path:
    try:
        return policy.check_path(path, write=False)
    except PolicyViolation as exc:
        raise ToolError(str(exc)) from exc


def make_desktop_tools(policy: PolicyEngine) -> list[ToolSpec]:
    def list_apps(_args: dict[str, Any]) -> dict[str, Any]:
        apps = _iter_desktop_entries()
        return {
            "desktop_available": desktop_available(),
            "approved_apps": list(policy.approved_apps),
            "installed": apps[:200],
        }

    def launch_app(args: dict[str, Any]) -> dict[str, Any]:
        name = args.get("name", "")
        if not name:
            raise ToolError("'name' must be a non-empty string")
        if not desktop_available():
            raise ToolError(
                "no desktop session detected (DISPLAY/WAYLAND_DISPLAY unset) — "
                "cannot launch applications"
            )

        entry = _find_desktop_entry(name)
        if entry is None and shutil.which(name) is None:
            raise ToolError(f"application not found: {name!r}")

        launcher = shutil.which("gtk-launch")
        if launcher and entry:
            argv = [launcher, entry["id"]]
        elif entry:
            # sanitize the Exec line: drop field codes, never use a shell
            exec_line = entry.get("exec", "")
            argv = [t for t in shlex.split(exec_line) if not t.startswith("%")]
            if not argv:
                raise ToolError(f"cannot determine launch command for {name!r}")
        else:
            argv = [name]

        try:
            proc = subprocess.Popen(
                argv,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            raise ToolError(f"failed to launch {name!r}: {exc}") from exc

        return {"name": name, "pid": proc.pid, "argv": argv, "launched": True}

    def is_running(args: dict[str, Any]) -> dict[str, Any]:
        name = args.get("name", "")
        if not name:
            raise ToolError("'name' must be a non-empty string")
        pids = _scan_proc(name)
        return {"name": name, "running": bool(pids), "pids": pids[:10]}

    def processes(_args: dict[str, Any]) -> dict[str, Any]:
        """Benign process listing from /proc — no shell, no full cmdline secrets."""
        out = []
        try:
            entries = list(Path("/proc").iterdir())
        except OSError:
            return {"processes": [], "note": "/proc not available"}
        for entry in entries:
            if not entry.name.isdigit():
                continue
            comm = ""
            rss_kib = None
            try:
                comm = (entry / "comm").read_text(encoding="utf-8", errors="ignore").strip()
                for line in (entry / "status").read_text(encoding="utf-8", errors="ignore").splitlines():
                    if line.startswith("VmRSS:"):
                        rss_kib = int(line.split()[1])
                        break
            except OSError:
                continue
            out.append({"pid": int(entry.name), "name": comm, "rss_kib": rss_kib})
            if len(out) >= 200:
                break
        out.sort(key=lambda p: p.get("rss_kib") or 0, reverse=True)
        return {"processes": out}

    def open_file(args: dict[str, Any]) -> dict[str, Any]:
        if not desktop_available():
            raise ToolError("no desktop session detected — cannot open files visually")
        target = _guard(policy, args.get("path", ""))
        if not target.exists():
            raise ToolError(f"file not found: {target}")
        opener = shutil.which("xdg-open")
        if not opener:
            raise ToolError("xdg-open is not available on this system")
        proc = subprocess.Popen(
            [opener, str(target)],
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {"path": str(target), "pid": proc.pid, "opened": True}

    def open_url(args: dict[str, Any]) -> dict[str, Any]:
        url = args.get("url", "")
        parsed = urlparse(url)
        if parsed.scheme not in policy.allowed_url_schemes:
            raise ToolError(
                f"URL scheme {parsed.scheme!r} is not permitted "
                f"(allowed: {', '.join(policy.allowed_url_schemes)})"
            )
        if not parsed.netloc:
            raise ToolError(f"invalid URL: {url!r}")
        if not desktop_available():
            raise ToolError("no desktop session detected — cannot open a browser")
        opener = shutil.which("xdg-open")
        if not opener:
            raise ToolError("xdg-open is not available on this system")
        proc = subprocess.Popen(
            [opener, url],
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {"url": url, "pid": proc.pid, "opened": True}

    return [
        ToolSpec(
            name="desktop.list_apps",
            description="List installed applications and desktop capability",
            handler=list_apps,
        ),
        ToolSpec(
            name="desktop.launch_app",
            description="Launch an approved application (allowlist enforced)",
            handler=launch_app,
            input_schema={"name": {"type": str, "required": True}},
        ),
        ToolSpec(
            name="desktop.is_running",
            description="Check whether a named process is running",
            handler=is_running,
            input_schema={"name": {"type": str, "required": True}},
        ),
        ToolSpec(
            name="desktop.processes",
            description="List benign process information (pid, name, memory)",
            handler=processes,
        ),
        ToolSpec(
            name="desktop.open_file",
            description="Open an approved file with its default application",
            handler=open_file,
            input_schema={"path": {"type": str, "required": True}},
        ),
        ToolSpec(
            name="desktop.open_url",
            description="Open an http(s) URL in the browser",
            handler=open_url,
            input_schema={"url": {"type": str, "required": True}},
        ),
    ]


def _scan_proc(name: str) -> list[int]:
    pids: list[int] = []
    try:
        entries = list(Path("/proc").iterdir())
    except OSError:
        return pids
    want = name.lower()
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            comm = (entry / "comm").read_text(encoding="utf-8", errors="ignore").strip().lower()
        except OSError:
            continue
        if comm == want or comm == want[:15]:  # /proc/comm truncates at 15 chars
            pids.append(int(entry.name))
    return pids
