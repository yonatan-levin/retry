#!/usr/bin/env python
"""Setup script for the honeygrabber package."""

from setuptools import setup, find_packages

if __name__ == "__main__":
    try:
        setup(
            # Metadata is defined in pyproject.toml
            # This is just a shim for backward compatibility
            packages=find_packages(),
            package_data={
                "retry": ["py.typed"],
            },
            py_modules=["honeygrabber"],  # Include the honeygrabber.py entry point
        )
    except:  # noqa
        print(
            "\n\nAn error occurred during setup. Please ensure that you have the latest version of pip, setuptools, and wheel installed.\n"
            "Try the following commands:\n"
            "  python -m pip install --upgrade pip setuptools wheel\n"
            "  python -m pip install -e .\n"
        )
        raise 
