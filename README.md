# mcp-devtools

An MCP (Model Context Protocol) server that exposes developer tools — file I/O, search, shell execution, task tracking, and web fetching — to LLM agents over HTTP.

## Overview

`mcp-devtools` wraps common developer operations as MCP tools, letting LLM agents (Claude, etc.) perform real work in a controlled environment. It runs as a FastAPI/FastMCP HTTP server and ships with security guardrails to prevent destructive or sensitive operations.

### Tools exposed

| Tool | Description |
|------|-------------|
| `read` | Read file contents |
| `write` | Write files |
| `edit` | Targeted string replacement in files |
| `glob` | File pattern matching |
| `grep` | Regex search across files |
| `bash` | Execute shell commands (guardrailed) |
| `web_fetch` | Fetch URLs (SSRF-protected) |
| `todo_write` | Manage task lists |

### Security guardrails

The server enforces guardrails at the tool layer — no configuration required:

- **Path protection** — blocks writes to system paths (`/etc`, `/bin`, `/System`, etc.)
- **Sensitive file blocking** — refuses access to `.env`, SSH keys, TLS certs, cloud credentials, etc.
- **Bash command blocking** — blocks destructive commands (rm -rf /, fork bombs, sudo, disk overwrites, curl-pipe-to-shell, etc.)
- **SSRF protection** — `web_fetch` blocks requests to private IP ranges and cloud metadata endpoints

## Installation

Requires Python 3.13+ and [uv](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/mredvard/mcp-devtools.git
cd mcp-devtools
uv sync
```

## Running locally

```bash
uv run uvicorn devtools.app:app --host 0.0.0.0 --port 8000
```

The MCP endpoint is available at `http://localhost:8000/llm` (streamable HTTP transport).

Health check: `GET /health`  
Tool discovery: `GET /llm/meta/tools`

## Running with Docker

```bash
docker build -t mcp-devtools .
docker run -p 8000:8000 mcp-devtools
```

## Kubernetes deployment

Manifests for a sandboxed Kubernetes deployment are in `k8s/llm-sandbox/`. See [`k8s/llm-sandbox/README.md`](k8s/llm-sandbox/README.md) for deployment instructions.

```bash
cd k8s/llm-sandbox
bash deploy.sh
```

## Development

```bash
uv sync --group dev
uv run pytest
```

## Project structure

```
src/devtools/
├── app.py          # FastAPI app with MCP mount
├── server.py       # FastMCP instance and tool registration
├── guardrails.py   # Security validation (paths, bash, SSRF)
└── tools/          # Individual tool implementations
k8s/llm-sandbox/    # Kubernetes manifests
```

## License

MIT
