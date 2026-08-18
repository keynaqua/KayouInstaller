# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH)
assets_root = project_root / 'assets'
asset_files = [
    (str(path), str(path.parent.relative_to(project_root)))
    for path in assets_root.rglob('*')
    if path.is_file()
]

a = Analysis(
    ['app\\main.py'],
    pathex=[],
    binaries=[],
    datas=asset_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='KayouInstaller',
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
    icon=['assets\\icons\\loveball.ico'],
    manifest='assets\\manifests\\admin.manifest',
)
