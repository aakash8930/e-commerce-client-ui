"""Configuration loading (TOML). Pure stdlib — Python 3.11+ tomllib.

Malformed configuration is a *controlled* failure: a clear ConfigError that
names the file, never a raw parser traceback mid-task.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Raised when a configuration file exists but cannot be parsed."""


def load_toml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open("rb") as fh:
            return tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{p} is malformed: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"cannot read {p}: {exc}") from exc


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
