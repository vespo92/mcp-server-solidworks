"""
Tests for SolidWorks MCP Server
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from src.mcp_host.server import SolidWorksMCPServer
from src.tools.solidworks_tools import SolidWorksTools
from src.context_builder.builder import SolidWorksContextBuilder
from src.solidworks_adapters.common.base_adapter import SolidWorksAdapter


@pytest.fixture
def mock_adapter():
    """Create a mock SolidWorks adapter"""
    adapter = Mock(spec=SolidWorksAdapter)
    adapter.connected = True
    adapter.get_model_info = AsyncMock(return_value={
        "title": "TestPart",
        "type": "Part",
        "path": "C:/test.sldprt"
    })
    adapter.get_features = AsyncMock(return_value=[
        {"name": "Extrude1", "type": "Extrusion", "suppressed": False}
    ])
    return adapter


@pytest.fixture
async def mcp_server():
    """Create MCP server instance"""
    server = SolidWorksMCPServer()
    yield server
    await server.cleanup()


class TestMCPServer:
    """Test MCP server functionality"""

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_server):
        """Test listing available tools"""
        tools = await mcp_server.server.list_tools()
        
        assert len(tools) > 0
        tool_names = [tool.name for tool in tools]
        
        # Check essential tools are present
        assert "open_model" in tool_names
        assert "get_features" in tool_names
        assert "modify_dimension" in tool_names
        assert "run_macro" in tool_names
        assert "update_design_table" in tool_names

    @pytest.mark.asyncio
    async def test_tool_execution(self, mcp_server, mock_adapter):
        """Test tool execution"""
        mcp_server.current_adapter = mock_adapter
        
        result = await mcp_server.server.call_tool(
            "get_model_info",
            {}
        )
        
        assert len(result) > 0
        assert result[0].type == "text"
        
        # Parse result
        data = json.loads(result[0].text)
        assert data["success"] == True
        assert "model_info" in data

    @pytest.mark.asyncio
    async def test_list_prompts(self, mcp_server):
        """Test listing available prompts"""
        prompts = await mcp_server.server.list_prompts()
        
        assert len(prompts) > 0
        prompt_names = [prompt.name for prompt in prompts]
        
        # Check essential prompts
        assert "analyze_model" in prompt_names
        assert "optimize_design" in prompt_names
        assert "create_variants" in prompt_names

    @pytest.mark.asyncio
    async def test_context_building(self, mcp_server, mock_adapter):
        """Test context building for prompts"""
        mcp_server.current_adapter = mock_adapter
        
        prompt_msg = await mcp_server.server.get_prompt(
            "analyze_model",
            {"file_path": "C:/test.sldprt"}
        )
        
        assert prompt_msg.role == "user"
        assert prompt_msg.content.type == "text"
        assert "Current Model Context" in prompt_msg.content.text


class TestSolidWorksTools:
    """Test SolidWorks tools implementation"""

    @pytest.fixture
    def tools(self):
        """Create tools instance"""
        return SolidWorksTools()

    @pytest.mark.asyncio
    async def test_open_model_success(self, tools, mock_adapter):
        """Test successful model opening"""
        mock_adapter.open_document = AsyncMock(return_value={
            "success": True,
            "document_type": "Part"
        })
        
        with patch("pathlib.Path.exists", return_value=True):
            result = await tools._open_model(
                {"file_path": "C:/test.sldprt"},
                mock_adapter
            )
        
        assert result["success"] == True
        assert "model_info" in result

    @pytest.mark.asyncio
    async def test_open_model_file_not_found(self, tools, mock_adapter):
        """Test opening non-existent file"""
        with patch("pathlib.Path.exists", return_value=False):
            result = await tools._open_model(
                {"file_path": "C:/nonexistent.sldprt"},
                mock_adapter
            )
        
        assert result["success"] == False
        assert "File not found" in result["error"]

    @pytest.mark.asyncio
    async def test_modify_dimension(self, tools, mock_adapter):
        """Test dimension modification"""
        mock_adapter.get_features = AsyncMock(return_value=[
            {
                "name": "Extrude1",
                "dimensions": [
                    {"name": "D1@Extrude1", "value": 10.0}
                ]
            }
        ])
        mock_adapter.modify_dimension = AsyncMock(return_value=True)
        
        result = await tools._modify_dimension(
            {
                "feature_name": "Extrude1",
                "dimension_name": "D1@Extrude1",
                "value": 15.0
            },
            mock_adapter
        )
        
        assert result["success"] == True
        assert result["new_value"] == 15.0
        assert "original_value" in result

    @pytest.mark.asyncio
    async def test_export_model(self, tools, mock_adapter):
        """Test model export"""
        mock_adapter.export_file = AsyncMock(return_value=True)
        
        with patch("pathlib.Path.mkdir"), \
             patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.stat") as mock_stat:
            
            mock_stat.return_value.st_size = 1024000
            
            result = await tools._export_model(
                {
                    "output_path": "C:/export/test.step",
                    "format": "STEP"
                },
                mock_adapter
            )
        
        assert result["success"] == True
        assert result["format"] == "STEP"
        assert "file_size_mb" in result


class TestContextBuilder:
    """Test context builder functionality"""

    @pytest.fixture
    def context_builder(self):
        """Create context builder instance"""
        return SolidWorksContextBuilder()

    @pytest.mark.asyncio
    async def test_build_model_context(self, context_builder, mock_adapter):
        """Test building model context"""
        context = await context_builder._build_model_context(mock_adapter)
        
        assert "Model: TestPart" in context
        assert "Type: Part" in context
        assert "Features Summary:" in context

    @pytest.mark.asyncio
    async def test_build_analysis_context(self, context_builder):
        """Test building analysis-specific context"""
        context = await context_builder._build_analysis_context(
            {"file_path": "C:/test.sldprt"},
            None
        )
        
        assert "part file" in context
        assert "Analysis should cover:" in context

    def test_summarize_features(self, context_builder):
        """Test feature summarization"""
        features = [
            {"type": "Extrusion", "suppressed": False},
            {"type": "Extrusion", "suppressed": False},
            {"type": "Cut", "suppressed": False},
            {"type": "Fillet", "suppressed": True}
        ]
        
        summary = context_builder._summarize_features(features)
        
        assert "Total features: 4" in summary
        assert "Extrusion: 2" in summary
        assert "Suppressed features: 1" in summary


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, mcp_server, mock_adapter):
        """Test a complete workflow"""
        mcp_server.current_adapter = mock_adapter
        
        # Open model
        mock_adapter.open_document = AsyncMock(return_value={
            "success": True,
            "title": "TestPart"
        })
        
        # Get features
        mock_adapter.get_features = AsyncMock(return_value=[
            {"name": "Base", "type": "Extrusion"},
            {"name": "Hole1", "type": "Cut"}
        ])
        
        # Modify dimension
        mock_adapter.modify_dimension = AsyncMock(return_value=True)
        
        # Export
        mock_adapter.export_file = AsyncMock(return_value=True)
        
        # Execute workflow
        tools = [
            ("open_model", {"file_path": "C:/test.sldprt"}),
            ("get_features", {}),
            ("modify_dimension", {
                "feature_name": "Base",
                "dimension_name": "D1@Base",
                "value": 25.0
            }),
            ("export_model", {
                "output_path": "C:/export/modified.step",
                "format": "STEP"
            })
        ]
        
        results = []
        for tool_name, args in tools:
            result = await mcp_server.server.call_tool(tool_name, args)
            results.append(json.loads(result[0].text))
        
        # Verify workflow completed successfully
        assert all(r.get("success", False) for r in results)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])