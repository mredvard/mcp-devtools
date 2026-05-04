"""Web search tool using SearXNG."""

import os

import httpx

from devtools.server import mcp
from devtools.tools.models import Infobox, SearchResult, WebSearchResult

SEARXNG_BASE_URL = os.environ.get(
    "SEARXNG_URL", "http://searxng.searxng.svc.cluster.local:8080"
)


@mcp.tool()
def web_search(
    query: str,
    categories: str = "general",
    language: str = "en",
    max_results: int = 10,
    timeout: int = 30,
) -> WebSearchResult:
    """Search the web using SearXNG metasearch engine.

    The query supports SearXNG search syntax:
      - Select engines with `!` prefix: `!google python`, `!wp berlin`, `!ddg test`
      - Chain multiple engines/categories: `!map !ddg !wp paris`
      - Filter by language with `:` prefix: `:fr !wp Wau Holland`, `:de berlin`
      - Use `!!` for external bangs (DuckDuckGo-style): `!!wfr Wau Holland`
      - Use `!!` alone to auto-redirect to first result: `!! Wau Holland`

    Args:
        query: The search query string. Supports SearXNG operators described above.
        categories: Comma-separated search categories (general, images, news, science, files, it, map, music, social media, videos).
        language: Search language code (default "en"). Can also be set in query with `:lang` prefix.
        max_results: Maximum number of results to return (default 10).
        timeout: Request timeout in seconds.

    Returns:
        Structured result with the query, ranked search results (title, url,
        snippet, engines, score, category, published date), suggestions, and
        infoboxes. `error` is populated if the backend returned a non-200.
    """
    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    params = {
        "q": query,
        "format": "json",
        "categories": categories,
        "language": language,
    }

    with httpx.Client(follow_redirects=True, timeout=timeout, verify=False) as client:
        response = client.get(f"{SEARXNG_BASE_URL}/search", params=params)

    if response.status_code != 200:
        return WebSearchResult(
            query=query,
            results=[],
            error=f"SearXNG returned status {response.status_code}: {response.text[:500]}",
        )

    data = response.json()
    raw_results = data.get("results", [])[:max_results]

    results = [
        SearchResult(
            title=r.get("title", "No title"),
            url=r.get("url", ""),
            snippet=r.get("content", ""),
            engines=r.get("engines", []),
            score=r.get("score"),
            category=r.get("category"),
            published_date=r.get("publishedDate"),
            thumbnail=r.get("thumbnail") or r.get("thumbnail_src") or None,
            img_src=r.get("img_src") or None,
        )
        for r in raw_results
    ]

    infoboxes = [
        Infobox(title=box.get("infobox", ""), content=box.get("content", ""))
        for box in data.get("infoboxes", [])
        if box.get("infobox") or box.get("content")
    ]

    return WebSearchResult(
        query=query,
        results=results,
        suggestions=data.get("suggestions", []),
        infoboxes=infoboxes,
    )
