# MCP Configuration Guide

## Overview

This guide provides detailed instructions for configuring the LightRAG MCP Server with various MCP clients, including Claude Desktop, and other MCP-compatible applications.

## Quick Setup

### 1. Basic Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python3",
      "args": [
        "-m",
        "daniel_lightrag_mcp"
      ],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "Insert-LightRAG-API-Key-Here"
      }
    }
  }
}
```

### 2. Verify Installation

Test the server installation:
```bash
python -m daniel_lightrag_mcp --version
```

### 3. Health Check

Use the `get_health` tool to verify connectivity:
```json
{
  "tool": "get_health",
  "arguments": {}
}
```

## Client-Specific Configurations

### Claude Desktop

**Configuration File Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

**Complete Configuration:**
```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "Insert-LightRAG-API-Key-Here",
        "LIGHTRAG_TIMEOUT": "30",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Restart Claude Desktop** after configuration changes.

### Other MCP Clients

For other MCP-compatible clients, use the same basic structure:

```json
{
  "servers": {
    "daniel-lightrag": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "environment": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "Insert-LightRAG-API-Key-Here"
      }
    }
  }
}
```

## Environment Variables

### Required Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LIGHTRAG_BASE_URL` | LightRAG server URL | `http://localhost:9621` | `http://localhost:9621` |
| `LIGHTRAG_API_KEY` | API key for authentication | None | `lightragsecretkey` |

### Transport Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MCP_TRANSPORT` | Transport type | `streamable-http` | `stdio` |
| `MCP_HOST` | Bind address for HTTP transport | `0.0.0.0` | `127.0.0.1` |
| `MCP_PORT` | Port for HTTP transport | `8080` | `3000` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LIGHTRAG_TIMEOUT` | Request timeout in seconds | `30` | `60` |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG` |
| `MAX_RETRIES` | Maximum retry attempts | `3` | `5` |
| `RETRY_DELAY` | Delay between retries (seconds) | `1` | `2` |

### Setting Environment Variables

**macOS/Linux:**
```bash
export LIGHTRAG_BASE_URL="http://localhost:9621"
export LIGHTRAG_API_KEY="Insert-LightRAG-API-Key-Here"
export LOG_LEVEL="DEBUG"
```

**Windows:**
```cmd
set LIGHTRAG_BASE_URL=http://localhost:9621
set LIGHTRAG_API_KEY=lightragsecretkey
set LOG_LEVEL=DEBUG
```

**In MCP Configuration:**
```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "Insert-LightRAG-API-Key-Here",
        "LIGHTRAG_TIMEOUT": "30",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Advanced Configuration

### Custom Installation Path

If installed in a custom location:

```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "/path/to/python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "cwd": "/path/to/installation",
      "env": {
        "PYTHONPATH": "/path/to/installation",
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "Insert-LightRAG-API-Key-Here"
      }
    }
  }
}
```

### Virtual Environment

Using a virtual environment:

```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "Insert-LightRAG-API-Key-Here"
      }
    }
  }
}
```

### Multiple LightRAG Instances

Configure multiple LightRAG servers:

```json
{
  "mcpServers": {
    "lightrag-primary": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "primary-key"
      }
    },
    "lightrag-secondary": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9622",
        "LIGHTRAG_API_KEY": "secondary-key"
      }
    }
  }
}
```

### Development Configuration

For development with debug logging:

```json
{
  "mcpServers": {
    "daniel-lightrag-dev": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "Insert-LightRAG-API-Key-Here",
        "LOG_LEVEL": "DEBUG",
        "LIGHTRAG_TIMEOUT": "60"
      }
    }
  }
}
```

### Streamable HTTP Transport

The server defaults to Streamable HTTP transport, which exposes an HTTP endpoint at `/mcp`. This allows MCP clients to connect over HTTP instead of launching the server as a subprocess.

#### Starting the Server with HTTP Transport

```bash
# Default: listens on http://0.0.0.0:8080/mcp
daniel-lightrag-mcp

# Custom host and port
daniel-lightrag-mcp --transport streamable-http --host 127.0.0.1 --port 3000

# Or via environment variables
MCP_TRANSPORT=streamable-http MCP_HOST=127.0.0.1 MCP_PORT=3000 daniel-lightrag-mcp
```

#### Configuring MCP Clients for HTTP Transport

For MCP clients that support connecting to an HTTP endpoint (instead of launching a subprocess), configure them to connect to the server's `/mcp` URL:

```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

If the server is running on a remote host or custom port:

```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "url": "http://your-server-host:8080/mcp"
    }
  }
}
```

#### Using STDIO Transport with MCP Clients

For MCP clients that launch the server as a subprocess (e.g., Claude Desktop), use STDIO transport:

```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp", "--transport", "stdio"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "Insert-LightRAG-API-Key-Here"
      }
    }
  }
}
```

Or set the transport via environment variable:

```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "Insert-LightRAG-API-Key-Here"
      }
    }
  }
}
```

#### Docker with HTTP Transport

```bash
# Build the image
docker build -t daniel-lightrag-mcp .

# Run with Streamable HTTP (default) — exposes port 8080
docker run -p 8080:8080 \
  -e LIGHTRAG_BASE_URL=http://host.docker.internal:9621 \
  daniel-lightrag-mcp

# Run with custom port
docker run -p 3000:3000 \
  -e MCP_PORT=3000 \
  -e LIGHTRAG_BASE_URL=http://host.docker.internal:9621 \
  daniel-lightrag-mcp

# Run with STDIO transport
docker run -i \
  -e MCP_TRANSPORT=stdio \
  -e LIGHTRAG_BASE_URL=http://host.docker.internal:9621 \
  daniel-lightrag-mcp
```

Then configure your MCP client to connect to `http://localhost:8080/mcp`.

## Security Configuration

### API Key Management

**Best Practices:**
1. **Never hardcode API keys** in configuration files
2. **Use environment variables** for sensitive data
3. **Rotate keys regularly** for production environments
4. **Use different keys** for different environments

**Secure Configuration:**
```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621"
      }
    }
  }
}
```

Then set the API key separately:
```bash
export LIGHTRAG_API_KEY="your-secure-api-key"
```

### Network Security

**HTTPS Configuration:**
```json
{
  "env": {
    "LIGHTRAG_BASE_URL": "https://your-lightrag-server.com:9621",
    "LIGHTRAG_API_KEY": "your-secure-api-key"
  }
}
```

**Custom Certificates:**
```json
{
  "env": {
    "LIGHTRAG_BASE_URL": "https://your-lightrag-server.com:9621",
    "LIGHTRAG_API_KEY": "your-secure-api-key",
    "SSL_CERT_PATH": "/path/to/certificate.pem",
    "SSL_VERIFY": "true"
  }
}
```

## Troubleshooting Configuration

### Common Issues

#### 1. Server Not Found
**Error**: `Command not found: python`
**Solution**: Use full path to Python executable
```json
{
  "command": "/usr/bin/python3",
  "args": ["-m", "daniel_lightrag_mcp"]
}
```

#### 2. Module Not Found
**Error**: `No module named 'daniel_lightrag_mcp'`
**Solutions**:
- Verify installation: `pip list | grep daniel-lightrag-mcp`
- Use full path: `"command": "/path/to/venv/bin/python"`
- Set PYTHONPATH: `"env": {"PYTHONPATH": "/path/to/installation"}`

#### 3. Connection Refused
**Error**: `Connection refused to http://localhost:9621`
**Solutions**:
- Verify LightRAG server is running
- Check URL in configuration
- Test with curl: `curl http://localhost:9621/health`

#### 4. Authentication Failed
**Error**: `HTTP 403: API Key required`
**Solutions**:
- Verify API key is set correctly
- Check environment variable: `echo $LIGHTRAG_API_KEY`
- Test API key with curl: `curl -H "Authorization: Bearer your-key" http://localhost:9621/health`

#### 5. Timeout Errors
**Error**: `Request timeout`
**Solutions**:
- Increase timeout: `"LIGHTRAG_TIMEOUT": "60"`
- Check server performance
- Verify network connectivity

### Debug Configuration

Enable debug mode:
```json
{
  "mcpServers": {
    "daniel-lightrag": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "Insert-LightRAG-API-Key-Here",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Validation Commands

**Test Configuration:**
```bash
# Test Python module
python -c "import daniel_lightrag_mcp; print('OK')"

# Test server connection
curl http://localhost:9621/health

# Test with API key
curl -H "Authorization: Bearer Insert-LightRAG-API-Key-Here" http://localhost:9621/health

# Test MCP server startup
python -m daniel_lightrag_mcp &
sleep 2
pkill -f daniel_lightrag_mcp
```

## Performance Tuning

### Timeout Configuration

Adjust timeouts based on your use case:

```json
{
  "env": {
    "LIGHTRAG_TIMEOUT": "30",     // Standard operations
    "QUERY_TIMEOUT": "60",        // Complex queries
    "UPLOAD_TIMEOUT": "120"       // Large file uploads
  }
}
```

### Connection Pooling

Configure connection limits:

```json
{
  "env": {
    "MAX_CONNECTIONS": "10",
    "MAX_KEEPALIVE_CONNECTIONS": "5",
    "KEEPALIVE_EXPIRY": "30"
  }
}
```

### Retry Configuration

Configure retry behavior:

```json
{
  "env": {
    "MAX_RETRIES": "3",
    "RETRY_DELAY": "1",
    "BACKOFF_FACTOR": "2"
  }
}
```

## Monitoring Configuration

### Logging Configuration

```json
{
  "env": {
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "json",
    "LOG_FILE": "/var/log/lightrag-mcp.log"
  }
}
```

### Health Check Configuration

```json
{
  "env": {
    "HEALTH_CHECK_INTERVAL": "30",
    "HEALTH_CHECK_TIMEOUT": "5",
    "HEALTH_CHECK_RETRIES": "3"
  }
}
```

## Production Deployment

### Production Configuration Template

```json
{
  "mcpServers": {
    "daniel-lightrag-prod": {
      "command": "/opt/venv/bin/python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "cwd": "/opt/lightrag-mcp",
      "env": {
        "LIGHTRAG_BASE_URL": "https://lightrag.yourdomain.com:9621",
        "LIGHTRAG_TIMEOUT": "60",
        "LOG_LEVEL": "INFO",
        "MAX_RETRIES": "5",
        "RETRY_DELAY": "2"
      }
    }
  }
}
```

### Environment-Specific Configurations

**Development:**
```json
{
  "env": {
    "LIGHTRAG_BASE_URL": "http://localhost:9621",
    "LOG_LEVEL": "DEBUG",
    "LIGHTRAG_TIMEOUT": "30"
  }
}
```

**Staging:**
```json
{
  "env": {
    "LIGHTRAG_BASE_URL": "https://staging-lightrag.yourdomain.com:9621",
    "LOG_LEVEL": "INFO",
    "LIGHTRAG_TIMEOUT": "45"
  }
}
```

**Production:**
```json
{
  "env": {
    "LIGHTRAG_BASE_URL": "https://lightrag.yourdomain.com:9621",
    "LOG_LEVEL": "WARNING",
    "LIGHTRAG_TIMEOUT": "60"
  }
}
```

## Configuration Validation

### Validation Checklist

- [ ] Python executable path is correct
- [ ] Module is installed and importable
- [ ] LightRAG server URL is accessible
- [ ] API key is valid and set
- [ ] Environment variables are configured
- [ ] Timeouts are appropriate for your use case
- [ ] Logging level is set correctly
- [ ] MCP client configuration is valid JSON

### Automated Validation

Create a validation script:

```bash
#!/bin/bash
# validate-config.sh

echo "Validating LightRAG MCP Configuration..."

# Test Python module
python -c "import daniel_lightrag_mcp; print('✅ Module import: OK')" || echo "❌ Module import: FAILED"

# Test server connection
curl -s http://localhost:9621/health > /dev/null && echo "✅ Server connection: OK" || echo "❌ Server connection: FAILED"

# Test API key
if [ -n "$LIGHTRAG_API_KEY" ]; then
    echo "✅ API key: SET"
else
    echo "❌ API key: NOT SET"
fi

# Test MCP server startup
python -m daniel_lightrag_mcp &
PID=$!
sleep 3
if kill -0 $PID 2>/dev/null; then
    echo "✅ MCP server startup: OK"
    kill $PID
else
    echo "❌ MCP server startup: FAILED"
fi

echo "Validation complete!"
```

Run validation:
```bash
chmod +x validate-config.sh
./validate-config.sh
```

This comprehensive configuration guide ensures proper setup and troubleshooting of the LightRAG MCP Server across different environments and use cases.