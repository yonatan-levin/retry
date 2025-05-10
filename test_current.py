#!/usr/bin/env python
"""
Simple test script to verify the current package installation.
"""

import sys
import honeygrabber  # This should work with the current installation

def main():
    """Display package information."""
    print(f"Package version: {honeygrabber.__version__}")
    print(f"Python version: {sys.version}")
    print("\nAvailable components:")
    
    # Check if core components are available
    components = [
        "HoneyGrabberSC",
        "Rule",
        "Rules",
        "ContentParser",
        "ContentExtractor"
    ]
    
    for component in components:
        if hasattr(honeygrabber, component):
            print(f"  ✓ {component}")
        else:
            print(f"  ✗ {component}")
    
    # Check if NLP components are available
    print("\nNLP components available:", "Yes" if hasattr(honeygrabber, "NLP_AVAILABLE") and honeygrabber.NLP_AVAILABLE else "No")

if __name__ == "__main__":
    main() 
