# 🤝 Contributing to mcp-server-solidworks

Thanks for your interest in contributing to **mcp-server-solidworks**, an AI-powered contextual assistant that communicates with SolidWorks through the Model Context Protocol (MCP) and local LLMs like Claude.  
Our goal is to make CAD smarter — and you're invited to help us build it.

We welcome all contributions, including code, documentation, bug reports, testing, feature suggestions, and UI design.

---

## 📦 Project Structure

Here's a comprehensive overview of the project directories:

| Folder | Description |
|--------|-------------|
| `adapters/` | C# Adapter DLLs for specific SolidWorks versions |
| ├── `2021/`, `2022/`... | Version-specific implementations |
| └── `common/` | Shared interfaces and base code for all adapters |
| `mcp/` | Python interface managing Claude communication and prompt generation |
| ├── `core/` | Core MCP logic (stream building, request routing) |
| ├── `prompts/` | Prompt templates and response patterns |
| └── `context/` | Building and updating context from user and model actions |
| `bridge/` | PythonNET bridge code that connects Python ↔ C# |
| `ui/` | User interface modules (planned) |
| `utils/` | Helper functions and shared utilities |
| `config/` | Configuration files (e.g., SolidWorks version, model port, Claude model ID) |
| `tests/` | Testing modules |
| ├── `unit/` | Unit tests for isolated logic |
| └── `integration/` | Full-stack tests with live SolidWorks models |
| `docs/` | Project documentation |
| └── `user/` | User guides and setup tutorials |
| `tools/` | Dev tools and CLI scripts |
| └── `api_analyzer/` | SolidWorks API diff tool for cross-version inspection |
| `examples/` | Example usage scenarios and quick demos |

---

## 🚀 How to Get Started

1. **Fork this repository** and clone your fork:
   ```bash
   git clone https://github.com/eyfel/mcp-server-solidworks.git
   cd mcp-server-solidworks
   
2.   **Install Python dependencies:**
   
pip install -r requirements.txt

3.   **Make sure you have:**

SolidWorks 2021+ installed
