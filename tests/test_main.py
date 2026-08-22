import pytest
from unittest.mock import patch
import workatastartup.__main__ as main_module


def test_main_calls_mcp_run():
    with patch("workatastartup.server.mcp.run") as mock_run:
        main_module.main()
        mock_run.assert_called_once()
