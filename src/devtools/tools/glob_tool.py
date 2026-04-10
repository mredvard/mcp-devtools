"""Glob file search tool."""

from pathlib import Path

from devtools.guardrails import validate_path_not_protected
from devtools.server import mcp

MAX_RESULTS = 1000


@mcp.tool()
def glob_files(pattern: str, path: str | None = None) -> str:
    """Find files matching a glob pattern.

    Args:
        pattern: Glob pattern to match (e.g., '**/*.py').
        path: Directory to search in. Defaults to current working directory.

    Returns:
        Matching file paths sorted by modification time (newest first), one per line.
    """
    base = Path(path) if path else Path.cwd()

    if not base.exists():
        raise FileNotFoundError(f"Directory not found: {base}")
    if not base.is_dir():
        raise NotADirectoryError(f"Not a directory: {base}")

    validate_path_not_protected(str(base))

    matches = sorted(base.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    if not matches:
        return "No files matched the pattern."

    results = [str(m) for m in matches[:MAX_RESULTS]]
    truncated = f"\n(showing {MAX_RESULTS} of {len(matches)} matches)" if len(matches) > MAX_RESULTS else ""
    return "\n".join(results) + truncated
