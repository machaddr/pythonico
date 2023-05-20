@echo off

REM Remove previous build files
if exist dist (
    rmdir /s /q dist
)
if exist build (
    rmdir /s /q build
)

REM Run PyInstaller
pyinstaller --onefile pythonico.py

REM Clean up unnecessary build files
if exist __pycache__ (
    rmdir /s /q __pycache__
)
del *.spec
