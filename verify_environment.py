#!/usr/bin/env python3

import sys
import subprocess
import pkg_resources
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version() -> bool:
    """Check Python version meets requirements"""
    required_version = (3, 9)
    current_version = sys.version_info[:2]
    
    if current_version >= required_version:
        logger.info(f"Python version {'.'.join(map(str, current_version))} meets requirements")
        return True
    else:
        logger.error(
            f"Python version {'.'.join(map(str, current_version))} "
            f"does not meet minimum requirement of {'.'.join(map(str, required_version))}"
        )
        return False

def check_poetry_installation() -> bool:
    """Check if Poetry is installed"""
    try:
        subprocess.run(['poetry', '--version'], check=True, capture_output=True)
        logger.info("Poetry is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Poetry is not installed")
        return False

def check_virtual_environment() -> bool:
    """Check if running in a virtual environment"""
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        logger.info("Running in virtual environment")
    else:
        logger.warning("Not running in virtual environment")
    return in_venv

def check_dependencies() -> bool:
    """Check if all required dependencies are installed"""
    try:
        # Core dependencies that must be available
        core_packages = [
            'fastapi',
            'uvicorn',
            'sqlalchemy',
            'numpy',
            'pandas',
            'pytest',
            'tensorflow'
        ]
        
        missing_packages = []
        for package in core_packages:
            try:
                pkg_resources.require(package)
                logger.info(f"Package {package} is installed")
            except pkg_resources.DistributionNotFound:
                missing_packages.append(package)
                logger.error(f"Package {package} is missing")
        
        return len(missing_packages) == 0
    
    except Exception as e:
        logger.error(f"Error checking dependencies: {str(e)}")
        return False

def check_project_structure() -> bool:
    """Check if project structure is correct"""
    required_dirs = [
        'services',
        'tests',
        'config',
        'data',
        'logs',
        'models'
    ]
    
    required_files = [
        'pyproject.toml',
        'README.md',
        '.env.example',
        'docker-compose.yml'
    ]
    
    missing_items = []
    
    # Check directories
    for dir_name in required_dirs:
        if not Path(dir_name).is_dir():
            missing_items.append(f"Directory: {dir_name}")
            logger.error(f"Missing directory: {dir_name}")
        else:
            logger.info(f"Found directory: {dir_name}")
    
    # Check files
    for file_name in required_files:
        if not Path(file_name).is_file():
            missing_items.append(f"File: {file_name}")
            logger.error(f"Missing file: {file_name}")
        else:
            logger.info(f"Found file: {file_name}")
    
    return len(missing_items) == 0

def check_environment_variables() -> bool:
    """Check if required environment variables are set"""
    required_vars = [
        'ENV',
        'AWS_DEFAULT_REGION',
        'DYNAMODB_ENDPOINT'
    ]
    
    import os
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            logger.error(f"Missing environment variable: {var}")
        else:
            logger.info(f"Found environment variable: {var}")
    
    return len(missing_vars) == 0

def check_docker() -> bool:
    """Check if Docker is installed and running"""
    try:
        # Check Docker installation
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        logger.info("Docker is installed")
        
        # Check Docker daemon
        subprocess.run(['docker', 'info'], check=True, capture_output=True)
        logger.info("Docker daemon is running")
        
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Docker is not installed or not running")
        return False

def main():
    """Run all environment checks"""
    checks = [
        ("Python Version", check_python_version),
        ("Poetry Installation", check_poetry_installation),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Environment Variables", check_environment_variables),
        ("Docker", check_docker)
    ]
    
    failed_checks = []
    
    logger.info("Starting environment verification...")
    
    for name, check_func in checks:
        logger.info(f"\nRunning {name} check...")
        try:
            if not check_func():
                failed_checks.append(name)
        except Exception as e:
            logger.error(f"Error during {name} check: {str(e)}")
            failed_checks.append(name)
    
    if failed_checks:
        logger.error("\nEnvironment verification failed!")
        logger.error("Failed checks: " + ", ".join(failed_checks))
        sys.exit(1)
    else:
        logger.info("\nEnvironment verification completed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
