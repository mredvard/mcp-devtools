"""Shared test fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_dir(tmp_path: Path) -> Path:
    """Create a sample directory with test files."""
    # Text files
    (tmp_path / "hello.txt").write_text("Hello, world!\nSecond line\nThird line\n")
    (tmp_path / "data.csv").write_text("name,age\nAlice,30\nBob,25\n")

    # Nested directory
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "nested.txt").write_text("Nested content\n")
    (sub / "code.py").write_text("def foo():\n    return 42\n")

    # Binary-ish file
    (tmp_path / "binary.bin").write_bytes(b"\x00\x01\x02\x03")

    return tmp_path
