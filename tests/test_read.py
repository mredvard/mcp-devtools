"""Tests for read_file tool."""

import json

from devtools.tools.read import read_file


def test_read_text_file(sample_dir):
    result = read_file(str(sample_dir / "hello.txt"))
    assert result.kind == "text"
    assert "1\tHello, world!" in result.content
    assert "2\tSecond line" in result.content
    assert "3\tThird line" in result.content
    assert result.line_count == 3
    assert result.start_line == 1
    assert result.truncated is False
    assert result.byte_size > 0


def test_read_with_offset(sample_dir):
    result = read_file(str(sample_dir / "hello.txt"), offset=1)
    assert "2\tSecond line" in result.content
    assert "Hello, world!" not in result.content
    assert result.start_line == 2


def test_read_with_limit(sample_dir):
    result = read_file(str(sample_dir / "hello.txt"), limit=1)
    assert "1\tHello, world!" in result.content
    assert "Second line" not in result.content
    assert result.line_count == 1
    assert result.truncated is True


def test_read_with_offset_and_limit(sample_dir):
    result = read_file(str(sample_dir / "hello.txt"), offset=1, limit=1)
    assert "2\tSecond line" in result.content
    assert "Hello, world!" not in result.content
    assert "Third line" not in result.content
    assert result.start_line == 2
    assert result.truncated is True


def test_read_nonexistent():
    try:
        read_file("/nonexistent/file.txt")
        assert False, "Should have raised"
    except FileNotFoundError:
        pass


def test_read_directory(sample_dir):
    try:
        read_file(str(sample_dir))
        assert False, "Should have raised"
    except IsADirectoryError:
        pass


def test_read_binary_file(sample_dir):
    result = read_file(str(sample_dir / "binary.bin"))
    assert result.kind == "binary"
    assert "[Binary file:" in result.content


def test_read_image_file(tmp_path):
    img = tmp_path / "test.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\nfakedata")
    result = read_file(str(img))
    assert result.kind == "image"
    assert "[Image: test.png]" in result.content
    assert "base64:" in result.content


def test_read_notebook(tmp_path):
    nb = {
        "cells": [
            {
                "cell_type": "code",
                "source": ["print('hello')"],
                "outputs": [{"text": ["hello\n"]}],
            },
            {
                "cell_type": "markdown",
                "source": ["# Title"],
                "outputs": [],
            },
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path = tmp_path / "test.ipynb"
    path.write_text(json.dumps(nb))
    result = read_file(str(path))
    assert result.kind == "notebook"
    assert "Cell 1 [code]" in result.content
    assert "print('hello')" in result.content
    assert "[Output]" in result.content
    assert "Cell 2 [markdown]" in result.content
    assert "# Title" in result.content
