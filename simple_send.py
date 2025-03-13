#!/usr/bin/env python3
import os
import sys
import logging
from telethon import TelegramClient, events

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Активная сессия для отправки
SESSION_FILE = "session_380664312381"  # Используем этот файл, т.к. он работает

# Выполняемые действия
async def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_send.py @username 'Your message text'")
        return
        
    recipient = sys.argv[1]
    message = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Тестовое сообщение"
    
    print(f"Trying to send message to {recipient}")
    print(f"Message: {message}")
    
    # Connect to Telegram
    client = TelegramClient(SESSION_FILE, int(API_ID), API_HASH)
    
    await client.connect()
    
    if not await client.is_user_authorized():
        print("Error: Not authorized. Session file may be invalid.")
        return
    
    # Получаем информацию о своём аккаунте
    me = await client.get_me()
    print(f"Sending from: {me.first_name} {me.last_name or ''}, ID: {me.id}, Phone: {me.phone}")
    
    try:
        # Пробуем получить информацию о получателе
        try:
            entity = await client.get_entity(recipient)
            print(f"Found entity: {entity}")
        except Exception as e:
            print(f"Error getting entity: {e}")
            print("Trying direct sending without resolving entity...")
            entity = recipient
        
        # Отправляем сообщение
        print(f"Sending message...")
        result = await client.send_message(entity, message)
        print(f"Message sent! Message id: {result.id}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Disconnect
        await client.disconnect()
        print("Disconnected from Telegram")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())