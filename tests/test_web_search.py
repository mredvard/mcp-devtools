"""Tests for web_search tool."""

from unittest.mock import MagicMock, patch

import httpx
import respx

from devtools.tools.web_search import SEARXNG_BASE_URL, web_search


SEARCH_RESPONSE = {
    "query": "python",
    "number_of_results": 50,
    "results": [
        {
            "template": "default.html",
            "url": "https://www.python.org/",
            "title": "Welcome to Python.org",
            "content": "Python is a versatile and easy-to-learn language.",
            "publishedDate": None,
            "thumbnail": "",
            "engine": "brave",
            "parsed_url": ["https", "www.python.org", "/", "", "", ""],
            "img_src": "",
            "priority": "",
            "engines": ["google", "startpage", "duckduckgo", "brave"],
            "positions": [1, 1, 1, 1],
            "score": 16.0,
            "category": "general",
        },
        {
            "template": "default.html",
            "url": "https://www.w3schools.com/python/",
            "title": "Python Tutorial - W3Schools",
            "content": "W3Schools offers free online tutorials.",
            "publishedDate": None,
            "thumbnail": "",
            "engine": "brave",
            "parsed_url": ["https", "www.w3schools.com", "/python/", "", "", ""],
            "img_src": "",
            "priority": "",
            "engines": ["google", "duckduckgo"],
            "positions": [2, 3],
            "score": 6.67,
            "category": "general",
        },
    ],
    "answers": [],
    "corrections": [],
    "infoboxes": [
        {
            "infobox": "Python",
            "id": "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "content": "general-purpose programming language",
            "img_src": "https://upload.wikimedia.org/image.png",
            "urls": [{"title": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Python"}],
            "engine": "wikidata",
            "engines": ["wikidata"],
        }
    ],
    "suggestions": ["Python free", "Python download", "python app"],
    "unresponsive_engines": [],
}


@respx.mock
def test_search_success():
    respx.get(f"{SEARXNG_BASE_URL}/search").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    result = web_search("python")
    assert "Welcome to Python.org" in result
    assert "https://www.python.org/" in result
    assert "Python is a versatile" in result
    assert "via: google, startpage, duckduckgo, brave" in result
    assert "score: 16.0" in result
    assert "category: general" in result


@respx.mock
def test_search_suggestions():
    respx.get(f"{SEARXNG_BASE_URL}/search").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    result = web_search("python")
    assert "Suggestions:" in result
    assert "Python free" in result


@respx.mock
def test_search_infobox():
    respx.get(f"{SEARXNG_BASE_URL}/search").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    result = web_search("python")
    assert "Infobox: Python" in result
    assert "general-purpose programming language" in result


@respx.mock
def test_search_no_results():
    respx.get(f"{SEARXNG_BASE_URL}/search").mock(
        return_value=httpx.Response(
            200,
            json={"query": "xyznonexistent", "number_of_results": 0, "results": [], "answers": [], "corrections": [], "infoboxes": [], "suggestions": [], "unresponsive_engines": []},
        )
    )
    result = web_search("xyznonexistent")
    assert "No results found" in result


@respx.mock
def test_search_max_results():
    many_results = {
        "query": "test",
        "number_of_results": 20,
        "results": [
            {
                "template": "default.html",
                "url": f"https://example.com/{i}",
                "title": f"Result {i}",
                "content": f"Snippet {i}",
                "publishedDate": None,
                "engine": "google",
                "engines": ["google"],
                "positions": [i],
                "score": 10.0 - i,
                "category": "general",
            }
            for i in range(20)
        ],
        "answers": [],
        "corrections": [],
        "infoboxes": [],
        "suggestions": [],
        "unresponsive_engines": [],
    }
    respx.get(f"{SEARXNG_BASE_URL}/search").mock(
        return_value=httpx.Response(200, json=many_results)
    )
    result = web_search("test", max_results=5)
    assert "Result 4" in result
    assert "Result 5" not in result


@respx.mock
def test_search_error_status():
    respx.get(f"{SEARXNG_BASE_URL}/search").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    result = web_search("test")
    assert "Error" in result
    assert "500" in result


def test_search_empty_query():
    try:
        web_search("   ")
        assert False, "Should have raised"
    except ValueError as e:
        assert "empty" in str(e).lower()


@respx.mock
def test_search_network_error():
    respx.get(f"{SEARXNG_BASE_URL}/search").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    try:
        web_search("test")
        assert False, "Should have raised"
    except httpx.ConnectError:
        pass


@respx.mock
def test_search_passes_categories():
    route = respx.get(f"{SEARXNG_BASE_URL}/search").mock(
        return_value=httpx.Response(
            200,
            json={"query": "test", "number_of_results": 0, "results": [], "answers": [], "corrections": [], "infoboxes": [], "suggestions": [], "unresponsive_engines": []},
        )
    )
    web_search("test", categories="news")
    assert route.called
    request = route.calls[0].request
    assert "categories=news" in str(request.url)


# --- Tavily provider tests ---

TAVILY_SEARCH_RESPONSE = {
    "query": "python",
    "results": [
        {
            "title": "Welcome to Python.org",
            "url": "https://www.python.org/",
            "content": "Python is a versatile and easy-to-learn language.",
            "score": 0.95,
        },
        {
            "title": "Python Tutorial - W3Schools",
            "url": "https://www.w3schools.com/python/",
            "content": "W3Schools offers free online tutorials.",
            "score": 0.88,
        },
    ],
}


@patch("devtools.tools.web_search.SEARCH_PROVIDER", "tavily")
@patch("devtools.tools.web_search.TavilyClient", create=True)
def test_tavily_search_success(mock_tavily_cls):
    mock_client = MagicMock()
    mock_client.search.return_value = TAVILY_SEARCH_RESPONSE
    mock_tavily_cls.return_value = mock_client

    with patch("devtools.tools.web_search._search_tavily") as original:
        # Call through to the real implementation but with mocked TavilyClient
        original.side_effect = None  # disable side_effect so we call real func
    # Actually call the real function with patched module-level import
    from devtools.tools.web_search import _search_tavily

    with patch("tavily.TavilyClient", return_value=mock_client):
        result = _search_tavily("python", 10)

    assert "Welcome to Python.org" in result
    assert "https://www.python.org/" in result
    assert "Python is a versatile" in result
    assert "score: 0.95" in result
    mock_client.search.assert_called_once_with(query="python", max_results=10)


@patch("tavily.TavilyClient")
@patch("devtools.tools.web_search.SEARCH_PROVIDER", "tavily")
def test_tavily_search_no_results(mock_tavily_cls):
    mock_client = MagicMock()
    mock_client.search.return_value = {"query": "xyznonexistent", "results": []}
    mock_tavily_cls.return_value = mock_client

    from devtools.tools.web_search import _search_tavily

    result = _search_tavily("xyznonexistent", 10)
    assert "No results found" in result


@patch("tavily.TavilyClient")
@patch("devtools.tools.web_search.SEARCH_PROVIDER", "tavily")
def test_tavily_search_max_results(mock_tavily_cls):
    mock_client = MagicMock()
    mock_client.search.return_value = TAVILY_SEARCH_RESPONSE
    mock_tavily_cls.return_value = mock_client

    from devtools.tools.web_search import _search_tavily

    result = _search_tavily("python", 5)
    mock_client.search.assert_called_once_with(query="python", max_results=5)
    assert "Welcome to Python.org" in result


@patch("tavily.TavilyClient")
@patch("devtools.tools.web_search.SEARCH_PROVIDER", "tavily")
def test_tavily_provider_routing(mock_tavily_cls):
    """Verify web_search dispatches to Tavily when SEARCH_PROVIDER=tavily."""
    mock_client = MagicMock()
    mock_client.search.return_value = TAVILY_SEARCH_RESPONSE
    mock_tavily_cls.return_value = mock_client

    result = web_search("python")
    assert "Welcome to Python.org" in result


def test_tavily_empty_query():
    """Empty query should raise ValueError regardless of provider."""
    try:
        web_search("   ")
        assert False, "Should have raised"
    except ValueError as e:
        assert "empty" in str(e).lower()
