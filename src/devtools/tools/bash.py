"""Bash command execution tool."""

import subprocess
from pathlib import Path

from devtools.guardrails import validate_bash_command
from devtools.server import DEFAULT_WORKDIR, mcp
from devtools.tools.models import BashExecResult

MAX_TIMEOUT = 600


@mcp.tool()
def bash_exec(command: str, timeout: int = 120, cwd: str | None = None) -> BashExecResult:
    """Execute a shell command and return its output.

    Args:
        command: The shell command to execute.
        timeout: Timeout in seconds (max 600).
        cwd: Working directory for the command. Defaults to the configured workdir.

    Returns:
        Structured result with command, working directory, captured stdout and
        stderr, exit code, and a timed_out flag (exit_code is -1 on timeout).
    """
    validate_bash_command(command)

    timeout = min(timeout, MAX_TIMEOUT)
    work_dir = cwd if cwd else DEFAULT_WORKDIR

    if work_dir and not Path(work_dir).is_dir():
        raise FileNotFoundError(f"Working directory not found: {work_dir}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=work_dir,
        )
    except subprocess.TimeoutExpired:
        return BashExecResult(
            command=command,
            cwd=work_dir,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds.",
            exit_code=-1,
            timed_out=True,
        )

    return BashExecResult(
        command=command,
        cwd=work_dir,
        stdout=result.stdout or "",
        stderr=result.stderr or "",
        exit_code=result.returncode,
        timed_out=False,
    )
