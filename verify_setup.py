#!/usr/bin/env python3

import sys
import pkg_resources
import subprocess
import os
import requests
import json
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version"""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        logger.error(
            f"Python {required_version[0]}.{required_version[1]} or higher is required"
        )
        return False
    return True

def check_dependencies():
    """Check installed dependencies"""
    try:
        requirements = pkg_resources.parse_requirements(
            open('requirements.txt').readlines()
        )
        pkg_resources.working_set.resolve(requirements)
        return True
    except Exception as e:
        logger.error(f"Dependency check failed: {str(e)}")
        return False

def check_aws_credentials():
    """Check AWS credentials"""
    try:
        import boto3
        sts = boto3.client('sts')
        sts.get_caller_identity()
        return True
    except Exception as e:
        logger.error(f"AWS credentials check failed: {str(e)}")
        return False

def check_directories():
    """Check required directories"""
    required_dirs = ['logs', 'data', 'models', 'tests/data']
    missing_dirs = []
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        logger.error(f"Missing directories: {', '.join(missing_dirs)}")
        return False
    return True

def check_environment_variables():
    """Check environment variables"""
    required_vars = [
        'ENV',
        'AWS_REGION',
        'DYNAMODB_ENDPOINT',
        'JWT_SECRET'
    ]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    return True

def check_services():
    """Check if services are running"""
    services = [
        ('http://localhost:8080/health', 'Patient Management'),
        ('http://localhost:8083/health', 'Treatment Prediction'),
        ('http://localhost:8084/health', 'Data Ingestion')
    ]
    
    failed_services = []
    for url, name in services:
        try:
            response = requests.get(url)
            if response.status_code != 200:
                failed_services.append(name)
        except:
            failed_services.append(name)
    
    if failed_services:
        logger.error(f"Failed services: {', '.join(failed_services)}")
        return False
    return True

def check_database():
    """Check database connection"""
    try:
        import boto3
        dynamodb = boto3.client('dynamodb', endpoint_url=os.getenv('DYNAMODB_ENDPOINT'))
        dynamodb.list_tables()
        return True
    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
        return False

def main():
    """Run all checks"""
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("AWS Credentials", check_aws_credentials),
        ("Directories", check_directories),
        ("Environment Variables", check_environment_variables),
        ("Database", check_database),
        ("Services", check_services)
    ]
    
    failed_checks = []
    
    for name, check_func in checks:
        logger.info(f"Checking {name}...")
        try:
            if not check_func():
                failed_checks.append(name)
        except Exception as e:
            logger.error(f"Check {name} failed with error: {str(e)}")
            failed_checks.append(name)
    
    if failed_checks:
        logger.error(f"Setup verification failed. Failed checks: {', '.join(failed_checks)}")
        sys.exit(1)
    else:
        logger.info("All checks passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
