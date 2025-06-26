"""
Version Manager for SolidWorks

Detects and manages different SolidWorks versions installed on the system.
"""

import os
import logging
import platform
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class VersionManager:
    """Manages SolidWorks version detection and compatibility"""

    def __init__(self):
        self.supported_versions = ["2021", "2022", "2023", "2024", "2025"]
        self.version_info: Dict[str, Dict[str, Any]] = {}
        self._detected_version: Optional[str] = None
        self._scan_for_versions()

    def _scan_for_versions(self):
        """Scan system for installed SolidWorks versions"""
        if platform.system() == "Windows":
            self._scan_windows()
        else:
            logger.warning("SolidWorks version detection only supported on Windows")

    def _scan_windows(self):
        """Scan Windows system for SolidWorks installations"""
        # Common installation paths
        base_paths = [
            r"C:\Program Files\SOLIDWORKS Corp",
            r"C:\Program Files (x86)\SOLIDWORKS Corp",
            r"D:\Program Files\SOLIDWORKS Corp",
        ]
        
        for base_path in base_paths:
            if not Path(base_path).exists():
                continue
                
            for version in self.supported_versions:
                sw_path = Path(base_path) / f"SOLIDWORKS {version}"
                if sw_path.exists():
                    self._register_version(version, sw_path)
        
        # Also check registry
        self._scan_registry()

    def _scan_registry(self):
        """Scan Windows registry for SolidWorks installations"""
        try:
            import winreg
            
            registry_base = r"SOFTWARE\SolidWorks"
            
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_base) as base_key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(base_key, i)
                            if subkey_name.startswith("SOLIDWORKS"):
                                # Extract version
                                parts = subkey_name.split()
                                if len(parts) > 1 and parts[1] in self.supported_versions:
                                    version = parts[1]
                                    
                                    # Get installation path
                                    with winreg.OpenKey(base_key, subkey_name) as version_key:
                                        try:
                                            install_path = winreg.QueryValueEx(
                                                version_key, 
                                                "SolidWorks Folder"
                                            )[0]
                                            self._register_version(version, Path(install_path))
                                        except WindowsError:
                                            pass
                            i += 1
                        except WindowsError:
                            break
            except WindowsError:
                logger.debug("SolidWorks registry key not found")
                
        except ImportError:
            logger.warning("winreg module not available")

    def _register_version(self, version: str, install_path: Path):
        """Register a detected SolidWorks version"""
        exe_path = install_path / "SLDWORKS.exe"
        
        if exe_path.exists():
            self.version_info[version] = {
                "path": str(install_path),
                "exe": str(exe_path),
                "api_dlls": self._find_api_dlls(install_path),
                "detected": True
            }
            logger.info(f"Detected SolidWorks {version} at {install_path}")

    def _find_api_dlls(self, install_path: Path) -> Dict[str, str]:
        """Find API DLL files for a SolidWorks installation"""
        api_path = install_path / "api" / "redist"
        dlls = {}
        
        required_dlls = [
            "SolidWorks.Interop.sldworks.dll",
            "SolidWorks.Interop.swconst.dll",
            "SolidWorks.Interop.swpublished.dll",
        ]
        
        for dll_name in required_dlls:
            dll_path = api_path / dll_name
            if dll_path.exists():
                dlls[dll_name] = str(dll_path)
            else:
                # Try alternate locations
                alt_path = install_path / dll_name
                if alt_path.exists():
                    dlls[dll_name] = str(alt_path)
        
        return dlls

    def detect_version(self) -> Optional[str]:
        """
        Detect the active SolidWorks version
        
        Returns:
            Version string or None if not detected
        """
        # Check environment variable first
        env_version = os.getenv("SOLIDWORKS_VERSION")
        if env_version and env_version in self.supported_versions:
            self._detected_version = env_version
            return env_version
        
        # Check for running instance
        running_version = self._detect_running_instance()
        if running_version:
            self._detected_version = running_version
            return running_version
        
        # Return newest installed version
        if self.version_info:
            newest = max(self.version_info.keys())
            self._detected_version = newest
            return newest
        
        return None

    def _detect_running_instance(self) -> Optional[str]:
        """Detect version of running SolidWorks instance"""
        if platform.system() != "Windows":
            return None
            
        try:
            import psutil
            
            for proc in psutil.process_iter(['name', 'exe']):
                if proc.info['name'] == 'SLDWORKS.exe':
                    exe_path = proc.info['exe']
                    if exe_path:
                        # Extract version from path
                        for version in self.supported_versions:
                            if f"SOLIDWORKS {version}" in exe_path:
                                return version
        except ImportError:
            logger.debug("psutil not available for process detection")
        except Exception as e:
            logger.debug(f"Error detecting running instance: {e}")
        
        return None

    def get_version_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific version"""
        return self.version_info.get(version)

    def get_installed_versions(self) -> List[str]:
        """Get list of installed versions"""
        return sorted(self.version_info.keys())

    def is_version_installed(self, version: str) -> bool:
        """Check if a specific version is installed"""
        return version in self.version_info

    def get_api_dlls(self, version: str) -> Dict[str, str]:
        """Get API DLL paths for a version"""
        info = self.get_version_info(version)
        if info:
            return info.get("api_dlls", {})
        return {}

    def get_exe_path(self, version: str) -> Optional[str]:
        """Get SolidWorks executable path for a version"""
        info = self.get_version_info(version)
        if info:
            return info.get("exe")
        return None

    def validate_version(self, version: str) -> Tuple[bool, str]:
        """
        Validate a SolidWorks version installation
        
        Returns:
            Tuple of (is_valid, message)
        """
        if version not in self.supported_versions:
            return False, f"Version {version} is not supported"
        
        if not self.is_version_installed(version):
            return False, f"Version {version} is not installed"
        
        info = self.get_version_info(version)
        
        # Check executable
        exe_path = info.get("exe")
        if not exe_path or not Path(exe_path).exists():
            return False, f"SolidWorks executable not found for version {version}"
        
        # Check API DLLs
        api_dlls = info.get("api_dlls", {})
        missing_dlls = []
        
        for dll_name, dll_path in api_dlls.items():
            if not Path(dll_path).exists():
                missing_dlls.append(dll_name)
        
        if missing_dlls:
            return False, f"Missing API DLLs for version {version}: {', '.join(missing_dlls)}"
        
        return True, f"Version {version} is properly installed"

    def export_version_info(self, output_path: str):
        """Export version information to a file"""
        export_data = {
            "detected_version": self._detected_version,
            "installed_versions": self.get_installed_versions(),
            "version_details": self.version_info,
            "system": platform.system(),
            "platform": platform.platform()
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported version info to {output_path}")

    def get_compatibility_info(self, version: str) -> Dict[str, Any]:
        """Get compatibility information for a version"""
        compatibility = {
            "2021": {
                "python_net": "3.0.0+",
                "dotnet_framework": "4.8",
                "windows_versions": ["Windows 10", "Windows 11"],
                "api_version": "28.0"
            },
            "2022": {
                "python_net": "3.0.0+",
                "dotnet_framework": "4.8",
                "windows_versions": ["Windows 10", "Windows 11"],
                "api_version": "29.0"
            },
            "2023": {
                "python_net": "3.0.0+",
                "dotnet_framework": "4.8",
                "windows_versions": ["Windows 10", "Windows 11"],
                "api_version": "30.0"
            },
            "2024": {
                "python_net": "3.0.0+",
                "dotnet_framework": "4.8",
                "windows_versions": ["Windows 10", "Windows 11"],
                "api_version": "31.0"
            },
            "2025": {
                "python_net": "3.0.0+",
                "dotnet_framework": "4.8",
                "windows_versions": ["Windows 10", "Windows 11"],
                "api_version": "32.0"
            }
        }
        
        return compatibility.get(version, {})