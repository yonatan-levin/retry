#!/usr/bin/env python
"""
Simple test script to verify the honeygrabber package works correctly.
"""

import sys
import honeygrabber  # This should now work if our package is correctly installed

def main():
    """Display package information."""
    print(f"honeygrabber version: {honeygrabber.__version__}")
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
    print("\nNLP components available:", "Yes" if honeygrabber.NLP_AVAILABLE else "No")
    
    if honeygrabber.NLP_AVAILABLE:
        nlp_components = [
            "EntityExtractor",
            "KeywordExtractor",
            "SentimentAnalyzer",
            "TextSummarizer"
        ]
        
        for component in nlp_components:
            if hasattr(honeygrabber, component):
                print(f"  ✓ {component}")
            else:
                print(f"  ✗ {component}")

if __name__ == "__main__":
    main() 
