"""Structured output models for devtools tools.

Each tool returns a Pydantic model so FastMCP can publish a JSON `outputSchema`
and emit `structuredContent` on the wire alongside the human-readable text
fallback. Field descriptions are part of the public schema — keep them
accurate and concise.
"""

from typing import Literal

from pydantic import BaseModel, Field


# --- read_file ---


class ReadFileResult(BaseModel):
    """Result of reading a file."""

    file_path: str = Field(description="Absolute path of the file that was read.")
    content: str = Field(
        description="File content. For text files: cat -n style numbered lines. "
        "For images: 'base64:<data>' marker. For binary files: a placeholder string."
    )
    kind: Literal["text", "image", "binary", "notebook"] = Field(
        description="What was read: plain text, an image (base64), a binary file (placeholder only), or a parsed Jupyter notebook."
    )
    line_count: int = Field(
        description="Number of text lines returned (0 for image/binary)."
    )
    start_line: int = Field(
        description="1-based line number of the first returned line (1 when offset=0)."
    )
    truncated: bool = Field(
        description="True if `limit` cut off lines that exist in the file."
    )
    byte_size: int = Field(description="Total size of the file on disk, in bytes.")


# --- edit_file ---


class EditFileResult(BaseModel):
    """Result of editing a file."""

    file_path: str = Field(description="Absolute path of the edited file.")
    replacements: int = Field(description="Number of occurrences replaced.")
    replace_all: bool = Field(
        description="Whether replace_all mode was used for this edit."
    )


# --- write_file ---


class WriteFileResult(BaseModel):
    """Result of writing a file."""

    file_path: str = Field(description="Absolute path of the written file.")
    bytes_written: int = Field(description="Number of bytes written to disk.")
    created: bool = Field(
        description="True if the file did not exist before this call (newly created); "
        "False if an existing file was overwritten."
    )


# --- glob_files ---


class GlobFilesResult(BaseModel):
    """Result of a glob search."""

    pattern: str = Field(description="The glob pattern that was matched.")
    base_path: str = Field(description="Directory the pattern was applied to.")
    matches: list[str] = Field(
        description="Matching file paths, sorted by mtime descending (newest first)."
    )
    total_matches: int = Field(
        description="Total number of files that matched, before any truncation."
    )
    truncated: bool = Field(
        description="True if `matches` was capped at the per-call limit."
    )


# --- grep_files ---


class GrepMatch(BaseModel):
    """A single grep match line."""

    file_path: str = Field(description="Absolute path of the file containing the match.")
    line_number: int = Field(description="1-based line number of the match.")
    line: str = Field(description="The full text of the matching line.")
    is_context: bool = Field(
        description="True if this entry is a surrounding context line, "
        "False if it is a line that actually matched the pattern."
    )


class GrepFilesResult(BaseModel):
    """Result of a grep search."""

    pattern: str = Field(description="The regex pattern that was searched for.")
    base_path: str = Field(description="File or directory that was searched.")
    matches: list[GrepMatch] = Field(
        description="Matching lines (and their context lines if `context` > 0)."
    )
    total_matches: int = Field(
        description="Number of matching/context lines returned (== len(matches))."
    )
    truncated: bool = Field(
        description="True if the search hit `max_results` and stopped early."
    )


# --- bash_exec ---


class BashExecResult(BaseModel):
    """Result of a shell command execution."""

    command: str = Field(description="The command that was executed.")
    cwd: str = Field(description="Working directory the command ran in.")
    stdout: str = Field(description="Captured standard output.")
    stderr: str = Field(description="Captured standard error.")
    exit_code: int = Field(
        description="Process exit code. -1 indicates the command timed out before exiting."
    )
    timed_out: bool = Field(
        description="True if the command was killed because it exceeded the timeout."
    )


# --- todo_write ---


class Todo(BaseModel):
    """A single todo entry."""

    id: str = Field(description="Stable short identifier for the todo.")
    content: str = Field(description="Human-readable task description.")
    status: Literal["pending", "in_progress", "done"] = Field(
        description="Current task state."
    )


class TodoWriteResult(BaseModel):
    """Result of a todo_write action."""

    action: Literal["add", "update", "remove", "list", "clear"] = Field(
        description="The action that was performed."
    )
    message: str = Field(description="Short human-readable summary of what happened.")
    todos: list[Todo] = Field(
        description="Full current todo list after the action was applied."
    )
    affected_id: str | None = Field(
        default=None,
        description="ID of the todo created/updated/removed by this call, if applicable.",
    )


# --- web_fetch ---


class WebFetchResult(BaseModel):
    """Result of fetching a URL."""

    url: str = Field(description="The URL that was fetched (after any redirects).")
    status_code: int = Field(description="HTTP status code of the response.")
    content: str = Field(
        description="Response body. May be HTML, plain text, or readable text "
        "extracted from HTML when extract_content=True."
    )
    content_type: str | None = Field(
        default=None, description="Value of the Content-Type response header, if present."
    )
    extracted: bool = Field(
        description="True if HTML was reduced to readable text (extract_content=True)."
    )
    start_index: int = Field(
        description="Character offset within the (possibly extracted) body where `content` begins."
    )
    returned_length: int = Field(description="Length of the returned `content` string.")
    total_length: int = Field(
        description="Total length of the (possibly extracted) body before pagination/truncation."
    )
    truncated: bool = Field(
        description="True if `content` was cut short by `max_length`."
    )


# --- web_search ---


class SearchResult(BaseModel):
    """A single search result entry."""

    title: str = Field(description="Result title.")
    url: str = Field(description="Result URL.")
    snippet: str = Field(description="Short excerpt from the result page.")
    engines: list[str] = Field(
        default_factory=list,
        description="Search engines that returned this result.",
    )
    score: float | None = Field(
        default=None, description="Relevance score reported by the metasearch engine."
    )
    category: str | None = Field(
        default=None, description="Category bucket of the result (e.g. 'general')."
    )
    published_date: str | None = Field(
        default=None, description="Publication date string from the source, if reported."
    )
    thumbnail: str | None = Field(
        default=None,
        description="Thumbnail URL. Populated for image/video results "
        "(SearXNG returns either `thumbnail` or `thumbnail_src` depending on engine).",
    )
    img_src: str | None = Field(
        default=None,
        description="Full-size image URL. Populated for image-category results.",
    )


class Infobox(BaseModel):
    """Knowledge-graph style infobox returned alongside web results."""

    title: str = Field(description="Infobox title.")
    content: str = Field(description="Infobox body text.")


class WebSearchResult(BaseModel):
    """Result of a web search query."""

    query: str = Field(description="The query that was sent to the search engine.")
    results: list[SearchResult] = Field(description="Ranked search results.")
    suggestions: list[str] = Field(
        default_factory=list, description="Related-query suggestions, if any."
    )
    infoboxes: list[Infobox] = Field(
        default_factory=list, description="Infoboxes associated with the query, if any."
    )
    error: str | None = Field(
        default=None,
        description="Error message if the search backend returned a non-200 status.",
    )
