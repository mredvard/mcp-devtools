"""Tests for read_file tool."""

import json
from pathlib import Path

from devtools.tools.read import read_file


def test_read_text_file(sample_dir):
    result = read_file(str(sample_dir / "hello.txt"))
    assert "1\tHello, world!" in result
    assert "2\tSecond line" in result
    assert "3\tThird line" in result


def test_read_with_offset(sample_dir):
    result = read_file(str(sample_dir / "hello.txt"), offset=1)
    assert "2\tSecond line" in result
    assert "Hello, world!" not in result


def test_read_with_limit(sample_dir):
    result = read_file(str(sample_dir / "hello.txt"), limit=1)
    assert "1\tHello, world!" in result
    assert "Second line" not in result


def test_read_with_offset_and_limit(sample_dir):
    result = read_file(str(sample_dir / "hello.txt"), offset=1, limit=1)
    assert "2\tSecond line" in result
    assert "Hello, world!" not in result
    assert "Third line" not in result


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
    assert "[Binary file:" in result


def test_read_image_file(tmp_path):
    img = tmp_path / "test.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\nfakedata")
    result = read_file(str(img))
    assert "[Image: test.png]" in result
    assert "base64:" in result


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
    assert "Cell 1 [code]" in result
    assert "print('hello')" in result
    assert "[Output]" in result
    assert "Cell 2 [markdown]" in result
    assert "# Title" in result
