"""Configuration loading (TOML). Pure stdlib — Python 3.11+ tomllib."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def load_toml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("rb") as fh:
        return tomllib.load(fh)


def load_config(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    settings = load_toml(root / "configs" / "settings.toml")
    permissions = load_toml(root / "configs" / "permissions.toml")

    # normalize relative paths against the project root
    paths = settings.setdefault("paths", {})
    for key, default in (
        ("data_dir", "data"),
        ("log_dir", "logs"),
        ("reports_dir", "data/reports"),
        ("memory_db", "data/jarvis_memory.db"),
    ):
        raw = paths.get(key, default)
        p = Path(raw)
        if not p.is_absolute():
            paths[key] = str(root / p)

    settings["_project_root"] = str(root)
    settings["_permissions"] = permissions
    return settings
