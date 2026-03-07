# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\A\\.openclaw\\workspace\\aios\\aios_exe.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\A\\.openclaw\\workspace\\aios\\core', 'core'), ('C:\\Users\\A\\.openclaw\\workspace\\aios\\config.yaml', '.'), ('C:\\Users\\A\\.openclaw\\workspace\\aios\\demo_file_monitor.py', '.'), ('C:\\Users\\A\\.openclaw\\workspace\\aios\\demo_api_health.py', '.'), ('C:\\Users\\A\\.openclaw\\workspace\\aios\\demo_log_analysis.py', '.'), ('C:\\Users\\A\\.openclaw\\workspace\\aios\\demo_simple.py', '.'), ('C:\\Users\\A\\.openclaw\\workspace\\aios\\warmup.py', '.'), ('C:\\Users\\A\\.openclaw\\workspace\\aios\\README.md', '.'), ('C:\\Users\\A\\.openclaw\\workspace\\aios\\LICENSE', '.')],
    hiddenimports=['json', 'pathlib', 'subprocess', 'datetime', 'argparse', 'uuid', 'dataclasses', 'typing', 'shutil'],
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
    name='AIOS-Full-20260307',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='AIOS-Full-20260307',
)
