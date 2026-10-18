"""Context resolver: which project/files/prior memory matter for this request."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from memory.database import MemoryDB

KNOWN_PROJECT_MARKERS = ("pyproject.toml", "setup.py", "package.json", ".git", "main.py")


class ContextResolver:
    def __init__(self, memory: MemoryDB, project_root: str | None = None) -> None:
        self.memory = memory
        self.project_root = Path(project_root).resolve() if project_root else Path.cwd()

    def _try_path(self, raw: str) -> Path | None:
        """Resolve a candidate against cwd, then the jarvis project root."""
        expanded = os.path.expanduser(str(raw))
        for base in (Path.cwd(), self.project_root):
            p = Path(expanded)
            if not p.is_absolute():
                p = base / p
            try:
                resolved = p.resolve()
            except (OSError, RuntimeError):
                continue
            if resolved.is_dir():
                return resolved
        return None

    def resolve(self, request: str, params: dict[str, Any]) -> dict[str, Any]:
        """Return a context dict: project path, prior memories, ambiguity flag."""
        context: dict[str, Any] = {}

        candidates: list[str] = []
        if params.get("path"):
            candidates.append(str(params["path"]))
        for c in params.get("path_candidates", []):
            if c not in candidates:
                candidates.append(str(c))

        def explicit(c: str) -> bool:
            return "/" in c or c.startswith(("~", ".", "/"))

        for cand in candidates:
            resolved = self._try_path(cand)
            if resolved is not None:
                context["project_path"] = str(resolved)
                context["project_name"] = resolved.name
                break
        else:
            hard = [c for c in candidates if explicit(c)]
            if hard:
                context["ambiguity"] = (
                    f"no existing directory among: {', '.join(hard[:4])}"
                )
                return context

        # match against known projects from memory when no explicit path
        if "project_path" not in context:
            matches = self.memory.find_project(request.split()[0] if request else "")
            if len(matches) == 1:
                context["project_path"] = matches[0]["root_path"]
                context["project_name"] = matches[0]["name"]
            elif len(matches) > 1:
                context["ambiguity"] = "multiple projects match — please choose"
                context["candidates"] = [m["root_path"] for m in matches]

        # relevant prior knowledge (small, ranked)
        if "project_path" in context:
            context["prior_memory"] = self.memory.search(request, limit=5)

        return context
