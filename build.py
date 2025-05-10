#!/usr/bin/env python
"""
Build script for creating honeygrabber distribution packages.
"""

import os
import sys
import shutil
import subprocess
import platform
from typing import List, Tuple

def run_command(command: List[str]) -> Tuple[int, str, str]:
    """Execute a command and return its exit code and output."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def clean_build_directories():
    """Remove build directories."""
    dirs_to_clean = ["build", "dist", "honeygrabber.egg-info"]
    for directory in dirs_to_clean:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            print(f"Removed {directory}")

def install_build_dependencies():
    """Install dependencies for building the package."""
    print("Installing build dependencies...")
    returncode, stdout, stderr = run_command([
        sys.executable, "-m", "pip", "install", 
        "--upgrade", "pip", "setuptools", "wheel", "build", "twine"
    ])
    
    if returncode != 0:
        print("Error installing build dependencies:")
        print(stderr)
        sys.exit(1)
    
    print("Build dependencies installed successfully.")

def build_package():
    """Build the package using the build module."""
    print("Building the package...")
    returncode, stdout, stderr = run_command([
        sys.executable, "-m", "build"
    ])
    
    if returncode != 0:
        print("Error building the package:")
        print(stderr)
        sys.exit(1)
    
    print("Package built successfully.")

def validate_package():
    """Validate the package with twine."""
    print("Validating the package...")
    returncode, stdout, stderr = run_command([
        sys.executable, "-m", "twine", "check", "dist/*"
    ])
    
    if returncode != 0:
        print("Error validating the package:")
        print(stderr)
        sys.exit(1)
    
    print("Package validation successful.")

def main():
    """Execute the build process."""
    print(f"Building honeygrabber package with Python {sys.version}")
    print(f"Platform: {platform.platform()}")
    
    # Clean old build files
    clean_build_directories()
    
    # Install build dependencies
    install_build_dependencies()
    
    # Build the package
    build_package()
    
    # Validate the package
    validate_package()
    
    print("\nBuild completed successfully!")
    print("\nTo install the package locally for testing:")
    print(f"  {sys.executable} -m pip install -e .")
    print("\nTo upload to PyPI:")
    print(f"  {sys.executable} -m twine upload dist/*")

if __name__ == "__main__":
    main() 
