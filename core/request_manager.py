"""Request manager: assigns task IDs, tracks state, recovers interrupted work."""

from __future__ import annotations

from typing import Any

from core.task import Task, TaskState
from memory.database import MemoryDB

# states that mean "was executing when the process stopped"
INTERRUPTED_STATES = ("running", "verifying")


class RequestManager:
    def __init__(self, memory: MemoryDB) -> None:
        self.memory = memory

    def create(self, goal: str) -> Task:
        task = Task(goal=goal)
        self.memory.create_task(task.id, goal)
        return task

    def record_state(self, task: Task) -> None:
        self.memory.set_task_state(task.id, task.state.value, task.error)

    def cancel(self, task: Task) -> None:
        if task.state not in {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED}:
            task.transition(TaskState.CANCELLED)
            self.record_state(task)

    def recover_interrupted(self) -> list[str]:
        """Mark tasks that were mid-execution at a crash/exit as failed with a
        clear 'interrupted' error, so nothing is ever stuck 'running'.

        Returns the recovered task ids. Called once at startup.
        """
        recovered: list[str] = []
        rows = self.memory.conn.execute(
            f"SELECT id FROM tasks WHERE status IN ({','.join('?' * len(INTERRUPTED_STATES))})",
            INTERRUPTED_STATES,
        ).fetchall()
        for row in rows:
            task_id = row["id"]
            self.memory.set_task_state(
                task_id,
                "failed",
                "interrupted — recovered at startup (no side effects are replayed)",
            )
            recovered.append(task_id)
        return recovered

    def history(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.memory.list_tasks(limit=limit)
