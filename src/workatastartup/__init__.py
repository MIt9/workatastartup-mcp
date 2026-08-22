"""WorkAtAStartup API Client package."""

from workatastartup.client import (
    WorkAtAStartupClient,
    DEFAULT_ALGOLIA_APP_ID,
    DEFAULT_ALGOLIA_API_KEY,
    DEFAULT_ALGOLIA_INDEX,
    ALGOLIA_URL,
    COMPANIES_URL,
    COMPANIES_FETCH_URL,
)
from workatastartup.exceptions import WorkAtAStartupError, AlgoliaError
from workatastartup.tools import (
    search_jobs,
    get_company_details,
    get_job_details,
    filter_jobs_by_skills,
)
from workatastartup.server import mcp

__all__ = [
    "WorkAtAStartupClient",
    "WorkAtAStartupError",
    "AlgoliaError",
    "DEFAULT_ALGOLIA_APP_ID",
    "DEFAULT_ALGOLIA_API_KEY",
    "DEFAULT_ALGOLIA_INDEX",
    "ALGOLIA_URL",
    "COMPANIES_URL",
    "COMPANIES_FETCH_URL",
    "search_jobs",
    "get_company_details",
    "get_job_details",
    "filter_jobs_by_skills",
    "mcp",
]
