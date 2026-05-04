"""Tests for todo_write tool."""

import json

import pytest

import devtools.tools.todo_write as todo_mod
from devtools.tools.todo_write import todo_write


def setup_function():
    """Clear todos before each test."""
    todo_mod._todos = []


def test_write_single_todo():
    result = todo_write([{"content": "Write tests"}])
    assert result.count == 1
    assert len(result.todos) == 1
    assert result.todos[0].content == "Write tests"
    assert result.todos[0].status == "pending"


def test_write_empty_list_clears():
    todo_write([{"content": "Task 1"}, {"content": "Task 2"}])
    result = todo_write([])
    assert result.count == 0
    assert result.todos == []
    assert "Cleared" in result.message


def test_write_batch_replaces_existing():
    todo_write([{"content": "Old"}])
    result = todo_write(
        [
            {"content": "Task 1", "status": "in_progress"},
            {"content": "Task 2", "status": "pending"},
            {"content": "Task 3", "status": "done"},
        ]
    )
    assert result.count == 3
    contents = [t.content for t in result.todos]
    assert contents == ["Task 1", "Task 2", "Task 3"]
    assert result.todos[0].status == "in_progress"
    assert result.todos[2].status == "done"


def test_status_defaults_to_pending():
    result = todo_write([{"content": "A"}, {"content": "B"}])
    assert all(t.status == "pending" for t in result.todos)


def test_update_status_via_rewrite():
    first = todo_write([{"content": "Do something"}])
    item = first.todos[0]
    result = todo_write([{"content": item.content, "status": "done"}])
    assert result.todos[0].status == "done"


def test_persistence(tmp_path):
    pf = str(tmp_path / "todos.json")
    todo_write([{"content": "Persisted"}], persist_file=pf)
    todo_mod._todos = []
    todo_mod._load(pf)
    assert len(todo_mod._todos) == 1
    assert todo_mod._todos[0].content == "Persisted"
    data = json.loads((tmp_path / "todos.json").read_text())
    assert len(data) == 1
    assert data[0]["content"] == "Persisted"


def test_invalid_status():
    with pytest.raises(Exception):
        todo_write([{"content": "x", "status": "invalid"}])


def test_empty_content_rejected():
    with pytest.raises(ValueError):
        todo_write([{"content": ""}])
