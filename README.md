# Work at a Startup MCP Server 🚀

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Specification](https://img.shields.io/badge/MCP-FastMCP-orange.svg)](https://modelcontextprotocol.io/)

A Model Context Protocol (MCP) server for querying **Y Combinator** jobs and companies via [Work at a Startup](https://www.workatastartup.com).

This MCP server equips AI assistants (Claude, Cursor, Gemini CLI, Antigravity) with direct access to search YC startups, explore active job listings, inspect tech stacks, filter by required skills, salary ranges, equity, and US visa sponsorship status.

---

## 🛠️ Features & Available Tools

The server provides 4 FastMCP tools:

1. **`search_jobs`**: Search YC startup job listings with advanced filters.
   - `query` (str): Search term (e.g. `"backend"`, `"AI agent"`, `"Rust"`).
   - `role` (Optional[str]): Functional role (`"eng"`, `"design"`, `"product"`, `"ops"`, `"sales"`, `"marketing"`).
   - `eng_type` (Optional[str]): Engineering specialization (`"be"`, `"fe"`, `"fs"`, `"ml"`, `"mobile"`).
   - `remote` (bool): Filter for remote positions (`True` / `False`).
   - `visa` (bool): Filter for US visa sponsorship (`True` / `False`).
   - `page` (int): Page index (default `0`).
   - `limit` (int): Number of companies per page (default `10`).

2. **`get_company_details`**: Fetch detailed YC company profile & open roles.
   - `company_id` (int): Unique YC company ID.
   - Returns: YC Batch, website, team size, location, founders, tech stack description, and active open job listings.

3. **`get_job_details`**: Retrieve full details for a specific job listing.
   - `job_id` (int): Unique job ID.
   - Returns: Full job description (Markdown), role type, experience level, salary range, equity range, visa status, required skills, and direct application URL.

4. **`filter_jobs_by_skills`**: Filter active jobs matching a list of target technologies/skills.
   - `skills` (List[str]): List of skills/technologies (e.g., `["Python", "PyTorch", "PostgreSQL"]`).
   - `limit` (int): Maximum number of matching jobs to return (default `10`).

---

## 💻 Quick Start & Installation

### Option 1: Using `uvx` or `pipx` (Recommended)

```bash
uvx workatastartup-mcp
```

### Option 2: Local Installation

```bash
git clone https://github.com/MIt9/workatastartup-mcp.git
cd workatastartup-mcp

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## ⚙️ Configuration for MCP Clients

### Claude Desktop

Add to your `claude_desktop_config.json`:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "workatastartup": {
      "command": "uvx",
      "args": ["workatastartup-mcp"]
    }
  }
}
```

Or using local python installation:

```json
{
  "mcpServers": {
    "workatastartup": {
      "command": "/path/to/workatastartup-mcp/.venv/bin/workatastartup-mcp"
    }
  }
}
```

### Cursor / VS Code / Gemini CLI / Antigravity

```json
{
  "mcpServers": {
    "workatastartup": {
      "command": "/path/to/workatastartup-mcp/.venv/bin/python",
      "args": ["-m", "workatastartup"]
    }
  }
}
```

---

## 🧪 Running Tests

```bash
# Run unit & integration tests
.venv/bin/pytest

# Run fast unit tests only (skip live API calls)
.venv/bin/pytest -m "not integration"
```

---

## 📜 License

Distributed under the [MIT License](LICENSE).
