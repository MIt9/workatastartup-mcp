import pytest
from unittest.mock import patch
import workatastartup.__main__ as main_module


def test_main_calls_mcp_run():
    with patch("workatastartup.server.mcp.run") as mock_run:
        main_module.main()
        mock_run.assert_called_once()


def test_version_export():
    import workatastartup

    assert hasattr(workatastartup, "__version__")
    assert isinstance(workatastartup.__version__, str)

