
# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Собираем все необходимые данные для telethon
telethon_datas, telethon_binaries, telethon_hiddenimports = collect_all('telethon')

a = Analysis(
    ['app.py'],
    pathex=[r'/home/runner/workspace'],
    binaries=telethon_binaries,
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('recipients.txt', '.'),
    ] + telethon_datas,
    hiddenimports=[
        'telethon', 'flask', 'flask_sqlalchemy', 'werkzeug', 
        'sqlalchemy', 'email_validator', 'logging', 'asyncio',
        'PIL', 'PIL._tkinter_finder', 'PIL._imagingtk',
        'win32api', 'win32con', 'win32gui', 'win32process', 
        'win32security', 'pywintypes', 'win32ui', 'win32pipe',
        'cryptography', 'encodings', 'packaging.requirements',
    ] + telethon_hiddenimports,
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
    target_platform='windows',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'/home/runner/workspace/static/favicon.ico' if os.path.exists(r'/home/runner/workspace/static/favicon.ico') else None,
    version='file_version_info.txt',
)
    