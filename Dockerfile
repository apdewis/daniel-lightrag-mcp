# =============================================================================
# Daniel LightRAG MCP Server Dockerfile
# =============================================================================
# This Dockerfile builds the MCP server for LightRAG integration.
# Supports both STDIO and Streamable HTTP transports (default: Streamable HTTP).
# The server expects an external LightRAG instance to be available.
# =============================================================================

# -----------------------------------------------------------------------------
# Build Stage
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and source for package build
COPY pyproject.toml README.md LICENSE src/ ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the package in editable mode
RUN pip install --no-cache-dir --no-build-isolation -e .

# -----------------------------------------------------------------------------
# Runtime Stage
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Install runtime dependencies (openssl for secure connections, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /home/appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application files needed for package installation
COPY --chown=appuser:appuser pyproject.toml README.md LICENSE /home/appuser/
COPY --chown=appuser:appuser src/ /home/appuser/src/

# Install the package in the runtime environment
RUN /opt/venv/bin/pip install --no-cache-dir --no-build-isolation -e /home/appuser

# Switch to non-root user
USER appuser

# -----------------------------------------------------------------------------
# Default Configuration
# -----------------------------------------------------------------------------
# These can be overridden at runtime via -e flag or docker-compose
ENV LIGHTRAG_BASE_URL=http://localhost:9621
ENV LIGHTRAG_TIMEOUT=30
ENV LOG_LEVEL=INFO
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8080

# Expose MCP Streamable HTTP transport port
EXPOSE 8080

# Health check - tries curl first (streamable-http mode), falls back to Python import (stdio mode)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${MCP_PORT}/mcp || python -c "import daniel_lightrag_mcp" || exit 1

# Default command - runs the MCP server
CMD ["python", "-m", "daniel_lightrag_mcp"]
