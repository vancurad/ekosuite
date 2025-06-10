# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_dynamic_libs,
    collect_data_files,
    collect_all
)

datas = [
    ('ekosuite/plugins', '.')
];
datas += collect_data_files('importlib_metadata');
datas += collect_submodules('ekosuite.plugins.plugin_implementations')

hiddenimports = [];
hiddenimports += [
    'importlib_metadata'
];

a = Analysis(
    ['ekosuite.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['fix_importlib_metadata.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ekosuite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ekosuite',
)
app = BUNDLE(
    coll,
    name='ekosuite.app',
    icon=None,
    bundle_identifier=None,
)
