# mcp-server-solidworks
 This MCP server integrates with SolidWorks API and structuring it into Claude-compatible context streams.
 ## 🚀 Contributing to SolidPilot

SolidPilot is an open-source AI Assistant for SolidWorks. Its architecture is modular, version-aware, and designed to work with local language models like Claude through the MCP (Model Context Protocol).

### 🧩 Architecture Overview
![mermaid-diagram-2025-04-11-182739](https://github.com/user-attachments/assets/50269ad7-0b31-4c1b-943e-14e146ab82eb)

The assistant is composed of:
- A **Claude UI** interface
- A **Python layer** for prompt generation and context building
- A **C# Adapter Layer** for SolidWorks version-specific automation
- A **COM bridge** via PythonNET

### 🛠️ How You Can Help

We welcome contributions in areas like:

- ✨ **New Adapter DLLs** for SolidWorks versions
- 🧠 **Improved Prompt Templates** for model understanding
- 🧪 **Testing MCP logic** with various LLMs
- 🧰 **Extending the C# API coverage**
- 🧾 **Enhancing context builders** (e.g., capturing dimensions, mates, assemblies)
- 🔐 **Security & filter logic** for Claude's action suggestions

Check the [`CONTRIBUTING.md`](CONTRIBUTING.md) file for details on how to get started.

---

### Want to propose a change?  

Fork this repo, make your improvements, and open a pull request. For large-scale changes, please open an issue first to discuss it.

---

