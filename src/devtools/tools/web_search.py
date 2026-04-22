"""Web search tool using SearXNG or Tavily."""

import os

import httpx

from devtools.server import mcp

SEARXNG_BASE_URL = os.environ.get(
    "SEARXNG_URL", "http://searxng.searxng.svc.cluster.local:8080"
)

SEARCH_PROVIDER = os.environ.get("SEARCH_PROVIDER", "searxng").lower()


def _search_tavily(query: str, max_results: int) -> str:
    """Execute a search using the Tavily API."""
    from tavily import TavilyClient

    client = TavilyClient()
    response = client.search(query=query, max_results=max_results)

    results = response.get("results", [])
    if not results:
        return f"No results found for: {query}"

    lines = [f"Search results for: {query}\n"]
    for i, r in enumerate(results, 1):
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("content", "")
        score = r.get("score")

        lines.append(f"{i}. {title}")
        lines.append(f"   URL: {url}")
        if snippet:
            lines.append(f"   {snippet}")
        meta_parts = []
        if score is not None:
            meta_parts.append(f"score: {score}")
        if meta_parts:
            lines.append(f"   [{' | '.join(meta_parts)}]")
        lines.append("")

    return "\n".join(lines)


def _search_searxng(
    query: str,
    categories: str,
    language: str,
    max_results: int,
    timeout: int,
) -> str:
    """Execute a search using SearXNG."""
    params = {
        "q": query,
        "format": "json",
        "categories": categories,
        "language": language,
    }

    with httpx.Client(follow_redirects=True, timeout=timeout, verify=False) as client:
        response = client.get(f"{SEARXNG_BASE_URL}/search", params=params)

    if response.status_code != 200:
        return f"[Error: SearXNG returned status {response.status_code}]\n{response.text[:500]}"

    data = response.json()
    results = data.get("results", [])

    if not results:
        return f"No results found for: {query}"

    results = results[:max_results]
    lines = [f"Search results for: {query}\n"]

    for i, r in enumerate(results, 1):
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("content", "")
        engines = ", ".join(r.get("engines", []))
        score = r.get("score")
        category = r.get("category", "")
        published = r.get("publishedDate")

        lines.append(f"{i}. {title}")
        lines.append(f"   URL: {url}")
        if snippet:
            lines.append(f"   {snippet}")
        meta_parts = []
        if engines:
            meta_parts.append(f"via: {engines}")
        if score is not None:
            meta_parts.append(f"score: {score}")
        if category:
            meta_parts.append(f"category: {category}")
        if published:
            meta_parts.append(f"published: {published}")
        if meta_parts:
            lines.append(f"   [{' | '.join(meta_parts)}]")
        lines.append("")

    suggestions = data.get("suggestions", [])
    if suggestions:
        lines.append(f"Suggestions: {', '.join(suggestions[:5])}")

    infoboxes = data.get("infoboxes", [])
    for box in infoboxes[:1]:
        box_title = box.get("infobox", "")
        box_content = box.get("content", "")
        if box_title or box_content:
            lines.append(f"\nInfobox: {box_title}")
            if box_content:
                lines.append(f"  {box_content}")

    return "\n".join(lines)


@mcp.tool()
def web_search(
    query: str,
    categories: str = "general",
    language: str = "en",
    max_results: int = 10,
    timeout: int = 30,
) -> str:
    """Search the web using SearXNG metasearch engine or Tavily.

    The search provider is selected via the SEARCH_PROVIDER env var
    ('searxng' [default] or 'tavily').

    When using SearXNG, the query supports SearXNG search syntax:
      - Select engines with `!` prefix: `!google python`, `!wp berlin`, `!ddg test`
      - Chain multiple engines/categories: `!map !ddg !wp paris`
      - Filter by language with `:` prefix: `:fr !wp Wau Holland`, `:de berlin`
      - Use `!!` for external bangs (DuckDuckGo-style): `!!wfr Wau Holland`
      - Use `!!` alone to auto-redirect to first result: `!! Wau Holland`

    Args:
        query: The search query string. Supports SearXNG operators when using SearXNG provider.
        categories: Comma-separated search categories (SearXNG only).
        language: Search language code (default "en"). SearXNG only.
        max_results: Maximum number of results to return (default 10).
        timeout: Request timeout in seconds (SearXNG only).

    Returns:
        Formatted search results with title, URL, snippet, score, and metadata.
    """
    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    if SEARCH_PROVIDER == "tavily":
        return _search_tavily(query, max_results)

    return _search_searxng(query, categories, language, max_results, timeout)
