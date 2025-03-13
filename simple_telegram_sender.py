#!/usr/bin/env python3
"""
Simple Telegram Sender - самый простой скрипт для отправки сообщений в Telegram
Используйте его для отправки сообщений напрямую через командную строку.

Использование:
    python simple_telegram_sender.py @username "Текст сообщения"
    python simple_telegram_sender.py --list usernames.txt "Текст сообщения"
"""

import os
import sys
import asyncio
import logging
from telethon import TelegramClient

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Авторизованная сессия
SESSION_FILE = "session_380664312381"

async def send_message(recipient, message):
    """Отправляет одно сообщение указанному получателю"""
    if not API_ID or not API_HASH:
        print("❌ Ошибка: API_ID или API_HASH не настроены в переменных окружения")
        return False
    
    # Создаем клиент Telegram с существующей сессией
    client = TelegramClient(SESSION_FILE, int(API_ID), API_HASH)
    
    try:
        # Подключаемся к API
        await client.connect()
        
        # Проверяем, авторизованы ли мы
        if not await client.is_user_authorized():
            print(f"❌ Ошибка: Сессия {SESSION_FILE} не авторизована")
            return False
        
        # Отправляем сообщение
        print(f"📤 Отправка сообщения для {recipient}...")
        
        try:
            # Пробуем найти получателя
            entity = await client.get_entity(recipient)
            # Отправляем сообщение
            await client.send_message(entity, message)
            print(f"✅ Сообщение для {recipient} успешно отправлено!")
            return True
        except Exception as e:
            print(f"❌ Ошибка при отправке {recipient}: {str(e)}")
            return False
    
    except Exception as e:
        print(f"❌ Общая ошибка: {str(e)}")
        return False
    
    finally:
        # Отключаемся
        await client.disconnect()

async def main():
    """Основная функция программы"""
    # Проверяем аргументы командной строки
    if len(sys.argv) < 3:
        print("Использование:")
        print("  python simple_telegram_sender.py @username 'Текст сообщения'")
        print("  python simple_telegram_sender.py --list usernames.txt 'Текст сообщения'")
        return
    
    # Определяем режим работы (один получатель или список)
    if sys.argv[1] == "--list":
        if len(sys.argv) < 4:
            print("Для режима списка нужно указать файл и сообщение.")
            return
        
        # Читаем список получателей из файла
        try:
            with open(sys.argv[2], 'r') as f:
                recipients = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Ошибка при чтении файла: {str(e)}")
            return
        
        message = sys.argv[3]
        
        # Отправляем сообщения всем получателям из списка
        print(f"🔄 Отправка сообщений {len(recipients)} получателям...")
        success_count = 0
        
        for recipient in recipients:
            if await send_message(recipient, message):
                success_count += 1
            
            # Пауза между сообщениями, чтобы избежать ограничений Telegram
            await asyncio.sleep(1.5)
        
        print(f"\n📊 Итоги: {success_count} из {len(recipients)} сообщений отправлено успешно")
    
    else:
        # Режим одного получателя
        recipient = sys.argv[1]
        message = sys.argv[2]
        
        await send_message(recipient, message)

if __name__ == "__main__":
    asyncio.run(main())