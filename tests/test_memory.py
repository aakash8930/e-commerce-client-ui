"""Memory tests: persistence across restart, dedup, keyword retrieval."""

from pathlib import Path

from memory.database import MemoryDB


def test_task_persists_across_restart(tmp_path: Path):
    db_path = tmp_path / "mem.db"
    db = MemoryDB(db_path)
    db.create_task("abc123", "fix the failing tests in demo project")
    db.set_task_state("abc123", "succeeded")
    db.log_step("abc123", 1, "scan", {"tool": "project.scan"}, "ok", "fine")
    db.close()

    db2 = MemoryDB(db_path)  # "restart"
    task = db2.get_task("abc123")
    assert task is not None
    assert task["goal"] == "fix the failing tests in demo project"
    assert task["status"] == "succeeded"
    assert len(task["steps"]) == 1
    db2.close()


def test_observation_dedup(tmp_path: Path):
    db = MemoryDB(tmp_path / "mem.db")
    first = db.add_observation("project X uses pytest for testing")
    second = db.add_observation("project X uses pytest for testing")
    assert first is not None
    assert second is None  # duplicate suppressed
    db.close()


def test_keyword_retrieval(tmp_path: Path):
    db = MemoryDB(tmp_path / "mem.db")
    db.add_observation("the calculator project has a bug in subtract", category="episodic")
    db.add_observation("unrelated note about gardening", category="episodic")
    db.add_decision("use pytest as the test runner", "standard tooling")

    results = db.search("calculator bug")
    assert results
    assert "calculator" in results[0]["content"].lower()
    db.close()


def test_retrieval_after_restart(tmp_path: Path):
    db_path = tmp_path / "mem.db"
    db = MemoryDB(db_path)
    db.add_observation("decision: approved roots are under ~/Projects", category="semantic")
    db.close()

    db2 = MemoryDB(db_path)
    hits = db2.search("approved roots")
    assert any("approved roots" in h["content"].lower() for h in hits)
    db2.close()


def test_tool_runs_recorded(tmp_path: Path):
    db = MemoryDB(tmp_path / "mem.db")
    db.log_tool_run("t1", "filesystem.read_text", "ok", 12)
    db.log_tool_run("t1", "terminal.run", "error", 30, "timed out")
    rows = db.conn.execute("SELECT * FROM tool_runs WHERE task_id='t1'").fetchall()
    assert len(rows) == 2
    db.close()
