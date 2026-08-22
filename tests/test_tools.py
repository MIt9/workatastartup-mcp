import pytest
from unittest.mock import MagicMock

from workatastartup.exceptions import WorkAtAStartupError, AlgoliaError
from workatastartup.tools import (
    search_jobs,
    get_company_details,
    get_job_details,
    filter_jobs_by_skills,
    format_company_markdown,
    format_job_markdown,
)


@pytest.fixture
def mock_company_data():
    return [
        {
            "id": 101,
            "name": "TestCorp",
            "batch": "W24",
            "website": "https://testcorp.com",
            "location": "San Francisco, CA",
            "description": "Building cool AI tools.",
            "tech_description": "Python, TypeScript, React",
            "founders": [
                {
                    "full_name": "Jane Doe",
                    "founder_bio": "CEO & Co-founder",
                    "linkedin": "https://linkedin.com/in/janedoe",
                }
            ],
            "jobs": [
                {
                    "id": 501,
                    "company_id": 101,
                    "title": "Backend Engineer",
                    "skills": ["Python", "PostgreSQL"],
                    "description": "Join our backend team to build fast APIs.",
                    "pretty_salary_range": "$120K - $160K",
                    "pretty_equity_range": "0.1% - 0.5%",
                    "pretty_sponsors_visa": "Will sponsor",
                    "pretty_location_or_remote": "Remote",
                    "show_path": "https://www.workatastartup.com/jobs/501",
                },
                {
                    "id": 502,
                    "company_id": 101,
                    "title": "Frontend Engineer",
                    "skills": ["TypeScript", "React"],
                    "description": "Build UI components with React.",
                    "pretty_salary_range": "$110K - $150K",
                    "pretty_equity_range": "0.1% - 0.3%",
                    "pretty_sponsors_visa": "No",
                    "pretty_location_or_remote": "San Francisco",
                    "show_path": "https://www.workatastartup.com/jobs/502",
                },
            ],
        }
    ]


def test_search_jobs_success(mock_company_data):
    mock_client = MagicMock()
    mock_client.get_company_ids_from_algolia_search.return_value = [101]
    mock_client.fetch_companies.return_value = mock_company_data

    result = search_jobs(query="backend", client=mock_client)

    assert "TestCorp" in result
    assert "W24" in result
    assert "Backend Engineer" in result
    assert "https://testcorp.com" in result

    mock_client.get_company_ids_from_algolia_search.assert_called_once_with(
        query="backend",
        page=0,
        hits_per_page=10,
        filters=None,
    )
    mock_client.fetch_companies.assert_called_once_with([101])


def test_search_jobs_with_filters(mock_company_data):
    mock_client = MagicMock()
    mock_client.get_company_ids_from_algolia_search.return_value = [101]
    mock_client.fetch_companies.return_value = mock_company_data

    result = search_jobs(
        query="python",
        role="eng",
        eng_type="be",
        remote=True,
        visa=True,
        page=1,
        limit=5,
        client=mock_client,
    )

    assert "TestCorp" in result
    expected_filter = 'role:"eng" AND eng_type:"be" AND NOT remote:no AND NOT us_visa_required:none'
    mock_client.get_company_ids_from_algolia_search.assert_called_once_with(
        query="python",
        page=1,
        hits_per_page=5,
        filters=expected_filter,
    )


def test_format_company_markdown_none_fields():
    company = {
        "id": 102,
        "name": "NullCorp",
        "description": None,
        "tech_description": None,
        "founders": [
            {
                "full_name": None,
                "first_name": None,
                "last_name": None,
                "founder_bio": None,
                "linkedin": None,
            }
        ],
        "jobs": [],
    }
    result = format_company_markdown(company)
    assert "# NullCorp" in result
    assert "Founder" in result


def test_format_job_markdown_none_fields():
    job = {
        "id": 503,
        "title": "Data Scientist",
        "description": None,
    }
    result = format_job_markdown(job)
    assert "# Data Scientist (ID: 503)" in result


def test_search_jobs_facet_quoting_and_escaping():
    mock_client = MagicMock()
    mock_client.get_company_ids_from_algolia_search.return_value = []

    search_jobs(
        role='Engineering "Manager"',
        eng_type="Data Science/Machine Learning",
        client=mock_client,
    )

    expected_filter = 'role:"Engineering \\"Manager\\"" AND eng_type:"Data Science/Machine Learning"'
    mock_client.get_company_ids_from_algolia_search.assert_called_once_with(
        query="",
        page=0,
        hits_per_page=10,
        filters=expected_filter,
    )



def test_search_jobs_no_results():
    mock_client = MagicMock()
    mock_client.get_company_ids_from_algolia_search.return_value = []
    mock_client.fetch_companies.return_value = []

    result = search_jobs(query="nonexistent", client=mock_client)

    assert "No jobs found" in result


def test_get_company_details_success(mock_company_data):
    mock_client = MagicMock()
    mock_client.fetch_companies.return_value = mock_company_data

    result = get_company_details(company_id=101, client=mock_client)

    assert "TestCorp" in result
    assert "W24" in result
    assert "Jane Doe" in result
    assert "Python, TypeScript, React" in result
    assert "Backend Engineer" in result
    assert "Frontend Engineer" in result

    mock_client.fetch_companies.assert_called_once_with([101])


def test_get_company_details_not_found():
    mock_client = MagicMock()
    mock_client.fetch_companies.return_value = []

    result = get_company_details(company_id=999, client=mock_client)

    assert "Company with ID 999 not found" in result


def test_get_job_details_success(mock_company_data):
    mock_client = MagicMock()
    mock_client.search_algolia.return_value = {
        "results": [{"hits": [{"id": 501, "company_id": 101}]}]
    }
    mock_client.fetch_companies.return_value = mock_company_data

    result = get_job_details(job_id=501, client=mock_client)

    assert "Backend Engineer" in result
    assert "TestCorp" in result
    assert "$120K - $160K" in result
    assert "Join our backend team" in result

    mock_client.search_algolia.assert_called_once_with(filters="id:501")
    mock_client.fetch_companies.assert_called_once_with([101])


def test_get_job_details_not_found():
    mock_client = MagicMock()
    mock_client.search_algolia.return_value = {"results": [{"hits": []}]}

    result = get_job_details(job_id=9999, client=mock_client)

    assert "Job with ID 9999 not found" in result


def test_filter_jobs_by_skills_success(mock_company_data):
    mock_client = MagicMock()
    mock_client.search_algolia.return_value = {
        "results": [{"hits": [{"company_id": 101}]}]
    }
    mock_client.fetch_companies.return_value = mock_company_data

    result = filter_jobs_by_skills(skills=["Python"], limit=5, client=mock_client)

    assert "Backend Engineer" in result
    assert "TestCorp" in result

    mock_client.search_algolia.assert_called_once_with(
        query="Python",
        hits_per_page=5,
    )


def test_filter_jobs_by_skills_no_match():
    mock_client = MagicMock()
    mock_client.search_algolia.return_value = {"results": [{"hits": []}]}

    result = filter_jobs_by_skills(skills=["Cobol"], client=mock_client)

    assert "No jobs found matching skills: Cobol" in result


def test_tools_handle_workatastartup_error():
    mock_client = MagicMock()
    mock_client.get_company_ids_from_algolia_search.side_effect = AlgoliaError("Algolia network timeout")
    mock_client.fetch_companies.side_effect = WorkAtAStartupError("API unavailable")
    mock_client.search_algolia.side_effect = AlgoliaError("Algolia search failed")

    res_search = search_jobs(query="python", client=mock_client)
    assert "Error:" in res_search or "Algolia network timeout" in res_search

    res_company = get_company_details(company_id=101, client=mock_client)
    assert "Error:" in res_company or "API unavailable" in res_company

    res_job = get_job_details(job_id=501, client=mock_client)
    assert "Error:" in res_job or "Algolia search failed" in res_job

    res_skills = filter_jobs_by_skills(skills=["Python"], client=mock_client)
    assert "Error:" in res_skills or "Algolia search failed" in res_skills


@pytest.mark.integration

def test_tools_live_integration():
    res = search_jobs(query="python", limit=2)
    assert "No jobs found" not in res
    assert "# " in res

    res_skills = filter_jobs_by_skills(skills=["Python"], limit=2)
    assert "No jobs found" not in res_skills
    assert "# " in res_skills

