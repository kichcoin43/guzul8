
# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[r'/home/runner/workspace'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('recipients.txt', '.'),
    ],
    hiddenimports=[
        'telethon', 'flask', 'flask_sqlalchemy', 'werkzeug', 
        'sqlalchemy', 'email_validator', 'logging', 'asyncio', 
        'win32api', 'win32con', 'win32gui', 'pywintypes'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ГУЦУЛЬСКАЯ_РАССЫЛКА',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'/home/runner/workspace/static/favicon.ico' if os.path.exists(r'/home/runner/workspace/static/favicon.ico') else None,
)
    