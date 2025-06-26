# SolidWorks MCP Server Installation Guide

## Prerequisites

### Required Software
1. **SolidWorks** (2021-2025) - Must be installed and licensed
2. **Python 3.9+** - For running the MCP server
3. **.NET Framework 4.8+** - For C# adapters
4. **.NET SDK** - For compiling C# adapters
5. **Visual Studio Build Tools** (optional) - For advanced C# compilation

### Python Dependencies
All Python dependencies are listed in `pyproject.toml` and will be installed automatically.

## Installation Steps

### 1. Clone the Repository
```bash
git clone <repository-url>
cd mcp-server-solidworks
```

### 2. Create Python Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install -e .
```

### 4. Install SolidWorks API References

The SolidWorks API references need to be copied from your SolidWorks installation:

```bash
# Windows typical paths
# Copy these DLLs to src/solidworks_adapters/references/
C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\SolidWorks.Interop.sldworks.dll
C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\SolidWorks.Interop.swconst.dll
C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\SolidWorks.Interop.swpublished.dll
```

### 5. Compile C# Adapters

For each SolidWorks version you want to support:

```bash
cd src/solidworks_adapters/sw2024
csc /target:library /out:SolidWorksAdapter2024.dll /reference:../references/*.dll SolidWorksAdapter2024.cs
```

Or use the provided build script:
```bash
python scripts/build_adapters.py
```

### 6. Configure ChromaDB (Optional)

If you want to use the AI knowledge base features:

```bash
# ChromaDB will create a local database in ./chroma_db/
# No additional configuration needed for local use
```

### 7. Set Up Environment Variables

Create a `.env` file in the project root:

```env
# SolidWorks Installation Path
SOLIDWORKS_PATH=C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS

# MCP Server Configuration
MCP_SERVER_PORT=3000
MCP_LOG_LEVEL=INFO

# ChromaDB Configuration (optional)
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=solidworks_operations

# API Keys (if using cloud services)
OPENAI_API_KEY=your-key-here  # Optional, for enhanced embeddings
```

### 8. Test the Installation

Run the test script to verify everything is working:

```bash
python scripts/test_installation.py
```

This will:
- Check Python dependencies
- Verify C# adapter compilation
- Test SolidWorks connection
- Validate ChromaDB setup

## Running the Server

### Start the MCP Server
```bash
python -m src.mcp_host.server
```

### Using with Claude Desktop

Add to your Claude Desktop configuration (`AppData\Roaming\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "solidworks": {
      "command": "python",
      "args": ["-m", "src.mcp_host.server"],
      "cwd": "C:\\path\\to\\mcp-server-solidworks"
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **"SolidWorks not found" error**
   - Ensure SolidWorks is running
   - Check SOLIDWORKS_PATH environment variable
   - Run as administrator if needed

2. **C# adapter compilation fails**
   - Install .NET SDK from Microsoft
   - Ensure SolidWorks API DLLs are in the references folder
   - Check file paths in the csc command

3. **PythonNET import errors**
   - Reinstall pythonnet: `pip install --force-reinstall pythonnet`
   - Ensure .NET Framework 4.8+ is installed

4. **ChromaDB errors**
   - Delete the chroma_db folder and let it recreate
   - Check disk space and permissions

### Debug Mode

Enable debug logging:
```bash
export MCP_LOG_LEVEL=DEBUG
python -m src.mcp_host.server
```

## Advanced Configuration

### Multiple SolidWorks Versions

To support multiple versions, compile adapters for each:

```bash
# In each version folder (sw2021, sw2022, etc.)
csc /target:library /out:SolidWorksAdapter20XX.dll /reference:../references/*.dll SolidWorksAdapter20XX.cs
```

### Custom VBA Macro Library

Place your VBA macros in a dedicated folder and configure:

```env
VBA_MACRO_LIBRARY=C:\SolidWorks\Macros
```

### Remote ChromaDB

To use a remote ChromaDB instance:

```env
CHROMA_HOST=your-chromadb-host
CHROMA_PORT=8000
CHROMA_API_KEY=your-api-key
```

## Security Considerations

1. **API Keys**: Store sensitive keys in environment variables, never in code
2. **File Access**: The server has access to your file system - configure appropriate permissions
3. **Macro Execution**: Only run trusted VBA macros as they have full system access
4. **Network Access**: If exposing the MCP server, use proper authentication and HTTPS

## Next Steps

1. Review the [examples](examples/) folder for usage patterns
2. Check the [API documentation](docs/API.md) for available tools
3. Explore the [design patterns](docs/DESIGN_PATTERNS.md) guide
4. Join our community for support and updates