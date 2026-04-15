"""Read file tool."""

import base64
import json
from pathlib import Path

from devtools.guardrails import validate_path_not_sensitive
from devtools.server import DEFAULT_WORKDIR, mcp

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".ico"}


@mcp.tool()
def read_file(file_path: str, offset: int = 0, limit: int = 0) -> str:
    """Read a file and return its contents with line numbers.

    Args:
        file_path: Absolute path to the file to read.
        offset: Line number to start reading from (0-based, default 0).
        limit: Maximum number of lines to read (0 means all).

    Returns:
        File contents with cat -n style line numbers, or base64 for images.
    """
    validate_path_not_sensitive(file_path, operation="read")

    p = Path(file_path) if Path(file_path).is_absolute() else Path(DEFAULT_WORKDIR) / file_path

    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if p.is_dir():
        raise IsADirectoryError(f"Is a directory: {file_path}")

    # Handle image files
    if p.suffix.lower() in IMAGE_EXTENSIONS:
        data = p.read_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        return f"[Image: {p.name}] base64:{encoded}"

    # Handle Jupyter notebooks
    if p.suffix.lower() == ".ipynb":
        return _read_notebook(p)

    # Detect binary files
    raw = p.read_bytes()
    if b"\x00" in raw[:8192]:
        return f"[Binary file: {p.name}, {len(raw)} bytes]"

    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines(keepends=True)

    # Apply offset and limit
    if offset > 0:
        lines = lines[offset:]
    if limit > 0:
        lines = lines[:limit]

    # Format with line numbers (cat -n style)
    start = offset + 1
    numbered = []
    for i, line in enumerate(lines):
        line_no = start + i
        numbered.append(f"{line_no:>6}\t{line.rstrip()}")

    return "\n".join(numbered)


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
