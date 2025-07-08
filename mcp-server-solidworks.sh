#!/bin/bash
# Unix/macOS launcher for SolidWorks MCP Server
# This runs the server directly without Docker

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Run the Python module directly
exec python3 -m mcp_server_solidworks.mcp_host.server "$@"