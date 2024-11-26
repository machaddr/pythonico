#!/bin/bash

# Remove previous build files
rm -rf dist
rm -rf build

# Run PyInstaller
pyinstaller --clean --onefile --windowed --add-data "icons/main.png:icons" --icon="icons/main.ico" pythonico.py

# Clean up unnecessary build files
rm -rf __pycache__
rm -rf *.spec
