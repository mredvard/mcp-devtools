"""FastAPI application with mounted MCP server."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from devtools.server import mcp

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create the FastAPI application with mounted MCP server."""
    mcp_app = mcp.http_app()

    @asynccontextmanager
    async def combined_lifespan(app: FastAPI):
        async with mcp_app.lifespan(app):
            yield

    app = FastAPI(
        title="DevTools Server",
        version="0.1.0",
        description="MCP DevTools server providing developer tools",
        lifespan=combined_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "mcp-devtools", "version": "0.1.0"}

    @app.get("/llm/meta/tools")
    async def list_tools():
        """Tool discovery endpoint."""
        tools = await mcp.list_tools()
        return [tool.to_mcp_tool() for tool in tools]

    app.mount("/llm", mcp_app)

    return app


app = create_app()
