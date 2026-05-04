"""Tests for grep_files tool."""

from devtools.tools.grep import grep_files


def test_grep_simple(sample_dir):
    result = grep_files("Hello", path=str(sample_dir))
    hits = [m for m in result.matches if m.file_path.endswith("hello.txt")]
    assert hits
    assert hits[0].line_number == 1
    assert "Hello, world!" in hits[0].line
    assert hits[0].is_context is False


def test_grep_regex(sample_dir):
    result = grep_files(r"def \w+", path=str(sample_dir))
    hits = [m for m in result.matches if m.file_path.endswith("code.py")]
    assert any("def foo" in m.line for m in hits)


def test_grep_case_insensitive(sample_dir):
    result = grep_files("hello", path=str(sample_dir), case_insensitive=True)
    assert any(m.file_path.endswith("hello.txt") for m in result.matches)


def test_grep_glob_filter(sample_dir):
    result = grep_files(".*", path=str(sample_dir), glob_filter="*.csv")
    files = {m.file_path for m in result.matches}
    assert any(f.endswith("data.csv") for f in files)
    assert not any(f.endswith("hello.txt") for f in files)


def test_grep_context(sample_dir):
    result = grep_files("Second", path=str(sample_dir), context=1)
    lines = [m.line for m in result.matches]
    assert any("Hello, world!" in line for line in lines)
    assert any("Third line" in line for line in lines)
    assert any(m.is_context for m in result.matches)
    assert any(not m.is_context for m in result.matches)


def test_grep_no_matches(sample_dir):
    result = grep_files("zzzznotfound", path=str(sample_dir))
    assert result.matches == []
    assert result.total_matches == 0
    assert result.truncated is False


def test_grep_skips_binary(sample_dir):
    result = grep_files(".*", path=str(sample_dir))
    assert not any(m.file_path.endswith("binary.bin") for m in result.matches)


def test_grep_invalid_regex(sample_dir):
    try:
        grep_files("[invalid", path=str(sample_dir))
        assert False, "Should have raised"
    except ValueError:
        pass
