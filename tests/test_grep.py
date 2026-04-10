"""Tests for grep_files tool."""

from devtools.tools.grep import grep_files


def test_grep_simple(sample_dir):
    result = grep_files("Hello", path=str(sample_dir))
    assert "hello.txt:1:Hello, world!" in result


def test_grep_regex(sample_dir):
    result = grep_files(r"def \w+", path=str(sample_dir))
    assert "code.py" in result
    assert "def foo" in result


def test_grep_case_insensitive(sample_dir):
    result = grep_files("hello", path=str(sample_dir), case_insensitive=True)
    assert "hello.txt" in result


def test_grep_glob_filter(sample_dir):
    result = grep_files(".*", path=str(sample_dir), glob_filter="*.csv")
    assert "data.csv" in result
    assert "hello.txt" not in result


def test_grep_context(sample_dir):
    result = grep_files("Second", path=str(sample_dir), context=1)
    assert "Hello, world!" in result
    assert "Third line" in result


def test_grep_no_matches(sample_dir):
    result = grep_files("zzzznotfound", path=str(sample_dir))
    assert "No matches found" in result


def test_grep_skips_binary(sample_dir):
    result = grep_files(".*", path=str(sample_dir))
    assert "binary.bin" not in result


def test_grep_invalid_regex(sample_dir):
    try:
        grep_files("[invalid", path=str(sample_dir))
        assert False, "Should have raised"
    except ValueError:
        pass
