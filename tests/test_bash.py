"""Tests for bash_exec tool."""

from unittest.mock import patch
import subprocess

import pytest

from devtools.tools.bash import bash_exec


@pytest.fixture
def workdir(tmp_path):
    """A real, existing working directory to satisfy bash_exec's cwd check.

    The default workdir is `/home/sandbox`, which only exists in the container
    image — host test runs need an explicit cwd.
    """
    return str(tmp_path)


def test_bash_echo(workdir):
    result = bash_exec("echo hello", cwd=workdir)
    assert "hello" in result.stdout
    assert result.exit_code == 0
    assert result.timed_out is False


def test_bash_stderr(workdir):
    result = bash_exec("echo err >&2", cwd=workdir)
    assert "err" in result.stderr


def test_bash_nonzero_exit(workdir):
    result = bash_exec("exit 42", cwd=workdir)
    assert result.exit_code == 42


def test_bash_cwd(tmp_path):
    result = bash_exec("pwd", cwd=str(tmp_path))
    assert str(tmp_path) in result.stdout
    assert result.cwd == str(tmp_path)


def test_bash_invalid_cwd():
    with pytest.raises(FileNotFoundError):
        bash_exec("echo hi", cwd="/nonexistent/dir")


def test_bash_timeout(workdir):
    with patch("devtools.tools.bash.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 1)):
        result = bash_exec("sleep 999", timeout=1, cwd=workdir)
        assert result.timed_out is True
        assert result.exit_code == -1
        assert "timed out" in result.stderr


def test_bash_timeout_cap(workdir):
    with patch("devtools.tools.bash.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args="", returncode=0, stdout="", stderr="")
        bash_exec("echo hi", timeout=9999, cwd=workdir)
        assert mock_run.call_args.kwargs["timeout"] == 600
