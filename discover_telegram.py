import os
import sys
import logging
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError, PhoneCodeInvalidError

# Настройка подробного логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Активная сессия
SESSION_FILE = "session_380664312381"  # Используем сессию, которая показала, что пользователь авторизован

async def discover_telegram():
    """
    Исследует доступные функции и возможности Telegram API
    """
    if not API_ID or not API_HASH:
        logger.error("API_ID или API_HASH не найдены в переменных окружения")
        return False
        
    # Создаем клиент с активной сессией
    client = TelegramClient(SESSION_FILE, int(API_ID), API_HASH)
    
    try:
        # Подключаемся
        logger.info(f"Подключение к Telegram с сессией {SESSION_FILE}...")
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            logger.error("Пользователь не авторизован в этой сессии")
            return False
            
        # Получаем информацию о текущем пользователе
        me = await client.get_me()
        logger.info(f"Текущий пользователь: id={me.id}, имя={me.first_name} {me.last_name if me.last_name else ''}, username={me.username}, phone={me.phone}")
        
        # Получаем список диалогов
        logger.info("Получение списка последних диалогов...")
        dialogs = await client.get_dialogs(limit=10)
        
        for i, dialog in enumerate(dialogs):
            entity_type = type(dialog.entity).__name__
            entity_id = dialog.entity.id
            dialog_name = dialog.name
            
            logger.info(f"Диалог {i+1}: {dialog_name}, тип: {entity_type}, ID: {entity_id}")
            
            if i < 3:  # Для первых трех диалогов получаем больше информации
                try:
                    # Получаем последние сообщения из диалога
                    messages = await client.get_messages(dialog.entity, limit=3)
                    logger.info(f"  Последние сообщения в диалоге {dialog_name}:")
                    
                    for j, msg in enumerate(messages):
                        sender = msg.sender
                        sender_name = f"{sender.first_name} {sender.last_name}" if sender else "Unknown"
                        logger.info(f"    Сообщение {j+1}: От {sender_name}, Текст: {msg.text[:50]}{'...' if msg.text and len(msg.text) > 50 else ''}")
                except Exception as e:
                    logger.error(f"  Ошибка при получении сообщений для диалога {dialog_name}: {str(e)}")
        
        # Проверяем доступные телефонные номера для сравнения
        logger.info("Проверка доступных телефонных номеров для сравнения...")
        try:
            # Получаем все диалоги
            all_dialogs = await client.get_dialogs()
            phone_contacts = []
            
            for dialog in all_dialogs:
                if hasattr(dialog.entity, 'phone') and dialog.entity.phone:
                    phone_contacts.append((dialog.name, dialog.entity.phone))
            
            if phone_contacts:
                logger.info(f"Найдено {len(phone_contacts)} телефонных контактов:")
                for name, phone in phone_contacts:
                    logger.info(f"  {name}: {phone}")
            else:
                logger.info("Телефонные контакты не найдены через диалоги")
        except Exception as e:
            logger.error(f"Ошибка при поиске телефонных контактов: {str(e)}")
            
        # Проверяем нашу собственную информацию
        me_full = await client.get_entity('me')
        logger.info(f"Полная информация о текущем пользователе: {me_full.__dict__}")
        
        return True
            
    except Exception as e:
        logger.error(f"Ошибка при исследовании Telegram: {str(e)}")
        return False
    finally:
        await client.disconnect()
        logger.info("Отключение от Telegram API")

async def main():
    """Основная функция для запуска процесса исследования"""
    print("Начинаем исследование API Telegram...")
    result = await discover_telegram()
    
    if result:
        print("✓ Исследование успешно завершено!")
    else:
        print("✗ Произошла ошибка при исследовании.")

if __name__ == "__main__":
    asyncio.run(main())