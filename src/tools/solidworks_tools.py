"""
SolidWorks Tools Implementation

Implements the actual tool operations that the MCP server exposes.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..solidworks_adapters.common.base_adapter import SolidWorksAdapter
from ..context_builder.knowledge_base import SolidWorksKnowledgeBase

logger = logging.getLogger(__name__)


class SolidWorksTools:
    """Implementation of SolidWorks MCP tools"""

    def __init__(self, knowledge_base: Optional[SolidWorksKnowledgeBase] = None):
        self.knowledge_base = knowledge_base or SolidWorksKnowledgeBase()
        self._operation_history = []

    async def execute(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any], 
        adapter: SolidWorksAdapter
    ) -> Dict[str, Any]:
        """
        Execute a tool operation
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            adapter: SolidWorks adapter instance
            
        Returns:
            Result dictionary
        """
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")
        
        # Map tool names to methods
        tool_methods = {
            "open_model": self._open_model,
            "get_features": self._get_features,
            "modify_dimension": self._modify_dimension,
            "run_macro": self._run_macro,
            "update_design_table": self._update_design_table,
            "export_model": self._export_model,
            "get_model_info": self._get_model_info,
            "rebuild_model": self._rebuild_model,
            "take_screenshot": self._take_screenshot,
            "get_mass_properties": self._get_mass_properties,
            "set_custom_property": self._set_custom_property,
            "get_custom_properties": self._get_custom_properties,
            "activate_configuration": self._activate_configuration,
            "get_configurations": self._get_configurations,
            "create_drawing": self._create_drawing,
            "execute_feature_action": self._execute_feature_action,
        }
        
        if tool_name not in tool_methods:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Execute the tool
        try:
            result = await tool_methods[tool_name](arguments, adapter)
            
            # Store in knowledge base if successful
            if self.knowledge_base:
                await self.knowledge_base.store_operation(
                    operation=tool_name,
                    context=arguments,
                    result=result,
                    success=result.get("success", True),
                    tags=self._generate_tags(tool_name, arguments)
                )
            
            # Add to history
            self._operation_history.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result,
                "success": result.get("success", True)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "arguments": arguments
            }
            
            # Store error in knowledge base
            if self.knowledge_base:
                await self.knowledge_base.store_error_solution(
                    error_message=str(e),
                    error_context={"tool": tool_name, "arguments": arguments},
                    solution="Check the error message and verify inputs",
                    solution_steps=["Verify file paths", "Check SolidWorks is running", "Validate arguments"]
                )
            
            return error_result

    async def _open_model(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Open a SolidWorks model"""
        file_path = args["file_path"]
        
        # Validate file exists
        if not Path(file_path).exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        result = await adapter.open_document(file_path)
        
        # Add additional info
        if result.get("success"):
            model_info = await adapter.get_model_info()
            result["model_info"] = model_info
        
        return result

    async def _get_features(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Get all features from the active model"""
        features = await adapter.get_features()
        
        # Analyze features for insights
        feature_summary = {
            "total_features": len(features),
            "suppressed_count": sum(1 for f in features if f.get("suppressed", False)),
            "feature_types": {}
        }
        
        for feature in features:
            feature_type = feature.get("type", "Unknown")
            feature_summary["feature_types"][feature_type] = \
                feature_summary["feature_types"].get(feature_type, 0) + 1
        
        return {
            "success": True,
            "features": features,
            "summary": feature_summary
        }

    async def _modify_dimension(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Modify a dimension value"""
        feature_name = args["feature_name"]
        dimension_name = args["dimension_name"]
        value = float(args["value"])
        
        # Store original value if possible
        features = await adapter.get_features()
        original_value = None
        
        for feature in features:
            if feature["name"] == feature_name:
                for dim in feature.get("dimensions", []):
                    if dim["name"] == dimension_name:
                        original_value = dim["value"]
                        break
        
        success = await adapter.modify_dimension(feature_name, dimension_name, value)
        
        result = {
            "success": success,
            "feature_name": feature_name,
            "dimension_name": dimension_name,
            "new_value": value
        }
        
        if original_value is not None:
            result["original_value"] = original_value
            result["change_percentage"] = ((value - original_value) / original_value * 100) if original_value != 0 else 0
        
        return result

    async def _run_macro(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Run a VBA macro"""
        macro_path = args["macro_path"]
        macro_name = args.get("macro_name")
        parameters = args.get("parameters", {})
        
        # Validate macro file exists
        if not Path(macro_path).exists():
            return {
                "success": False,
                "error": f"Macro file not found: {macro_path}"
            }
        
        # Store macro pattern if successful
        result = await adapter.run_macro(macro_path, macro_name, parameters)
        
        if result.get("success") and self.knowledge_base:
            # Extract macro info for knowledge base
            macro_info = Path(macro_path).stem
            await self.knowledge_base.store_macro_pattern(
                macro_name=macro_info,
                description=f"Macro executed: {macro_name or 'main'}",
                code_snippet="",  # Could read the macro file if needed
                use_cases=[f"Called from {args.get('context', 'MCP')}"],
                parameters=parameters
            )
        
        return result

    async def _update_design_table(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Update design table values"""
        table_name = args["table_name"]
        configuration = args.get("configuration", "")
        values = args["values"]
        
        success = await adapter.update_design_table(table_name, configuration, values)
        
        return {
            "success": success,
            "table_name": table_name,
            "configuration": configuration,
            "updated_values": values,
            "value_count": len(values)
        }

    async def _export_model(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Export the model to various formats"""
        output_path = args["output_path"]
        format = args["format"].upper()
        options = args.get("options", {})
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        success = await adapter.export_file(output_path, format, options)
        
        result = {
            "success": success,
            "output_path": output_path,
            "format": format
        }
        
        if success and Path(output_path).exists():
            result["file_size"] = Path(output_path).stat().st_size
            result["file_size_mb"] = round(result["file_size"] / (1024 * 1024), 2)
        
        return result

    async def _get_model_info(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Get detailed model information"""
        info = await adapter.get_model_info()
        
        # Add analysis if available
        if "mass" in info:
            info["weight_kg"] = round(info["mass"], 3)
            info["weight_lbs"] = round(info["mass"] * 2.20462, 3)
        
        return {
            "success": True,
            "model_info": info
        }

    async def _rebuild_model(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Rebuild the model"""
        force = args.get("force", False)
        
        success, errors = await adapter.rebuild_model(force)
        
        return {
            "success": success,
            "force_rebuild": force,
            "errors": errors,
            "error_count": len(errors)
        }

    async def _take_screenshot(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Take a screenshot of the current view"""
        output_path = args["output_path"]
        width = args.get("width", 1920)
        height = args.get("height", 1080)
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        success = await adapter.take_screenshot(output_path, width, height)
        
        result = {
            "success": success,
            "output_path": output_path,
            "resolution": f"{width}x{height}"
        }
        
        if success and Path(output_path).exists():
            result["file_size"] = Path(output_path).stat().st_size
        
        return result

    async def _get_mass_properties(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Get mass properties of the model"""
        properties = await adapter.get_mass_properties()
        
        return {
            "success": True,
            "mass_properties": properties,
            "units": {
                "mass": "kg",
                "volume": "m³",
                "surface_area": "m²",
                "center_of_mass": "m"
            }
        }

    async def _set_custom_property(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Set a custom property"""
        property_name = args["property_name"]
        value = args["value"]
        configuration = args.get("configuration")
        
        success = await adapter.set_custom_property(property_name, value, configuration)
        
        return {
            "success": success,
            "property_name": property_name,
            "value": value,
            "configuration": configuration or "Default"
        }

    async def _get_custom_properties(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Get custom properties"""
        properties = await adapter.get_custom_properties()
        
        return {
            "success": True,
            "properties": properties,
            "property_count": len(properties)
        }

    async def _activate_configuration(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Activate a specific configuration"""
        config_name = args["configuration_name"]
        
        success = await adapter.activate_configuration(config_name)
        
        return {
            "success": success,
            "activated_configuration": config_name
        }

    async def _get_configurations(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Get all configurations"""
        configurations = await adapter.get_configurations()
        
        return {
            "success": True,
            "configurations": configurations,
            "configuration_count": len(configurations)
        }

    async def _create_drawing(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Create a drawing from the model"""
        template_path = args["template_path"]
        
        success = await adapter.create_drawing(template_path)
        
        return {
            "success": success,
            "template_used": template_path
        }

    async def _execute_feature_action(self, args: Dict[str, Any], adapter: SolidWorksAdapter) -> Dict[str, Any]:
        """Execute an action on a feature"""
        feature_name = args["feature_name"]
        action = args["action"]
        parameters = args.get("parameters", {})
        
        result = await adapter.execute_feature_action(feature_name, action, parameters)
        
        return {
            "success": result is not None,
            "feature_name": feature_name,
            "action": action,
            "result": result
        }

    def _generate_tags(self, tool_name: str, arguments: Dict[str, Any]) -> List[str]:
        """Generate tags for knowledge base storage"""
        tags = [tool_name]
        
        # Add file type tags
        if "file_path" in arguments:
            ext = Path(arguments["file_path"]).suffix.lower()
            if ext == ".sldprt":
                tags.append("part")
            elif ext == ".sldasm":
                tags.append("assembly")
            elif ext == ".slddrw":
                tags.append("drawing")
        
        # Add operation type tags
        if tool_name in ["modify_dimension", "update_design_table"]:
            tags.append("parametric")
        elif tool_name in ["export_model", "take_screenshot"]:
            tags.append("export")
        elif tool_name == "run_macro":
            tags.append("automation")
        
        return tags

    def get_operation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent operation history"""
        return self._operation_history[-limit:]