# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files

# Collect data files for various packages
datas = []
datas += collect_data_files('PyQt6')

# Add icon data file
datas += [('icons/main.png', 'icons')]

a = Analysis(
    ['pythonico.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'anthropic',
        'aiohttp',
        'speech_recognition',
        'pyaudio',
        'markdown',
        'adblockparser',
        'pyqtconsole',
        'json',
        'asyncio',
        're',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'numpy',
        'pandas'
    ],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pythonico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/main.ico'
)

# For Linux/macOS app bundle (optional)
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Pythonico.app',
        icon='icons/main.ico',
        bundle_identifier='com.pythonico.editor',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'NSRequiresAquaSystemAppearance': 'False'
        }
    )
elif sys.platform == 'linux':
    app = BUNDLE(
        exe,
        name='Pythonico',
        icon='icons/main.png',
        bundle_identifier='com.pythonico.editor',
        info_plist={
            'Desktop Entry': {
                'Name': 'Pythonico',
                'Comment': 'Pythonico Editor',
                'Exec': 'pythonico',
                'Icon': 'pythonico',
                'Type': 'Application',
                'Categories': 'Development;IDE;'
            }
        }
    )        