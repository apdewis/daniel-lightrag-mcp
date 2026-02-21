"""
Docker integration tests for the MCP server with Streamable HTTP transport.

These tests build and run the Docker image to verify the server starts
and responds to HTTP requests on the /mcp endpoint.

Requirements:
    - Docker must be installed and accessible
    - Tests are marked with @pytest.mark.docker so they can be skipped in CI
      or environments without Docker

Usage:
    pytest tests/test_docker.py -v
    pytest tests/test_docker.py -v -m docker
"""

import json
import os
import subprocess
import time
import pytest
import httpx

# Mark all tests in this module as docker tests
pytestmark = pytest.mark.docker

# Docker image configuration
IMAGE_NAME = "daniel-lightrag-mcp"
IMAGE_TAG = "test"
FULL_IMAGE = f"{IMAGE_NAME}:{IMAGE_TAG}"
CONTAINER_NAME = "daniel-lightrag-mcp-test"
MCP_PORT = 18080  # Use non-standard port to avoid conflicts


def docker_available() -> bool:
    """Check if Docker is available on the system."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def build_docker_image() -> bool:
    """Build the Docker image from the project Dockerfile."""
    result = subprocess.run(
        ["docker", "build", "-t", FULL_IMAGE, "."],
        capture_output=True,
        text=True,
        timeout=300,  # 5 minute timeout for build
    )
    if result.returncode != 0:
        print(f"Docker build failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
    return result.returncode == 0


def start_container() -> bool:
    """Start a Docker container with the MCP server."""
    # Remove any existing container with the same name
    subprocess.run(
        ["docker", "rm", "-f", CONTAINER_NAME],
        capture_output=True,
    )

    result = subprocess.run(
        [
            "docker", "run", "-d",
            "--name", CONTAINER_NAME,
            "-p", f"{MCP_PORT}:8080",
            "-e", "MCP_TRANSPORT=streamable-http",
            "-e", "MCP_PORT=8080",
            "-e", "MCP_HOST=0.0.0.0",
            "-e", "LOG_LEVEL=DEBUG",
            FULL_IMAGE,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        print(f"Container start failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
    return result.returncode == 0


def stop_container():
    """Stop and remove the Docker container."""
    subprocess.run(
        ["docker", "rm", "-f", CONTAINER_NAME],
        capture_output=True,
        timeout=30,
    )


def get_container_logs() -> str:
    """Get logs from the Docker container."""
    result = subprocess.run(
        ["docker", "logs", CONTAINER_NAME],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"


def wait_for_server(timeout: int = 30) -> bool:
    """Wait for the MCP server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.post(
                f"http://localhost:{MCP_PORT}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "test-client", "version": "0.1.0"},
                    },
                },
                headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
                timeout=5.0,
                follow_redirects=True,
            )
            if response.status_code in (200, 307, 400, 405):
                # Server is responding (even errors/redirects mean it's up)
                return True
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ReadError, httpx.RemoteProtocolError):
            pass
        time.sleep(1)
    return False


@pytest.fixture(scope="module")
def docker_image():
    """Build the Docker image once for all tests in this module."""
    if not docker_available():
        pytest.skip("Docker is not available")

    if not build_docker_image():
        pytest.fail("Failed to build Docker image")

    yield FULL_IMAGE

    # Optionally clean up the image after tests
    # subprocess.run(["docker", "rmi", FULL_IMAGE], capture_output=True)


@pytest.fixture(scope="module")
def docker_container(docker_image):
    """Start a Docker container for testing."""
    if not start_container():
        logs = get_container_logs()
        pytest.fail(f"Failed to start Docker container. Logs:\n{logs}")

    # Wait for server to be ready
    if not wait_for_server(timeout=30):
        logs = get_container_logs()
        stop_container()
        pytest.fail(f"Server did not become ready within 30s. Logs:\n{logs}")

    yield CONTAINER_NAME

    # Cleanup
    stop_container()


class TestDockerBuild:
    """Tests for Docker image build."""

    def test_image_builds_successfully(self, docker_image):
        """Test that the Docker image builds without errors."""
        result = subprocess.run(
            ["docker", "image", "inspect", docker_image],
            capture_output=True,
            timeout=10,
        )
        assert result.returncode == 0, "Docker image should exist after build"


class TestDockerStreamableHTTP:
    """Tests for Streamable HTTP transport in Docker container."""

    def test_server_starts_and_listens(self, docker_container):
        """Test that the MCP server starts and listens on port 8080."""
        # If we got here, the fixture already confirmed the server is responding
        assert docker_container == CONTAINER_NAME

    def test_mcp_endpoint_responds(self, docker_container):
        """Test that the /mcp endpoint responds to HTTP POST."""
        response = httpx.post(
            f"http://localhost:{MCP_PORT}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "0.1.0"},
                },
            },
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            timeout=10.0,
            follow_redirects=True,
        )
        # The server should respond (status 200 for success, or other codes)
        assert response.status_code in (200, 400, 405, 500), \
            f"Expected HTTP response, got {response.status_code}: {response.text}"

    def test_mcp_initialize_response(self, docker_container):
        """Test that MCP initialize returns valid JSON-RPC response."""
        response = httpx.post(
            f"http://localhost:{MCP_PORT}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "0.1.0"},
                },
            },
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            timeout=10.0,
            follow_redirects=True,
        )
        # Try to parse as JSON-RPC response
        if response.status_code == 200:
            # Could be JSON or SSE
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                data = response.json()
                assert "jsonrpc" in data or "result" in data or "error" in data, \
                    f"Expected JSON-RPC response, got: {data}"
            elif "text/event-stream" in content_type:
                # SSE response - just verify it's not empty
                assert len(response.text) > 0, "SSE response should not be empty"

    def test_container_logs_show_startup(self, docker_container):
        """Test that container logs show successful startup messages."""
        logs = get_container_logs()
        # Check for key startup messages
        assert "STARTING LIGHTRAG MCP SERVER" in logs or "streamable" in logs.lower(), \
            f"Expected startup messages in logs:\n{logs}"

    def test_get_request_rejected(self, docker_container):
        """Test that GET requests to /mcp are handled appropriately."""
        response = httpx.get(
            f"http://localhost:{MCP_PORT}/mcp",
            timeout=10.0,
            follow_redirects=True,
        )
        # GET should either be rejected (405) or handled differently
        # The exact behavior depends on the SDK version
        assert response.status_code in (200, 400, 405, 406), \
            f"Unexpected status for GET: {response.status_code}"

    def test_concurrent_requests(self, docker_container):
        """Test that multiple concurrent MCP requests are handled correctly.
        
        This verifies the StreamableHTTPSessionManager worker pool handles
        concurrent sessions without blocking or errors.
        """
        import concurrent.futures

        def send_initialize(client_name: str, request_id: int):
            return httpx.post(
                f"http://localhost:{MCP_PORT}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": client_name, "version": "1.0"},
                    },
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                timeout=10.0,
                follow_redirects=True,
            )

        # Send 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(send_initialize, f"client-{i}", i)
                for i in range(5)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        for response in results:
            assert response.status_code == 200, \
                f"Concurrent request failed with {response.status_code}: {response.text}"

    def test_cors_preflight(self, docker_container):
        """Test that CORS preflight requests are handled correctly.
        
        LibreChat and other browser-based clients may send OPTIONS preflight
        requests before actual MCP requests.
        """
        response = httpx.options(
            f"http://localhost:{MCP_PORT}/mcp",
            headers={
                "Origin": "http://localhost:3080",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
            timeout=10.0,
            follow_redirects=True,
        )
        assert response.status_code == 200, \
            f"CORS preflight failed with {response.status_code}: {response.text}"
        assert "access-control-allow-origin" in response.headers, \
            "Missing Access-Control-Allow-Origin header"

    def test_cors_headers_on_post(self, docker_container):
        """Test that CORS headers are present on POST responses."""
        response = httpx.post(
            f"http://localhost:{MCP_PORT}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "cors-test", "version": "1.0"},
                },
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Origin": "http://localhost:3080",
            },
            timeout=10.0,
            follow_redirects=True,
        )
        assert response.status_code == 200, \
            f"POST with Origin failed with {response.status_code}"
        assert response.headers.get("access-control-allow-origin") == "*", \
            f"Expected CORS allow-origin *, got: {response.headers.get('access-control-allow-origin')}"

    def test_session_manager_in_logs(self, docker_container):
        """Test that container logs show StreamableHTTPSessionManager startup."""
        logs = get_container_logs()
        assert "StreamableHTTPSessionManager" in logs or "session manager" in logs.lower(), \
            f"Expected session manager messages in logs:\n{logs}"
