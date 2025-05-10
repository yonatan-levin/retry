#!/usr/bin/env python
"""Setup script for the honeygrabber package."""

# This file is intentionally minimal as all configuration is in pyproject.toml
# Since this package hasn't been published yet, we don't need backward compatibility

from setuptools import setup

if __name__ == "__main__":
    try:
        setup()
    except Exception:  # Using explicit Exception instead of bare except
        print(
            "\n\nAn error occurred during setup. Please ensure that you have the latest version of pip, setuptools, and wheel installed.\n"
            "Try the following commands:\n"
            "  python -m pip install --upgrade pip setuptools wheel\n"
            "  python -m pip install -e .\n"
        )
        raise
