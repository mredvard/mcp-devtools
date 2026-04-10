"""Grep search tool."""

import re
from pathlib import Path

from devtools.guardrails import validate_path_not_protected
from devtools.server import mcp

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".tox", ".mypy_cache"}


@mcp.tool()
def grep_files(
    pattern: str,
    path: str | None = None,
    glob_filter: str | None = None,
    context: int = 0,
    case_insensitive: bool = False,
    max_results: int = 250,
) -> str:
    """Search file contents using regex.

    Args:
        pattern: Regular expression pattern to search for.
        path: Directory to search in. Defaults to current working directory.
        glob_filter: Optional glob pattern to filter files (e.g., '*.py').
        context: Number of context lines before and after each match.
        case_insensitive: If True, search case-insensitively.
        max_results: Maximum number of matching lines to return.

    Returns:
        Matching lines in filepath:lineno:content format.
    """
    base = Path(path) if path else Path.cwd()

    if not base.exists():
        raise FileNotFoundError(f"Path not found: {base}")

    validate_path_not_protected(str(base))

    flags = re.IGNORECASE if case_insensitive else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")

    results: list[str] = []

    if base.is_file():
        files = [base]
    else:
        files = sorted(base.rglob(glob_filter or "*"))

    for fp in files:
        if not fp.is_file():
            continue
        if any(part in SKIP_DIRS for part in fp.parts):
            continue

        # Skip binary files
        try:
            raw = fp.read_bytes()
        except (PermissionError, OSError):
            continue
        if b"\x00" in raw[:8192]:
            continue

        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            continue

        lines = text.splitlines()
        for i, line in enumerate(lines):
            if regex.search(line):
                if context > 0:
                    start = max(0, i - context)
                    end = min(len(lines), i + context + 1)
                    for j in range(start, end):
                        sep = ":" if j == i else "-"
                        results.append(f"{fp}:{j + 1}{sep}{lines[j]}")
                    results.append("--")
                else:
                    results.append(f"{fp}:{i + 1}:{line}")

                if len(results) >= max_results:
                    results.append(f"(truncated at {max_results} results)")
                    return "\n".join(results)

    if not results:
        return "No matches found."

    return "\n".join(results)
