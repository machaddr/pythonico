#!/bin/bash

# Remove previous build files
rm -rf dist
rm -rf build

# Run PyInstaller
pyinstaller --onefile pythonico.py

# Clean up unnecessary build files
rm -rf __pycache__
rm -rf *.spec
