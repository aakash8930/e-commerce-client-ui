"""Policy engine: risk classification and technical enforcement.

The policy engine is the single gate between a requested Action and the
tool that would execute it. It enforces:

* approved read/write roots (resolved paths, symlinks followed, escapes denied)
* secret-file protection
* command allowlisting (no arbitrary shell strings)
* risk classification with approval requirements
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.action import Action, PolicyViolation, RiskLevel


@dataclass
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    risk: RiskLevel
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "requires_approval": self.requires_approval,
            "risk": self.risk.value,
            "reason": self.reason,
        }


# Which risk levels require explicit user approval before execution.
APPROVAL_REQUIRED = {
    RiskLevel.LOW: False,
    RiskLevel.MODERATE: False,  # moderate: preview/apply permitted ops (logged)
    RiskLevel.HIGH: True,
    RiskLevel.CRITICAL: True,
}

# Which risk levels are blocked outright unless explicitly authorized.
BLOCKED_BY_DEFAULT = {RiskLevel.CRITICAL}


class PolicyEngine:
    def __init__(
        self,
        approved_roots: list[str],
        write_roots: list[str],
        blocked_names: list[str],
        blocked_dirs: list[str],
        command_specs: dict[str, dict[str, Any]] | None = None,
        project_root: str | None = None,
        approved_apps: list[str] | None = None,
        allowed_url_schemes: list[str] | None = None,
    ) -> None:
        self._root = Path(project_root or os.getcwd()).resolve()
        self.approved_roots = [self._resolve_root(p) for p in approved_roots]
        self.write_roots = [self._resolve_root(p) for p in write_roots]
        self.blocked_names = list(blocked_names)
        self.blocked_dirs = list(blocked_dirs)
        self.command_specs = command_specs or {}
        self.approved_apps = [a.lower() for a in (approved_apps or [])]
        self.allowed_url_schemes = [s.lower() for s in (allowed_url_schemes or ["https", "http"])]
        self._known_tool_risk: dict[str, RiskLevel] = {}

    def set_known_tools(self, tools: list[dict[str, Any]]) -> None:
        """Register the tool inventory with policy so unknown tools are denied
        and known custom tools inherit their declared risk."""
        self._known_tool_risk = {
            t["name"]: RiskLevel(t["risk"]) for t in tools
        }

    # ------------------------------------------------------------------ setup

    def _resolve_root(self, raw: str) -> Path:
        expanded = os.path.expanduser(raw)
        p = Path(expanded)
        if not p.is_absolute():
            p = self._root / p
        return p.resolve()

    @classmethod
    def from_config(cls, config: dict[str, Any], project_root: str | None = None) -> "PolicyEngine":
        fs = config.get("filesystem", {})
        secrets = config.get("secrets", {})
        desktop = config.get("desktop", {})
        return cls(
            approved_roots=list(fs.get("approved_roots", ["."])),
            write_roots=list(fs.get("write_roots", [])),
            blocked_names=list(secrets.get("blocked_names", [])),
            blocked_dirs=list(secrets.get("blocked_dirs", [])),
            command_specs=config.get("commands", {}),
            project_root=project_root,
            approved_apps=list(desktop.get("approved_apps", [])),
            allowed_url_schemes=list(desktop.get("allowed_url_schemes", ["https", "http"])),
        )

    # ------------------------------------------------------------------ paths

    def _is_within(self, path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def check_path(self, path: str | os.PathLike, write: bool = False) -> Path:
        """Resolve a path (following symlinks) and enforce scope rules.

        Raises PolicyViolation on any escape or protected target.
        """
        expanded = os.path.expanduser(str(path))
        candidate = Path(expanded)
        if not candidate.is_absolute():
            candidate = self._root / candidate

        try:
            resolved = candidate.resolve(strict=False)
        except (OSError, RuntimeError) as exc:  # symlink loops etc.
            raise PolicyViolation(f"cannot resolve path {path!r}: {exc}") from exc

        # secret protection applies to the resolved name and its parents
        self._check_secrets(resolved)

        roots = self.write_roots if write else self.approved_roots
        if write:
            # writing still requires the target to be inside a readable root
            if not any(self._is_within(resolved, r) for r in self.approved_roots):
                raise PolicyViolation(
                    f"write target outside approved roots: {resolved}"
                )
        if not any(self._is_within(resolved, r) for r in roots):
            kind = "write" if write else "read"
            raise PolicyViolation(
                f"{kind} outside permitted directories: {resolved}"
            )
        return resolved

    def _check_secrets(self, resolved: Path) -> None:
        for part in resolved.parts:
            if part in self.blocked_dirs:
                raise PolicyViolation(
                    f"access to protected directory {part!r} is blocked "
                    f"(credential safety)"
                )
        name = resolved.name
        for pattern in self.blocked_names:
            if fnmatch.fnmatch(name, pattern):
                raise PolicyViolation(
                    f"access to protected file {name!r} is blocked (credential safety)"
                )

    # ------------------------------------------------------ commands (terminal)

    def check_command(self, name: str, cwd: str | os.PathLike) -> dict[str, Any]:
        """Validate a registered command; returns its spec.

        Arbitrary shell strings are impossible: only allowlisted names resolve.
        """
        spec = self.command_specs.get(name)
        if not spec:
            raise PolicyViolation(
                f"command {name!r} is not allowlisted in permissions.toml"
            )
        resolved_cwd = self.check_path(cwd, write=False)
        if not resolved_cwd.is_dir():
            raise PolicyViolation(f"working directory does not exist: {resolved_cwd}")
        return {**spec, "cwd": str(resolved_cwd)}

    # ---------------------------------------------------------- action policy

    def check_action(self, action: Action) -> PolicyDecision:
        """Classify and vet a structured action. Never raises for policy
        outcomes — returns a decision so callers can log and explain."""
        try:
            tool = action.tool

            if tool.startswith("filesystem."):
                write = tool in {"filesystem.write_text", "filesystem.delete", "filesystem.move"}
                if tool == "filesystem.move":
                    source = action.arguments.get("source")
                    dest = action.arguments.get("dest")
                    if not source or not dest:
                        return PolicyDecision(
                            False, False, RiskLevel.HIGH,
                            "filesystem.move requires 'source' and 'dest'",
                        )
                    self.check_path(source, write=True)
                    self.check_path(dest, write=True)
                    risk = RiskLevel.HIGH  # moving files needs explicit approval
                else:
                    path = action.arguments.get("path")
                    if not path:
                        return PolicyDecision(False, False, RiskLevel.LOW, "missing 'path' argument")
                    self.check_path(path, write=write)
                    risk = {
                        "filesystem.read_text": RiskLevel.LOW,
                        "filesystem.list_dir": RiskLevel.LOW,
                        "filesystem.search": RiskLevel.LOW,
                        "filesystem.catalog": RiskLevel.LOW,
                        "filesystem.write_text": RiskLevel.MODERATE,
                        "filesystem.delete": RiskLevel.HIGH,
                    }.get(tool, RiskLevel.MODERATE)

            elif tool.startswith("desktop."):
                risk = {
                    "desktop.list_apps": RiskLevel.LOW,
                    "desktop.is_running": RiskLevel.LOW,
                    "desktop.processes": RiskLevel.LOW,
                    "desktop.launch_app": RiskLevel.MODERATE,
                    "desktop.open_file": RiskLevel.MODERATE,
                    "desktop.open_url": RiskLevel.MODERATE,
                }.get(tool, RiskLevel.HIGH)

                if tool == "desktop.launch_app":
                    name = str(action.arguments.get("name", "")).lower()
                    if name.endswith(".desktop"):
                        name = name[: -len(".desktop")]
                    if name not in self.approved_apps:
                        return PolicyDecision(
                            False,
                            False,
                            RiskLevel.HIGH,
                            f"application {action.arguments.get('name')!r} is not in the "
                            "approved_apps allowlist — refused",
                        )
                if tool == "desktop.open_file":
                    path = action.arguments.get("path")
                    if not path:
                        return PolicyDecision(False, False, RiskLevel.MODERATE, "missing 'path' argument")
                    self.check_path(path, write=False)
                if tool == "desktop.open_url":
                    from urllib.parse import urlparse

                    scheme = urlparse(str(action.arguments.get("url", ""))).scheme.lower()
                    if scheme not in self.allowed_url_schemes:
                        return PolicyDecision(
                            False,
                            False,
                            RiskLevel.CRITICAL,
                            f"URL scheme {scheme!r} is not permitted",
                        )

            elif tool == "terminal.run":
                name = action.arguments.get("command", "")
                spec = self.command_specs.get(name)
                if not spec:
                    return PolicyDecision(
                        False,
                        False,
                        RiskLevel.CRITICAL,
                        f"command {name!r} is not allowlisted — refused",
                    )
                self.check_command(name, action.arguments.get("cwd", "."))
                risk = RiskLevel(spec.get("risk", "moderate"))

            elif tool.startswith(("project.", "system.", "memory.")):
                risk = self._known_tool_risk.get(tool) or {
                    "project.run_tests": RiskLevel.MODERATE,
                    "project.scan": RiskLevel.LOW,
                    "project.find_symbol": RiskLevel.LOW,
                    "system.info": RiskLevel.LOW,
                }.get(tool, RiskLevel.LOW)
                # filesystem-touching project tools still validate their root
                if "path" in action.arguments:
                    self.check_path(action.arguments["path"], write=False)

            elif tool in self._known_tool_risk:
                # custom registered tools inherit their declared risk
                risk = self._known_tool_risk[tool]
                if "path" in action.arguments:
                    self.check_path(action.arguments["path"], write=False)

            else:
                return PolicyDecision(
                    False, False, RiskLevel.HIGH, f"unknown tool: {tool}"
                )

            if action.risk is not None and action.risk.value > risk.value:
                risk = action.risk

        except PolicyViolation as exc:
            return PolicyDecision(False, False, RiskLevel.CRITICAL, str(exc))
        except Exception as exc:  # defensive: policy errors deny
            return PolicyDecision(False, False, RiskLevel.CRITICAL, f"policy error: {exc}")

        if risk in BLOCKED_BY_DEFAULT:
            return PolicyDecision(
                False, False, risk, "critical-risk action is blocked by default"
            )
        return PolicyDecision(True, APPROVAL_REQUIRED[risk], risk, "permitted by policy")
