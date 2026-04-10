"""Write file tool."""

from pathlib import Path

from devtools.guardrails import validate_path_not_protected, validate_path_not_sensitive
from devtools.server import mcp


@mcp.tool()
def write_file(file_path: str, content: str, create_dirs: bool = True) -> str:
    """Create or overwrite a file with the given content.

    Args:
        file_path: Absolute path to the file to write.
        content: The content to write to the file.
        create_dirs: If True, create parent directories as needed.

    Returns:
        Success message with byte count.
    """
    validate_path_not_protected(file_path)
    validate_path_not_sensitive(file_path, operation="write")

    p = Path(file_path)

    if create_dirs:
        p.parent.mkdir(parents=True, exist_ok=True)

    p.write_text(content, encoding="utf-8")
    byte_count = p.stat().st_size
    return f"Successfully wrote {byte_count} bytes to {file_path}"
