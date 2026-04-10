"""Web fetch tool."""

from urllib.parse import urlparse

import httpx

from devtools.guardrails import validate_url_not_internal
from devtools.server import mcp

ALLOWED_SCHEMES = {"http", "https"}


@mcp.tool()
def web_fetch(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    max_length: int = 100_000,
) -> str:
    """Fetch content from a URL.

    Args:
        url: The URL to fetch.
        method: HTTP method (default GET).
        headers: Optional request headers.
        timeout: Request timeout in seconds.
        max_length: Maximum response body length to return.

    Returns:
        Status code and response body text.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Invalid URL scheme '{parsed.scheme}'. Must be http or https.")

    validate_url_not_internal(url)

    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        response = client.request(method, url, headers=headers)

    body = response.text
    truncated = ""
    if len(body) > max_length:
        body = body[:max_length]
        truncated = f"\n(truncated to {max_length} characters)"

    return f"[Status: {response.status_code}]\n{body}{truncated}"
