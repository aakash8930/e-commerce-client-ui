"""Request manager: assigns task IDs and tracks task state."""

from __future__ import annotations

from typing import Any

from core.task import Task, TaskState
from memory.database import MemoryDB


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

    def history(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.memory.list_tasks(limit=limit)
