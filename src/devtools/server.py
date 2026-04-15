"""FastMCP server instance and tool registration."""

import os

from fastmcp import FastMCP

DEFAULT_WORKDIR = os.environ.get("DEFAULT_WORKDIR", "/home/sandbox")

mcp = FastMCP(
    name="DevTools Server",
    instructions="Developer tools server providing file I/O, search, shell, task tracking, and web fetching capabilities.",
)

# Import tool modules so @mcp.tool() decorators register
import devtools.tools.read  # noqa: E402, F401
import devtools.tools.edit  # noqa: E402, F401
import devtools.tools.write  # noqa: E402, F401
import devtools.tools.glob_tool  # noqa: E402, F401
import devtools.tools.grep  # noqa: E402, F401
import devtools.tools.bash  # noqa: E402, F401
import devtools.tools.todo_write  # noqa: E402, F401
import devtools.tools.web_fetch  # noqa: E402, F401
import devtools.tools.web_search  # noqa: E402, F401
