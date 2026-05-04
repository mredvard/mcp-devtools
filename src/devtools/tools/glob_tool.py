"""Glob file search tool."""

from pathlib import Path

from devtools.guardrails import validate_path_not_protected
from devtools.server import DEFAULT_WORKDIR, mcp
from devtools.tools.models import GlobFilesResult

MAX_RESULTS = 1000


@mcp.tool()
def glob_files(pattern: str, path: str | None = None) -> GlobFilesResult:
    """Find files matching a glob pattern.

    Args:
        pattern: Glob pattern to match (e.g., '**/*.py').
        path: Directory to search in. Defaults to the configured workdir.

    Returns:
        Structured result with the pattern, base path, matching file paths
        sorted by mtime (newest first), the total number of matches before
        truncation, and a truncation flag.
    """
    base = Path(path) if path else Path(DEFAULT_WORKDIR)

    if not base.exists():
        raise FileNotFoundError(f"Directory not found: {base}")
    if not base.is_dir():
        raise NotADirectoryError(f"Not a directory: {base}")

    validate_path_not_protected(str(base))

    matches = sorted(base.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    total = len(matches)
    truncated = total > MAX_RESULTS
    results = [str(m) for m in matches[:MAX_RESULTS]]

    return GlobFilesResult(
        pattern=pattern,
        base_path=str(base),
        matches=results,
        total_matches=total,
        truncated=truncated,
    )
