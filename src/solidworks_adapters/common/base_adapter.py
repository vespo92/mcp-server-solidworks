"""
Base SolidWorks Adapter

Abstract base class for SolidWorks version-specific adapters.
Defines the common interface that all adapters must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SolidWorksAdapter(ABC):
    """Abstract base class for SolidWorks adapters"""

    def __init__(self, version: str):
        self.version = version
        self.swapp = None
        self.active_doc = None
        self.connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to SolidWorks instance"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from SolidWorks"""
        pass

    @abstractmethod
    async def open_document(self, file_path: str) -> Dict[str, Any]:
        """Open a SolidWorks document"""
        pass

    @abstractmethod
    async def close_document(self, save: bool = True) -> bool:
        """Close the active document"""
        pass

    @abstractmethod
    async def get_features(self) -> List[Dict[str, Any]]:
        """Get all features from the active model"""
        pass

    @abstractmethod
    async def modify_dimension(
        self, 
        feature_name: str, 
        dimension_name: str, 
        value: float
    ) -> bool:
        """Modify a dimension value"""
        pass

    @abstractmethod
    async def get_design_tables(self) -> List[Dict[str, Any]]:
        """Get all design tables in the model"""
        pass

    @abstractmethod
    async def update_design_table(
        self, 
        table_name: str, 
        configuration: str, 
        values: Dict[str, Any]
    ) -> bool:
        """Update design table values"""
        pass

    @abstractmethod
    async def run_macro(
        self, 
        macro_path: str, 
        macro_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Run a VBA macro"""
        pass

    @abstractmethod
    async def export_file(
        self, 
        output_path: str, 
        format: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Export the model to various formats"""
        pass

    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Get detailed information about the current model"""
        pass

    @abstractmethod
    async def rebuild_model(self, force: bool = False) -> Tuple[bool, List[str]]:
        """Rebuild the model and return status and any errors"""
        pass

    @abstractmethod
    async def get_configurations(self) -> List[Dict[str, Any]]:
        """Get all configurations in the model"""
        pass

    @abstractmethod
    async def activate_configuration(self, config_name: str) -> bool:
        """Activate a specific configuration"""
        pass

    @abstractmethod
    async def get_custom_properties(self) -> Dict[str, Any]:
        """Get custom properties of the model"""
        pass

    @abstractmethod
    async def set_custom_property(
        self, 
        property_name: str, 
        value: Any, 
        configuration: Optional[str] = None
    ) -> bool:
        """Set a custom property"""
        pass

    @abstractmethod
    async def get_mass_properties(self) -> Dict[str, float]:
        """Get mass properties of the model"""
        pass

    @abstractmethod
    async def get_bounding_box(self) -> Dict[str, float]:
        """Get bounding box of the model"""
        pass

    @abstractmethod
    async def create_drawing(self, template_path: str) -> bool:
        """Create a drawing from the model"""
        pass

    @abstractmethod
    async def list_open_documents(self) -> List[Dict[str, Any]]:
        """List all open documents"""
        pass

    @abstractmethod
    async def get_document_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a specific document"""
        pass

    @abstractmethod
    async def take_screenshot(
        self, 
        output_path: str, 
        width: int = 1920, 
        height: int = 1080
    ) -> bool:
        """Take a screenshot of the current view"""
        pass

    @abstractmethod
    async def execute_feature_action(
        self, 
        feature_name: str, 
        action: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute an action on a feature (suppress, unsuppress, edit, etc.)"""
        pass

    # Helper methods that can be shared across adapters
    def _validate_file_path(self, file_path: str) -> Path:
        """Validate and normalize file path"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return path

    def _get_file_type(self, file_path: str) -> str:
        """Determine SolidWorks file type from extension"""
        ext = Path(file_path).suffix.lower()
        file_types = {
            '.sldprt': 'Part',
            '.sldasm': 'Assembly',
            '.slddrw': 'Drawing'
        }
        return file_types.get(ext, 'Unknown')

    def _format_export_options(self, format: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Format export options based on file format"""
        default_options = {
            'STEP': {
                'version': 'AP214',
                'export_as_solid': True
            },
            'IGES': {
                'export_curves': True,
                'export_surfaces': True
            },
            'STL': {
                'binary': True,
                'quality': 'fine'
            },
            'PDF': {
                'high_quality': True,
                'embed_fonts': True
            }
        }
        
        format_defaults = default_options.get(format, {})
        if options:
            format_defaults.update(options)
        return format_defaults