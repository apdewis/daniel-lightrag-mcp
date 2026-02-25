"""
Unit tests for multimodal asset retrieval functionality.

Tests cover:
- MultimodalAssetBase64Response and MultimodalAssetURLResponse models
- LightRAGClient._make_raw_request method
- LightRAGClient.get_multimodal_asset_base64 method
- LightRAGClient.get_multimodal_asset_url method
- Server tool registration for multimodal tools
- Server tool handlers for multimodal tools
- MULTIMODAL_ASSET_MODE environment variable
- Argument validation for multimodal tools
"""

import base64
import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from daniel_lightrag_mcp.client import (
    LightRAGClient,
    LightRAGError,
    LightRAGConnectionError,
    LightRAGAuthError,
    LightRAGValidationError,
    LightRAGAPIError,
    LightRAGTimeoutError,
)
from daniel_lightrag_mcp.models import (
    MultimodalAssetBase64Response,
    MultimodalAssetURLResponse,
)
from daniel_lightrag_mcp.server import (
    handle_list_tools,
    handle_call_tool,
    _validate_tool_arguments,
)


# ============================================================================
# Model Tests
# ============================================================================


class TestMultimodalAssetModels:
    """Test multimodal asset Pydantic models."""

    def test_base64_response_creation(self):
        """Test MultimodalAssetBase64Response creation with valid data."""
        response = MultimodalAssetBase64Response(
            file_path="doc/auto/images/figure1.png",
            mime_type="image/png",
            data="iVBORw0KGgoAAAANSUhEUg==",
            size_bytes=1024,
        )
        assert response.file_path == "doc/auto/images/figure1.png"
        assert response.mime_type == "image/png"
        assert response.data == "iVBORw0KGgoAAAANSUhEUg=="
        assert response.size_bytes == 1024

    def test_base64_response_serialization(self):
        """Test MultimodalAssetBase64Response serialization via model_dump."""
        response = MultimodalAssetBase64Response(
            file_path="images/test.jpg",
            mime_type="image/jpeg",
            data="base64data",
            size_bytes=512,
        )
        dumped = response.model_dump()
        assert dumped == {
            "file_path": "images/test.jpg",
            "mime_type": "image/jpeg",
            "data": "base64data",
            "size_bytes": 512,
        }

    def test_url_response_creation(self):
        """Test MultimodalAssetURLResponse creation with valid data."""
        response = MultimodalAssetURLResponse(
            file_path="doc/auto/images/figure1.png",
            url="http://localhost:9621/multimodal-assets/doc/auto/images/figure1.png?api_key=test",
        )
        assert response.file_path == "doc/auto/images/figure1.png"
        assert "multimodal-assets" in response.url
        assert "api_key=test" in response.url

    def test_url_response_serialization(self):
        """Test MultimodalAssetURLResponse serialization via model_dump."""
        response = MultimodalAssetURLResponse(
            file_path="images/test.png",
            url="http://example.com/multimodal-assets/images/test.png",
        )
        dumped = response.model_dump()
        assert dumped == {
            "file_path": "images/test.png",
            "url": "http://example.com/multimodal-assets/images/test.png",
        }

    def test_base64_response_missing_required_fields(self):
        """Test that missing required fields raise validation errors."""
        with pytest.raises(Exception):
            MultimodalAssetBase64Response(file_path="test.png")

    def test_url_response_missing_required_fields(self):
        """Test that missing required fields raise validation errors."""
        with pytest.raises(Exception):
            MultimodalAssetURLResponse(file_path="test.png")


# ============================================================================
# Client Tests
# ============================================================================


class TestMakeRawRequest:
    """Test LightRAGClient._make_raw_request method."""

    @pytest.fixture
    def client_with_mock(self):
        """Create a LightRAGClient with mocked httpx client."""
        client = LightRAGClient(base_url="http://localhost:9621", api_key="test-key")
        client.client = AsyncMock(spec=httpx.AsyncClient)
        return client

    @pytest.mark.asyncio
    async def test_raw_request_success(self, client_with_mock):
        """Test successful raw binary request."""
        # Create a small PNG-like binary payload
        fake_image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_image_bytes
        mock_response.headers = {"content-type": "image/png"}
        mock_response.raise_for_status = MagicMock()

        client_with_mock.client.get = AsyncMock(return_value=mock_response)

        raw_bytes, content_type = await client_with_mock._make_raw_request(
            "GET", "/multimodal-assets/test.png", params={"api_key": "test-key"}
        )

        assert raw_bytes == fake_image_bytes
        assert content_type == "image/png"
        client_with_mock.client.get.assert_called_once_with(
            "http://localhost:9621/multimodal-assets/test.png",
            params={"api_key": "test-key"},
        )

    @pytest.mark.asyncio
    async def test_raw_request_default_content_type(self, client_with_mock):
        """Test raw request falls back to application/octet-stream when no content-type."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"binary data"
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        client_with_mock.client.get = AsyncMock(return_value=mock_response)

        raw_bytes, content_type = await client_with_mock._make_raw_request(
            "GET", "/multimodal-assets/test.bin"
        )

        assert content_type == "application/octet-stream"

    @pytest.mark.asyncio
    async def test_raw_request_http_404(self, client_with_mock):
        """Test raw request with 404 response raises LightRAGAPIError."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "File not found"
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                message="HTTP 404",
                request=MagicMock(),
                response=mock_response,
            )
        )

        client_with_mock.client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(LightRAGAPIError):
            await client_with_mock._make_raw_request(
                "GET", "/multimodal-assets/nonexistent.png"
            )

    @pytest.mark.asyncio
    async def test_raw_request_http_401(self, client_with_mock):
        """Test raw request with 401 response raises LightRAGAuthError."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Authentication required"
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                message="HTTP 401",
                request=MagicMock(),
                response=mock_response,
            )
        )

        client_with_mock.client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(LightRAGAuthError):
            await client_with_mock._make_raw_request(
                "GET", "/multimodal-assets/secret.png"
            )

    @pytest.mark.asyncio
    async def test_raw_request_http_403(self, client_with_mock):
        """Test raw request with 403 response raises LightRAGAuthError (path traversal)."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Access denied"
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                message="HTTP 403",
                request=MagicMock(),
                response=mock_response,
            )
        )

        client_with_mock.client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(LightRAGAuthError):
            await client_with_mock._make_raw_request(
                "GET", "/multimodal-assets/../../etc/passwd"
            )

    @pytest.mark.asyncio
    async def test_raw_request_connection_error(self, client_with_mock):
        """Test raw request with connection error raises LightRAGConnectionError."""
        client_with_mock.client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(LightRAGConnectionError):
            await client_with_mock._make_raw_request(
                "GET", "/multimodal-assets/test.png"
            )

    @pytest.mark.asyncio
    async def test_raw_request_timeout(self, client_with_mock):
        """Test raw request with timeout raises LightRAGTimeoutError."""
        client_with_mock.client.get = AsyncMock(
            side_effect=httpx.ReadTimeout("Read timed out")
        )

        with pytest.raises(LightRAGTimeoutError):
            await client_with_mock._make_raw_request(
                "GET", "/multimodal-assets/large-image.png"
            )

    @pytest.mark.asyncio
    async def test_raw_request_unsupported_method(self, client_with_mock):
        """Test raw request with unsupported HTTP method raises LightRAGError."""
        with pytest.raises(LightRAGError):
            await client_with_mock._make_raw_request(
                "POST", "/multimodal-assets/test.png"
            )


class TestGetMultimodalAssetBase64:
    """Test LightRAGClient.get_multimodal_asset_base64 method."""

    @pytest.fixture
    def client_with_mock(self):
        """Create a LightRAGClient with mocked httpx client."""
        client = LightRAGClient(base_url="http://localhost:9621", api_key="test-key")
        client.client = AsyncMock(spec=httpx.AsyncClient)
        return client

    @pytest.mark.asyncio
    async def test_base64_success(self, client_with_mock):
        """Test successful base64 asset retrieval."""
        fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        expected_b64 = base64.b64encode(fake_image).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_image
        mock_response.headers = {"content-type": "image/png"}
        mock_response.raise_for_status = MagicMock()

        client_with_mock.client.get = AsyncMock(return_value=mock_response)

        result = await client_with_mock.get_multimodal_asset_base64(
            "doc/auto/images/figure1.png"
        )

        assert isinstance(result, MultimodalAssetBase64Response)
        assert result.file_path == "doc/auto/images/figure1.png"
        assert result.mime_type == "image/png"
        assert result.data == expected_b64
        assert result.size_bytes == len(fake_image)

        # Verify api_key was passed as query param
        client_with_mock.client.get.assert_called_once()
        call_args = client_with_mock.client.get.call_args
        assert call_args[1]["params"]["api_key"] == "test-key"

    @pytest.mark.asyncio
    async def test_base64_no_auth(self):
        """Test base64 retrieval without API key."""
        client = LightRAGClient(base_url="http://localhost:9621")
        client.client = AsyncMock(spec=httpx.AsyncClient)

        fake_image = b"JPEG data"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_image
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_response.raise_for_status = MagicMock()

        client.client.get = AsyncMock(return_value=mock_response)

        result = await client.get_multimodal_asset_base64("images/test.jpg")

        assert result.mime_type == "image/jpeg"
        # Verify no params were passed (no api_key)
        call_args = client.client.get.call_args
        assert call_args[1].get("params") is None

    @pytest.mark.asyncio
    async def test_base64_empty_path_raises(self, client_with_mock):
        """Test that empty file_path raises validation error."""
        with pytest.raises(LightRAGValidationError):
            await client_with_mock.get_multimodal_asset_base64("")

    @pytest.mark.asyncio
    async def test_base64_whitespace_path_raises(self, client_with_mock):
        """Test that whitespace-only file_path raises validation error."""
        with pytest.raises(LightRAGValidationError):
            await client_with_mock.get_multimodal_asset_base64("   ")


class TestGetMultimodalAssetURL:
    """Test LightRAGClient.get_multimodal_asset_url method."""

    @pytest.mark.asyncio
    async def test_url_with_auth(self):
        """Test URL construction with API key."""
        client = LightRAGClient(
            base_url="http://localhost:9621", api_key="my-secret-key"
        )

        result = await client.get_multimodal_asset_url("doc/auto/images/figure1.png")

        assert isinstance(result, MultimodalAssetURLResponse)
        assert result.file_path == "doc/auto/images/figure1.png"
        assert result.url == (
            "http://localhost:9621/multimodal-assets/doc/auto/images/figure1.png"
            "?api_key=my-secret-key"
        )

    @pytest.mark.asyncio
    async def test_url_without_auth(self):
        """Test URL construction without API key."""
        client = LightRAGClient(base_url="http://localhost:9621")

        result = await client.get_multimodal_asset_url("images/test.png")

        assert isinstance(result, MultimodalAssetURLResponse)
        assert result.file_path == "images/test.png"
        assert result.url == "http://localhost:9621/multimodal-assets/images/test.png"
        assert "api_key" not in result.url

    @pytest.mark.asyncio
    async def test_url_empty_path_raises(self):
        """Test that empty file_path raises validation error."""
        client = LightRAGClient(base_url="http://localhost:9621")
        with pytest.raises(LightRAGValidationError):
            await client.get_multimodal_asset_url("")

    @pytest.mark.asyncio
    async def test_url_whitespace_path_raises(self):
        """Test that whitespace-only file_path raises validation error."""
        client = LightRAGClient(base_url="http://localhost:9621")
        with pytest.raises(LightRAGValidationError):
            await client.get_multimodal_asset_url("   ")

    @pytest.mark.asyncio
    async def test_url_nested_path(self):
        """Test URL construction with deeply nested path."""
        client = LightRAGClient(
            base_url="http://myserver:9621", api_key="key123"
        )

        result = await client.get_multimodal_asset_url(
            "project/doc/auto/images/subfolder/figure1.png"
        )

        assert "project/doc/auto/images/subfolder/figure1.png" in result.url
        assert result.url.startswith("http://myserver:9621/multimodal-assets/")

    @pytest.mark.asyncio
    async def test_url_special_characters_in_api_key(self):
        """Test URL construction with special characters in API key."""
        client = LightRAGClient(
            base_url="http://localhost:9621", api_key="key+with/special=chars"
        )

        result = await client.get_multimodal_asset_url("test.png")

        # urlencode should properly encode special characters
        assert "api_key=" in result.url
        assert "key" in result.url


# ============================================================================
# Server Tool Registration Tests
# ============================================================================


class TestMultimodalToolRegistration:
    """Test that multimodal tools are properly registered."""

    @pytest.mark.asyncio
    async def test_multimodal_tools_listed(self):
        """Test that both multimodal tools appear in the tool listing."""
        tools = await handle_list_tools()
        tool_names = [t.name for t in tools]

        assert "get_multimodal_asset_base64" in tool_names
        assert "get_multimodal_asset_url" in tool_names

    @pytest.mark.asyncio
    async def test_multimodal_tool_schemas(self):
        """Test that multimodal tools have correct input schemas."""
        tools = await handle_list_tools()
        tool_map = {t.name: t for t in tools}

        # Check base64 tool schema
        base64_tool = tool_map["get_multimodal_asset_base64"]
        assert base64_tool.inputSchema["type"] == "object"
        assert "file_path" in base64_tool.inputSchema["properties"]
        assert "file_path" in base64_tool.inputSchema["required"]

        # Check URL tool schema
        url_tool = tool_map["get_multimodal_asset_url"]
        assert url_tool.inputSchema["type"] == "object"
        assert "file_path" in url_tool.inputSchema["properties"]
        assert "file_path" in url_tool.inputSchema["required"]

    @pytest.mark.asyncio
    async def test_multimodal_tool_descriptions(self):
        """Test that multimodal tools have meaningful descriptions."""
        tools = await handle_list_tools()
        tool_map = {t.name: t for t in tools}

        base64_tool = tool_map["get_multimodal_asset_base64"]
        assert "base64" in base64_tool.description.lower()
        assert "multimodal" in base64_tool.description.lower()

        url_tool = tool_map["get_multimodal_asset_url"]
        assert "url" in url_tool.description.lower()
        assert "multimodal" in url_tool.description.lower()

    @pytest.mark.asyncio
    async def test_multimodal_asset_mode_default(self):
        """Test that default mode (base64) is reflected in tool descriptions."""
        # Clear any existing env var
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MULTIMODAL_ASSET_MODE", None)
            tools = await handle_list_tools()
            tool_map = {t.name: t for t in tools}

            base64_tool = tool_map["get_multimodal_asset_base64"]
            assert "(default mode)" in base64_tool.description

    @pytest.mark.asyncio
    async def test_multimodal_asset_mode_url(self):
        """Test that url mode is reflected in tool descriptions."""
        with patch.dict(os.environ, {"MULTIMODAL_ASSET_MODE": "url"}):
            tools = await handle_list_tools()
            tool_map = {t.name: t for t in tools}

            url_tool = tool_map["get_multimodal_asset_url"]
            assert "(default mode)" in url_tool.description

            base64_tool = tool_map["get_multimodal_asset_base64"]
            assert "(default mode)" not in base64_tool.description


# ============================================================================
# Server Argument Validation Tests
# ============================================================================


class TestMultimodalArgumentValidation:
    """Test argument validation for multimodal tools."""

    def test_validate_base64_tool_args_success(self):
        """Test successful validation of get_multimodal_asset_base64 arguments."""
        _validate_tool_arguments(
            "get_multimodal_asset_base64", {"file_path": "test.png"}
        )

    def test_validate_url_tool_args_success(self):
        """Test successful validation of get_multimodal_asset_url arguments."""
        _validate_tool_arguments(
            "get_multimodal_asset_url", {"file_path": "test.png"}
        )

    def test_validate_base64_tool_missing_file_path(self):
        """Test validation fails when file_path is missing for base64 tool."""
        with pytest.raises(LightRAGValidationError):
            _validate_tool_arguments("get_multimodal_asset_base64", {})

    def test_validate_url_tool_missing_file_path(self):
        """Test validation fails when file_path is missing for URL tool."""
        with pytest.raises(LightRAGValidationError):
            _validate_tool_arguments("get_multimodal_asset_url", {})


# ============================================================================
# Server Tool Handler Tests
# ============================================================================


class TestMultimodalToolHandlers:
    """Test server tool handlers for multimodal asset tools."""

    @pytest.mark.asyncio
    async def test_base64_handler_success(self):
        """Test get_multimodal_asset_base64 handler returns ImageContent."""
        fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        expected_b64 = base64.b64encode(fake_image).decode("utf-8")

        mock_result = MultimodalAssetBase64Response(
            file_path="doc/images/fig1.png",
            mime_type="image/png",
            data=expected_b64,
            size_bytes=len(fake_image),
        )

        mock_client = AsyncMock()
        mock_client.get_multimodal_asset_base64 = AsyncMock(return_value=mock_result)
        mock_client.base_url = "http://localhost:9621"
        mock_client.api_key = "test-key"

        with patch("daniel_lightrag_mcp.server.lightrag_client", mock_client):
            response = await handle_call_tool(
                "get_multimodal_asset_base64",
                {"file_path": "doc/images/fig1.png"},
            )

        assert "content" in response
        content = response["content"]
        assert len(content) == 2

        # First content should be ImageContent
        image_content = content[0]
        assert image_content["type"] == "image"
        assert image_content["data"] == expected_b64
        assert image_content["mimeType"] == "image/png"

        # Second content should be TextContent with metadata
        text_content = content[1]
        assert text_content["type"] == "text"
        metadata = json.loads(text_content["text"])
        assert metadata["file_path"] == "doc/images/fig1.png"
        assert metadata["mime_type"] == "image/png"
        assert metadata["size_bytes"] == len(fake_image)

    @pytest.mark.asyncio
    async def test_url_handler_success(self):
        """Test get_multimodal_asset_url handler returns TextContent with URL."""
        mock_result = MultimodalAssetURLResponse(
            file_path="doc/images/fig1.png",
            url="http://localhost:9621/multimodal-assets/doc/images/fig1.png?api_key=test",
        )

        mock_client = AsyncMock()
        mock_client.get_multimodal_asset_url = AsyncMock(return_value=mock_result)
        mock_client.base_url = "http://localhost:9621"
        mock_client.api_key = "test-key"

        with patch("daniel_lightrag_mcp.server.lightrag_client", mock_client):
            response = await handle_call_tool(
                "get_multimodal_asset_url",
                {"file_path": "doc/images/fig1.png"},
            )

        assert "content" in response
        content = response["content"]
        assert len(content) == 1
        assert content[0]["type"] == "text"

        # Parse the response text
        result_data = json.loads(content[0]["text"])
        assert result_data["file_path"] == "doc/images/fig1.png"
        assert "multimodal-assets" in result_data["url"]

    @pytest.mark.asyncio
    async def test_base64_handler_empty_path(self):
        """Test base64 handler rejects empty file_path."""
        mock_client = AsyncMock()
        mock_client.base_url = "http://localhost:9621"
        mock_client.api_key = None

        with patch("daniel_lightrag_mcp.server.lightrag_client", mock_client):
            response = await handle_call_tool(
                "get_multimodal_asset_base64",
                {"file_path": ""},
            )

        # Should return error response
        assert response.get("isError", False) is True

    @pytest.mark.asyncio
    async def test_url_handler_empty_path(self):
        """Test URL handler rejects empty file_path."""
        mock_client = AsyncMock()
        mock_client.base_url = "http://localhost:9621"
        mock_client.api_key = None

        with patch("daniel_lightrag_mcp.server.lightrag_client", mock_client):
            response = await handle_call_tool(
                "get_multimodal_asset_url",
                {"file_path": ""},
            )

        # Should return error response
        assert response.get("isError", False) is True

    @pytest.mark.asyncio
    async def test_base64_handler_api_error(self):
        """Test base64 handler handles API errors gracefully."""
        mock_client = AsyncMock()
        mock_client.get_multimodal_asset_base64 = AsyncMock(
            side_effect=LightRAGAPIError("Not Found: File not found", status_code=404)
        )
        mock_client.base_url = "http://localhost:9621"
        mock_client.api_key = "test-key"

        with patch("daniel_lightrag_mcp.server.lightrag_client", mock_client):
            response = await handle_call_tool(
                "get_multimodal_asset_base64",
                {"file_path": "nonexistent.png"},
            )

        assert response.get("isError", False) is True

    @pytest.mark.asyncio
    async def test_base64_handler_auth_error(self):
        """Test base64 handler handles auth errors gracefully."""
        mock_client = AsyncMock()
        mock_client.get_multimodal_asset_base64 = AsyncMock(
            side_effect=LightRAGAuthError("Unauthorized", status_code=401)
        )
        mock_client.base_url = "http://localhost:9621"
        mock_client.api_key = None

        with patch("daniel_lightrag_mcp.server.lightrag_client", mock_client):
            response = await handle_call_tool(
                "get_multimodal_asset_base64",
                {"file_path": "secret.png"},
            )

        assert response.get("isError", False) is True
