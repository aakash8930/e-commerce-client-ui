"""Performance measurement — reproducible reports for constrained hardware.

Everything is measured with stdlib only (time.perf_counter, /proc, resource).
The goal is a baseline you can compare against after each change, not a
micro-benchmark suite. Keep workloads sequential: target machine has 8 GB RAM
and an HDD.
"""

from __future__ import annotations

import resource
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.action import Action


def _current_rss_mib() -> float | None:
    try:
        with open("/proc/self/status", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        return None
    return None


def _peak_rss_mib() -> float:
    # Linux reports ru_maxrss in KiB
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)


def run_benchmark(app: Any, project_root: str, target_path: str | None = None) -> dict[str, Any]:
    """Measure startup, indexing, search, memory retrieval and resources."""
    from core.app import JarvisApp

    target = target_path or str(Path(project_root) / "demo_project")
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": target,
    }

    # 1. cold startup: assembling the whole application
    t0 = time.perf_counter()
    cold = JarvisApp(project_root=project_root, memory_db=str(Path(project_root) / "data" / "perf-probe.db"))
    report["startup_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    # 2. project scan (indexing)
    t0 = time.perf_counter()
    scan, _ = app.orchestrator.run_action(
        Action(tool="project.scan", arguments={"path": target}, reason="benchmark")
    )
    report["scan_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    report["scan_files"] = scan.data.get("file_count", 0) if scan.ok else 0

    # 3. filesystem keyword search
    t0 = time.perf_counter()
    search, _ = app.orchestrator.run_action(
        Action(tool="filesystem.search", arguments={"path": target, "query": "def"}, reason="benchmark")
    )
    report["fs_search_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    report["fs_search_hits"] = len(search.data.get("hits", [])) if search.ok else 0

    # 4. memory retrieval
    t0 = time.perf_counter()
    app.memory.search("project bug", limit=8)
    report["memory_search_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    # 5. system info
    t0 = time.perf_counter()
    info, _ = app.orchestrator.run_action(Action(tool="system.info", arguments={}, reason="benchmark"))
    report["system_info_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    # 6. resources
    report["rss_current_mib"] = _current_rss_mib()
    report["rss_peak_mib"] = _peak_rss_mib()
    if info.ok:
        report["machine"] = {
            "python": info.data.get("python"),
            "platform": info.data.get("platform"),
            "cpu_count": info.data.get("cpu_count"),
            "memory_total_mib": info.data.get("memory_total_mib"),
            "memory_available_mib": info.data.get("memory_available_mib"),
            "disk_free_gib": info.data.get("disk_free_gib"),
        }

    # 7. persist report
    reports = Path(app.config["paths"]["reports_dir"])
    reports.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = reports / f"{stamp}-performance.md"
    path.write_text(_render(report), encoding="utf-8")
    report["report_path"] = str(path)
    return report


def _render(r: dict[str, Any]) -> str:
    lines = [
        "# Performance report",
        "",
        f"Generated: {r['generated_at']}",
        f"Target: {r['target']}",
        "",
        "| Measurement | Value |",
        "| --- | --- |",
        f"| cold startup | {r['startup_ms']} ms |",
        f"| project scan ({r['scan_files']} files) | {r['scan_ms']} ms |",
        f"| filesystem search ({r['fs_search_hits']} hits) | {r['fs_search_ms']} ms |",
        f"| memory retrieval | {r['memory_search_ms']} ms |",
        f"| system info | {r['system_info_ms']} ms |",
        f"| RSS current | {r['rss_current_mib']} MiB |",
        f"| RSS peak | {r['rss_peak_mib']} MiB |",
    ]
    machine = r.get("machine") or {}
    if machine:
        lines += ["", "## Machine", ""]
        for k, v in machine.items():
            lines.append(f"- {k}: {v}")
    lines += [
        "",
        "## Notes",
        "- Sequential workloads only — the target machine has 8 GB RAM and an HDD.",
        "- Compare future runs against this baseline after each change.",
        "",
    ]
    return "\n".join(lines)
