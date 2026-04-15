"""Edit file tool."""

from pathlib import Path

from devtools.guardrails import validate_path_not_protected, validate_path_not_sensitive
from devtools.server import DEFAULT_WORKDIR, mcp


@mcp.tool()
def edit_file(file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """Perform exact string replacement in a file.

    Args:
        file_path: Absolute path to the file to edit.
        old_string: The exact text to find and replace.
        new_string: The replacement text.
        replace_all: If True, replace all occurrences. If False, require exactly one match.

    Returns:
        Success message with replacement count.
    """
    validate_path_not_protected(file_path)
    validate_path_not_sensitive(file_path, operation="edit")

    p = Path(file_path) if Path(file_path).is_absolute() else Path(DEFAULT_WORKDIR) / file_path

    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = p.read_text(encoding="utf-8")
    count = content.count(old_string)

    if count == 0:
        raise ValueError(f"old_string not found in {file_path}")

    if not replace_all and count > 1:
        raise ValueError(
            f"old_string appears {count} times in {file_path}. "
            "Use replace_all=True to replace all occurrences, or provide a more specific string."
        )

    new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
    p.write_text(new_content, encoding="utf-8")

    replaced = count if replace_all else 1
    return f"Successfully replaced {replaced} occurrence(s) in {file_path}"
