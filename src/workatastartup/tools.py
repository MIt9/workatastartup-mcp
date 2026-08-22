"""WorkAtAStartup FastMCP Tools implementation."""

from typing import Any, Dict, List, Optional
from workatastartup.client import WorkAtAStartupClient
from workatastartup.exceptions import WorkAtAStartupError, AlgoliaError


def _format_skills(skills: Any) -> List[str]:
    if not isinstance(skills, list):
        return []
    res = []
    for item in skills:
        if isinstance(item, str):
            res.append(item)
        elif isinstance(item, dict):
            val = item.get("name") or item.get("title") or str(item)
            res.append(str(val))
        elif item is not None:
            res.append(str(item))
    return res


def format_company_markdown(company: Dict[str, Any]) -> str:
    """Format company and its open jobs into Markdown."""
    name = company.get("name", "Unknown Company")
    batch = company.get("batch", "N/A")
    website = company.get("website") or company.get("website_url") or "N/A"
    location = company.get("pretty_location") or company.get("location") or "N/A"
    team_size = company.get("team_size", "N/A")
    primary_vertical = (
        company.get("primary_vertical") or company.get("parent_sector") or "N/A"
    )
    description = (company.get("description") or "").strip()
    tech = (company.get("tech_description") or "").strip()

    lines = [
        f"# {name} ({batch})",
        f"- **Website**: {website}",
        f"- **Location**: {location}",
        f"- **Team Size**: {team_size}",
        f"- **Sector**: {primary_vertical}",
    ]
    if description:
        lines.append(f"\n**Description**:\n{description}")
    if tech:
        lines.append(f"\n**Tech Stack**:\n{tech}")

    founders = company.get("founders", [])
    if founders:
        lines.append("\n### Founders")
        for f in founders:
            fname = (
                f.get("full_name")
                or f"{(f.get('first_name') or '')} {(f.get('last_name') or '')}".strip()
                or "Founder"
            )
            bio = (f.get("founder_bio") or "").strip()
            linkedin = f.get("linkedin", "")
            f_str = f"- **{fname}**"
            if bio:
                f_str += f": {bio}"
            if linkedin:
                f_str += f" ([LinkedIn]({linkedin}))"
            lines.append(f_str)

    jobs = company.get("jobs", [])
    if jobs:
        lines.append(f"\n### Open Jobs ({len(jobs)})")
        for j in jobs:
            j_id = j.get("id")
            title = j.get("title", "Untitled Job")
            salary = j.get("pretty_salary_range") or "N/A"
            equity = j.get("pretty_equity_range") or "N/A"
            visa = j.get("pretty_sponsors_visa") or j.get("visa") or "N/A"
            job_loc = j.get("pretty_location_or_remote") or "N/A"
            link = j.get("show_path") or f"https://www.workatastartup.com/jobs/{j_id}"
            skills = _format_skills(j.get("skills", []))
            skills_str = f", Skills: {', '.join(skills)}" if skills else ""

            lines.append(f"#### {title} (ID: {j_id})")
            lines.append(f"- **Location**: {job_loc}")
            lines.append(f"- **Salary**: {salary} | **Equity**: {equity}")
            lines.append(f"- **Visa**: {visa}{skills_str}")
            lines.append(f"- **Link**: {link}")

    return "\n".join(lines)


def format_job_markdown(
    job: Dict[str, Any], company: Optional[Dict[str, Any]] = None
) -> str:
    """Format job details into Markdown."""
    j_id = job.get("id")
    title = job.get("title", "Untitled Job")
    company_name = (
        company.get("name") if company else job.get("company_name", "Unknown Company")
    )
    batch = (
        company.get("batch") if company else job.get("company_batch", "N/A")
    )
    website = (
        (company.get("website") or company.get("website_url"))
        if company
        else job.get("company_website", "N/A")
    )

    job_loc = (
        job.get("pretty_location_or_remote")
        or job.get("remote")
        or "N/A"
    )
    salary = job.get("pretty_salary_range") or "N/A"
    equity = job.get("pretty_equity_range") or "N/A"
    visa = job.get("pretty_sponsors_visa") or job.get("us_visa_required") or "N/A"
    job_type = job.get("pretty_job_type") or job.get("job_type") or "N/A"
    min_exp = (
        job.get("pretty_min_experience")
        or f"{job.get('min_experience', 'N/A')} years"
    )
    link = job.get("show_path") or f"https://www.workatastartup.com/jobs/{j_id}"
    skills = _format_skills(job.get("skills", []))
    description = (job.get("description") or "").strip()

    lines = [
        f"# {title} (ID: {j_id})",
        f"**Company**: {company_name} ({batch})",
        f"**Website**: {website}",
        "",
        "## Job Overview",
        f"- **Job Type**: {job_type}",
        f"- **Location**: {job_loc}",
        f"- **Salary Range**: {salary}",
        f"- **Equity Range**: {equity}",
        f"- **Visa Sponsorship**: {visa}",
        f"- **Min Experience**: {min_exp}",
    ]
    if skills:
        lines.append(f"- **Required Skills**: {', '.join(skills)}")
    lines.append(f"- **Apply Link**: {link}")

    if description:
        lines.append("\n## Description\n")
        lines.append(description)

    return "\n".join(lines)


def search_jobs(
    query: str = "",
    role: Optional[str] = None,
    eng_type: Optional[str] = None,
    remote: bool = False,
    visa: bool = False,
    page: int = 0,
    limit: int = 10,
    client: Optional[WorkAtAStartupClient] = None,
) -> str:
    """Search YC startup jobs on WorkAtAStartup."""
    filters_parts = []
    if role:
        escaped_role = role.replace('"', '\\"')
        filters_parts.append(f'role:"{escaped_role}"')
    if eng_type:
        escaped_eng_type = eng_type.replace('"', '\\"')
        filters_parts.append(f'eng_type:"{escaped_eng_type}"')
    if remote:
        filters_parts.append("NOT remote:no")
    if visa:
        filters_parts.append("NOT us_visa_required:none")

    filters = " AND ".join(filters_parts) if filters_parts else None

    close_client = False
    if client is None:
        client = WorkAtAStartupClient()
        close_client = True

    try:
        company_ids = client.get_company_ids_from_algolia_search(
            query=query,
            page=page,
            hits_per_page=limit,
            filters=filters,
        )
        if not company_ids:
            return "No jobs found matching the criteria."

        companies = client.fetch_companies(company_ids)
        if not companies:
            return "No jobs found matching the criteria."

        output_blocks = [format_company_markdown(c) for c in companies]
        return "\n\n---\n\n".join(output_blocks)
    except WorkAtAStartupError as e:
        return f"Error interacting with WorkAtAStartup service: {e}"
    finally:
        if close_client:
            client.close()


def get_company_details(
    company_id: int,
    client: Optional[WorkAtAStartupClient] = None,
) -> str:
    """Get full company details by ID."""
    close_client = False
    if client is None:
        client = WorkAtAStartupClient()
        close_client = True

    try:
        companies = client.fetch_companies([company_id])
        if not companies:
            return f"Company with ID {company_id} not found."
        return format_company_markdown(companies[0])
    except WorkAtAStartupError as e:
        return f"Error interacting with WorkAtAStartup service: {e}"
    finally:
        if close_client:
            client.close()


def get_job_details(
    job_id: int,
    client: Optional[WorkAtAStartupClient] = None,
) -> str:
    """Get job details by ID."""
    close_client = False
    if client is None:
        client = WorkAtAStartupClient()
        close_client = True

    try:
        algolia_data = client.search_algolia(filters=f"id:{job_id}")
        hits = []
        if isinstance(algolia_data, dict):
            results = algolia_data.get("results", [])
            if results and isinstance(results[0], dict):
                hits = results[0].get("hits", []) or []

        if not hits:
            return f"Job with ID {job_id} not found."

        hit = hits[0]
        company_id = hit.get("company_id")
        company = None

        if company_id:
            companies = client.fetch_companies([company_id])
            if companies:
                company = companies[0]

        if company and "jobs" in company:
            for job in company["jobs"]:
                if job.get("id") == job_id:
                    return format_job_markdown(job, company)

        return format_job_markdown(hit, company)
    except WorkAtAStartupError as e:
        return f"Error interacting with WorkAtAStartup service: {e}"
    finally:
        if close_client:
            client.close()


def filter_jobs_by_skills(
    skills: List[str],
    limit: int = 10,
    client: Optional[WorkAtAStartupClient] = None,
) -> str:
    """Filter jobs by list of required skills."""
    if not skills:
        return "Please provide at least one skill to filter."

    query_str = " ".join(skills)
    close_client = False
    if client is None:
        client = WorkAtAStartupClient()
        close_client = True

    try:
        algolia_data = client.search_algolia(query=query_str, hits_per_page=limit)
        company_ids = []
        if isinstance(algolia_data, dict):
            results = algolia_data.get("results", [])
            if results and isinstance(results[0], dict):
                hits = results[0].get("hits", []) or []
                for h in hits:
                    cid = h.get("company_id")
                    if cid and cid not in company_ids:
                        company_ids.append(cid)

        if not company_ids:
            return f"No jobs found matching skills: {', '.join(skills)}."

        companies = client.fetch_companies(company_ids)
        if not companies:
            return f"No jobs found matching skills: {', '.join(skills)}."

        output_blocks = [format_company_markdown(c) for c in companies]
        return "\n\n---\n\n".join(output_blocks)
    except WorkAtAStartupError as e:
        return f"Error interacting with WorkAtAStartup service: {e}"
    finally:
        if close_client:
            client.close()
