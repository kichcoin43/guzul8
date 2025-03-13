import os
import sys
import logging
import asyncio
import random
import pprint
from telethon import TelegramClient
from telethon.tl.types import InputPhoneContact
from telethon.tl.functions.contacts import ImportContactsRequest

# Настройка подробного логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Активная сессия
SESSION_FILE = "session_380664312381"  # Используем сессию, которая показала, что пользователь авторизован

async def send_direct_message(recipient, message):
    """
    Отправляет сообщение напрямую указанному получателю
    
    Args:
        recipient (str): @username или телефон получателя
        message (str): Текст сообщения
        
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    if not API_ID or not API_HASH:
        logger.error("API_ID или API_HASH не найдены в переменных окружения")
        return False
        
    # Создаем клиент с активной сессией
    client = TelegramClient(SESSION_FILE, int(API_ID), API_HASH)
    
    try:
        # Подключаемся с подробным логированием
        logger.debug(f"Подключение к Telegram с сессией {SESSION_FILE}...")
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            logger.error("Пользователь не авторизован в этой сессии")
            return False
            
        # Получаем информацию о текущем пользователе для проверки
        me = await client.get_me()
        logger.info(f"Отправка от имени пользователя: id={me.id}, имя={me.first_name} {me.last_name if me.last_name else ''}, phone={me.phone}")
        
        # Определяем тип получателя (телефон или юзернейм)
        is_phone = recipient.startswith('+')
        
        try:
            entity = None
            
            if is_phone:
                logger.info(f"Получатель - телефонный номер: {recipient}")
                
                # Создаем временный контакт
                contact = InputPhoneContact(
                    client_id=random.randint(1, 100000),  # Случайный ID
                    phone=recipient,
                    first_name="Test",
                    last_name="Contact"
                )
                
                # Импортируем контакт с подробным логированием
                logger.debug(f"Импортируем контакт: {contact}")
                import_result = await client(ImportContactsRequest([contact]))
                logger.info(f"Результат импорта: {import_result.users[0].id if import_result.users else 'нет пользователей'}")
                
                if import_result.users:
                    entity = import_result.users[0]
                    logger.info(f"Пользователь найден: {entity.first_name} {entity.last_name if entity.last_name else ''}")
                else:
                    # Если не нашли пользователя через импорт, пробуем отправить напрямую
                    logger.warning(f"Пользователь не найден при импорте контакта, попробуем использовать номер напрямую")
                    entity = recipient
            else:
                # Для имен пользователей
                if not recipient.startswith('@'):
                    recipient = '@' + recipient
                    
                logger.info(f"Получатель - имя пользователя: {recipient}")
                # Получаем сущность
                entity = await client.get_entity(recipient)
                logger.info(f"Пользователь найден: тип={type(entity).__name__}")
                
            # Теперь отправляем сообщение с полным логированием
            logger.debug(f"Отправка сообщения: {message}")
            result = await client.send_message(entity, message)
            logger.info(f"Результат отправки: id={result.id}, тип={type(result).__name__}")
            
            # Успешная отправка!
            return True
                
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {str(e)}", exc_info=True)
            return False
    except Exception as e:
        logger.error(f"Ошибка при установке соединения: {str(e)}", exc_info=True)
        return False
    finally:
        # Отключаемся от API
        await client.disconnect()
        logger.info("Отключение от Telegram API")

async def main():
    """Основная функция для отправки тестового сообщения"""
    if len(sys.argv) < 3:
        print("Использование: python send_direct_message.py <получатель> <сообщение>")
        print("Получатель может быть телефонным номером (+380123456789) или именем пользователя (@username)")
        return
        
    recipient = sys.argv[1]
    message = sys.argv[2]
    
    print(f"Отправка сообщения '{message}' получателю '{recipient}'...")
    result = await send_direct_message(recipient, message)
    
    if result:
        print("✅ Сообщение успешно отправлено!")
    else:
        print("❌ Не удалось отправить сообщение.")

if __name__ == "__main__":
    asyncio.run(main())