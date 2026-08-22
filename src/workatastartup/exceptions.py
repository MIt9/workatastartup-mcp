"""Exceptions for WorkAtAStartup API Client."""


class WorkAtAStartupError(Exception):
    """Base exception for WorkAtAStartup client errors."""

    pass


class AlgoliaError(WorkAtAStartupError):
    """Exception raised for errors during Algolia API operations."""

    pass
