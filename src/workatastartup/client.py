import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from workatastartup.exceptions import AlgoliaError, WorkAtAStartupError

DEFAULT_ALGOLIA_APP_ID = "45BWZJ1SGC"
DEFAULT_ALGOLIA_API_KEY = (
    "NTUxMGE3NGIyODI2MGY4ZDgyMjZkN2YyOGZlOWQyOGJmZjc5ZDNmZDMzZDliMjc0ZDU0MjVmZDEyZjI0ZGYx"
    "Y2FuYWx5dGljc1RhZ3M9d2FhcyZyZXN0cmljdEluZGljZXM9JTJBX3Byb2R1Y3Rpb24mdGFnRmlsdGVycz0l"
    "NUIlNUIlMjJqb2JzX2FwcGxpY2FudCUyMiU1RCU1RCZ1c2VyVG9rZW49THloQldzMGY1T0NVTSUyRmQxWTdP"
    "Q0xNUGYlMkJmY0djMVZjNmxiZU5FRHFMdDQlM0QmdmFsaWRVbnRpbD0xNzg3NDA0NTgx"
)
FULL_ALGOLIA_API_KEY = DEFAULT_ALGOLIA_API_KEY

DEFAULT_ALGOLIA_INDEX = "WaaSPublicCompanyJob_created_at_desc_production"
ALGOLIA_URL = "https://45bwzj1sgc-dsn.algolia.net/1/indexes/*/queries"
COMPANIES_URL = "https://www.workatastartup.com/companies"
COMPANIES_FETCH_URL = "https://www.workatastartup.com/companies/fetch"


DEFAULT_HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
    ),
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
}


class WorkAtAStartupClient:
    """Client for WorkAtAStartup Algolia search and company fetch APIs."""

    def __init__(
        self,
        app_id: str = DEFAULT_ALGOLIA_APP_ID,
        api_key: str = DEFAULT_ALGOLIA_API_KEY,
        index_name: str = DEFAULT_ALGOLIA_INDEX,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.app_id = app_id
        self.api_key = api_key
        self.index_name = index_name
        self.http_client = http_client or httpx.Client(
            headers=DEFAULT_HEADERS.copy(),
            follow_redirects=True,
        )
        self.csrf_token: Optional[str] = None

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self.http_client.close()

    def __enter__(self) -> "WorkAtAStartupClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[type] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional[Any] = None,
    ) -> None:
        self.close()

    def fetch_csrf_token(self) -> str:
        """Fetch companies HTML page, parse CSRF token, and store session cookies."""
        try:
            response = self.http_client.get(COMPANIES_URL)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise WorkAtAStartupError(f"HTTP error fetching CSRF token: {e}") from e

        html = response.text
        match = re.search(
            r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if not match:
            match = re.search(
                r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']csrf-token["\']',
                html,
                re.IGNORECASE,
            )

        if not match:
            raise ValueError("CSRF token not found in HTML response")

        self.csrf_token = match.group(1)
        return self.csrf_token

    def search_algolia(
        self,
        query: str = "",
        page: int = 0,
        hits_per_page: int = 10,
        filters: Optional[str] = None,
        params_extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query Algolia search API for company jobs."""
        params_dict: Dict[str, Any] = {
            "query": query,
            "page": page,
            "hitsPerPage": hits_per_page,
        }
        if filters:
            params_dict["filters"] = filters
        if params_extra:
            params_dict.update(params_extra)

        params_str = urlencode(params_dict)

        payload = {
            "requests": [
                {
                    "indexName": self.index_name,
                    "params": params_str,
                }
            ]
        }

        headers = {
            "x-algolia-application-id": self.app_id,
            "x-algolia-api-key": self.api_key,
            "content-type": "application/json",
        }

        try:
            response = self.http_client.post(
                ALGOLIA_URL,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise AlgoliaError(f"Algolia HTTP error: {e}") from e
        except (json.JSONDecodeError, ValueError) as e:
            raise AlgoliaError(f"Invalid JSON response from Algolia: {e}") from e

        if not isinstance(data, dict):
            raise AlgoliaError(f"Expected dict response from Algolia, got {type(data).__name__}")

        return data

    def get_company_ids_from_algolia_search(
        self,
        query: str = "",
        page: int = 0,
        hits_per_page: int = 10,
        filters: Optional[str] = None,
    ) -> List[int]:
        """Execute Algolia search and extract unique company_ids from hits."""
        data = self.search_algolia(
            query=query, page=page, hits_per_page=hits_per_page, filters=filters
        )
        company_ids: List[int] = []
        if not isinstance(data, dict):
            return company_ids

        results = data.get("results", [])
        if isinstance(results, list):
            for result in results:
                if isinstance(result, dict):
                    hits = result.get("hits", [])
                    if isinstance(hits, list):
                        for hit in hits:
                            if isinstance(hit, dict):
                                cid = hit.get("company_id")
                                if cid is not None and cid not in company_ids:
                                    company_ids.append(cid)
        return company_ids

    def fetch_companies(self, company_ids: List[int]) -> List[Dict[str, Any]]:
        """Fetch detailed company info for given company IDs using WorkAtAStartup fetch API."""
        if not self.csrf_token:
            self.fetch_csrf_token()

        headers = {
            "x-csrf-token": self.csrf_token or "",
            "content-type": "application/json",
        }
        payload = {"ids": company_ids}

        try:
            response = self.http_client.post(
                COMPANIES_FETCH_URL,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise WorkAtAStartupError(f"HTTP error fetching companies: {e}") from e
        except (json.JSONDecodeError, ValueError) as e:
            raise WorkAtAStartupError(f"Invalid JSON response from companies fetch: {e}") from e

        if not isinstance(data, dict):
            raise WorkAtAStartupError(
                f"Expected dict response from companies fetch, got {type(data).__name__}"
            )

        companies = data.get("companies", [])
        if not isinstance(companies, list):
            return []

        return companies
