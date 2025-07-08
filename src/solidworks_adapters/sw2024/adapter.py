"""
SolidWorks 2024 Python Adapter

Python adapter that uses PythonNET to bridge to the C# SolidWorks adapter.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import clr
import System
from System.Threading.Tasks import Task
from System.Collections.Generic import Dictionary as NetDict

from ..common.base_adapter import SolidWorksAdapter

logger = logging.getLogger(__name__)


class SolidWorks2024Adapter(SolidWorksAdapter):
    """Python adapter for SolidWorks 2024 using PythonNET bridge"""

    def __init__(self):
        super().__init__("2024")
        self.cs_adapter = None
        self._load_assembly()

    def _load_assembly(self):
        """Load the C# assembly"""
        try:
            # Add reference to our C# adapter DLL
            assembly_path = Path(__file__).parent / "SolidWorksAdapter2024.dll"
            if assembly_path.exists():
                clr.AddReference(str(assembly_path))
            else:
                # Try to compile the C# code if DLL doesn't exist
                self._compile_cs_adapter()
                clr.AddReference(str(assembly_path))
            
            # Import the namespace
            from MCP.SolidWorks.Adapters import SolidWorksAdapter2024
            self.cs_adapter = SolidWorksAdapter2024()
            
        except Exception as e:
            logger.error(f"Failed to load C# adapter: {e}")
            raise

    def _compile_cs_adapter(self):
        """Compile the C# adapter if needed"""
        import subprocess
        
        cs_file = Path(__file__).parent / "SolidWorksAdapter2024.cs"
        dll_file = Path(__file__).parent / "SolidWorksAdapter2024.dll"
        
        # Simple compilation command (requires .NET SDK)
        cmd = [
            "csc",
            "/target:library",
            f"/out:{dll_file}",
            "/reference:SolidWorks.Interop.sldworks.dll",
            "/reference:SolidWorks.Interop.swconst.dll",
            "/reference:SolidWorks.Interop.swpublished.dll",
            str(cs_file)
        ]
        
        subprocess.run(cmd, check=True)

    async def connect(self) -> bool:
        """Connect to SolidWorks instance"""
        try:
            # Call async method from C#
            task = self.cs_adapter.ConnectAsync()
            result = await self._await_task(task)
            self.connected = result
            return result
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from SolidWorks"""
        if self.cs_adapter:
            task = self.cs_adapter.DisconnectAsync()
            await self._await_task(task)
            self.connected = False

    async def open_document(self, file_path: str) -> Dict[str, Any]:
        """Open a SolidWorks document"""
        validated_path = self._validate_file_path(file_path)
        task = self.cs_adapter.OpenDocumentAsync(str(validated_path))
        result = await self._await_task(task)
        return self._convert_net_dict_to_dict(result)

    async def get_features(self) -> List[Dict[str, Any]]:
        """Get all features from the active model"""
        task = self.cs_adapter.GetFeaturesAsync()
        result = await self._await_task(task)
        return [self._convert_net_dict_to_dict(feat) for feat in result]

    async def modify_dimension(
        self, 
        feature_name: str, 
        dimension_name: str, 
        value: float
    ) -> bool:
        """Modify a dimension value"""
        task = self.cs_adapter.ModifyDimensionAsync(feature_name, dimension_name, value)
        return await self._await_task(task)

    async def get_design_tables(self) -> List[Dict[str, Any]]:
        """Get all design tables in the model"""
        # This would need to be implemented in the C# adapter
        # For now, return empty list
        return []

    async def update_design_table(
        self, 
        table_name: str, 
        configuration: str, 
        values: Dict[str, Any]
    ) -> bool:
        """Update design table values"""
        # Convert Python dict to .NET Dictionary
        net_dict = NetDict[System.String, System.Object]()
        for k, v in values.items():
            net_dict[k] = v
        
        task = self.cs_adapter.UpdateDesignTableAsync(table_name, configuration, net_dict)
        return await self._await_task(task)

    async def run_macro(
        self, 
        macro_path: str, 
        macro_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Run a VBA macro"""
        net_params = None
        if parameters:
            net_params = NetDict[System.String, System.Object]()
            for k, v in parameters.items():
                net_params[k] = v
        
        task = self.cs_adapter.RunMacroAsync(
            macro_path, 
            macro_name or "", 
            net_params or NetDict[System.String, System.Object]()
        )
        result = await self._await_task(task)
        return self._convert_net_dict_to_dict(result)

    async def export_file(
        self, 
        output_path: str, 
        format: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Export the model to various formats"""
        formatted_options = self._format_export_options(format, options or {})
        
        net_options = NetDict[System.String, System.Object]()
        for k, v in formatted_options.items():
            net_options[k] = v
        
        task = self.cs_adapter.ExportFileAsync(output_path, format, net_options)
        return await self._await_task(task)

    async def get_model_info(self) -> Dict[str, Any]:
        """Get detailed information about the current model"""
        task = self.cs_adapter.GetModelInfoAsync()
        result = await self._await_task(task)
        return self._convert_net_dict_to_dict(result)

    async def rebuild_model(self, force: bool = False) -> Tuple[bool, List[str]]:
        """Rebuild the model and return status and any errors"""
        task = self.cs_adapter.RebuildModelAsync(force)
        result = await self._await_task(task)
        return result.Item1, list(result.Item2)

    async def get_configurations(self) -> List[Dict[str, Any]]:
        """Get all configurations in the model"""
        # To be implemented in C# adapter
        return []

    async def activate_configuration(self, config_name: str) -> bool:
        """Activate a specific configuration"""
        # To be implemented in C# adapter
        return False

    async def get_custom_properties(self) -> Dict[str, Any]:
        """Get custom properties of the model"""
        info = await self.get_model_info()
        return info.get("customProperties", {})

    async def set_custom_property(
        self, 
        property_name: str, 
        value: Any, 
        configuration: Optional[str] = None
    ) -> bool:
        """Set a custom property"""
        # To be implemented in C# adapter
        return False

    async def get_mass_properties(self) -> Dict[str, float]:
        """Get mass properties of the model"""
        info = await self.get_model_info()
        return {
            "mass": info.get("mass", 0.0),
            "volume": info.get("volume", 0.0),
            "surface_area": info.get("surfaceArea", 0.0),
            "center_of_mass_x": info.get("centerOfMass", [0, 0, 0])[0],
            "center_of_mass_y": info.get("centerOfMass", [0, 0, 0])[1],
            "center_of_mass_z": info.get("centerOfMass", [0, 0, 0])[2],
        }

    async def get_bounding_box(self) -> Dict[str, float]:
        """Get bounding box of the model"""
        # To be implemented in C# adapter
        return {}

    async def create_drawing(self, template_path: str) -> bool:
        """Create a drawing from the model"""
        # To be implemented in C# adapter
        return False

    async def list_open_documents(self) -> List[Dict[str, Any]]:
        """List all open documents"""
        # To be implemented in C# adapter
        return []

    async def get_document_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a specific document"""
        # To be implemented in C# adapter
        return {}

    async def take_screenshot(
        self, 
        output_path: str, 
        width: int = 1920, 
        height: int = 1080
    ) -> bool:
        """Take a screenshot of the current view"""
        # To be implemented in C# adapter
        return False

    async def execute_feature_action(
        self, 
        feature_name: str, 
        action: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute an action on a feature"""
        # To be implemented in C# adapter
        return None

    # Helper methods
    async def _await_task(self, task):
        """Convert .NET Task to Python awaitable"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, task.Result)

    def _convert_net_dict_to_dict(self, net_dict) -> Dict[str, Any]:
        """Convert .NET Dictionary to Python dict"""
        if net_dict is None:
            return {}
        
        py_dict = {}
        for key in net_dict.Keys:
            value = net_dict[key]
            if hasattr(value, 'Keys'):  # Nested dictionary
                py_dict[str(key)] = self._convert_net_dict_to_dict(value)
            elif hasattr(value, '__iter__') and not isinstance(value, str):  # List
                py_dict[str(key)] = list(value)
            else:
                py_dict[str(key)] = value
        
        return py_dict