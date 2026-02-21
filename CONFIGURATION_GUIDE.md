# Daniel LightRAG MCP Server - Configuration Guide

## Overview
This MCP server provides comprehensive integration with your local LightRAG server, offering 22 tools across 4 categories for complete document management, querying, knowledge graph operations, and system management.

## Prerequisites

- Python 3.8 or higher
- LightRAG server running on http://localhost:9621
- MCP-compatible client (e.g., Claude Desktop, Cline, etc.)

## Installation & Setup

### 1. Install the MCP Server
```bash
# Clone or navigate to the project directory
cd path/to/daniel-lightrag-mcp

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### 2. Verify Installation
```bash
# Test the server can start
python -m daniel_lightrag_mcp --help

# Check if all dependencies are installed
python -c "import daniel_lightrag_mcp; print('Installation successful')"
```

### 3. Configure in MCP Client

#### For Claude Desktop
Add this configuration to your Claude Desktop MCP settings file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### For Cline/Other MCP Clients
Add this configuration to your MCP settings:

```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python3",
      "args": ["-m", "daniel_lightrag_mcp"],
      "cwd": "/path/to/daniel-lightrag-mcp",
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621"
      }
    }
  }
}
```

### 4. Start LightRAG Server
Ensure your LightRAG server is running on the configured URL before using the MCP server:

```bash
# Verify LightRAG is accessible
curl http://localhost:9621/health
```

## Configuration Options

### Environment Variables

- `LIGHTRAG_BASE_URL`: LightRAG server URL (default: "http://localhost:9621")
- `LIGHTRAG_API_KEY`: API key for authentication (optional)
- `LIGHTRAG_TIMEOUT`: Request timeout in seconds (default: 30.0)
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR (default: "INFO")
- `MCP_TRANSPORT`: Transport type - `stdio` or `streamable-http` (default: "streamable-http")
- `MCP_HOST`: Bind address for HTTP transport (default: "0.0.0.0")
- `MCP_PORT`: Port for HTTP transport (default: 8080)

### Transport Selection

The server supports two transport modes:

| Transport | Description | Use Case |
|-----------|-------------|----------|
| `streamable-http` (default) | HTTP-based transport on `/mcp` endpoint | Docker, remote access, web clients |
| `stdio` | Standard input/output transport | Local MCP clients (e.g., Claude Desktop) |

#### Using STDIO Transport (for local MCP clients)

```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp", "--transport", "stdio"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Alternatively, set the transport via environment variable:

```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "LIGHTRAG_BASE_URL": "http://localhost:9621"
      }
    }
  }
}
```

#### Using Streamable HTTP Transport (default)

Start the server (it will listen on `http://0.0.0.0:8080/mcp` by default):

```bash
daniel-lightrag-mcp
# or with custom host/port:
daniel-lightrag-mcp --transport streamable-http --host 127.0.0.1 --port 3000
```

MCP clients that support HTTP transport can connect to the `/mcp` endpoint URL directly (e.g., `http://localhost:8080/mcp`).

#### Docker with Transport Configuration

```bash
# Run with Streamable HTTP (default) — exposes port 8080
docker run -p 8080:8080 -e LIGHTRAG_BASE_URL=http://host.docker.internal:9621 daniel-lightrag-mcp

# Run with STDIO transport
docker run -i -e MCP_TRANSPORT=stdio -e LIGHTRAG_BASE_URL=http://host.docker.internal:9621 daniel-lightrag-mcp
```

### Example with Custom Configuration
```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:8080",
        "LIGHTRAG_API_KEY": "your-api-key-here",
        "LIGHTRAG_TIMEOUT": "60",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## Available Tools (22 Total)

### Document Management Tools (8 tools)

1. **`insert_text`** - Insert text content into LightRAG
2. **`insert_texts`** - Insert multiple text documents into LightRAG
3. **`upload_document`** - Upload a document file to LightRAG
4. **`scan_documents`** - Scan for new documents in LightRAG
5. **`get_documents`** - Retrieve all documents from LightRAG
6. **`get_documents_paginated`** - Retrieve documents with pagination
7. **`delete_document`** - Delete a specific document by ID
8. **`clear_documents`** - Clear all documents from LightRAG

### Query Tools (2 tools)

9. **`query_text`** - Query LightRAG with text
10. **`query_text_stream`** - Stream query results from LightRAG

### Knowledge Graph Tools (7 tools)

11. **`get_knowledge_graph`** - Retrieve the knowledge graph from LightRAG
12. **`get_graph_labels`** - Get labels from the knowledge graph
13. **`check_entity_exists`** - Check if an entity exists in the knowledge graph
14. **`update_entity`** - Update an entity in the knowledge graph
15. **`update_relation`** - Update a relation in the knowledge graph
16. **`delete_entity`** - Delete an entity from the knowledge graph
17. **`delete_relation`** - Delete a relation from the knowledge graph

### System Management Tools (5 tools)

18. **`get_pipeline_status`** - Get the pipeline status from LightRAG
19. **`get_track_status`** - Get track status by ID
20. **`get_document_status_counts`** - Get document status counts
21. **`clear_cache`** - Clear LightRAG cache
22. **`get_health`** - Check LightRAG server health

## Usage Examples

### Document Management

#### Insert Single Text Document
```json
{
  "tool": "insert_text",
  "arguments": {
    "text": "Artificial Intelligence is revolutionizing how we process and understand information. Machine learning algorithms can now identify patterns in vast datasets that would be impossible for humans to detect manually."
  }
}
```

#### Insert Multiple Documents
```json
{
  "tool": "insert_texts",
  "arguments": {
    "texts": [
      {
        "title": "AI Fundamentals",
        "content": "AI encompasses machine learning, deep learning, and neural networks...",
        "metadata": {"category": "education", "level": "beginner"}
      },
      {
        "title": "Advanced ML Techniques",
        "content": "Transformer architectures have revolutionized natural language processing...",
        "metadata": {"category": "research", "level": "advanced"}
      }
    ]
  }
}
```

#### Upload Document File
```json
{
  "tool": "upload_document",
  "arguments": {
    "file_path": "/Users/username/Documents/research_paper.pdf"
  }
}
```

#### Get Documents with Pagination
```json
{
  "tool": "get_documents_paginated",
  "arguments": {
    "page": 1,
    "page_size": 20
  }
}
```

### Query Operations

#### Basic Query
```json
{
  "tool": "query_text",
  "arguments": {
    "query": "What are the main applications of machine learning in healthcare?",
    "mode": "hybrid"
  }
}
```

#### Streaming Query
```json
{
  "tool": "query_text_stream",
  "arguments": {
    "query": "Explain the evolution of artificial intelligence from the 1950s to today",
    "mode": "global"
  }
}
```

#### Context-Only Query
```json
{
  "tool": "query_text",
  "arguments": {
    "query": "What are neural networks?",
    "mode": "local",
    "only_need_context": true
  }
}
```

### Knowledge Graph Operations

#### Check Entity Existence
```json
{
  "tool": "check_entity_exists",
  "arguments": {
    "entity_name": "Machine Learning"
  }
}
```

#### Update Entity Properties
```json
{
  "tool": "update_entity",
  "arguments": {
    "entity_id": "entity_ml_001",
    "properties": {
      "description": "A subset of AI focused on algorithms that learn from data",
      "category": "AI Technology",
      "importance": "high"
    }
  }
}
```

#### Update Relation Properties
```json
{
  "tool": "update_relation",
  "arguments": {
    "relation_id": "rel_implements_002",
    "properties": {
      "strength": 0.95,
      "confidence": 0.88,
      "type": "implements"
    }
  }
}
```

### System Management

#### Health Check
```json
{
  "tool": "get_health",
  "arguments": {}
}
```

#### Get Pipeline Status
```json
{
  "tool": "get_pipeline_status",
  "arguments": {}
}
```

#### Clear Cache
```json
{
  "tool": "clear_cache",
  "arguments": {}
}
```

## Testing the Setup

### 1. Basic Connectivity Test
```bash
# Test if the MCP server can start
python -m daniel_lightrag_mcp &
sleep 2
pkill -f daniel_lightrag_mcp
```

### 2. LightRAG Server Test
```bash
# Test LightRAG server health
curl -X GET http://localhost:9621/health
```

### 3. Full Integration Test
Use your MCP client to call the `get_health` tool to verify end-to-end connectivity.

## Troubleshooting

### Common Issues

#### 1. Server Not Responding
**Symptoms:** Connection timeouts, "server unreachable" errors

**Solutions:**
1. Verify LightRAG server is running:
   ```bash
   curl http://localhost:9621/health
   ```
2. Check if port 9621 is in use:
   ```bash
   lsof -i :9621
   ```
3. Verify firewall settings allow connections to port 9621
4. Check LightRAG server logs for errors

#### 2. Import/Installation Errors
**Symptoms:** "Module not found", import errors

**Solutions:**
1. Reinstall the package:
   ```bash
   pip uninstall daniel-lightrag-mcp
   pip install -e .
   ```
2. Verify Python path:
   ```bash
   python -c "import sys; print(sys.path)"
   ```
3. Check all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

#### 3. Authentication Errors
**Symptoms:** 401 Unauthorized, authentication failed

**Solutions:**
1. Verify API key is correct in environment variables
2. Check LightRAG server authentication configuration
3. Test direct API access with curl:
   ```bash
   curl -H "X-API-Key: your-key" http://localhost:9621/health
   ```

#### 4. Timeout Errors
**Symptoms:** Request timeout, slow responses

**Solutions:**
1. Increase timeout in environment variables:
   ```bash
   export LIGHTRAG_TIMEOUT=60
   ```
2. Check LightRAG server performance and resources
3. Verify network connectivity and latency

#### 5. Validation Errors
**Symptoms:** "Invalid parameters", validation failed

**Solutions:**
1. Check parameter types and required fields in tool schemas
2. Verify JSON format is correct
3. Review tool documentation for parameter requirements

### Debugging

#### Enable Debug Logging
```json
{
  "env": {
    "LOG_LEVEL": "DEBUG"
  }
}
```

#### Check Server Logs
The MCP server logs to stdout/stderr. Check your MCP client logs for detailed error information.

#### Test Individual Tools
Use your MCP client's tool testing feature to test individual tools with known good parameters.

## Performance Considerations

### Optimization Tips

1. **Use Pagination**: For large document sets, use `get_documents_paginated` instead of `get_documents`
2. **Choose Appropriate Query Modes**: 
   - Use "local" for specific document queries
   - Use "global" for broad knowledge queries
   - Use "hybrid" for balanced results
3. **Stream Large Queries**: Use `query_text_stream` for long-form responses
4. **Cache Management**: Regularly use `clear_cache` to maintain performance

### Resource Usage

- **Memory**: Low memory footprint, scales with concurrent requests
- **CPU**: Minimal CPU usage, most processing done by LightRAG server
- **Network**: Bandwidth usage depends on document sizes and query complexity

## Security Considerations

1. **API Keys**: Store API keys securely in environment variables, not in configuration files
2. **Network Security**: Ensure LightRAG server is not exposed to untrusted networks
3. **Input Validation**: The server validates all inputs, but ensure your LightRAG server also validates data
4. **Logging**: Be aware that debug logging may include sensitive information

## Next Steps

1. **Start LightRAG Server**: Ensure your LightRAG server is running on the configured port
2. **Configure MCP Client**: Add the server configuration to your MCP client
3. **Restart Client**: Restart your MCP client to load the new server configuration
4. **Test Connection**: Use the `get_health` tool to verify connectivity
5. **Explore Tools**: Try different tools to familiarize yourself with the capabilities

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review server logs for detailed error information
3. Verify LightRAG server is functioning correctly
4. Test with minimal examples to isolate issues
