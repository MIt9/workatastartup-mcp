import json
import httpx
import pytest

from workatastartup.client import (
    ALGOLIA_URL,
    COMPANIES_FETCH_URL,
    COMPANIES_URL,
    DEFAULT_ALGOLIA_API_KEY,
    DEFAULT_ALGOLIA_APP_ID,
    DEFAULT_ALGOLIA_INDEX,
    WorkAtAStartupClient,
)
from workatastartup.exceptions import AlgoliaError, WorkAtAStartupError


def test_client_init_defaults():
    client = WorkAtAStartupClient()
    assert client.app_id == DEFAULT_ALGOLIA_APP_ID
    assert client.api_key == DEFAULT_ALGOLIA_API_KEY
    assert client.index_name == DEFAULT_ALGOLIA_INDEX
    assert client.csrf_token is None


def test_client_init_custom():
    custom_httpx = httpx.Client()
    client = WorkAtAStartupClient(
        app_id="CUSTOM_APP_ID",
        api_key="CUSTOM_API_KEY",
        index_name="custom_index",
        http_client=custom_httpx,
    )
    assert client.app_id == "CUSTOM_APP_ID"
    assert client.api_key == "CUSTOM_API_KEY"
    assert client.index_name == "custom_index"
    assert client.http_client is custom_httpx


def test_client_context_manager_and_close():
    custom_httpx = httpx.Client()
    with WorkAtAStartupClient(http_client=custom_httpx) as client:
        assert client.http_client is custom_httpx
        assert not custom_httpx.is_closed
    assert custom_httpx.is_closed


def test_fetch_csrf_token_success():
    mock_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="csrf-param" content="authenticity_token" />
        <meta name="csrf-token" content="test-csrf-token-12345" />
    </head>
    <body></body>
    </html>
    """

    def handler(request: httpx.Request):
        assert request.url == COMPANIES_URL
        return httpx.Response(200, html=mock_html)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    token = client.fetch_csrf_token()

    assert token == "test-csrf-token-12345"
    assert client.csrf_token == "test-csrf-token-12345"


def test_fetch_csrf_token_missing_raises_error():
    mock_html = "<html><head></head><body>No CSRF token here</body></html>"

    def handler(request: httpx.Request):
        return httpx.Response(200, html=mock_html)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    with pytest.raises(ValueError, match="CSRF token not found"):
        client.fetch_csrf_token()


def test_fetch_csrf_token_http_error():
    def handler(request: httpx.Request):
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    with pytest.raises(WorkAtAStartupError, match="HTTP error fetching CSRF token"):
        client.fetch_csrf_token()


def test_search_algolia_success():
    expected_response = {
        "results": [
            {
                "hits": [
                    {"company_id": 101, "objectID": "1"},
                    {"company_id": 102, "objectID": "2"},
                ],
                "nbHits": 2,
                "page": 0,
                "nbPages": 1,
            }
        ]
    }

    def handler(request: httpx.Request):
        assert str(request.url).startswith("https://45bwzj1sgc-dsn.algolia.net/1/indexes/*/queries")
        assert request.headers.get("x-algolia-application-id") == DEFAULT_ALGOLIA_APP_ID
        assert request.headers.get("x-algolia-api-key") == DEFAULT_ALGOLIA_API_KEY

        body = json.loads(request.content.decode("utf-8"))
        assert "requests" in body
        req_item = body["requests"][0]
        assert req_item["indexName"] == DEFAULT_ALGOLIA_INDEX
        assert "page=0" in req_item["params"]
        assert "hitsPerPage=10" in req_item["params"]

        return httpx.Response(200, json=expected_response)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    res = client.search_algolia(query="", page=0, hits_per_page=10)

    assert res == expected_response
    hits = res["results"][0]["hits"]
    assert len(hits) == 2
    assert hits[0]["company_id"] == 101


def test_search_algolia_http_error():
    def handler(request: httpx.Request):
        return httpx.Response(403, text="Forbidden")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    with pytest.raises(AlgoliaError, match="Algolia HTTP error"):
        client.search_algolia(query="test")


def test_search_algolia_network_timeout():
    def handler(request: httpx.Request):
        raise httpx.ReadTimeout("Read timed out", request=request)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    with pytest.raises(AlgoliaError, match="Algolia HTTP error"):
        client.search_algolia(query="test")


def test_search_algolia_invalid_json():
    def handler(request: httpx.Request):
        return httpx.Response(200, text="Not JSON content")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    with pytest.raises(AlgoliaError, match="Invalid JSON response from Algolia"):
        client.search_algolia(query="test")


def test_search_algolia_non_dict_json():
    def handler(request: httpx.Request):
        return httpx.Response(200, json=["unexpected", "list"])

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    with pytest.raises(AlgoliaError, match="Expected dict response from Algolia"):
        client.search_algolia(query="test")


def test_get_company_ids_from_algolia_search():
    expected_response = {
        "results": [
            {
                "hits": [
                    {"company_id": 201, "objectID": "1"},
                    {"company_id": 202, "objectID": "2"},
                    {"company_id": 201, "objectID": "3"},  # Duplicate ID
                    {"objectID": "4"},  # Missing company_id
                ]
            }
        ]
    }

    def handler(request: httpx.Request):
        return httpx.Response(200, json=expected_response)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    company_ids = client.get_company_ids_from_algolia_search(query="engineer")

    assert company_ids == [201, 202]


@pytest.mark.parametrize(
    "empty_response",
    [
        {},
        {"results": []},
        {"results": [{}]},
        {"results": [{"hits": None}]},
    ],
)
def test_get_company_ids_algolia_empty_responses(empty_response):
    def handler(request: httpx.Request):
        return httpx.Response(200, json=empty_response)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    company_ids = client.get_company_ids_from_algolia_search()
    assert company_ids == []


def test_fetch_companies_auto_fetches_csrf_and_posts():
    mock_html = '<meta name="csrf-token" content="mock-token-xyz" />'
    mock_companies_response = {
        "companies": [
            {"id": 301, "name": "Company A", "slug": "company-a"},
            {"id": 302, "name": "Company B", "slug": "company-b"},
        ]
    }

    requests_made = []

    def handler(request: httpx.Request):
        requests_made.append(request)
        if request.url == COMPANIES_URL:
            return httpx.Response(200, html=mock_html)
        elif request.url == COMPANIES_FETCH_URL:
            assert request.headers.get("x-csrf-token") == "mock-token-xyz"
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {"ids": [301, 302]}
            return httpx.Response(200, json=mock_companies_response)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    assert client.csrf_token is None

    companies = client.fetch_companies([301, 302])

    assert len(requests_made) == 2
    assert requests_made[0].url == COMPANIES_URL
    assert requests_made[1].url == COMPANIES_FETCH_URL
    assert len(companies) == 2
    assert companies[0]["id"] == 301
    assert client.csrf_token == "mock-token-xyz"


def test_fetch_companies_http_error():
    mock_html = '<meta name="csrf-token" content="mock-token-xyz" />'

    def handler(request: httpx.Request):
        if request.url == COMPANIES_URL:
            return httpx.Response(200, html=mock_html)
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    with pytest.raises(WorkAtAStartupError, match="HTTP error fetching companies"):
        client.fetch_companies([101])


def test_fetch_companies_invalid_json():
    mock_html = '<meta name="csrf-token" content="mock-token-xyz" />'

    def handler(request: httpx.Request):
        if request.url == COMPANIES_URL:
            return httpx.Response(200, html=mock_html)
        return httpx.Response(200, text="Not JSON")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    with pytest.raises(WorkAtAStartupError, match="Invalid JSON response from companies fetch"):
        client.fetch_companies([101])


def test_fetch_companies_non_dict_json():
    mock_html = '<meta name="csrf-token" content="mock-token-xyz" />'

    def handler(request: httpx.Request):
        if request.url == COMPANIES_URL:
            return httpx.Response(200, html=mock_html)
        return httpx.Response(200, json=["not", "a", "dict"])

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    with pytest.raises(WorkAtAStartupError, match="Expected dict response from companies fetch"):
        client.fetch_companies([101])


@pytest.mark.parametrize(
    "empty_response",
    [
        {},
        {"companies": None},
        {"companies": "invalid_type"},
    ],
)
def test_fetch_companies_empty_or_malformed_responses(empty_response):
    mock_html = '<meta name="csrf-token" content="mock-token-xyz" />'

    def handler(request: httpx.Request):
        if request.url == COMPANIES_URL:
            return httpx.Response(200, html=mock_html)
        return httpx.Response(200, json=empty_response)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = WorkAtAStartupClient(http_client=http_client)
    companies = client.fetch_companies([101])
    assert companies == []


@pytest.mark.integration
def test_live_integration():
    """Live integration test against Algolia and WorkAtAStartup."""
    client = WorkAtAStartupClient()
    company_ids = client.get_company_ids_from_algolia_search(query="", hits_per_page=2)
    assert len(company_ids) > 0

    token = client.fetch_csrf_token()
    assert token is not None
    assert len(token) > 10

    companies = client.fetch_companies(company_ids)
    assert len(companies) > 0
    assert "name" in companies[0]
