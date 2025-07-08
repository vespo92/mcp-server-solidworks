"""
SolidWorks MCP Server

Main server implementation for the SolidWorks Model Context Protocol server.
Handles MCP protocol communication and routes requests to appropriate handlers.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddingContent,
    CompletionResult,
    Resource,
    ResourceTemplate,
    Prompt,
    PromptMessage,
    PromptArgument,
)

from ..context_builder.builder import SolidWorksContextBuilder
from ..solidworks_adapters.factory import AdapterFactory
from ..tools.solidworks_tools import SolidWorksTools
from ..events.event_manager import EventManager
from ..version_manager.manager import VersionManager

logger = logging.getLogger(__name__)


class SolidWorksMCPServer:
    """Main MCP server for SolidWorks integration"""

    def __init__(self):
        self.server = Server("solidworks-mcp")
        self.context_builder = SolidWorksContextBuilder()
        self.adapter_factory = AdapterFactory()
        self.tools = SolidWorksTools()
        self.event_manager = EventManager()
        self.version_manager = VersionManager()
        self.current_adapter = None
        
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP protocol handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available SolidWorks tools"""
            return [
                Tool(
                    name="open_model",
                    description="Open a SolidWorks model file",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the SolidWorks file (.sldprt, .sldasm, .slddrw)"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_features",
                    description="Get all features from the active model",
                    input_schema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="modify_dimension",
                    description="Modify a dimension value in the model",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "feature_name": {
                                "type": "string",
                                "description": "Name of the feature containing the dimension"
                            },
                            "dimension_name": {
                                "type": "string",
                                "description": "Name of the dimension to modify"
                            },
                            "value": {
                                "type": "number",
                                "description": "New value for the dimension"
                            }
                        },
                        "required": ["feature_name", "dimension_name", "value"]
                    }
                ),
                Tool(
                    name="run_macro",
                    description="Run a VBA macro in SolidWorks",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "macro_path": {
                                "type": "string",
                                "description": "Path to the VBA macro file (.swp)"
                            },
                            "macro_name": {
                                "type": "string",
                                "description": "Name of the macro procedure to run"
                            }
                        },
                        "required": ["macro_path"]
                    }
                ),
                Tool(
                    name="update_design_table",
                    description="Update values in a design table",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the design table"
                            },
                            "configuration": {
                                "type": "string",
                                "description": "Configuration name"
                            },
                            "values": {
                                "type": "object",
                                "description": "Key-value pairs of parameters to update"
                            }
                        },
                        "required": ["table_name", "values"]
                    }
                ),
                Tool(
                    name="export_model",
                    description="Export the model to various formats",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "output_path": {
                                "type": "string",
                                "description": "Path for the exported file"
                            },
                            "format": {
                                "type": "string",
                                "enum": ["STEP", "IGES", "STL", "PDF", "DXF", "DWG"],
                                "description": "Export format"
                            }
                        },
                        "required": ["output_path", "format"]
                    }
                ),
                Tool(
                    name="get_model_info",
                    description="Get detailed information about the current model",
                    input_schema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="rebuild_model",
                    description="Rebuild the current model",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "force": {
                                "type": "boolean",
                                "description": "Force rebuild even if not needed",
                                "default": False
                            }
                        }
                    }
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute a SolidWorks tool"""
            try:
                # Initialize adapter if needed
                if not self.current_adapter:
                    version = self.version_manager.detect_version()
                    self.current_adapter = self.adapter_factory.get_adapter(version)
                    await self.current_adapter.connect()

                # Execute the tool
                result = await self.tools.execute(name, arguments, self.current_adapter)
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "tool": name,
                        "arguments": arguments
                    }, indent=2)
                )]

        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """List available prompts for SolidWorks operations"""
            return [
                Prompt(
                    name="analyze_model",
                    description="Analyze a SolidWorks model and provide insights",
                    arguments=[
                        PromptArgument(
                            name="file_path",
                            description="Path to the SolidWorks file",
                            required=True
                        )
                    ]
                ),
                Prompt(
                    name="optimize_design",
                    description="Suggest optimizations for a design",
                    arguments=[
                        PromptArgument(
                            name="optimization_goal",
                            description="What to optimize for (weight, strength, cost, etc.)",
                            required=True
                        )
                    ]
                ),
                Prompt(
                    name="create_variants",
                    description="Generate design variants based on parameters",
                    arguments=[
                        PromptArgument(
                            name="parameters",
                            description="Parameters to vary",
                            required=True
                        ),
                        PromptArgument(
                            name="count",
                            description="Number of variants to generate",
                            required=False
                        )
                    ]
                ),
            ]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, Any]) -> PromptMessage:
            """Get a prompt with context"""
            context = await self.context_builder.build_context(
                self.current_adapter,
                prompt_name=name,
                arguments=arguments
            )
            
            return PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=context
                )
            )

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available SolidWorks resources"""
            if not self.current_adapter:
                return []
                
            models = await self.current_adapter.list_open_documents()
            return [
                Resource(
                    uri=f"solidworks://{model['path']}",
                    name=model['name'],
                    description=f"{model['type']} - {model['path']}",
                    mime_type="application/x-solidworks"
                )
                for model in models
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> TextContent:
            """Read a SolidWorks resource"""
            if not uri.startswith("solidworks://"):
                raise ValueError("Invalid SolidWorks URI")
                
            file_path = uri.replace("solidworks://", "")
            info = await self.current_adapter.get_document_info(file_path)
            
            return TextContent(
                type="text",
                text=json.dumps(info, indent=2)
            )

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

    async def cleanup(self):
        """Clean up resources"""
        if self.current_adapter:
            await self.current_adapter.disconnect()
        await self.event_manager.cleanup()


async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = SolidWorksMCPServer()
    
    try:
        await server.run()
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())