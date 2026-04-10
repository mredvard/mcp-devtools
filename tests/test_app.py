"""Tests for the FastAPI app and /llm/meta/tools endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from devtools.app import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "mcp-devtools"


async def test_list_tools(client):
    resp = await client.get("/llm/meta/tools")
    assert resp.status_code == 200
    tools = resp.json()
    assert isinstance(tools, list)
    tool_names = {t["name"] for t in tools}
    expected = {"read_file", "edit_file", "write_file", "glob_files", "grep_files", "bash_exec", "todo_write", "web_fetch"}
    assert expected.issubset(tool_names)


async def test_tool_schema_has_input_schema(client):
    resp = await client.get("/llm/meta/tools")
    tools = resp.json()
    for tool in tools:
        assert "name" in tool
        assert "inputSchema" in tool
