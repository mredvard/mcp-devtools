"""Web search tool using SearXNG."""

import os

import httpx

from devtools.server import mcp

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
) -> str:
    """Search the web using SearXNG metasearch engine.

    Args:
        query: The search query string.
        categories: Comma-separated search categories (general, images, news, science, files, it, map, music, social media, videos).
        language: Search language code (default "en").
        max_results: Maximum number of results to return (default 10).
        timeout: Request timeout in seconds.

    Returns:
        Formatted search results with title, URL, and snippet.
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
