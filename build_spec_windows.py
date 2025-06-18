#!/usr/bin/env python3
"""
Spec file generator for Windows executable
"""

spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['njet-game-2.py'],
    pathex=[],
    binaries=[],
    datas=[('music', 'music')],
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
    [],
    exclude_binaries=True,
    name='Njet-Windows',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
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
    name='Njet-Windows',
)
'''

with open('Njet-Windows.spec', 'w') as f:
    f.write(spec_content.strip())

print("Windows spec file created successfully")