#!/usr/bin/env python3
"""
Cross-platform launcher for SolidWorks MCP Server

This script can be used on any platform (Windows, macOS, Linux) to launch
the SolidWorks MCP server.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Launch the MCP server"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Run the server module directly
    cmd = [sys.executable, "-m", "mcp_server_solidworks.mcp_host.server"]
    
    # Set the working directory to the project root
    env = os.environ.copy()
    env['PYTHONPATH'] = str(script_dir)
    
    try:
        # Run the server
        subprocess.run(cmd, cwd=script_dir, env=env, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error running server: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())