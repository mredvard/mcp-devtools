"""Todo/task tracking tool."""

import json
import uuid
from pathlib import Path

from devtools.server import mcp
from devtools.tools.models import Todo, TodoWriteResult

_todos: dict[str, dict] = {}

VALID_STATUSES = {"pending", "in_progress", "done"}
VALID_ACTIONS = {"add", "update", "remove", "list", "clear"}


def _snapshot() -> list[Todo]:
    return [Todo(**t) for t in _todos.values()]


@mcp.tool()
def todo_write(
    action: str,
    content: str | None = None,
    todo_id: str | None = None,
    status: str | None = None,
    persist_file: str | None = None,
) -> TodoWriteResult:
    """Manage a task list with add, update, remove, list, and clear actions.

    Args:
        action: One of 'add', 'update', 'remove', 'list', 'clear'.
        content: Task description (required for 'add').
        todo_id: Task ID (required for 'update' and 'remove').
        status: Task status: 'pending', 'in_progress', or 'done'.
        persist_file: Optional JSON file path for persistence.

    Returns:
        Structured result with the action, a human-readable message, the full
        current todo list, and the affected todo id (when applicable).
    """
    global _todos

    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid action '{action}'. Must be one of: add, update, remove, list, clear")

    if persist_file:
        _load(persist_file)

    affected_id: str | None = None
    message: str

    if action == "add":
        if not content:
            raise ValueError("content is required for 'add' action")
        if status and status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")
        tid = str(uuid.uuid4())[:8]
        _todos[tid] = {
            "id": tid,
            "content": content,
            "status": status or "pending",
        }
        _save(persist_file)
        affected_id = tid
        message = f"Added todo {tid}: {content}"

    elif action == "update":
        if not todo_id:
            raise ValueError("todo_id is required for 'update' action")
        if todo_id not in _todos:
            raise KeyError(f"Todo not found: {todo_id}")
        if content:
            _todos[todo_id]["content"] = content
        if status:
            if status not in VALID_STATUSES:
                raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")
            _todos[todo_id]["status"] = status
        _save(persist_file)
        affected_id = todo_id
        message = f"Updated todo {todo_id}"

    elif action == "remove":
        if not todo_id:
            raise ValueError("todo_id is required for 'remove' action")
        if todo_id not in _todos:
            raise KeyError(f"Todo not found: {todo_id}")
        del _todos[todo_id]
        _save(persist_file)
        affected_id = todo_id
        message = f"Removed todo {todo_id}"

    elif action == "list":
        message = "No todos." if not _todos else f"{len(_todos)} todo(s)."

    else:  # clear
        count = len(_todos)
        _todos.clear()
        _save(persist_file)
        message = f"Cleared {count} todos."

    return TodoWriteResult(
        action=action,
        message=message,
        todos=_snapshot(),
        affected_id=affected_id,
    )


def _load(persist_file: str | None):
    global _todos
    if persist_file:
        p = Path(persist_file)
        if p.exists():
            _todos = json.loads(p.read_text(encoding="utf-8"))


def _save(persist_file: str | None):
    if persist_file:
        p = Path(persist_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(_todos, indent=2), encoding="utf-8")
