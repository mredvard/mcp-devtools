"""Todo/task tracking tool."""

import json
from pathlib import Path

from devtools.server import mcp
from devtools.tools.models import Todo, TodoWriteResult

_todos: list[Todo] = []

VALID_STATUSES = {"pending", "in_progress", "done"}


@mcp.tool()
def todo_write(
    todos: list[Todo],
    persist_file: str | None = None,
) -> TodoWriteResult:
    """Replace the current task list with the provided todos.

    Pass the entire desired list on every call. The previous list is discarded
    and fully replaced — there is no add/update/remove; you express the new
    state declaratively.

    Args:
        todos: The full desired todo list. Each item has `content` and an
            optional `status` ('pending', 'in_progress', or 'done';
            defaults to 'pending').
        persist_file: Optional JSON file path for persistence.

    Returns:
        Structured result with a human-readable message, the full todo list
        as it now stands, and its count.
    """
    global _todos

    normalized: list[Todo] = []
    for i, t in enumerate(todos):
        item = t if isinstance(t, Todo) else Todo(**t)
        if item.status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{item.status}' at index {i}. "
                f"Must be one of: {sorted(VALID_STATUSES)}"
            )
        if not item.content:
            raise ValueError(f"Empty content at index {i}.")
        normalized.append(item)

    _todos = normalized
    _save(persist_file)

    return TodoWriteResult(
        message=f"Wrote {len(_todos)} todo(s)." if _todos else "Cleared todo list.",
        todos=list(_todos),
        count=len(_todos),
    )


def _load(persist_file: str | None):
    global _todos
    if persist_file:
        p = Path(persist_file)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            _todos = [Todo(**t) for t in data]


def _save(persist_file: str | None):
    if persist_file:
        p = Path(persist_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps([t.model_dump() for t in _todos], indent=2),
            encoding="utf-8",
        )
