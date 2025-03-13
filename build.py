import os
import sys
import subprocess
import logging
import platform

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_requirements():
    """Check if necessary packages are installed"""
    required_packages = ['pyinstaller', 'telethon', 'flask', 'flask-sqlalchemy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.info("Installing missing packages...")
        
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                logger.info(f"Successfully installed {package}")
            except subprocess.CalledProcessError:
                logger.error(f"Failed to install {package}")
                return False
    
    return True

def build_executable():
    """Build the executable with PyInstaller"""
    if not check_requirements():
        logger.error("Requirements check failed. Aborting build.")
        return False
    
    logger.info("Starting build process...")
    
    # Determine the output name based on platform
    if platform.system() == 'Windows':
        output_name = 'telegram_bulk_messenger.exe'
    else:
        output_name = 'telegram_bulk_messenger'
    
    # Создаем spec файл для PyInstaller с кодом для сохранения переменных окружения
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Сохраняем текущие переменные окружения
api_id = os.environ.get('TELEGRAM_API_ID', '')
api_hash = os.environ.get('TELEGRAM_API_HASH', '')
demo_mode = os.environ.get('TELEGRAM_DEMO_MODE', '')

a = Analysis(
    ['main.py'],
    pathex=['{os.getcwd()}'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
    ],
    hiddenimports=['telethon', 'flask', 'flask_sqlalchemy', 'werkzeug', 'sqlalchemy', 'email_validator'],
    hookspath=[],
    hooksconfig={{}},
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
    name='{output_name}',
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
    # Код для сохранения переменных окружения в скомпилированном EXE
    contents=f'''
import os

# Устанавливаем переменные окружения из сохраненных значений
if api_id:
    os.environ['TELEGRAM_API_ID'] = api_id
if api_hash:
    os.environ['TELEGRAM_API_HASH'] = api_hash
if demo_mode:
    os.environ['TELEGRAM_DEMO_MODE'] = demo_mode
''',
)
    """
    
    # Записываем spec-файл
    spec_path = os.path.join(os.getcwd(), 'telegram_messenger.spec')
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    # PyInstaller command с использованием spec-файла
    cmd = [
        'pyinstaller',
        'telegram_messenger.spec'
    ]
    
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        
        # Check if the executable was created
        dist_dir = os.path.join(os.getcwd(), 'dist')
        executable_path = os.path.join(dist_dir, output_name)
        
        if os.path.exists(executable_path):
            logger.info(f"Build successful! Executable created at: {executable_path}")
            return True
        else:
            logger.error(f"Build failed: Executable not found at {executable_path}")
            return False
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Build failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during build: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Telegram Bulk Messenger - Build Tool")
    print("=" * 60)
    
    success = build_executable()
    
    if success:
        print("\nBuild completed successfully!")
        print("\nYou can find the executable in the 'dist' directory.")
    else:
        print("\nBuild failed. Please check the logs for details.")