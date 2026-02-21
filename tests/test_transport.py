"""
Tests for MCP transport selection and configuration.
"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


class TestTransportSelection:
    """Tests for transport type selection via env vars and parameters."""

    @patch("daniel_lightrag_mcp.server.InitializationOptions")
    @patch("daniel_lightrag_mcp.server.stdio_server")
    async def test_main_stdio_transport_via_param(self, mock_stdio, mock_init_options):
        """Test that transport='stdio' parameter uses STDIO transport."""
        from daniel_lightrag_mcp.server import main

        # Setup mock stdio_server context manager
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_stdio.return_value = mock_ctx

        # Mock server.run to avoid actual execution
        with patch("daniel_lightrag_mcp.server.server") as mock_server:
            mock_server.run = AsyncMock()
            mock_server.get_capabilities = MagicMock(return_value=MagicMock())

            await main(transport="stdio")

            mock_stdio.assert_called_once()
            mock_server.run.assert_called_once()

    @patch("daniel_lightrag_mcp.server.run_streamable_http")
    async def test_main_streamable_http_transport_via_param(self, mock_run_http):
        """Test that transport='streamable-http' parameter uses HTTP transport."""
        from daniel_lightrag_mcp.server import main

        mock_run_http.return_value = None

        await main(transport="streamable-http", host="127.0.0.1", port=9999)

        mock_run_http.assert_called_once_with("127.0.0.1", 9999)

    @patch("daniel_lightrag_mcp.server.run_streamable_http")
    async def test_main_default_transport_is_streamable_http(self, mock_run_http):
        """Test that default transport (no env var, no param) is streamable-http."""
        from daniel_lightrag_mcp.server import main

        mock_run_http.return_value = None

        # Ensure MCP_TRANSPORT is not set
        with patch.dict(os.environ, {}, clear=False):
            env = os.environ.copy()
            env.pop("MCP_TRANSPORT", None)
            with patch.dict(os.environ, env, clear=True):
                await main()

        mock_run_http.assert_called_once()

    @patch("daniel_lightrag_mcp.server.InitializationOptions")
    @patch("daniel_lightrag_mcp.server.stdio_server")
    async def test_main_stdio_transport_via_env(self, mock_stdio, mock_init_options):
        """Test that MCP_TRANSPORT=stdio env var uses STDIO transport."""
        from daniel_lightrag_mcp.server import main

        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_stdio.return_value = mock_ctx

        with patch("daniel_lightrag_mcp.server.server") as mock_server:
            mock_server.run = AsyncMock()
            mock_server.get_capabilities = MagicMock(return_value=MagicMock())

            with patch.dict(os.environ, {"MCP_TRANSPORT": "stdio"}):
                await main()

            mock_stdio.assert_called_once()

    async def test_main_invalid_transport_raises_error(self):
        """Test that an invalid transport type raises ValueError."""
        from daniel_lightrag_mcp.server import main

        with pytest.raises(ValueError, match="Unknown transport"):
            await main(transport="invalid-transport")


class TestTransportConfiguration:
    """Tests for transport host/port configuration."""

    @patch("daniel_lightrag_mcp.server.run_streamable_http")
    async def test_default_host_and_port(self, mock_run_http):
        """Test default host (0.0.0.0) and port (8080)."""
        from daniel_lightrag_mcp.server import main

        mock_run_http.return_value = None

        with patch.dict(os.environ, {"MCP_TRANSPORT": "streamable-http"}, clear=False):
            # Remove MCP_HOST and MCP_PORT if set
            env = os.environ.copy()
            env.pop("MCP_HOST", None)
            env.pop("MCP_PORT", None)
            env["MCP_TRANSPORT"] = "streamable-http"
            with patch.dict(os.environ, env, clear=True):
                await main()

        mock_run_http.assert_called_once_with("0.0.0.0", 8080)

    @patch("daniel_lightrag_mcp.server.run_streamable_http")
    async def test_custom_host_and_port_via_env(self, mock_run_http):
        """Test custom host and port from env vars."""
        from daniel_lightrag_mcp.server import main

        mock_run_http.return_value = None

        with patch.dict(os.environ, {
            "MCP_TRANSPORT": "streamable-http",
            "MCP_HOST": "192.168.1.1",
            "MCP_PORT": "3000",
        }):
            await main()

        mock_run_http.assert_called_once_with("192.168.1.1", 3000)

    @patch("daniel_lightrag_mcp.server.run_streamable_http")
    async def test_param_overrides_env(self, mock_run_http):
        """Test that function parameters override env vars."""
        from daniel_lightrag_mcp.server import main

        mock_run_http.return_value = None

        with patch.dict(os.environ, {
            "MCP_TRANSPORT": "stdio",
            "MCP_HOST": "10.0.0.1",
            "MCP_PORT": "5000",
        }):
            await main(transport="streamable-http", host="127.0.0.1", port=9999)

        mock_run_http.assert_called_once_with("127.0.0.1", 9999)


class TestCLIArguments:
    """Tests for CLI argument parsing."""

    @patch("daniel_lightrag_mcp.cli.main")
    @patch("daniel_lightrag_mcp.cli.asyncio")
    def test_cli_passes_transport_args(self, mock_asyncio, mock_main):
        """Test that CLI passes --transport, --host, --port to main()."""
        import sys
        from daniel_lightrag_mcp.cli import cli

        mock_asyncio.run = MagicMock()

        with patch.object(sys, "argv", ["daniel-lightrag-mcp", "--transport", "stdio"]):
            try:
                cli()
            except SystemExit:
                pass

        mock_asyncio.run.assert_called_once()
        # Verify the call was made with transport="stdio"
        call_args = mock_asyncio.run.call_args
        # The argument to asyncio.run is the coroutine from main()
        mock_main.assert_called_once_with(transport="stdio", host=None, port=None)

    @patch("daniel_lightrag_mcp.cli.main")
    @patch("daniel_lightrag_mcp.cli.asyncio")
    def test_cli_passes_all_args(self, mock_asyncio, mock_main):
        """Test that CLI passes all arguments to main()."""
        import sys
        from daniel_lightrag_mcp.cli import cli

        mock_asyncio.run = MagicMock()

        with patch.object(sys, "argv", [
            "daniel-lightrag-mcp",
            "--transport", "streamable-http",
            "--host", "127.0.0.1",
            "--port", "3000",
        ]):
            try:
                cli()
            except SystemExit:
                pass

        mock_main.assert_called_once_with(
            transport="streamable-http", host="127.0.0.1", port=3000
        )

    @patch("daniel_lightrag_mcp.cli.main")
    @patch("daniel_lightrag_mcp.cli.asyncio")
    def test_cli_defaults_to_none(self, mock_asyncio, mock_main):
        """Test that CLI defaults all args to None when not specified."""
        import sys
        from daniel_lightrag_mcp.cli import cli

        mock_asyncio.run = MagicMock()

        with patch.object(sys, "argv", ["daniel-lightrag-mcp"]):
            try:
                cli()
            except SystemExit:
                pass

        mock_main.assert_called_once_with(transport=None, host=None, port=None)
