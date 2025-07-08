@echo off
REM Windows launcher for SolidWorks MCP Server
REM This runs the server directly without Docker

REM Change to the directory where this script is located
cd /d "%~dp0"

REM Run the Python module directly
python -m mcp_server_solidworks.mcp_host.server %*