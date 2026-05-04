"""Write file tool."""

from pathlib import Path

from devtools.guardrails import validate_path_not_protected, validate_path_not_sensitive
from devtools.server import DEFAULT_WORKDIR, mcp
from devtools.tools.models import WriteFileResult


@mcp.tool()
def write_file(file_path: str, content: str, create_dirs: bool = True) -> WriteFileResult:
    """Create or overwrite a file with the given content.

    IMPORTANT: Both file_path and content are required and must be provided
    together in a single call. Do not call this tool without supplying the
    full content — there is no way to append or fill it in afterward.

    Args:
        file_path: Absolute path to the file to write.
        content: The full text content to write to the file. Must not be
            omitted or left empty; include the entire file body here.
        create_dirs: If True, create parent directories as needed.

    Returns:
        Structured result with file path, bytes written, and whether the file
        was newly created or overwritten.
    """
    validate_path_not_protected(file_path)
    validate_path_not_sensitive(file_path, operation="write")

    p = Path(file_path) if Path(file_path).is_absolute() else Path(DEFAULT_WORKDIR) / file_path

    existed = p.exists()

    if create_dirs:
        p.parent.mkdir(parents=True, exist_ok=True)

    p.write_text(content, encoding="utf-8")
    return WriteFileResult(
        file_path=str(p),
        bytes_written=p.stat().st_size,
        created=not existed,
    )
