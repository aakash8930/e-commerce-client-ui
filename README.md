# jarvis-os — Local AI Operating Environment

A JARVIS-style operating environment that understands requests, inspects
projects, executes controlled actions, verifies results, and remembers what
it did — **entirely locally**. Model-independent by design: the agent runtime
never depends on a remote API or a specific model.

> Target machine: Intel i3 10th Gen, 8 GB RAM, MX Linux, 1 TB HDD.
> Core runtime is **pure Python stdlib** (3.11+); pytest is the only dev dependency.

## What works today (Milestone A + first verified workflow)

- **Structured action format** — the planner never emits raw shell strings; it
  requests typed `Action`s from the orchestrator (`core/action.py`)
- **Tool registry** — 9 tools with input schemas, risk levels and timeouts;
  failures return structured `ToolResult(ok=False)` instead of crashing
- **Policy engine** — approved read/write roots (resolved paths, symlink
  escapes denied), secret-file protection, command allowlist, risk classes
  (low/moderate/high/critical) with approval gates
- **Task state machine** — CREATED → PLANNED → WAITING_FOR_APPROVAL → RUNNING →
  VERIFYING → SUCCEEDED/FAILED/CANCELLED, checkpointed to SQLite
- **Bounded recovery** — max 2 repair attempts, and only for retry-safe steps
- **Memory** — SQLite (projects, tasks, steps, tool runs, observations,
  decisions) with keyword retrieval, dedup by content hash, provenance
- **Project intelligence** — project scans, symbol/reference search, structured
  pytest failure extraction
- **Workflow A: project diagnosis** — runs the tests, captures real failure
  evidence, locates the failing code, reads the implicated source, and writes
  an evidence-based report (never invented architecture)
- **Observability** — `logs/jarvis.log` + `logs/audit.jsonl` audit trail
- **CLI** — doctor, status, projects, index, tasks, task, memory, tools, run, demo

## Quick start (MX Linux / any Linux)

```bash
git clone <this repo> && cd jarvis-os
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# first-run diagnostics
.venv/bin/python main.py doctor

# the showcase: Workflow A finds a real bug in the demo project
.venv/bin/python main.py demo

# natural-language request → intent → plan → verified execution
.venv/bin/python main.py --yes run "diagnose failing tests in demo_project"
```

## CLI

```
python3 main.py doctor                  first-run diagnostics
python3 main.py status                  tasks, projects, resources
python3 main.py projects                known projects
python3 main.py index <path>            register + scan a project
python3 main.py tasks / task <id>       task history
python3 main.py memory "<query>"        search memory
python3 main.py tools                   registered tools & commands
python3 main.py run "<request>"         interpret + plan + execute
python3 main.py demo                    Workflow A on demo_project
```

`--yes` auto-approves risky actions; without it you get an approval prompt.

## Architecture

```
USER → CLI → Request Manager → Context Resolver → Planner
      → Policy Engine → Orchestrator → Tool Registry
      (filesystem / terminal / project / system)
      → Verifier → Memory Manager → SQLite
      → Optional Intelligence Layer (RuleBasedEngine today)
```

Key rule: **the planner never executes anything**. It produces a structured
plan; the orchestrator checks policy, asks for approval when risk demands it,
executes a registered tool, and the verifier checks the actual outcome.

| Package | Responsibility |
| --- | --- |
| `core/` | action contracts, task states, policy, planner, orchestrator, verifier |
| `tools/` | registry + filesystem, terminal (allowlisted), system, project tools |
| `memory/` | SQLite persistence, keyword retrieval, logging/audit |
| `models/` | `ReasoningEngine` interface + deterministic `RuleBasedEngine` |
| `automation/` | workflows: project diagnosis, change verification, maintenance |
| `interfaces/` | CLI |
| `demo_project/` | tiny project with a deliberate bug (`subtract` returns `a + b`) |
| `tests/` | safety, tools, memory, planner, orchestrator, end-to-end |

## Safety model

- Filesystem access is validated on **resolved** paths (symlinks followed,
  traversal escapes denied) against roots in `configs/permissions.toml`
- Secret files (`.env`, `*.pem`, `id_rsa`, `.ssh`, `.aws`, …) are blocked by default
- The terminal tool runs **only allowlisted commands** from `permissions.toml`,
  with `shell=False` and hard timeouts
- Risky actions require explicit approval; critical actions are blocked outright
- File/document contents are treated as **untrusted data**, never as instructions
  that can change policy

## Tests

```bash
.venv/bin/python -m pytest
```

38 tests: policy escape attempts (traversal, symlinks, secrets), tool failure
handling & timeouts, memory persistence across restart, planner validation,
orchestrator state machine & bounded repair, and an end-to-end diagnosis of the
demo project's known bug.

## Roadmap status

| Phase | Status |
| --- | --- |
| 0 — audit baseline, reproducible env, test suite | ✅ |
| 1 — execution engine (action format, states, timeouts) | ✅ |
| 2 — safety & permissions | ✅ |
| 3 — memory as knowledge system | ✅ baseline (keyword retrieval, dedup, provenance) |
| 4 — project intelligence | ✅ baseline (scan, symbols, failure extraction) |
| 5 — task planner | ✅ baseline (deterministic templates + validation) |
| 6 — intelligence layer | ✅ interface + rule-based engine (model plug-in point) |
| 7 — desktop control | ⬜ next |
| 8 — automation workflows | ✅ A/B/D; C (file organization) pending |
| 9 — verification & self-repair | ✅ bounded repair (max 2) |
| 10 — interface | ✅ CLI; desktop/web UI later |
| 11 — reliability & offline | ⬜ offline works; perf report pending |
| 12 — alpha release | ⬜ |

## Data & privacy

Everything lives in `data/` (SQLite memory, reports) and `logs/` — both are
git-ignored. Nothing leaves the machine. To wipe: delete `data/` and `logs/`.
