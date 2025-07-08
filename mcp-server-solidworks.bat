@echo off
REM Simple wrapper script for Claude Desktop to connect to the MCP server

REM Change to the project directory
cd /d "%~dp0"

REM Ensure services are running
docker-compose up -d >nul 2>&1

REM Connect to the MCP server stdio
docker-compose exec -T mcp-server python -m mcp_server_solidworks.mcp_host.server