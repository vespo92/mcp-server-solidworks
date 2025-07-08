"""
MCP Server for SolidWorks

A Model Context Protocol server that provides AI assistance for SolidWorks CAD automation.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .mcp_host.server import SolidWorksMCPServer, main

__all__ = ["SolidWorksMCPServer", "main"]
