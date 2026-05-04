"""Tests for edit_file tool."""

from devtools.tools.edit import edit_file


def test_edit_single_replacement(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello world")
    result = edit_file(str(f), "Hello", "Goodbye")
    assert result.replacements == 1
    assert result.replace_all is False
    assert f.read_text() == "Goodbye world"


def test_edit_replace_all(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("aaa bbb aaa")
    result = edit_file(str(f), "aaa", "ccc", replace_all=True)
    assert result.replacements == 2
    assert result.replace_all is True
    assert f.read_text() == "ccc bbb ccc"


def test_edit_not_found(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello world")
    try:
        edit_file(str(f), "missing", "replacement")
        assert False, "Should have raised"
    except ValueError as e:
        assert "not found" in str(e)


def test_edit_ambiguous(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("aaa bbb aaa")
    try:
        edit_file(str(f), "aaa", "ccc", replace_all=False)
        assert False, "Should have raised"
    except ValueError as e:
        assert "2 times" in str(e)


def test_edit_nonexistent():
    try:
        edit_file("/nonexistent/file.txt", "a", "b")
        assert False, "Should have raised"
    except FileNotFoundError:
        pass


def test_edit_multiline(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("line1\nline2\nline3\n")
    result = edit_file(str(f), "line2\nline3", "replaced")
    assert result.replacements == 1
    assert f.read_text() == "line1\nreplaced\n"
