
import os
import sys
import subprocess
import logging
import platform
import json
import shutil

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_requirements():
    """Проверяет наличие необходимых модулей для сборки"""
    try:
        import PyInstaller
        logger.info("PyInstaller установлен.")
    except ImportError:
        logger.error("PyInstaller не установлен. Устанавливаем...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            logger.info("PyInstaller успешно установлен.")
        except Exception as e:
            logger.error(f"Не удалось установить PyInstaller: {str(e)}")
            return False
    return True

def build_executable(target_platform=None):
    """Сборка исполняемого файла с PyInstaller
    
    Args:
        target_platform: Целевая платформа ('Windows' или None для текущей)
    """
    if not check_requirements():
        logger.error("Не удалось проверить требования. Отмена сборки.")
        return False
    
    logger.info("Начинаем процесс сборки...")
    
    # Определяем имя выходного файла в зависимости от платформы
    is_windows = platform.system() == 'Windows' or target_platform == 'Windows'
    
    if is_windows:
        output_name = 'ГУЦУЛЬСКАЯ_РАССЫЛКА.exe'
    else:
        output_name = 'ГУЦУЛЬСКАЯ_РАССЫЛКА'
    
    # Создаем директорию для сборки, если она не существует
    build_dir = os.path.join(os.getcwd(), 'build')
    dist_dir = os.path.join(os.getcwd(), 'dist')
    
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    
    # Создаем spec-файл для PyInstaller с поддержкой русских символов и иконкой
    icon_path = os.path.join(os.getcwd(), 'static', 'favicon.ico')
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
    ['app.py'],
    pathex=['{os.getcwd()}'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('recipients.txt', '.'),
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
    icon=['{icon_path}'] if os.path.exists('{icon_path}') else None,
    contents='''
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
    spec_path = os.path.join(os.getcwd(), 'гуцульская_рассылка.spec')
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    # Команда PyInstaller с использованием spec-файла
    cmd = [
        'pyinstaller',
        'гуцульская_рассылка.spec',
        '--clean'
    ]
    
    try:
        logger.info(f"Запуск команды: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        
        # Проверяем, был ли создан исполняемый файл
        executable_path = os.path.join(dist_dir, output_name)
        
        if os.path.exists(executable_path):
            logger.info(f"Сборка успешна! Исполняемый файл создан: {executable_path}")
            return True
        else:
            logger.error(f"Сборка не удалась: Исполняемый файл не найден по пути {executable_path}")
            return False
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Сборка не удалась: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при сборке: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ГУЦУЛЬСКАЯ РАССЫЛКА - Сборка EXE-файла")
    print("=" * 60)
    
    # Создаем папку для иконки если её нет
    static_dir = os.path.join(os.getcwd(), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # Добавляем иконку для приложения
    icon_path = os.path.join(static_dir, 'favicon.ico')
    if not os.path.exists(icon_path):
        # Можно использовать существующую иконку если есть
        if os.path.exists('generated-icon.png'):
            from PIL import Image
            import io
            try:
                # Преобразуем PNG в ICO
                img = Image.open('generated-icon.png')
                img.save(icon_path)
                logger.info(f"Создана иконка из PNG: {icon_path}")
            except Exception as e:
                logger.error(f"Не удалось создать иконку: {str(e)}")
    
    success = build_executable()
    
    if success:
        print("\nСборка EXE-файла завершена успешно!")
        
        # Определяем путь к исполняемому файлу
        if platform.system() == 'Windows':
            output_name = 'ГУЦУЛЬСКАЯ_РАССЫЛКА.exe'
        else:
            output_name = 'ГУЦУЛЬСКАЯ_РАССЫЛКА'
        
        dist_dir = os.path.join(os.getcwd(), 'dist')
        executable_path = os.path.join(dist_dir, output_name)
        
        print(f"\nРасположение исполняемого файла: {executable_path}")
        print("\nВы можете скопировать этот файл на свой компьютер и запустить.")
        print("Все необходимые файлы включены в исполняемый файл.")
    else:
        print("\nСборка EXE-файла не удалась. Проверьте логи для получения деталей.")
        sys.exit(1)
