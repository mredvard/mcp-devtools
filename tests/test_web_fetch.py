"""Tests for web_fetch tool."""

import httpx
import respx

from devtools.tools.web_fetch import _extract_text, web_fetch


@respx.mock
def test_fetch_success():
    respx.get("https://example.com/api").mock(
        return_value=httpx.Response(200, text="Hello from API")
    )
    result = web_fetch("https://example.com/api")
    assert "[Status: 200]" in result
    assert "Hello from API" in result


@respx.mock
def test_fetch_404():
    respx.get("https://example.com/missing").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    result = web_fetch("https://example.com/missing")
    assert "[Status: 404]" in result
    assert "Not Found" in result


@respx.mock
def test_fetch_truncation():
    long_text = "x" * 200
    respx.get("https://example.com/long").mock(
        return_value=httpx.Response(200, text=long_text)
    )
    result = web_fetch("https://example.com/long", max_length=50)
    assert "content truncated" in result
    assert "x" * 50 in result


def test_fetch_invalid_scheme():
    try:
        web_fetch("ftp://example.com/file")
        assert False, "Should have raised"
    except ValueError as e:
        assert "Invalid URL scheme" in str(e)


@respx.mock
def test_fetch_post():
    respx.post("https://example.com/submit").mock(
        return_value=httpx.Response(201, text="Created")
    )
    result = web_fetch("https://example.com/submit", method="POST")
    assert "[Status: 201]" in result


@respx.mock
def test_fetch_with_headers():
    route = respx.get("https://example.com/auth").mock(
        return_value=httpx.Response(200, text="OK")
    )
    web_fetch("https://example.com/auth", headers={"Authorization": "Bearer token"})
    assert route.called


@respx.mock
def test_fetch_network_error():
    respx.get("https://example.com/fail").mock(side_effect=httpx.ConnectError("Connection refused"))
    try:
        web_fetch("https://example.com/fail")
        assert False, "Should have raised"
    except httpx.ConnectError:
        pass


# --- extract_content tests ---


def test_extract_text_strips_scripts_and_styles():
    html = "<html><head><style>body{}</style></head><body><script>alert(1)</script><p>Hello</p></body></html>"
    result = _extract_text(html)
    assert "alert" not in result
    assert "body{}" not in result
    assert "Hello" in result


def test_extract_text_strips_nav_header_footer():
    html = """
    <html><body>
        <nav><a href="/">Home</a><a href="/about">About</a></nav>
        <header><h1>Site Title</h1></header>
        <main><p>Actual content here</p></main>
        <footer>Copyright 2024</footer>
    </body></html>
    """
    result = _extract_text(html)
    assert "Home" not in result
    assert "Site Title" not in result
    assert "Copyright" not in result
    assert "Actual content here" in result


def test_extract_text_collapses_blank_lines():
    html = "<p>A</p><br><br><br><br><br><p>B</p>"
    result = _extract_text(html)
    # Should not have more than one blank line between A and B
    assert "\n\n\n" not in result
    assert "A" in result
    assert "B" in result


@respx.mock
def test_fetch_with_extract_content():
    html = "<html><body><nav>Menu</nav><script>x=1</script><p>Real content</p></body></html>"
    respx.get("https://example.com/page").mock(
        return_value=httpx.Response(200, text=html)
    )
    result = web_fetch("https://example.com/page", extract_content=True)
    assert "Real content" in result
    assert "Menu" not in result
    assert "x=1" not in result


# --- start_index tests ---


@respx.mock
def test_fetch_with_start_index():
    text = "A" * 100 + "B" * 100
    respx.get("https://example.com/long").mock(
        return_value=httpx.Response(200, text=text)
    )
    result = web_fetch("https://example.com/long", start_index=100)
    assert "B" * 100 in result
    assert "A" * 100 not in result
    assert "from character 100" in result


@respx.mock
def test_fetch_start_index_with_truncation():
    text = "A" * 50 + "B" * 50 + "C" * 50
    respx.get("https://example.com/long").mock(
        return_value=httpx.Response(200, text=text)
    )
    result = web_fetch("https://example.com/long", start_index=50, max_length=50)
    assert "B" * 50 in result
    assert "content truncated" in result
    assert "50-100 of 150" in result


@respx.mock
def test_fetch_extract_content_with_start_index():
    html = "<html><body><nav>Menu</nav><p>" + "X" * 200 + "</p></body></html>"
    respx.get("https://example.com/page").mock(
        return_value=httpx.Response(200, text=html)
    )
    result = web_fetch("https://example.com/page", extract_content=True, start_index=100, max_length=50)
    assert "Menu" not in result
    assert "content truncated" in result
