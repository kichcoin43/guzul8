
import os
import sys
import logging
import platform
import subprocess
import shutil

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_pyinstaller():
    """Проверяет наличие PyInstaller и устанавливает его при необходимости"""
    try:
        import PyInstaller
        logger.info("PyInstaller установлен.")
        return True
    except ImportError:
        logger.info("PyInstaller не установлен. Устанавливаем...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller==5.13.2"])
            logger.info("PyInstaller успешно установлен.")
            return True
        except Exception as e:
            logger.error(f"Не удалось установить PyInstaller: {str(e)}")
            return False

def build_windows_exe():
    """Сборка Windows EXE файла"""
    logger.info("Начинаем сборку EXE для Windows...")
    
    # Определяем операционную систему
    current_os = platform.system()
    logger.info(f"Текущая операционная система: {current_os}")
    
    if current_os != "Windows":
        logger.warning("ВНИМАНИЕ: Вы собираете Windows EXE не на Windows! Это вызовет проблемы совместимости.")
        logger.info("Для создания полноценного Windows EXE необходимо использовать Windows-систему.")
        
        print("\n===========================================================")
        print("ВАЖНО: СБОРКА НА REPLIT НЕ СОВМЕСТИМА С WINDOWS 10")
        print("===========================================================")
        print("Для создания работающего EXE файла для Windows 10 выполните следующие шаги:")
        print("")
        print("1. Скачайте этот проект с Replit (используйте кнопку 'Download as zip')")
        print("2. Распакуйте архив на компьютере с Windows 10")
        print("3. Установите Python с сайта python.org")
        print("4. Откройте командную строку в распакованной папке")
        print("5. Выполните команды:")
        print("   pip install pyinstaller telethon flask flask-sqlalchemy pillow")
        print("   python build_portable.py")
        print("")
        print("Это создаст работающий EXE файл для Windows 10")
        print("===========================================================")
    
    # Проверяем наличие PyInstaller
    if not check_pyinstaller():
        return False
    
    # Устанавливаем необходимые зависимости для Windows
    try:
        print("Устанавливаем необходимые Windows-зависимости...")
        packages = [
            "pywin32-ctypes",
            "pywin32",
            "pefile",
            "pyinstaller-hooks-contrib",
            "pillow",
            "cryptography"
        ]
        
        for package in packages:
            try:
                print(f"Установка {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except Exception as e:
                print(f"Ошибка при установке {package}: {str(e)}")
                # Продолжаем, даже если не удалось установить некоторые пакеты
    except Exception as e:
        logger.error(f"Ошибка при установке зависимостей: {str(e)}")
    
    # Создаем папку для иконки если её нет
    static_dir = os.path.join(os.getcwd(), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # Проверяем наличие иконки
    icon_path = os.path.join(static_dir, 'favicon.ico')
    if not os.path.exists(icon_path):
        logger.warning("Иконка не найдена! Сборка будет без иконки.")
    
    # Создаем spec-файл для PyInstaller с более подробными настройками
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Собираем все необходимые данные для telethon
telethon_datas, telethon_binaries, telethon_hiddenimports = collect_all('telethon')

a = Analysis(
    ['app.py'],
    pathex=[r'%s'],
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
    icon=r'%s' if os.path.exists(r'%s') else None,
    version='file_version_info.txt',
)
    """ % (os.getcwd().replace('\\', '\\\\'), 
           icon_path.replace('\\', '\\\\'), 
           icon_path.replace('\\', '\\\\'))
    
    # Создаем файл версии для EXE
    version_info = """
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'ГУЦУЛЬСКАЯ РАССЫЛКА'),
        StringStruct(u'FileDescription', u'ГУЦУЛЬСКАЯ РАССЫЛКА'),
        StringStruct(u'FileVersion', u'1.0.0'),
        StringStruct(u'InternalName', u'ГУЦУЛЬСКАЯ_РАССЫЛКА'),
        StringStruct(u'LegalCopyright', u'© 2025 ГУЦУЛЬСКАЯ РАССЫЛКА. Все права защищены.'),
        StringStruct(u'OriginalFilename', u'ГУЦУЛЬСКАЯ_РАССЫЛКА.exe'),
        StringStruct(u'ProductName', u'ГУЦУЛЬСКАЯ РАССЫЛКА'),
        StringStruct(u'ProductVersion', u'1.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    # Записываем spec-файл
    spec_path = os.path.join(os.getcwd(), 'гуцульская_рассылка.spec')
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    # Записываем файл версии
    version_path = os.path.join(os.getcwd(), 'file_version_info.txt')
    with open(version_path, 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    # Создаём README для запуска на Windows
    windows_readme = """# ГУЦУЛЬСКАЯ РАССЫЛКА - ИНСТРУКЦИЯ ПО ЗАПУСКУ НА WINDOWS 10

## ВАЖНО: Запуск приложения на Windows

1. Скачайте весь проект с Replit:
   - Нажмите на меню "..." в верхнем правом углу
   - Выберите "Download as zip"
   - Сохраните файл на компьютер

2. Распакуйте скачанный ZIP архив в любую папку

3. Установите Python для Windows:
   - Скачайте Python с официального сайта https://www.python.org/downloads/
   - Установите Python, **ОБЯЗАТЕЛЬНО ОТМЕТЬТЕ** опцию "Add Python to PATH"

4. Откройте командную строку как администратор:
   - Нажмите Win+X и выберите "Командная строка (админ)" или "PowerShell (админ)"

5. Перейдите в распакованную папку с проектом:
   ```
   cd путь/к/распакованной/папке
   ```

6. Установите необходимые зависимости:
   ```
   pip install telethon flask flask-sqlalchemy pillow pyinstaller
   ```

7. Запустите скрипт сборки:
   ```
   python build_portable.py
   ```

8. После успешной сборки, EXE-файл будет находиться в папке dist_windows
   - Просто запустите файл ГУЦУЛЬСКАЯ_РАССЫЛКА.exe

## Прямой запуск без создания EXE (для тестирования)

Если вы хотите просто запустить приложение без создания EXE:

1. Откройте командную строку в папке с проектом
2. Выполните:
   ```
   python app.py
   ```
3. Откройте браузер и перейдите по адресу http://localhost:5000
"""
    
    windows_readme_path = os.path.join(os.getcwd(), 'ИНСТРУКЦИЯ_ДЛЯ_WINDOWS.md')
    with open(windows_readme_path, 'w', encoding='utf-8') as f:
        f.write(windows_readme)
    
    # Если мы не на Windows, то просто создаем заглушку для pywin32
    if current_os != "Windows":
        logger.info("Создаем пустые модули-заглушки для Windows-зависимостей...")
        win32_stub_dir = os.path.join(os.getcwd(), 'win32_stubs')
        if not os.path.exists(win32_stub_dir):
            os.makedirs(win32_stub_dir)
        
        # Создаем заглушки для основных win32 модулей
        for module in ['win32api', 'win32con', 'win32gui', 'pywintypes']:
            with open(os.path.join(win32_stub_dir, f'{module}.py'), 'w') as f:
                f.write('# Stub module for PyInstaller\n')
        
        # Добавляем путь к заглушкам
        sys.path.insert(0, win32_stub_dir)
    
    # Команда для сборки
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        'гуцульская_рассылка.spec',
        '--clean',
        '--distpath', './dist_windows'
    ]
    
    try:
        logger.info(f"Запуск команды: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        
        # Проверяем результат
        dist_dir = os.path.join(os.getcwd(), 'dist_windows')
        executable_path = os.path.join(dist_dir, "ГУЦУЛЬСКАЯ_РАССЫЛКА.exe")
        
        if os.path.exists(executable_path):
            # Копируем необходимые файлы в папку с EXE-файлом
            logger.info("Копирование необходимых файлов в папку с EXE...")
            
            # Создаем README файл с инструкциями
            readme_path = os.path.join(dist_dir, "README.txt")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write("""ГУЦУЛЬСКАЯ РАССЫЛКА
===================

Инструкция по использованию:
1. Дважды кликните на файл "ГУЦУЛЬСКАЯ_РАССЫЛКА.exe" для запуска программы
2. Откроется консольное окно и веб-интерфейс в вашем браузере
3. Следуйте инструкциям в веб-интерфейсе для настройки и отправки сообщений

Важно: Для работы программы необходимо подключение к интернету!
""")
            
            logger.info(f"Сборка успешна! EXE файл создан: {executable_path}")
            
            # Создаем ZIP-архив для удобства скачивания
            try:
                import shutil
                zip_path = os.path.join(os.getcwd(), 'ГУЦУЛЬСКАЯ_РАССЫЛКА.zip')
                logger.info(f"Создание ZIP-архива для скачивания: {zip_path}")
                shutil.make_archive('ГУЦУЛЬСКАЯ_РАССЫЛКА', 'zip', dist_dir)
                logger.info(f"ZIP-архив создан: {zip_path}")
            except Exception as e:
                logger.error(f"Ошибка при создании ZIP-архива: {str(e)}")
            
            return True
        else:
            logger.error(f"Сборка не удалась: EXE файл не найден по пути {executable_path}")
            return False
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при сборке: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ГУЦУЛЬСКАЯ РАССЫЛКА - Создание EXE-файла для Windows")
    print("=" * 60)
    print(f"Система сборки: {platform.system()} {platform.release()} {platform.machine()}")
    print(f"Python версия: {platform.python_version()}")
    
    # Устанавливаем необходимые пакеты
    print("\nУстановка необходимых зависимостей...")
    pip_packages = [
        "pyinstaller==5.13.2",  # Используем стабильную версию
        "pillow",
        "cryptography",
        "pywin32-ctypes",
        "pyinstaller-hooks-contrib"
    ]
    
    for package in pip_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"- {package} установлен")
        except Exception as e:
            print(f"- Ошибка установки {package}: {str(e)}")
    
    print("\nНачинаем создание EXE файла для Windows...")
    success = build_windows_exe()
    
    if success:
        print("\n" + "=" * 60)
        print("EXE-файл успешно создан в папке dist_windows!")
        print("\nВы можете скачать архив ГУЦУЛЬСКАЯ_РАССЫЛКА.zip, который содержит готовое приложение.")
        print("\nРаспакуйте архив на вашем Windows компьютере и запустите ГУЦУЛЬСКАЯ_РАССЫЛКА.exe")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("ВНИМАНИЕ: Сборка EXE в Replit для Windows 10 не удалась!")
        print("\nРекомендуемое решение:")
        print("1. Скачайте весь проект через 'Download as zip' в меню Replit")
        print("2. Распакуйте архив на вашем компьютере с Windows 10")
        print("3. Установите Python с сайта python.org")
        print("4. Запустите командную строку в папке с проектом и выполните:")
        print("   pip install telethon flask flask-sqlalchemy pillow pyinstaller")
        print("   python build_portable.py")
        print("\nЭто создаст рабочий EXE-файл на вашем компьютере с Windows 10")
        print("=" * 60)
        print("\nИли запустите приложение напрямую без EXE:")
        print("python app.py")
        print("И откройте браузер по адресу http://localhost:5000")
