"""Filesystem tools — all paths pass through the policy engine first."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.action import ToolError
from core.policy_engine import PolicyEngine, PolicyViolation
from tools.registry import ToolSpec


def _guard(policy: PolicyEngine, path: Any, write: bool = False) -> Path:
    try:
        return policy.check_path(path, write=write)
    except PolicyViolation as exc:
        raise ToolError(str(exc)) from exc


def make_filesystem_tools(policy: PolicyEngine, max_read_bytes: int, max_hits: int) -> list[ToolSpec]:
    def list_dir(args: dict[str, Any]) -> dict[str, Any]:
        target = _guard(policy, args["path"])
        if not target.is_dir():
            raise ToolError(f"not a directory: {target}")
        entries = []
        for child in sorted(target.iterdir())[:500]:
            entries.append(
                {
                    "name": child.name,
                    "type": "dir" if child.is_dir() else "file",
                    "size": child.stat().st_size if child.is_file() else None,
                }
            )
        return {"path": str(target), "entries": entries}

    def read_text(args: dict[str, Any]) -> dict[str, Any]:
        target = _guard(policy, args["path"])
        if not target.is_file():
            raise ToolError(f"file not found: {target}")
        raw = target.read_bytes()[:max_read_bytes]
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            content = raw.decode("utf-8", errors="replace")
        return {
            "path": str(target),
            "content": content,
            "truncated": target.stat().st_size > max_read_bytes,
        }

    def write_text(args: dict[str, Any]) -> dict[str, Any]:
        target = _guard(policy, args["path"], write=True)
        content = args.get("content", "")
        if not isinstance(content, str):
            raise ToolError("'content' must be a string")
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        return {"path": str(target), "created": not existed, "bytes": len(content.encode())}

    def search(args: dict[str, Any]) -> dict[str, Any]:
        root = _guard(policy, args["path"])
        query = args.get("query", "")
        if not query:
            raise ToolError("'query' must be a non-empty string")
        if not root.exists():
            raise ToolError(f"search path does not exist: {root}")

        hits: list[dict[str, Any]] = []
        scanned = 0
        skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", ".pytest_cache"}
        files = [root] if root.is_file() else list(root.rglob("*"))
        for fp in files:
            if len(hits) >= max_hits:
                break
            if not fp.is_file():
                continue
            if any(part in skip_dirs for part in fp.parts):
                continue
            if fp.stat().st_size > max_read_bytes * 5:
                continue
            scanned += 1
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if query.lower() in line.lower():
                    hits.append(
                        {
                            "path": str(fp),
                            "line": lineno,
                            "text": line.strip()[:300],
                        }
                    )
                    if len(hits) >= max_hits:
                        break
        return {"query": query, "hits": hits, "files_scanned": scanned}

    return [
        ToolSpec(
            name="filesystem.list_dir",
            description="List entries of an approved directory",
            handler=list_dir,
            input_schema={"path": {"type": str, "required": True}},
        ),
        ToolSpec(
            name="filesystem.read_text",
            description="Read a text file inside approved roots",
            handler=read_text,
            input_schema={"path": {"type": str, "required": True}},
        ),
        ToolSpec(
            name="filesystem.write_text",
            description="Write a text file inside approved write roots",
            handler=write_text,
            input_schema={
                "path": {"type": str, "required": True},
                "content": {"type": str, "required": True},
            },
        ),
        ToolSpec(
            name="filesystem.search",
            description="Keyword search across files under a path",
            handler=search,
            input_schema={
                "path": {"type": str, "required": True},
                "query": {"type": str, "required": True},
            },
        ),
    ]
