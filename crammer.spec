import sys
import os

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('crammer/i18n/locales', 'crammer/i18n/locales'),
        ('resources/assets', 'resources/assets'),
        ('resources/templates', 'resources/templates')
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

icon_path = None
if sys.platform.startswith('win'):
    icon_path = 'resources/assets/logo.ico'
elif sys.platform.startswith('darwin'):
    icon_path = None 

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Crammer',
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
    icon=icon_path
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Crammer',
)