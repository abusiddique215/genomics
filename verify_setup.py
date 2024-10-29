#!/usr/bin/env python3
import sys
import subprocess
import pkg_resources
from typing import List, Tuple
import importlib

def check_python_version():
    """Check Python version"""
    print("\nChecking Python version...")
    required = (3, 10)
    current = sys.version_info[:2]
    
    if current >= required:
        print(f"✅ Python version {'.'.join(map(str, current))} meets minimum requirement")
        return True
    else:
        print(f"❌ Python version {'.'.join(map(str, current))} does not meet minimum requirement of {'.'.join(map(str, required))}")
        return False

def check_dependencies() -> List[Tuple[str, bool]]:
    """Check all dependencies are installed"""
    print("\nChecking dependencies...")
    results = []
    
    with open('requirements.txt') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    for req in requirements:
        try:
            # Remove version specifier
            package = req.split('==')[0]
            importlib.import_module(package.replace('-', '_'))
            results.append((req, True))
        except ImportError:
            results.append((req, False))
    
    return results

def check_java():
    """Check Java installation"""
    print("\nChecking Java installation...")
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Java is installed")
            return True
        else:
            print("❌ Java is not installed")
            return False
    except FileNotFoundError:
        print("❌ Java is not installed")
        return False

def main():
    """Run all verification checks"""
    print("=== Verifying System Setup ===")
    
    # Check Python version
    python_ok = check_python_version()
    
    # Check Java
    java_ok = check_java()
    
    # Check dependencies
    results = check_dependencies()
    deps_ok = all(r[1] for r in results)
    
    # Print dependency results
    print("\nDependency Status:")
    for package, installed in results:
        status = "✅" if installed else "❌"
        print(f"{status} {package}")
    
    # Print summary
    print("\n=== Setup Verification Summary ===")
    all_ok = python_ok and java_ok and deps_ok
    
    if all_ok:
        print("\n✅ All requirements are satisfied!")
        print("You can now run the system using: python run_system.py")
    else:
        print("\n❌ Some requirements are not met:")
        if not python_ok:
            print("- Python version requirement not met")
        if not java_ok:
            print("- Java is not installed")
        if not deps_ok:
            print("- Some Python packages are missing")
        print("\nPlease install missing requirements and try again.")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
