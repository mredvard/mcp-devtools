"""Tests for todo_write tool."""

import json

import devtools.tools.todo_write as todo_mod
from devtools.tools.todo_write import todo_write


def setup_function():
    """Clear todos before each test."""
    todo_mod._todos.clear()


def test_add_todo():
    result = todo_write("add", content="Write tests")
    assert "Added todo" in result
    assert "Write tests" in result


def test_list_empty():
    result = todo_write("list")
    assert "No todos" in result


def test_add_and_list():
    todo_write("add", content="Task 1")
    todo_write("add", content="Task 2")
    result = todo_write("list")
    assert "Task 1" in result
    assert "Task 2" in result


def test_update_status():
    result = todo_write("add", content="Do something")
    tid = result.split()[2].rstrip(":")
    todo_write("update", todo_id=tid, status="done")
    listing = todo_write("list")
    assert "[done]" in listing


def test_update_content():
    result = todo_write("add", content="Old content")
    tid = result.split()[2].rstrip(":")
    todo_write("update", todo_id=tid, content="New content")
    listing = todo_write("list")
    assert "New content" in listing


def test_remove():
    result = todo_write("add", content="Remove me")
    tid = result.split()[2].rstrip(":")
    todo_write("remove", todo_id=tid)
    listing = todo_write("list")
    assert "No todos" in listing


def test_clear():
    todo_write("add", content="A")
    todo_write("add", content="B")
    result = todo_write("clear")
    assert "Cleared 2" in result
    assert "No todos" in todo_write("list")


def test_persistence(tmp_path):
    pf = str(tmp_path / "todos.json")
    todo_write("add", content="Persisted", persist_file=pf)
    # Clear in-memory and reload from file
    todo_mod._todos.clear()
    result = todo_write("list", persist_file=pf)
    assert "Persisted" in result
    # Verify file content
    data = json.loads((tmp_path / "todos.json").read_text())
    assert len(data) == 1


def test_invalid_action():
    try:
        todo_write("invalid")
        assert False, "Should have raised"
    except ValueError:
        pass


def test_add_missing_content():
    try:
        todo_write("add")
        assert False, "Should have raised"
    except ValueError:
        pass


def test_update_missing_id():
    try:
        todo_write("update", status="done")
        assert False, "Should have raised"
    except ValueError:
        pass


def test_update_invalid_status():
    result = todo_write("add", content="Test")
    tid = result.split()[2].rstrip(":")
    try:
        todo_write("update", todo_id=tid, status="invalid")
        assert False, "Should have raised"
    except ValueError:
        pass


def test_remove_nonexistent():
    try:
        todo_write("remove", todo_id="nonexistent")
        assert False, "Should have raised"
    except KeyError:
        pass
