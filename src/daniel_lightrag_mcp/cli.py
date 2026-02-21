"""
CLI entry point for the Daniel LightRAG MCP server.
"""

import argparse
import asyncio
import sys
from .server import main


def cli():
    """CLI entry point with transport configuration options."""
    parser = argparse.ArgumentParser(
        description="Daniel LightRAG MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables (overridden by CLI arguments):
  MCP_TRANSPORT    Transport type: stdio or streamable-http (default: streamable-http)
  MCP_HOST         Bind address for HTTP transport (default: 0.0.0.0)
  MCP_PORT         Port for HTTP transport (default: 8080)
  LIGHTRAG_BASE_URL  LightRAG API URL (default: http://localhost:9621)
  LIGHTRAG_TIMEOUT   HTTP client timeout in seconds (default: 30)
  LOG_LEVEL          Log level (default: INFO)
        """,
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default=None,
        help="Transport type (default: from MCP_TRANSPORT env var, or streamable-http)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Bind address for HTTP transport (default: from MCP_HOST env var, or 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port for HTTP transport (default: from MCP_PORT env var, or 8080)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(main(transport=args.transport, host=args.host, port=args.port))
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
