# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ui/app_qt.py'],
    pathex=[],
    binaries=[],
    datas=[('core', 'core'), ('crypto', 'crypto'), ('storage', 'storage'), ('ui', 'ui')],
    hiddenimports=['ui.app_qt', 'core.vault', 'crypto.keyring', 'storage.repository'],
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
    name='MaNelly',
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
    icon=['assets/icon.icns'],
)
app = BUNDLE(
    exe,
    name='MaNelly.app',
    icon='assets/icon.icns',
    bundle_identifier=None,
)
