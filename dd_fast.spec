# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('feature', 'feature')],  # 移除 system，构建脚本不应被打包
    hiddenimports=['rumps', 'flask', 'flask_cors', 'pymysql', 'json', 'pathlib', 'typing', 'tkinter', 'threading', 'subprocess', 'webbrowser'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['distutils', 'email', 'html', 'http', 'urllib', 'xml', 'pydoc'],  # 排除不需要的模块
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='dd_fast',
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
    name='dd_fast',
)
app = BUNDLE(
    coll,
    name='dd_fast.app',
    icon=None,
    bundle_identifier=None,
)
