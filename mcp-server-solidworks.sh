#!/bin/bash
# Simple wrapper script for Claude Desktop to connect to the MCP server

# Change to the project directory
cd "$(dirname "$0")"

# Ensure services are running
docker-compose up -d >/dev/null 2>&1

# Connect to the MCP server stdio
docker-compose exec -T mcp-server python -m src.mcp_host.server