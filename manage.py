#!/usr/bin/env python3

import click
import subprocess
import sys
import os
from typing import List, Optional
from pathlib import Path

@click.group()
def cli():
    """Management script for the Genomics Treatment System"""
    pass

@cli.command()
@click.option('--dev', is_flag=True, help='Start in development mode')
def start(dev: bool):
    """Start the system"""
    cmd = ['./start_genomics_project.sh', 'dev' if dev else 'start']
    subprocess.run(cmd, check=True)

@cli.command()
def stop():
    """Stop the system"""
    subprocess.run(['./start_genomics_project.sh', 'stop'], check=True)

@cli.command()
def status():
    """Show system status"""
    subprocess.run(['./start_genomics_project.sh', 'status'], check=True)

@cli.command()
@click.option('--unit', is_flag=True, help='Run unit tests only')
@click.option('--integration', is_flag=True, help='Run integration tests only')
@click.option('--coverage', is_flag=True, help='Generate coverage report')
def test(unit: bool, integration: bool, coverage: bool):
    """Run tests"""
    cmd = ['pytest']
    
    if unit:
        cmd.append('-m unit')
    elif integration:
        cmd.append('-m integration')
    
    if coverage:
        cmd.extend(['--cov=services', '--cov-report=html'])
    
    subprocess.run(cmd, check=True)

@cli.command()
@click.option('--count', default=10, help='Number of patients to generate')
@click.option('--output', help='Output file path')
def generate_data(count: int, output: Optional[str]):
    """Generate test data"""
    cmd = ['python', 'generate_mock_patients.py', '--count', str(count)]
    if output:
        cmd.extend(['--output', output])
    subprocess.run(cmd, check=True)

@cli.command()
def clean():
    """Clean up generated files"""
    patterns = [
        '**/__pycache__',
        '**/*.pyc',
        '**/*.pyo',
        '**/*.pyd',
        '.coverage',
        'htmlcov',
        'dist',
        'build',
        '*.egg-info'
    ]
    
    for pattern in patterns:
        for path in Path('.').glob(pattern):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
    
    click.echo("Cleanup completed")

@cli.command()
@click.option('--check', is_flag=True, help='Check code style without modifying')
def format(check: bool):
    """Format code using black and isort"""
    if check:
        subprocess.run(['black', '--check', '.'], check=True)
        subprocess.run(['isort', '--check-only', '.'], check=True)
    else:
        subprocess.run(['black', '.'], check=True)
        subprocess.run(['isort', '.'], check=True)

@cli.command()
def lint():
    """Run linting checks"""
    subprocess.run(['flake8', 'services', 'tests'], check=True)
    subprocess.run(['mypy', 'services', 'tests'], check=True)
    subprocess.run(['pylint', 'services', 'tests'], check=True)

@cli.command()
def docs():
    """Generate documentation"""
    subprocess.run(['mkdocs', 'build'], check=True)

@cli.command()
@click.argument('service')
def logs(service: str):
    """View logs for a specific service"""
    log_file = f'logs/{service}.log'
    if os.path.exists(log_file):
        subprocess.run(['tail', '-f', log_file], check=True)
    else:
        click.echo(f"No logs found for service: {service}")

if __name__ == '__main__':
    cli()
