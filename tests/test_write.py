"""Tests for write_file tool."""

from devtools.tools.write import write_file


def test_write_new_file(tmp_path):
    path = str(tmp_path / "new.txt")
    result = write_file(path, "hello world")
    assert result.bytes_written == 11
    assert result.created is True
    assert (tmp_path / "new.txt").read_text() == "hello world"


def test_write_overwrite(tmp_path):
    path = str(tmp_path / "existing.txt")
    (tmp_path / "existing.txt").write_text("old content")
    result = write_file(path, "new content")
    assert result.bytes_written == 11
    assert result.created is False
    assert (tmp_path / "existing.txt").read_text() == "new content"


def test_write_creates_parent_dirs(tmp_path):
    path = str(tmp_path / "a" / "b" / "c" / "file.txt")
    result = write_file(path, "deep")
    assert result.bytes_written == 4
    assert result.created is True
    assert (tmp_path / "a" / "b" / "c" / "file.txt").read_text() == "deep"


def test_write_no_create_dirs(tmp_path):
    path = str(tmp_path / "missing" / "file.txt")
    try:
        write_file(path, "content", create_dirs=False)
        assert False, "Should have raised"
    except (FileNotFoundError, OSError):
        pass


def test_write_empty_file(tmp_path):
    path = str(tmp_path / "empty.txt")
    result = write_file(path, "")
    assert result.bytes_written == 0
    assert result.created is True
