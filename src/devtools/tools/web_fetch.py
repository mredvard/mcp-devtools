"""Web fetch tool."""

import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from devtools.guardrails import validate_url_not_internal
from devtools.server import mcp
from devtools.tools.models import WebFetchResult

ALLOWED_SCHEMES = {"http", "https"}

STRIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "svg", "img", "iframe"}


def _extract_text(html: str) -> str:
    """Extract readable text content from HTML, stripping boilerplate elements."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    return text.strip()


@mcp.tool()
def web_fetch(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    max_length: int = 100_000,
    start_index: int = 0,
    extract_content: bool = False,
) -> WebFetchResult:
    """Fetch content from a URL.

    For long pages where the useful content is beyond the initial portion,
    use extract_content=True to strip HTML boilerplate (scripts, nav, headers,
    footers) and return only readable text. Use start_index to paginate through
    large responses (e.g. start_index=50000 to skip the first 50000 characters).

    Args:
        url: The URL to fetch.
        method: HTTP method (default GET).
        headers: Optional request headers.
        timeout: Request timeout in seconds.
        max_length: Maximum response body length to return.
        start_index: Character offset to start reading from (default 0).
            Useful for paginating through long content.
        extract_content: If True, extract readable text from HTML by stripping
            scripts, styles, nav, headers, footers, and other boilerplate.

    Returns:
        Structured result with the URL, status code, content body, content
        type, extraction flag, pagination offsets, returned/total length, and
        a truncation flag.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Invalid URL scheme '{parsed.scheme}'. Must be http or https.")

    validate_url_not_internal(url)

    with httpx.Client(follow_redirects=True, timeout=timeout, verify=False) as client:
        response = client.request(method, url, headers=headers)

    body = response.text
    if extract_content:
        body = _extract_text(body)

    total_length = len(body)
    if start_index > 0:
        body = body[start_index:]

    truncated = False
    if len(body) > max_length:
        body = body[:max_length]
        truncated = True

    return WebFetchResult(
        url=str(response.url),
        status_code=response.status_code,
        content=body,
        content_type=response.headers.get("content-type"),
        extracted=extract_content,
        start_index=start_index,
        returned_length=len(body),
        total_length=total_length,
        truncated=truncated,
    )
