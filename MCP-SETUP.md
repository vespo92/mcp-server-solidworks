# MCP Setup for SolidWorks Server

This document explains how to configure the SolidWorks MCP server for use with Claude Desktop.

## Prerequisites

1. Install Python dependencies:
   ```bash
   pip install -e .
   ```
   
   Or install just the required packages:
   ```bash
   pip install mcp pythonnet pydantic asyncio
   ```

2. Ensure SolidWorks is installed on your Windows machine (if running locally)

## Configuration Options

### Option 1: Direct Python Module

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "solidworks": {
      "command": "python3",
      "args": ["-m", "mcp_server_solidworks.mcp_host.server"],
      "cwd": "/path/to/mcp-server-solidworks",
      "env": {
        "PYTHONPATH": "/path/to/mcp-server-solidworks"
      }
    }
  }
}
```

### Option 2: Using Launch Script

```json
{
  "mcpServers": {
    "solidworks": {
      "command": "/path/to/mcp-server-solidworks/mcp-server-solidworks"
    }
  }
}
```

### Option 3: Cross-platform Script

```json
{
  "mcpServers": {
    "solidworks": {
      "command": "python3",
      "args": ["/path/to/mcp-server-solidworks/run.py"]
    }
  }
}
```

## Windows-specific Configuration

On Windows, use `python` instead of `python3`:

```json
{
  "mcpServers": {
    "solidworks": {
      "command": "python",
      "args": ["-m", "mcp_server_solidworks.mcp_host.server"],
      "cwd": "C:\\path\\to\\mcp-server-solidworks"
    }
  }
}
```

Or use the batch file:

```json
{
  "mcpServers": {
    "solidworks": {
      "command": "C:\\path\\to\\mcp-server-solidworks\\mcp-server-solidworks.bat"
    }
  }
}
```

## Environment Variables

You can set environment variables for the server:

- `SOLIDWORKS_VERSION`: Specify SolidWorks version (e.g., "2024")
- `SOLIDWORKS_PATH`: Override default SolidWorks installation path
- `LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)

Example:

```json
{
  "mcpServers": {
    "solidworks": {
      "command": "python3",
      "args": ["-m", "mcp_server_solidworks.mcp_host.server"],
      "cwd": "/path/to/mcp-server-solidworks",
      "env": {
        "SOLIDWORKS_VERSION": "2024",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Troubleshooting

1. **Module not found errors**: Ensure all dependencies are installed
2. **SolidWorks connection errors**: Verify SolidWorks is installed and the COM interface is available
3. **Permission errors**: Run with appropriate permissions for SolidWorks automation

## Docker Removal Note

This server no longer requires Docker. The previous Docker-based approach has been replaced with direct Python execution for better MCP compliance and reduced overhead.