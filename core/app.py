"""Application assembly: wire config → policy → tools → memory → engine.

This is the composition root. Components stay independent and testable;
only this module knows about all of them at once.
"""

from __future__ import annotations

from typing import Any

from core.config import load_config
from core.context_resolver import ContextResolver
from core.orchestrator import Orchestrator
from core.planner import Planner
from core.policy_engine import PolicyEngine
from core.request_manager import RequestManager
from memory.database import MemoryDB
from memory.logger import Logger
from models.reasoning_interface import RuleBasedEngine
from tools.filesystem import make_filesystem_tools
from tools.project_tools import make_project_tools
from tools.registry import ToolRegistry
from tools.system import make_system_tool
from tools.terminal import make_terminal_tool


class JarvisApp:
    """Everything the CLI (or any future interface) needs."""

    def __init__(
        self,
        project_root: str,
        approver=None,
        memory_db: str | None = None,
        reports_dir: str | None = None,
    ) -> None:
        self.config = load_config(project_root)
        self.permissions = self.config["_permissions"]
        limits = self.config.get("limits", {})

        if memory_db:
            self.config["paths"]["memory_db"] = memory_db
        if reports_dir:
            self.config["paths"]["reports_dir"] = reports_dir

        self.policy = PolicyEngine.from_config(self.permissions, project_root=project_root)
        self.registry = ToolRegistry()
        for spec in make_filesystem_tools(
            self.policy,
            max_read_bytes=int(limits.get("max_file_read_bytes", 200000)),
            max_hits=int(limits.get("max_search_hits", 50)),
        ):
            self.registry.register(spec)
        self.registry.register(
            make_terminal_tool(self.policy, default_timeout_s=int(limits.get("tool_timeout_s", 30)))
        )
        self.registry.register(make_system_tool(self.config["paths"]["data_dir"]))
        for spec in make_project_tools(
            self.policy,
            command_timeout_s=int(limits.get("command_timeout_s", 120)),
            max_files=int(limits.get("max_index_files", 5000)),
        ):
            self.registry.register(spec)
        # policy learns the tool inventory: unknown tools are denied,
        # custom tools inherit their declared risk
        self.policy.set_known_tools(self.registry.describe())

        self.memory = MemoryDB(self.config["paths"]["memory_db"])
        self.logger = Logger(self.config["paths"]["log_dir"])
        self.engine = RuleBasedEngine()
        self.planner = Planner(self.engine, self.registry)
        self.requests = RequestManager(self.memory)
        self.context = ContextResolver(self.memory, project_root=project_root)
        self.orchestrator = Orchestrator(
            registry=self.registry,
            policy=self.policy,
            memory=self.memory,
            logger=self.logger,
            approver=approver,
            max_repair_attempts=int(limits.get("max_repair_attempts", 2)),
        )

    def doctor(self) -> dict[str, Any]:
        """First-run diagnostic: is the environment sane?"""
        import os
        import sys

        checks: list[tuple[str, bool, str]] = []

        checks.append(
            ("python >= 3.11", sys.version_info >= (3, 11), f"found {sys.version.split()[0]}")
        )
        for key, label in (("data_dir", "data dir"), ("log_dir", "log dir"), ("reports_dir", "reports dir")):
            path = self.config["paths"][key]
            exists = os.path.isdir(path)
            checks.append((f"{label} writable", exists or _try_mkdir(path), path))

        checks.append(
            ("memory db open", True, self.config["paths"]["memory_db"])
        )
        checks.append(
            ("approved roots", len(self.policy.approved_roots) > 0,
             ", ".join(str(r) for r in self.policy.approved_roots))
        )
        checks.append(
            ("registered tools", len(self.registry.names()) > 0, ", ".join(self.registry.names()))
        )
        cmds = list(self.permissions.get("commands", {}))
        checks.append(("registered commands", len(cmds) > 0, ", ".join(cmds)))

        ok = all(c[1] for c in checks)
        return {"ok": ok, "checks": [{"name": n, "passed": p, "detail": d} for n, p, d in checks]}


def _try_mkdir(path: str) -> bool:
    import os

    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False
