"""Tests for todo_write tool."""

import json

import devtools.tools.todo_write as todo_mod
from devtools.tools.todo_write import todo_write


def setup_function():
    """Clear todos before each test."""
    todo_mod._todos.clear()


def test_add_todo():
    result = todo_write("add", content="Write tests")
    assert result.action == "add"
    assert result.affected_id is not None
    assert len(result.todos) == 1
    assert result.todos[0].content == "Write tests"
    assert result.todos[0].status == "pending"


def test_list_empty():
    result = todo_write("list")
    assert result.todos == []
    assert "No todos" in result.message


def test_add_and_list():
    todo_write("add", content="Task 1")
    todo_write("add", content="Task 2")
    result = todo_write("list")
    contents = [t.content for t in result.todos]
    assert "Task 1" in contents
    assert "Task 2" in contents


def test_update_status():
    add = todo_write("add", content="Do something")
    todo_write("update", todo_id=add.affected_id, status="done")
    listing = todo_write("list")
    assert listing.todos[0].status == "done"


def test_update_content():
    add = todo_write("add", content="Old content")
    todo_write("update", todo_id=add.affected_id, content="New content")
    listing = todo_write("list")
    assert listing.todos[0].content == "New content"


def test_remove():
    add = todo_write("add", content="Remove me")
    rem = todo_write("remove", todo_id=add.affected_id)
    assert rem.affected_id == add.affected_id
    listing = todo_write("list")
    assert listing.todos == []


def test_clear():
    todo_write("add", content="A")
    todo_write("add", content="B")
    result = todo_write("clear")
    assert "Cleared 2" in result.message
    assert result.todos == []


def test_persistence(tmp_path):
    pf = str(tmp_path / "todos.json")
    todo_write("add", content="Persisted", persist_file=pf)
    todo_mod._todos.clear()
    result = todo_write("list", persist_file=pf)
    assert any(t.content == "Persisted" for t in result.todos)
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
    add = todo_write("add", content="Test")
    try:
        todo_write("update", todo_id=add.affected_id, status="invalid")
        assert False, "Should have raised"
    except ValueError:
        pass


def test_remove_nonexistent():
    try:
        todo_write("remove", todo_id="nonexistent")
        assert False, "Should have raised"
    except KeyError:
        pass
