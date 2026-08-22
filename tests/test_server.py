import pytest
from unittest.mock import MagicMock, patch
from mcp.server.fastmcp import FastMCP
from workatastartup.server import mcp


def test_server_instance():
    assert isinstance(mcp, FastMCP)
    assert mcp.name == "WorkAtAStartup"


@pytest.mark.anyio
async def test_server_registered_tools():
    tools = await mcp.list_tools()
    tool_names = {tool.name for tool in tools}

    assert "search_jobs" in tool_names
    assert "get_company_details" in tool_names
    assert "get_job_details" in tool_names
    assert "filter_jobs_by_skills" in tool_names


@pytest.mark.anyio
async def test_server_call_search_jobs_tool():
    mock_company = {
        "id": 101,
        "name": "ServerTestCorp",
        "batch": "S24",
        "website": "https://servertest.com",
        "description": "Server test company",
        "jobs": [
            {
                "id": 501,
                "title": "Software Engineer",
                "show_path": "https://www.workatastartup.com/jobs/501",
            }
        ],
    }

    with patch("workatastartup.tools.WorkAtAStartupClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.get_company_ids_from_algolia_search.return_value = [101]
        mock_instance.fetch_companies.return_value = [mock_company]

        result, meta = await mcp.call_tool("search_jobs", {"query": "python"})
        assert len(result) > 0
        text = result[0].text
        assert "ServerTestCorp" in text
        assert "S24" in text
        assert "Software Engineer" in text


@pytest.mark.anyio
async def test_server_call_search_jobs_tool_with_new_filters():
    mock_company = {
        "id": 101,
        "name": "ServerTestCorp",
        "batch": "S24",
        "website": "https://servertest.com",
        "jobs": [{"id": 501, "title": "Software Engineer"}],
    }

    with patch("workatastartup.tools.WorkAtAStartupClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.get_company_ids_from_algolia_search.return_value = [101]
        mock_instance.fetch_companies.return_value = [mock_company]

        result, meta = await mcp.call_tool(
            "search_jobs",
            {
                "query": "python",
                "job_type": "fulltime",
                "min_experience": 2,
                "max_team_size": 20,
                "batch": "S24",
            },
        )
        assert len(result) > 0
        text = result[0].text
        assert "ServerTestCorp" in text

        expected_filter = 'job_type:"fulltime" AND min_experience <= 2 AND company_team_size <= 20 AND batch:"S24"'
        mock_instance.get_company_ids_from_algolia_search.assert_called_once_with(
            query="python",
            page=0,
            hits_per_page=10,
            filters=expected_filter,
        )


@pytest.mark.anyio
async def test_server_call_get_company_details_tool():
    mock_company = {
        "id": 102,
        "name": "CompanyDetailsCorp",
        "batch": "W25",
        "website": "https://companydetails.com",
    }

    with patch("workatastartup.tools.WorkAtAStartupClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.fetch_companies.return_value = [mock_company]

        result, meta = await mcp.call_tool("get_company_details", {"company_id": 102})
        assert len(result) > 0
        text = result[0].text
        assert "CompanyDetailsCorp" in text
        assert "W25" in text


@pytest.mark.anyio
async def test_server_call_get_job_details_tool():
    mock_company = {
        "id": 103,
        "name": "JobDetailsCorp",
        "batch": "S25",
        "jobs": [{"id": 777, "title": "Lead AI Architect"}],
    }

    with patch("workatastartup.tools.WorkAtAStartupClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.search_algolia.return_value = {
            "results": [{"hits": [{"id": 777, "company_id": 103}]}]
        }
        mock_instance.fetch_companies.return_value = [mock_company]

        result, meta = await mcp.call_tool("get_job_details", {"job_id": 777})
        assert len(result) > 0
        text = result[0].text
        assert "Lead AI Architect" in text
        assert "JobDetailsCorp" in text


@pytest.mark.anyio
async def test_server_call_filter_jobs_by_skills_tool():
    mock_company = {
        "id": 104,
        "name": "SkillCorp",
        "batch": "F25",
        "jobs": [{"id": 888, "title": "Python Developer", "skills": ["Python"]}],
    }

    with patch("workatastartup.tools.WorkAtAStartupClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.search_algolia.return_value = {
            "results": [{"hits": [{"company_id": 104}]}]
        }
        mock_instance.fetch_companies.return_value = [mock_company]

        result, meta = await mcp.call_tool("filter_jobs_by_skills", {"skills": ["Python"]})
        assert len(result) > 0
        text = result[0].text
        assert "SkillCorp" in text
        assert "Python Developer" in text
