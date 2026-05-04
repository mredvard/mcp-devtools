"""Tests for glob_files tool."""

from devtools.tools.glob_tool import glob_files


def test_glob_all_files(sample_dir):
    result = glob_files("*", path=str(sample_dir))
    names = [m.split("/")[-1] for m in result.matches]
    assert "hello.txt" in names
    assert "data.csv" in names
    assert result.total_matches >= 2


def test_glob_by_extension(sample_dir):
    result = glob_files("**/*.py", path=str(sample_dir))
    names = [m.split("/")[-1] for m in result.matches]
    assert "code.py" in names
    assert "hello.txt" not in names


def test_glob_recursive(sample_dir):
    result = glob_files("**/*.txt", path=str(sample_dir))
    names = [m.split("/")[-1] for m in result.matches]
    assert "hello.txt" in names
    assert "nested.txt" in names


def test_glob_no_matches(sample_dir):
    result = glob_files("*.xyz", path=str(sample_dir))
    assert result.matches == []
    assert result.total_matches == 0
    assert result.truncated is False


def test_glob_nonexistent_dir():
    try:
        glob_files("*", path="/nonexistent/dir")
        assert False, "Should have raised"
    except FileNotFoundError:
        pass
