"""Tests for web_fetch tool."""

import httpx
import respx

from devtools.tools.web_fetch import web_fetch


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
    assert "(truncated to 50 characters)" in result
    # Body should be exactly 50 chars of 'x'
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
