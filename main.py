#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Отправитель сообщений Telegram для Украины
========================================

Универсальная точка входа для системы отправки сообщений Telegram.
Включает веб-интерфейс на Flask для удобного управления.

Использование:
   - В Replit: Нажмите кнопку Run для запуска веб-интерфейса
   - Из командной строки: python main.py - запуск веб-интерфейса
   - Консольный режим: python main.py cli
"""

import os
import sys
import logging
from app import app
import importlib.util

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_telethon_available():
    """Проверяет доступность библиотеки Telethon"""
    try:
        import telethon
        logger.info("Библиотека Telethon доступна")
        return True
    except ImportError:
        logger.error("Библиотека Telethon не установлена!")
        return False

def run_cli(args):
    """Запускает консольный режим с переданными аргументами"""
    # Проверяем наличие Telethon
    if not check_telethon_available():
        print("\nДля работы с Telegram необходимо установить Telethon:")
        print("  pip install telethon")
        return False
    
    # Проверяем наличие файла ua_cli.py
    cli_path = os.path.join("ua_telegram_sender", "ua_cli.py")
    if not os.path.exists(cli_path):
        logger.error(f"Файл {cli_path} не найден!")
        return False
    
    try:
        # Загружаем модуль CLI динамически
        spec = importlib.util.spec_from_file_location("ua_cli", cli_path)
        if spec:
            ua_cli = importlib.util.module_from_spec(spec)
            if spec.loader:
                spec.loader.exec_module(ua_cli)
                
                # Запускаем CLI с переданными аргументами
                logger.info("Запуск консольного режима...")
                sys.argv = [cli_path] + args
                ua_cli.main()
                return True
            else:
                logger.error("Ошибка: spec.loader отсутствует")
        else:
            logger.error(f"Ошибка загрузки модуля {cli_path}")
        return False
    except Exception as e:
        logger.error(f"Ошибка запуска консольного режима: {e}")
        return False

def run_quick_send(message):
    """Запускает быстрый режим отправки с указанным сообщением"""
    runner_path = os.path.join("ua_telegram_sender", "run_sender.py")
    if not os.path.exists(runner_path):
        logger.error(f"Файл {runner_path} не найден!")
        return False
    
    try:
        # Загружаем модуль run_sender динамически
        spec = importlib.util.spec_from_file_location("run_sender", runner_path)
        if spec:
            runner = importlib.util.module_from_spec(spec)
            if spec.loader:
                spec.loader.exec_module(runner)
                
                # Запускаем с сообщением
                logger.info(f"Быстрая отправка сообщения: {message[:30]}...")
                sys.argv = [runner_path, message]
                runner.main()
                return True
            else:
                logger.error("Ошибка: spec.loader отсутствует")
        else:
            logger.error(f"Ошибка загрузки модуля {runner_path}")
        return False
    except Exception as e:
        logger.error(f"Ошибка быстрой отправки: {e}")
        return False

def print_help():
    """Выводит справку по использованию программы"""
    print("\nОтправитель сообщений Telegram для Украины")
    print("========================================")
    print("\nИспользование:")
    print("  python main.py                     - запуск веб-интерфейса")
    print("  python main.py cli                 - запуск консольного режима")
    print("  python main.py send \"Сообщение\"    - быстрая отправка указанного сообщения")
    print("  python main.py help                - показать эту справку")
    print("\nДополнительные параметры для консольного режима:")
    print("  python main.py cli --phone=\"+380xxxxxxxxx\" --code=\"12345\" --message=\"Текст\"")
    print("\nДля получения полной документации посетите /help в веб-интерфейсе")

def handle_cli_args():
    """Обрабатывает аргументы командной строки"""
    if len(sys.argv) < 2:
        # Запуск веб-интерфейса по умолчанию
        return None
        
    command = sys.argv[1].lower()
    
    if command == "cli":
        # Консольный режим
        run_cli(sys.argv[2:])
        return True
    elif command == "send" and len(sys.argv) > 2:
        # Быстрая отправка сообщения
        run_quick_send(sys.argv[2])
        return True
    elif command in ["help", "--help", "-h"]:
        # Справка
        print_help()
        return True
    
    # Запуск веб-интерфейса для всех других случаев
    return None

# Точка входа в программу
if __name__ == "__main__":
    # Проверяем директории и зависимости
    if not os.path.exists("ua_telegram_sender"):
        os.makedirs("ua_telegram_sender", exist_ok=True)
        logger.info("Создана директория ua_telegram_sender")

    # Обрабатываем аргументы командной строки
    cli_result = handle_cli_args()
    
    # Если команда не была обработана, запускаем веб-интерфейс
    if cli_result is None:
        # Проверяем, не запущен ли уже веб-сервер
        import socket
        port = 5000
        try:
            # Пытаемся определить, занят ли порт 5000
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('0.0.0.0', port))
            sock.close()

            # Если порт уже занят, значит веб-сервер уже запущен
            if result == 0:
                logger.warning(f"Порт {port} уже используется. Веб-интерфейс уже запущен или используется другим процессом.")
                logger.info("Для использования веб-интерфейса перейдите по URL в браузере.")
                # Ждём, чтобы пользователь мог прочитать сообщение
                import time
                time.sleep(60)
                sys.exit(0)
        except Exception as e:
            logger.warning(f"Ошибка при проверке порта: {e}")

        # Продолжаем запуск веб-интерфейса
        logger.info("Запуск веб-интерфейса на порту 5000")
        app.run(host='0.0.0.0', port=5000, debug=True)