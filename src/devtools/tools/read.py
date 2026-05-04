"""Read file tool."""

import base64
import json
from pathlib import Path

from devtools.guardrails import validate_path_not_sensitive
from devtools.server import DEFAULT_WORKDIR, mcp
from devtools.tools.models import ReadFileResult

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".ico"}


@mcp.tool()
def read_file(file_path: str, offset: int = 0, limit: int = 0) -> ReadFileResult:
    """Read a file and return its contents with line numbers.

    Args:
        file_path: Absolute path to the file to read.
        offset: Line number to start reading from (0-based, default 0).
        limit: Maximum number of lines to read (0 means all).

    Returns:
        Structured result with file content (cat -n style line numbers for text,
        base64 marker for images, placeholder for binary), kind, line count,
        starting line, truncation flag, and total file size.
    """
    validate_path_not_sensitive(file_path, operation="read")

    p = Path(file_path) if Path(file_path).is_absolute() else Path(DEFAULT_WORKDIR) / file_path

    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if p.is_dir():
        raise IsADirectoryError(f"Is a directory: {file_path}")

    byte_size = p.stat().st_size

    if p.suffix.lower() in IMAGE_EXTENSIONS:
        data = p.read_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        return ReadFileResult(
            file_path=str(p),
            content=f"[Image: {p.name}] base64:{encoded}",
            kind="image",
            line_count=0,
            start_line=1,
            truncated=False,
            byte_size=byte_size,
        )

    if p.suffix.lower() == ".ipynb":
        rendered = _read_notebook(p)
        return ReadFileResult(
            file_path=str(p),
            content=rendered,
            kind="notebook",
            line_count=len(rendered.splitlines()),
            start_line=1,
            truncated=False,
            byte_size=byte_size,
        )

    raw = p.read_bytes()
    if b"\x00" in raw[:8192]:
        return ReadFileResult(
            file_path=str(p),
            content=f"[Binary file: {p.name}, {len(raw)} bytes]",
            kind="binary",
            line_count=0,
            start_line=1,
            truncated=False,
            byte_size=byte_size,
        )

    text = raw.decode("utf-8", errors="replace")
    all_lines = text.splitlines(keepends=True)

    lines = all_lines[offset:] if offset > 0 else all_lines
    truncated = False
    if limit > 0 and len(lines) > limit:
        lines = lines[:limit]
        truncated = True

    start = offset + 1
    numbered = [f"{start + i:>6}\t{line.rstrip()}" for i, line in enumerate(lines)]

    return ReadFileResult(
        file_path=str(p),
        content="\n".join(numbered),
        kind="text",
        line_count=len(lines),
        start_line=start,
        truncated=truncated,
        byte_size=byte_size,
    )


def _read_notebook(p: Path) -> str:
    """Parse and format a Jupyter notebook."""
    data = json.loads(p.read_text(encoding="utf-8"))
    cells = data.get("cells", [])
    parts = []

    for i, cell in enumerate(cells):
        cell_type = cell.get("cell_type", "unknown")
        source = "".join(cell.get("source", []))
        parts.append(f"--- Cell {i + 1} [{cell_type}] ---")
        parts.append(source)

        outputs = cell.get("outputs", [])
        for out in outputs:
            if "text" in out:
                parts.append("[Output]")
                parts.append("".join(out["text"]))
            elif "data" in out:
                for mime, content in out["data"].items():
                    if mime == "text/plain":
                        parts.append("[Output]")
                        parts.append("".join(content) if isinstance(content, list) else content)

    return "\n".join(parts)
