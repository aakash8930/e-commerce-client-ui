"""CLI interface — the primary way to interact with jarvis-os.

Commands:
  jarvis doctor                  first-run diagnostics
  jarvis status                  tasks, projects, config summary
  jarvis projects                list known projects
  jarvis index <path>            register + scan a project
  jarvis tasks / task <id>       task history
  jarvis memory <query>          search memory
  jarvis tools                   list registered tools
  jarvis run "<request>"         interpret + plan + execute a request
  jarvis demo [--yes]            Workflow A on the demo project
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.action import Action
from core.app import JarvisApp
from core.task import TaskState

ROOT = str(Path(__file__).resolve().parent.parent)


def _approver_auto(action: Action, reason: str) -> bool:
    return True


def _approver_prompt(action: Action, reason: str) -> bool:
    print(f"\n⚠ Approval required ({action.risk.value if action.risk else 'risk?'} risk)")
    print(f"  tool:   {action.tool}")
    print(f"  args:   {json.dumps(action.arguments, ensure_ascii=False)[:200]}")
    print(f"  reason: {action.reason}")
    try:
        answer = input("Proceed? [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def _print(msg: str = "") -> None:
    print(msg)


def cmd_doctor(app: JarvisApp, _args: argparse.Namespace) -> int:
    report = app.doctor()
    _print("jarvis-os doctor")
    _print("=" * 50)
    for check in report["checks"]:
        mark = "✔" if check["passed"] else "�’"
        _print(f"  {mark} {check['name']:<24} {check['detail']}")
    _print("=" * 50)
    _print("environment OK" if report["ok"] else "problems found")
    return 0 if report["ok"] else 1


def cmd_status(app: JarvisApp, _args: argparse.Namespace) -> int:
    tasks = app.memory.list_tasks(5)
    projects = app.memory.list_projects()
    sysinfo, _ = app.orchestrator.run_action(Action(tool="system.info", arguments={}))
    _print("jarvis-os status")
    _print("=" * 50)
    _print(f"  tasks recorded:   {len(app.memory.list_tasks(100))}")
    _print(f"  projects known:   {len(projects)}")
    _print(f"  tools registered: {len(app.registry.names())}")
    if sysinfo.ok:
        _print(
            f"  memory free:      {sysinfo.data.get('memory_available_mib')} MiB / "
            f"{sysinfo.data.get('memory_total_mib')} MiB"
        )
        _print(f"  disk free:        {sysinfo.data.get('disk_free_gib')} GiB")
    if tasks:
        _print("\nrecent tasks:")
        for t in tasks:
            _print(f"  [{t['status']:<10}] {t['id']} — {t['goal'][:60]}")
    return 0


def cmd_projects(app: JarvisApp, _args: argparse.Namespace) -> int:
    for p in app.memory.list_projects():
        _print(f"  {p['name']:<30} {p['root_path']}")
    return 0


def cmd_index(app: JarvisApp, args: argparse.Namespace) -> int:
    path = str(Path(args.path).expanduser().resolve())
    result, refusal = app.orchestrator.run_action(
        Action(tool="project.scan", arguments={"path": path}, reason="Register and scan project")
    )
    if not result.ok:
        _print(f"index failed: {result.error}")
        return 1
    app.memory.register_project(path, Path(path).name)
    data = result.data
    _print(f"indexed {data['root']}: {data['file_count']} files, "
           f"entry points: {', '.join(data['entry_points']) or 'none'}")
    return 0


def cmd_tasks(app: JarvisApp, args: argparse.Namespace) -> int:
    if getattr(args, "task_id", None):
        task = app.memory.get_task(args.task_id)
        if not task:
            _print(f"task not found: {args.task_id}")
            return 1
        _print(json.dumps(task, indent=2))
        return 0
    for t in app.memory.list_tasks():
        _print(f"  [{t['status']:<10}] {t['id']} — {t['goal'][:70]}")
    return 0


def cmd_memory(app: JarvisApp, args: argparse.Namespace) -> int:
    results = app.memory.search(args.query, limit=8)
    if not results:
        _print("no memory matches")
        return 0
    for r in results:
        _print(f"  [{r['kind']}/{r['category']}] {r['content'][:110]}")
        if r.get("provenance"):
            _print(f"      provenance: {r['provenance'][:90]}")
    return 0


def cmd_tools(app: JarvisApp, _args: argparse.Namespace) -> int:
    for spec in app.registry.describe():
        _print(f"  {spec['name']:<24} [{spec['risk']:<8}] {spec['description']}")
    _print("\nregistered commands: " + ", ".join(app.permissions.get("commands", {})))
    return 0


def cmd_run(app: JarvisApp, args: argparse.Namespace) -> int:
    request = args.request
    intent = app.planner.understand(request, {})
    if intent.name == "unknown":
        _print(intent.clarify)
        return 1

    context = app.context.resolve(request, intent.params)
    if context.get("ambiguity"):
        _print(f"need clarification: {context['ambiguity']}")
        return 1

    _print(f"interpreted intent: {intent.name} (confidence {intent.confidence})")
    if context.get("project_path"):
        _print(f"project: {context['project_path']}")

    if intent.name == "diagnose_project":
        return _run_diagnosis(app, context, args)
    if intent.name == "verify_changes":
        return _run_verification(app, context, args)
    if intent.name == "maintenance_report":
        return _run_maintenance(app, context, args)

    task = app.requests.create(request)
    plan = app.planner.build_plan(task, intent, context)
    _print(f"plan: {len(plan.steps)} steps (task {task.id})")
    outcome = app.orchestrator.run_plan(task)
    for s in outcome.steps:
        mark = "✔" if s.verified else "✖"
        _print(f"  {mark} step {s.sequence}: {s.objective} — {s.verify_detail}")
    _print(f"\ntask {task.id}: {task.state.value}")
    return 0 if outcome.succeeded else 1


def _run_diagnosis(app: JarvisApp, context: dict, args: argparse.Namespace) -> int:
    from automation.project_diagnosis import diagnose

    task = app.requests.create(f"diagnose {context.get('project_path', '?')}")
    report = diagnose(
        app.orchestrator,
        project_path=context.get("project_path", "."),
        reports_dir=app.config["paths"]["reports_dir"],
        task_id=task.id,
    )
    app.memory.set_task_state(task.id, TaskState.SUCCEEDED.value)
    _print(f"\ncause: {report['cause_analysis']}")
    _print(f"report: {report['report_path']}")
    return 0 if report["test_passed"] or report["failing_tests"] else 1


def _run_verification(app: JarvisApp, context: dict, args: argparse.Namespace) -> int:
    from automation.code_verification import verify_changes

    report = verify_changes(
        app.orchestrator,
        project_path=context.get("project_path", "."),
        reports_dir=app.config["paths"]["reports_dir"],
    )
    _print(f"tests passed: {report['tests_passed']}")
    _print(f"report: {report['report_path']}")
    return 0


def _run_maintenance(app: JarvisApp, context: dict, args: argparse.Namespace) -> int:
    from automation.maintenance import maintenance_report

    report = maintenance_report(
        app.orchestrator,
        project_path=context.get("project_path", "."),
        reports_dir=app.config["paths"]["reports_dir"],
    )
    _print(f"report: {report['report_path']}")
    return 0


def cmd_demo(app: JarvisApp, args: argparse.Namespace) -> int:
    from automation.project_diagnosis import diagnose

    demo_path = str((Path(ROOT) / "demo_project").resolve())
    _print("Running Workflow A (project diagnosis) on the demo project…")
    _print(f"demo project: {demo_path}\n")
    report = diagnose(
        app.orchestrator,
        project_path=demo_path,
        reports_dir=app.config["paths"]["reports_dir"],
        task_id="demo",
    )
    _print(f"tests passed: {report['test_passed']}")
    _print(f"cause:\n  {report['cause_analysis']}")
    for e in report["evidence"]:
        _print(f"  evidence: {e}")
    _print(f"\nreport saved: {report['report_path']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jarvis", description="Local AI operating environment")
    parser.add_argument("--yes", action="store_true", help="auto-approve risky actions")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor")
    sub.add_parser("status")
    sub.add_parser("projects")
    sub.add_parser("tools")

    p = sub.add_parser("index")
    p.add_argument("path")

    p = sub.add_parser("task")
    p.add_argument("task_id")

    sub.add_parser("tasks")

    p = sub.add_parser("memory")
    p.add_argument("query")

    p = sub.add_parser("run")
    p.add_argument("request")

    sub.add_parser("demo")
    return parser


COMMANDS = {
    "doctor": cmd_doctor,
    "status": cmd_status,
    "projects": cmd_projects,
    "index": cmd_index,
    "task": cmd_tasks,
    "tasks": cmd_tasks,
    "memory": cmd_memory,
    "tools": cmd_tools,
    "run": cmd_run,
    "demo": cmd_demo,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    approver = _approver_auto if args.yes else _approver_prompt
    app = JarvisApp(project_root=ROOT, approver=approver)
    handler = COMMANDS[args.command]
    return handler(app, args)
