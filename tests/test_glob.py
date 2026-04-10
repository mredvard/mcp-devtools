"""Tests for glob_files tool."""

from devtools.tools.glob_tool import glob_files


def test_glob_all_files(sample_dir):
    result = glob_files("*", path=str(sample_dir))
    assert "hello.txt" in result
    assert "data.csv" in result


def test_glob_by_extension(sample_dir):
    result = glob_files("**/*.py", path=str(sample_dir))
    assert "code.py" in result
    assert "hello.txt" not in result


def test_glob_recursive(sample_dir):
    result = glob_files("**/*.txt", path=str(sample_dir))
    assert "hello.txt" in result
    assert "nested.txt" in result


def test_glob_no_matches(sample_dir):
    result = glob_files("*.xyz", path=str(sample_dir))
    assert "No files matched" in result


def test_glob_nonexistent_dir():
    try:
        glob_files("*", path="/nonexistent/dir")
        assert False, "Should have raised"
    except FileNotFoundError:
        pass
