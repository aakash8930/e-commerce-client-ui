"""System information tool — read-only facts about the local machine."""

from __future__ import annotations

import os
import platform
import shutil
import sys
from typing import Any

from tools.registry import ToolSpec


def make_system_tool(data_dir: str) -> ToolSpec:
    def info(_args: dict[str, Any]) -> dict[str, Any]:
        mem: dict[str, int] = {}
        try:
            with open("/proc/meminfo", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith(("MemTotal:", "MemAvailable:")):
                        key = line.split(":")[0]
                        mem[key] = int(line.split()[1]) // 1024  # MiB
        except OSError:
            pass

        disk = shutil.disk_usage(os.path.abspath(data_dir))
        return {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
            "memory_total_mib": mem.get("MemTotal"),
            "memory_available_mib": mem.get("MemAvailable"),
            "disk_total_gib": round(disk.total / 1024**3, 1),
            "disk_free_gib": round(disk.free / 1024**3, 1),
        }

    return ToolSpec(
        name="system.info",
        description="Read basic system information (memory, disk, platform)",
        handler=info,
    )
