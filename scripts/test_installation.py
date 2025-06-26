#!/usr/bin/env python3
"""
Test script to verify SolidWorks MCP server installation

This script checks that all components are properly installed and configured.
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_python_version():
    """Check Python version"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires 3.9+")
        return False


def check_dependencies():
    """Check Python dependencies"""
    print("\n🔍 Checking Python dependencies...")
    
    required_packages = [
        "mcp",
        "pythonnet",
        "pydantic",
        "chromadb",
        "aiofiles",
        "jinja2",
        "watchdog"
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == "pythonnet":
                import clr
                print(f"✅ {package} - OK")
            else:
                importlib.import_module(package)
                print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing.append(package)
    
    return len(missing) == 0, missing


def check_project_structure():
    """Check project structure"""
    print("\n🔍 Checking project structure...")
    
    required_dirs = [
        "src/mcp_host",
        "src/solidworks_adapters",
        "src/context_builder",
        "src/events",
        "src/tools",
        "src/version_manager",
        "src/prompts",
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✅ {dir_path} - OK")
        else:
            print(f"❌ {dir_path} - Missing")
            missing.append(dir_path)
    
    return len(missing) == 0, missing


def check_csharp_adapters():
    """Check C# adapter DLLs"""
    print("\n🔍 Checking C# adapters...")
    
    adapter_dir = project_root / "src" / "solidworks_adapters"
    versions = ["2021", "2022", "2023", "2024", "2025"]
    
    found = []
    missing = []
    
    for version in versions:
        dll_path = adapter_dir / f"sw{version}" / f"SolidWorksAdapter{version}.dll"
        if dll_path.exists():
            print(f"✅ SolidWorks {version} adapter - OK")
            found.append(version)
        else:
            print(f"⚠️  SolidWorks {version} adapter - Not built")
            missing.append(version)
    
    return len(found) > 0, missing


def check_solidworks_installation():
    """Check SolidWorks installation"""
    print("\n🔍 Checking SolidWorks installation...")
    
    sw_path = os.getenv("SOLIDWORKS_PATH", r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS")
    
    if Path(sw_path).exists():
        print(f"✅ SolidWorks found at: {sw_path}")
        
        # Check for specific versions
        base_path = Path(sw_path).parent
        versions = []
        for version in ["2021", "2022", "2023", "2024", "2025"]:
            version_path = base_path / f"SOLIDWORKS {version}"
            if version_path.exists():
                versions.append(version)
        
        if versions:
            print(f"✅ Detected versions: {', '.join(versions)}")
        
        return True
    else:
        print(f"❌ SolidWorks not found at: {sw_path}")
        print("   Set SOLIDWORKS_PATH environment variable if installed elsewhere")
        return False


def check_chromadb():
    """Check ChromaDB setup"""
    print("\n🔍 Checking ChromaDB...")
    
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_test")
        collection = client.create_collection("test")
        print("✅ ChromaDB - OK")
        
        # Clean up
        client.delete_collection("test")
        import shutil
        shutil.rmtree("./chroma_test", ignore_errors=True)
        
        return True
    except Exception as e:
        print(f"❌ ChromaDB - Error: {e}")
        return False


def check_docker_setup():
    """Check Docker setup"""
    print("\n🔍 Checking Docker setup...")
    
    # Check Docker installation
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker - {result.stdout.strip()}")
        else:
            print("❌ Docker - Not installed or not in PATH")
            return False
    except FileNotFoundError:
        print("❌ Docker - Not installed")
        return False
    
    # Check docker-compose.yml
    compose_file = project_root / "docker-compose.yml"
    if compose_file.exists():
        print("✅ docker-compose.yml - Found")
        return True
    else:
        print("❌ docker-compose.yml - Missing")
        return False


def test_basic_imports():
    """Test basic imports"""
    print("\n🔍 Testing basic imports...")
    
    try:
        from src.mcp_host.server import SolidWorksMCPServer
        print("✅ MCP Server import - OK")
        
        from src.tools.solidworks_tools import SolidWorksTools
        print("✅ Tools import - OK")
        
        from src.context_builder.knowledge_base import SolidWorksKnowledgeBase
        print("✅ Knowledge base import - OK")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*50)
    print("INSTALLATION TEST SUMMARY")
    print("="*50)
    
    all_passed = all(results.values())
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test}: {status}")
    
    print("="*50)
    
    if all_passed:
        print("✅ All tests passed! Installation is complete.")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        
        # Provide helpful suggestions
        print("\n📝 Suggestions:")
        
        if not results.get("dependencies"):
            print("- Run: pip install -e .")
        
        if not results.get("csharp_adapters"):
            print("- Run: python scripts/build_adapters.py")
        
        if not results.get("solidworks"):
            print("- Ensure SolidWorks is installed")
            print("- Set SOLIDWORKS_PATH environment variable")
    
    return all_passed


def main():
    """Main test routine"""
    print("SolidWorks MCP Server Installation Test")
    print("="*50)
    
    results = {
        "python_version": check_python_version(),
        "dependencies": check_dependencies()[0],
        "project_structure": check_project_structure()[0],
        "csharp_adapters": check_csharp_adapters()[0],
        "solidworks": check_solidworks_installation(),
        "chromadb": check_chromadb(),
        "docker": check_docker_setup(),
        "imports": test_basic_imports(),
    }
    
    success = print_summary(results)
    
    # Write results to file
    results_file = project_root / "installation_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "success": success,
            "results": results,
            "timestamp": str(Path.ctime(Path(__file__)))
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()