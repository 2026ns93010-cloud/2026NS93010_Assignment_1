from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile

VALID_PRIORITIES = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
VALID_STATUSES = {"TODO", "IN_PROGRESS", "DONE"}
ALLOWED_TRANSITIONS = {
    "TODO": {"IN_PROGRESS", "DONE"},
    "IN_PROGRESS": {"DONE"},
    "DONE": set(),
}


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    status: str = "TODO"
    priority: str = "MEDIUM"
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Task":
        tags = payload.get("tags", [])
        if not isinstance(tags, list):
            raise ValueError("Task tags must be a list of strings.")
        return cls(
            id=str(payload["id"]),
            title=str(payload["title"]),
            description=str(payload.get("description", "")),
            status=str(payload.get("status", "TODO")),
            priority=str(payload.get("priority", "MEDIUM")),
            tags=[str(item) for item in tags],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "tags": self.tags,
        }


class TaskStore:
    def __init__(self, storage_path: str | Path):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._write_tasks([])

    def _read_tasks(self) -> list[Task]:
        try:
            raw = self.storage_path.read_text(encoding="utf-8")
            if not raw.strip():
                return []
            payload = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            return []

        if isinstance(payload, dict):
            payload = payload.get("tasks", [])
        if not isinstance(payload, list):
            return []

        tasks: list[Task] = []
        for item in payload:
            if isinstance(item, dict):
                tasks.append(Task.from_dict(item))
        return tasks

    def _write_tasks(self, tasks: list[Task]) -> None:
        serializable = [task.to_dict() for task in tasks]
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=str(self.storage_path.parent),
            delete=False,
        ) as handle:
            json.dump(serializable, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, self.storage_path)

    def list_tasks(self) -> list[Task]:
        return self._read_tasks()

    def save_tasks(self, tasks: list[Task]) -> None:
        self._write_tasks(tasks)


class TaskService:
    def __init__(self, storage_path: str | Path):
        self.store = TaskStore(storage_path)

    @staticmethod
    def _validate_priority(priority: str) -> str:
        upper = priority.upper()
        if upper not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}")
        return upper

    @staticmethod
    def _validate_status(status: str) -> str:
        upper = status.upper()
        if upper not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        return upper

    @staticmethod
    def _ensure_transition(current_status: str, next_status: str) -> None:
        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if next_status not in allowed:
            raise ValueError(
                f"Invalid status transition from {current_status} to {next_status}."
            )

    def add_task(
        self,
        task_id: str,
        title: str,
        description: str = "",
        status: str = "TODO",
        priority: str = "MEDIUM",
        tags: list[str] | None = None,
    ) -> Task:
        task_id = str(task_id)
        tasks = self.store.list_tasks()
        if any(task.id == task_id for task in tasks):
            raise ValueError(f"Task id already exists: {task_id}")

        normalized_status = self._validate_status(status)
        normalized_priority = self._validate_priority(priority)
        if normalized_status != "TODO":
            raise ValueError("New tasks must start in TODO status.")

        task = Task(
            id=task_id,
            title=title,
            description=description,
            status=normalized_status,
            priority=normalized_priority,
            tags=[str(tag) for tag in (tags or [])],
        )
        tasks.append(task)
        self.store.save_tasks(tasks)
        return task

    def get_task(self, task_id: str) -> Task | None:
        for task in self.store.list_tasks():
            if task.id == task_id:
                return task
        return None

    def update_status(self, task_id: str, new_status: str) -> Task:
        tasks = self.store.list_tasks()
        for index, task in enumerate(tasks):
            if task.id == task_id:
                validated_status = self._validate_status(new_status)
                self._ensure_transition(task.status, validated_status)
                task.status = validated_status
                tasks[index] = task
                self.store.save_tasks(tasks)
                return task
        raise ValueError(f"Task not found: {task_id}")

    def delete_task(self, task_id: str) -> None:
        tasks = self.store.list_tasks()
        filtered = [task for task in tasks if task.id != task_id]
        if len(filtered) == len(tasks):
            raise ValueError(f"Task not found: {task_id}")
        self.store.save_tasks(filtered)

    def list_tasks(
        self,
        tag: str | None = None,
        status: str | None = None,
    ) -> list[Task]:
        tasks = self.store.list_tasks()
        if tag is not None:
            tasks = [task for task in tasks if tag in task.tags]
        if status is not None:
            normalized = self._validate_status(status)
            tasks = [task for task in tasks if task.status == normalized]
        return sorted(
            tasks,
            key=lambda task: (-VALID_PRIORITIES[task.priority], task.title.lower(), task.id),
        )
