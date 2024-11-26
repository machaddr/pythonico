@echo off

REM Remove previous build files
if exist dist (
    rmdir /s /q dist
)
if exist build (
    rmdir /s /q build
)

REM Run PyInstaller with icon
pyinstaller --clean --onefile --windowed --add-data "icons/main.png;icons" --icon="icons/main.ico" pythonico.py

REM Clean up unnecessary build files
if exist __pycache__ (
    rmdir /s /q __pycache__
)
del *.spec
