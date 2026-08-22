"""FastMCP Server for WorkAtAStartup."""

from typing import List, Optional
from mcp.server.fastmcp import FastMCP

import workatastartup.tools as tools

mcp = FastMCP("WorkAtAStartup")


@mcp.tool()
def search_jobs(
    query: str = "",
    role: Optional[str] = None,
    eng_type: Optional[str] = None,
    job_type: Optional[str] = None,
    min_experience: Optional[int] = None,
    max_team_size: Optional[int] = None,
    batch: Optional[str] = None,
    remote: bool = False,
    visa: bool = False,
    page: int = 0,
    limit: int = 10,
) -> str:
    """Search YC startup jobs on WorkAtAStartup."""
    return tools.search_jobs(
        query=query,
        role=role,
        eng_type=eng_type,
        job_type=job_type,
        min_experience=min_experience,
        max_team_size=max_team_size,
        batch=batch,
        remote=remote,
        visa=visa,
        page=page,
        limit=limit,
    )


@mcp.tool()
def get_company_details(company_id: int) -> str:
    """Get full company details by ID."""
    return tools.get_company_details(company_id=company_id)


@mcp.tool()
def get_job_details(job_id: int) -> str:
    """Get job details by ID."""
    return tools.get_job_details(job_id=job_id)


@mcp.tool()
def filter_jobs_by_skills(skills: List[str], limit: int = 10) -> str:
    """Filter jobs by list of required skills."""
    return tools.filter_jobs_by_skills(skills=skills, limit=limit)


def main():
    """Run FastMCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
