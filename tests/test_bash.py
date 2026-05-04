"""Tests for bash_exec tool."""

from unittest.mock import patch
import subprocess

from devtools.tools.bash import bash_exec


def test_bash_echo():
    result = bash_exec("echo hello")
    assert "hello" in result.stdout
    assert result.exit_code == 0
    assert result.timed_out is False


def test_bash_stderr():
    result = bash_exec("echo err >&2")
    assert "err" in result.stderr


def test_bash_nonzero_exit():
    result = bash_exec("exit 42")
    assert result.exit_code == 42


def test_bash_cwd(tmp_path):
    result = bash_exec("pwd", cwd=str(tmp_path))
    assert str(tmp_path) in result.stdout
    assert result.cwd == str(tmp_path)


def test_bash_invalid_cwd():
    try:
        bash_exec("echo hi", cwd="/nonexistent/dir")
        assert False, "Should have raised"
    except FileNotFoundError:
        pass


def test_bash_timeout():
    with patch("devtools.tools.bash.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 1)):
        result = bash_exec("sleep 999", timeout=1)
        assert result.timed_out is True
        assert result.exit_code == -1
        assert "timed out" in result.stderr


def test_bash_timeout_cap():
    with patch("devtools.tools.bash.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args="", returncode=0, stdout="", stderr="")
        bash_exec("echo hi", timeout=9999)
        assert mock_run.call_args.kwargs["timeout"] == 600
