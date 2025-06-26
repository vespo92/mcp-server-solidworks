#!/usr/bin/env python3
"""
Build script for SolidWorks C# adapters

This script compiles the C# adapters for each SolidWorks version.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_csc_compiler():
    """Find the C# compiler"""
    # Try common locations
    possible_paths = [
        r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe",
        r"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn\csc.exe",
        r"C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\Roslyn\csc.exe",
        r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\Roslyn\csc.exe",
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            return path
    
    # Try to find in PATH
    result = shutil.which("csc")
    if result:
        return result
    
    # Try dotnet CLI
    if shutil.which("dotnet"):
        return "dotnet"
    
    return None


def copy_solidworks_dlls():
    """Copy SolidWorks DLLs from installation to references folder"""
    sw_base = os.getenv("SOLIDWORKS_PATH", r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS")
    
    if not Path(sw_base).exists():
        logger.warning(f"SolidWorks installation not found at: {sw_base}")
        return False
    
    # Create references directory
    ref_dir = Path(__file__).parent.parent / "src" / "solidworks_adapters" / "references"
    ref_dir.mkdir(exist_ok=True)
    
    # DLLs to copy
    dlls = [
        "SolidWorks.Interop.sldworks.dll",
        "SolidWorks.Interop.swconst.dll",
        "SolidWorks.Interop.swpublished.dll",
    ]
    
    # Look for DLLs in common locations
    search_paths = [
        Path(sw_base) / "api" / "redist",
        Path(sw_base),
    ]
    
    copied = 0
    for dll in dlls:
        found = False
        for search_path in search_paths:
            dll_path = search_path / dll
            if dll_path.exists():
                dest = ref_dir / dll
                shutil.copy2(dll_path, dest)
                logger.info(f"Copied {dll} to references folder")
                copied += 1
                found = True
                break
        
        if not found:
            logger.warning(f"Could not find {dll}")
    
    return copied == len(dlls)


def build_with_csc(csc_path: str, version: str):
    """Build adapter using csc compiler"""
    base_dir = Path(__file__).parent.parent
    adapter_dir = base_dir / "src" / "solidworks_adapters"
    version_dir = adapter_dir / f"sw{version}"
    
    # Ensure version directory exists
    version_dir.mkdir(exist_ok=True)
    
    cs_file = version_dir / f"SolidWorksAdapter{version}.cs"
    output_dll = version_dir / f"SolidWorksAdapter{version}.dll"
    
    if not cs_file.exists():
        logger.warning(f"C# source file not found: {cs_file}")
        return False
    
    # Build command
    cmd = [
        csc_path,
        "/target:library",
        f"/out:{output_dll}",
        "/platform:x64",
        "/optimize+",
        f"/reference:{adapter_dir}/references/SolidWorks.Interop.sldworks.dll",
        f"/reference:{adapter_dir}/references/SolidWorks.Interop.swconst.dll",
        f"/reference:{adapter_dir}/references/SolidWorks.Interop.swpublished.dll",
        str(cs_file)
    ]
    
    logger.info(f"Building adapter for SolidWorks {version}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info(f"Successfully built {output_dll}")
        return True
    else:
        logger.error(f"Build failed for version {version}")
        logger.error(result.stderr)
        return False


def build_with_dotnet():
    """Build all adapters using dotnet CLI"""
    base_dir = Path(__file__).parent.parent
    project_file = base_dir / "src" / "solidworks_adapters" / "SolidWorksAdapters.csproj"
    
    if not project_file.exists():
        logger.error(f"Project file not found: {project_file}")
        return False
    
    cmd = ["dotnet", "build", str(project_file), "-c", "Release"]
    
    logger.info("Building adapters with dotnet...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info("Successfully built all adapters")
        return True
    else:
        logger.error("Build failed")
        logger.error(result.stderr)
        return False


def create_version_specific_adapters():
    """Create version-specific adapter classes from template"""
    base_dir = Path(__file__).parent.parent
    adapter_dir = base_dir / "src" / "solidworks_adapters"
    
    # Read the 2024 adapter as template
    template_file = adapter_dir / "sw2024" / "SolidWorksAdapter2024.cs"
    if not template_file.exists():
        logger.error("Template adapter file not found")
        return
    
    template_content = template_file.read_text()
    
    versions = ["2021", "2022", "2023", "2025"]
    
    for version in versions:
        version_dir = adapter_dir / f"sw{version}"
        version_dir.mkdir(exist_ok=True)
        
        # Replace version numbers in template
        content = template_content.replace("2024", version)
        content = content.replace("32", str(int(version) - 1993))  # API version calculation
        
        output_file = version_dir / f"SolidWorksAdapter{version}.cs"
        output_file.write_text(content)
        logger.info(f"Created adapter source for version {version}")


def main():
    """Main build process"""
    logger.info("Starting SolidWorks adapter build process...")
    
    # Step 1: Copy SolidWorks DLLs
    logger.info("Step 1: Copying SolidWorks reference DLLs...")
    if not copy_solidworks_dlls():
        logger.warning("Could not copy all SolidWorks DLLs. Build may fail.")
    
    # Step 2: Create version-specific adapters
    logger.info("Step 2: Creating version-specific adapters...")
    create_version_specific_adapters()
    
    # Step 3: Find compiler
    logger.info("Step 3: Finding C# compiler...")
    compiler = find_csc_compiler()
    
    if not compiler:
        logger.error("No C# compiler found. Please install .NET SDK or Visual Studio.")
        sys.exit(1)
    
    logger.info(f"Using compiler: {compiler}")
    
    # Step 4: Build adapters
    logger.info("Step 4: Building adapters...")
    
    if compiler == "dotnet":
        success = build_with_dotnet()
    else:
        # Build each version
        versions = ["2021", "2022", "2023", "2024", "2025"]
        success = True
        
        for version in versions:
            if not build_with_csc(compiler, version):
                success = False
    
    if success:
        logger.info("Build completed successfully!")
    else:
        logger.error("Build failed for one or more adapters")
        sys.exit(1)


if __name__ == "__main__":
    main()