# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pythonico.py'],
    pathex=[],
    binaries=[],
    datas=[('icon/icon.png', 'icon'), ('icon/icon.ico', 'icon')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    icon='icon/icon.ico' if os.name == 'nt' else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
