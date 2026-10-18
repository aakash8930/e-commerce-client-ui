"""End-to-end: Workflow A must find the real bug in the demo project.

The demo project contains a deliberate defect (subtract returns a + b).
The diagnosis workflow must produce evidence from real files and real
test output — and must not claim success it cannot prove.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from automation.project_diagnosis import diagnose
from core.action import Action
from core.app import JarvisApp

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo_project"


@pytest.fixture()
def app(tmp_path: Path) -> JarvisApp:
    # isolated data so tests never touch the developer's DB
    return JarvisApp(
        project_root=str(ROOT),
        approver=lambda a, r: True,
        memory_db=str(tmp_path / "m.db"),
        reports_dir=str(tmp_path / "reports"),
    )


def test_demo_project_has_a_known_defect():
    """Guard: the demo bug must exist, or the e2e is meaningless."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=str(DEMO),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode != 0, "demo project should fail its tests"
    assert "test_subtract" in (proc.stdout + proc.stderr)


def test_diagnosis_finds_the_failing_test(app: JarvisApp, tmp_path: Path):
    report = diagnose(
        app.orchestrator,
        project_path=str(DEMO),
        reports_dir=str(tmp_path / "reports"),
        task_id="e2e",
    )
    assert report["test_passed"] is False
    assert report["failing_tests"], "must capture structured failures"
    test_names = [f["test"] for f in report["failing_tests"]]
    assert any("test_subtract" in t for t in test_names)
    assert "subtract" in (report.get("failing_symbol") or "") or report.get("failing_file")
    assert Path(report["report_path"]).exists()
    content = Path(report["report_path"]).read_text(encoding="utf-8")
    assert "test_subtract" in content
    assert "evidence" in content.lower()


def test_diagnosis_remembers_the_outcome(app: JarvisApp, tmp_path: Path):
    diagnose(app.orchestrator, str(DEMO), str(tmp_path / "reports"), task_id="e2e-mem")
    hits = app.memory.search("diagnosed calculator subtract")
    assert hits, "workflow outcome must be retrievable from memory"


def test_file_tools_never_escape_demo(tmp_path: Path):
    """The whole stack must refuse reads outside approved roots."""
    app = JarvisApp(project_root=str(ROOT), approver=lambda a, r: True)
    result, refusal = app.orchestrator.run_action(
        Action(
            tool="filesystem.read_text",
            arguments={"path": "/etc/shadow"},
            reason="should be refused",
        )
    )
    assert not result.ok
    assert refusal is not None


# ---------------------------------------------------------------- Workflow C


@pytest.fixture()
def organize_target(tmp_path: Path) -> Path:
    target = tmp_path / "messy"
    (target / "Documents").mkdir(parents=True)
    (target / "notes.md").write_text("# notes", encoding="utf-8")
    (target / "report.pdf").write_bytes(b"%PDF")
    (target / "photo.png").write_bytes(b"\x89PNG")
    (target / "backup.zip").write_bytes(b"PK")
    (target / "script.py").write_text("print('hi')", encoding="utf-8")
    (target / "mystery.xyz").write_bytes(b"??")
    return target


def _organize_app(tmp_path: Path) -> JarvisApp:
    return JarvisApp(
        project_root=str(ROOT),
        approver=lambda a, r: True,
        memory_db=str(tmp_path / "m.db"),
        reports_dir=str(tmp_path / "reports"),
    )


def test_organize_preview_only_moves_nothing(tmp_path: Path, organize_target: Path):
    from automation.file_organization import organize_files

    app = _organize_app(tmp_path)
    app.policy.approved_roots.append(organize_target.resolve())
    app.policy.write_roots.append(organize_target.resolve())

    report = organize_files(
        app.orchestrator,
        target_dir=str(organize_target),
        reports_dir=str(tmp_path / "reports"),
        approve=lambda plan: False,  # user declines
    )
    assert report["applied"] is False
    assert len(report["planned_moves"]) == 6
    assert (organize_target / "notes.md").exists()  # nothing moved
    assert report["note"].lower().startswith("no files were deleted")


def test_organize_applies_and_verifies(tmp_path: Path, organize_target: Path):
    from automation.file_organization import organize_files

    app = _organize_app(tmp_path)
    app.policy.approved_roots.append(organize_target.resolve())
    app.policy.write_roots.append(organize_target.resolve())

    report = organize_files(
        app.orchestrator,
        target_dir=str(organize_target),
        reports_dir=str(tmp_path / "reports"),
        approve=lambda plan: True,
    )
    assert report["applied"] is True
    assert report["verified"] == 6
    assert (organize_target / "Documents" / "report.pdf").exists()
    assert (organize_target / "Images" / "photo.png").exists()
    assert (organize_target / "Archives" / "backup.zip").exists()
    assert (organize_target / "Code" / "script.py").exists()
    assert (organize_target / "Other" / "mystery.xyz").exists()
    assert not (organize_target / "notes.md").exists()
    # pre-existing Documents dir untouched apart from receiving the pdf
    assert (organize_target / "Documents").is_dir()


def test_organize_move_escape_is_blocked(tmp_path: Path, organize_target: Path):
    """filesystem.move must refuse destinations outside write roots."""
    from automation.file_organization import organize_files

    app = _organize_app(tmp_path)
    # read is allowed, but write_roots deliberately NOT extended →
    # every move must fail safely
    app.policy.approved_roots.append(organize_target.resolve())

    report = organize_files(
        app.orchestrator,
        target_dir=str(organize_target),
        reports_dir=str(tmp_path / "reports"),
        approve=lambda plan: True,
    )
    assert report["verified"] == 0
    assert report["moves_failed"], "every move should be refused"
    assert (organize_target / "notes.md").exists()
