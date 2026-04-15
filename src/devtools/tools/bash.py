"""Bash command execution tool."""

import subprocess
from pathlib import Path

from devtools.guardrails import validate_bash_command
from devtools.server import DEFAULT_WORKDIR, mcp

MAX_TIMEOUT = 600


@mcp.tool()
def bash_exec(command: str, timeout: int = 120, cwd: str | None = None) -> str:
    """Execute a shell command and return its output.

    Args:
        command: The shell command to execute.
        timeout: Timeout in seconds (max 600).
        cwd: Working directory for the command. Defaults to /home/sandbox.

    Returns:
        Command output including stdout, stderr, and return code.
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
        return f"Command timed out after {timeout} seconds."

    parts = []
    if result.stdout:
        parts.append(result.stdout)
    if result.stderr:
        parts.append(f"[stderr]\n{result.stderr}")
    parts.append(f"[exit code: {result.returncode}]")

    return "\n".join(parts)
