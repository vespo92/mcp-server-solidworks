"""
Adapter Factory for SolidWorks version management

Dynamically loads the appropriate adapter based on the installed SolidWorks version.
"""

import os
import logging
from typing import Dict, Optional
from pathlib import Path

from .common.base_adapter import SolidWorksAdapter

logger = logging.getLogger(__name__)


class AdapterFactory:
    """Factory for creating version-specific SolidWorks adapters"""

    def __init__(self):
        self._adapters: Dict[str, type] = {}
        self._load_adapters()

    def _load_adapters(self):
        """Dynamically load all available adapters"""
        adapters_path = Path(__file__).parent
        
        # List of supported versions
        versions = ["sw2021", "sw2022", "sw2023", "sw2024", "sw2025"]
        
        for version in versions:
            version_path = adapters_path / version
            if version_path.exists():
                try:
                    # Import the adapter module
                    module_name = f"src.solidworks_adapters.{version}.adapter"
                    adapter_module = __import__(module_name, fromlist=["adapter"])
                    
                    # Get the adapter class (convention: SolidWorks{YEAR}Adapter)
                    year = version[2:]  # Extract year from 'sw2024'
                    class_name = f"SolidWorks{year}Adapter"
                    
                    if hasattr(adapter_module, class_name):
                        adapter_class = getattr(adapter_module, class_name)
                        self._adapters[year] = adapter_class
                        logger.info(f"Loaded adapter for SolidWorks {year}")
                    else:
                        logger.warning(f"Adapter class {class_name} not found in {module_name}")
                        
                except ImportError as e:
                    logger.warning(f"Could not load adapter for {version}: {e}")
                except Exception as e:
                    logger.error(f"Error loading adapter for {version}: {e}")

    def get_adapter(self, version: str) -> Optional[SolidWorksAdapter]:
        """
        Get an adapter instance for the specified version
        
        Args:
            version: SolidWorks version (e.g., "2024")
            
        Returns:
            Adapter instance or None if version not supported
        """
        if version in self._adapters:
            adapter_class = self._adapters[version]
            return adapter_class()
        else:
            # Try to find the closest version
            available_versions = sorted(self._adapters.keys())
            
            if not available_versions:
                raise RuntimeError("No SolidWorks adapters available")
            
            # Find the closest lower version
            closest_version = None
            for v in reversed(available_versions):
                if v <= version:
                    closest_version = v
                    break
            
            if closest_version:
                logger.warning(
                    f"SolidWorks {version} adapter not found. "
                    f"Using adapter for version {closest_version}"
                )
                adapter_class = self._adapters[closest_version]
                return adapter_class()
            else:
                # Use the oldest available version
                oldest_version = available_versions[0]
                logger.warning(
                    f"No compatible adapter found for SolidWorks {version}. "
                    f"Using adapter for version {oldest_version}"
                )
                adapter_class = self._adapters[oldest_version]
                return adapter_class()

    def list_supported_versions(self) -> List[str]:
        """Get list of supported SolidWorks versions"""
        return sorted(self._adapters.keys())

    def detect_installed_version(self) -> Optional[str]:
        """Attempt to detect the installed SolidWorks version"""
        # Check environment variable first
        env_version = os.getenv("SOLIDWORKS_VERSION")
        if env_version:
            return env_version
        
        # Check registry on Windows
        if os.name == 'nt':
            try:
                import winreg
                
                # Common registry paths for SolidWorks
                registry_paths = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\SolidWorks\SOLIDWORKS 2024"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\SolidWorks\SOLIDWORKS 2023"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\SolidWorks\SOLIDWORKS 2022"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\SolidWorks\SOLIDWORKS 2021"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\SolidWorks\SOLIDWORKS 2025"),
                ]
                
                for hkey, path in registry_paths:
                    try:
                        with winreg.OpenKey(hkey, path) as key:
                            # Extract version from path
                            version = path.split()[-1]
                            logger.info(f"Detected SolidWorks {version} from registry")
                            return version
                    except WindowsError:
                        continue
                        
            except ImportError:
                logger.warning("winreg module not available")
        
        # Check file system for installation
        common_paths = [
            r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS 2024",
            r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS 2023",
            r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS 2022",
            r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS 2021",
            r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS 2025",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                version = path.split()[-1]
                logger.info(f"Detected SolidWorks {version} from file system")
                return version
        
        logger.warning("Could not detect SolidWorks version")
        return None

    def get_best_adapter(self) -> SolidWorksAdapter:
        """Get the best available adapter based on detected version"""
        detected_version = self.detect_installed_version()
        
        if detected_version:
            return self.get_adapter(detected_version)
        else:
            # Return the newest available adapter
            if self._adapters:
                newest_version = sorted(self._adapters.keys())[-1]
                logger.info(f"Using newest available adapter: {newest_version}")
                return self.get_adapter(newest_version)
            else:
                raise RuntimeError("No SolidWorks adapters available")