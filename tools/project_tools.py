"""Project intelligence tools: scan structure, run tests, find symbols.

Lightweight on purpose: regex-based extraction instead of a full language
server, incremental-friendly content hashing, and hard exclusions for
caches/venvs/build outputs.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any

from core.action import ToolError
from core.policy_engine import PolicyEngine, PolicyViolation
from tools.registry import ToolSpec

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", ".tox",
    ".pytest_cache", ".mypy_cache", "build", "dist", ".next", "coverage",
}
TEXT_SUFFIXES = {
    ".py", ".md", ".toml", ".yaml", ".yml", ".json", ".txt", ".ini", ".cfg", ".sh",
}
SYMBOL_RE = re.compile(r"^\s*(?:async\s+)?(def|class)\s+([A-Za-z_]\w*)", re.M)
IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M)


def _guard(policy: PolicyEngine, path: Any) -> Path:
    try:
        return policy.check_path(path, write=False)
    except PolicyViolation as exc:
        raise ToolError(str(exc)) from exc


def make_project_tools(
    policy: PolicyEngine,
    command_timeout_s: int,
    max_files: int,
) -> list[ToolSpec]:
    def scan(args: dict[str, Any]) -> dict[str, Any]:
        root = _guard(policy, args["path"])
        if not root.is_dir():
            raise ToolError(f"not a project directory: {root}")

        files: list[dict[str, Any]] = []
        languages: dict[str, int] = {}
        for fp in sorted(root.rglob("*")):
            if len(files) >= max_files:
                break
            if any(part in SKIP_DIRS for part in fp.parts):
                continue
            if not fp.is_file() or fp.suffix not in TEXT_SUFFIXES:
                continue
            try:
                data = fp.read_bytes()
            except OSError:
                continue
            rel = str(fp.relative_to(root))
            files.append(
                {
                    "path": rel,
                    "size": len(data),
                    "hash": hashlib.sha256(data).hexdigest()[:16],
                }
            )
            languages[fp.suffix] = languages.get(fp.suffix, 0) + 1

        entry_points = [
            n for n in ("main.py", "manage.py", "app.py", "package.json", "Makefile", "pyproject.toml")
            if (root / n).exists()
        ]
        test_dirs = sorted(
            {str(p.relative_to(root)) for p in root.rglob("test*") if p.is_dir() and not any(s in p.parts for s in SKIP_DIRS)}
        )
        config_files = [
            f["path"] for f in files
            if f["path"].endswith((".toml", ".yaml", ".yml", ".json", ".ini", ".cfg"))
            and "/" not in f["path"]
        ]

        return {
            "root": str(root),
            "file_count": len(files),
            "files": files[:200],
            "languages": languages,
            "entry_points": entry_points,
            "test_dirs": test_dirs,
            "config_files": config_files,
        }

    def run_tests(args: dict[str, Any]) -> dict[str, Any]:
        import sys

        root = _guard(policy, args["path"])
        if not root.is_dir():
            raise ToolError(f"not a project directory: {root}")
        target = args.get("test_path")
        argv = [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"]
        if args.get("fail_fast"):
            argv.append("-x")
        if target:
            argv.append(str(_guard(policy, target)))

        try:
            proc = subprocess.run(
                argv,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=command_timeout_s,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            raise ToolError(
                f"test run timed out after {command_timeout_s}s and was stopped"
            ) from None

        output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        failures = _extract_failures(output)
        passed = proc.returncode == 0
        return {
            "command": " ".join(argv),
            "exit_code": proc.returncode,
            "passed": passed,
            "output": output[-20000:],
            "failures": failures,
        }

    def find_symbol(args: dict[str, Any]) -> dict[str, Any]:
        root = _guard(policy, args["path"])
        name = args.get("name", "")
        if not name:
            raise ToolError("'name' must be a non-empty string")

        defs: list[dict[str, Any]] = []
        refs: list[dict[str, Any]] = []
        imports: list[dict[str, Any]] = []
        files = [root] if root.is_file() else [
            fp for fp in root.rglob("*")
            if fp.is_file() and fp.suffix == ".py" and not any(s in fp.parts for s in SKIP_DIRS)
        ]
        for fp in files:
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = str(fp)
            for lineno, line in enumerate(text.splitlines(), start=1):
                m = SYMBOL_RE.match(line)
                if m and m.group(2) == name:
                    defs.append({"path": rel, "line": lineno, "kind": m.group(1)})
                elif re.search(rf"\b{re.escape(name)}\b", line):
                    if line.strip().startswith(("#", '"', "'")):
                        continue
                    im = IMPORT_RE.match(line)
                    if im and name in line:
                        imports.append({"path": rel, "line": lineno, "text": line.strip()[:200]})
                    else:
                        refs.append({"path": rel, "line": lineno, "text": line.strip()[:200]})
        return {
            "name": name,
            "definitions": defs[:50],
            "references": refs[:50],
            "imports": imports[:50],
        }

    return [
        ToolSpec(
            name="project.scan",
            description="Scan a project: files, entry points, tests, config",
            handler=scan,
            input_schema={"path": {"type": str, "required": True}},
        ),
        ToolSpec(
            name="project.run_tests",
            description="Run pytest in a project and capture structured failures",
            handler=run_tests,
            input_schema={
                "path": {"type": str, "required": True},
                "test_path": {"type": str, "required": False},
                "fail_fast": {"type": bool, "required": False},
            },
        ),
        ToolSpec(
            name="project.find_symbol",
            description="Find definitions, imports and references of a symbol",
            handler=find_symbol,
            input_schema={
                "path": {"type": str, "required": True},
                "name": {"type": str, "required": True},
            },
        ),
    ]


def _extract_failures(output: str) -> list[dict[str, Any]]:
    """Parse pytest output into structured failure records (evidence-driven)."""
    failures: list[dict[str, Any]] = []
    blocks = re.split(r"_{5,} (.*?) _{5,}", output)
    # blocks: [preamble, name1, body1, name2, body2, ...]
    for i in range(1, len(blocks) - 1, 2):
        name = blocks[i].strip()
        body = blocks[i + 1]
        if not name.startswith(("FAILED", "ERROR")) and "FAIL" not in name.upper():
            # pytest -q splits on test names like "test_x - Failed: ..."
            pass
        error_line = ""
        for line in body.splitlines():
            if re.match(r"^E\s+", line):
                error_line = line.strip()
        file_match = re.search(r"^([^\s:]+\.py):(\d+)", body, re.M)
        failures.append(
            {
                "test": name,
                "error": error_line[:300] or (body.strip().splitlines() or [""])[-1][:300],
                "file": file_match.group(1) if file_match else None,
                "line": int(file_match.group(2)) if file_match else None,
            }
        )
    # also catch the short summary lines of pytest -q: "FAILED tests/test_x.py::test_y - ..."
    for m in re.finditer(r"^(FAILED|ERROR)\s+(\S+)(?:\s+-\s+(.*))?$", output, re.M):
        node = m.group(2)
        file_part = node.split("::")[0] if "::" in node else None
        failures.append(
            {
                "test": node,
                "error": (m.group(3) or "")[:300],
                "file": file_part,
                "line": None,
            }
        )
    # dedupe by test name
    seen: set[str] = set()
    unique = []
    for f in failures:
        key = f["test"]
        if key and key not in seen:
            seen.add(key)
            unique.append(f)
    return unique
