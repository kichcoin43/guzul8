import os
import sys
import logging
import asyncio
import random
from telethon import TelegramClient
from telethon.tl.types import User

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Активная сессия - использовать ту, которая показала, что пользователь авторизован
SESSION_FILE = "session_380664312381"

# Тестовый получатель (самому себе)
TEST_RECIPIENT = "me"

async def test_self_messaging():
    """
    Тест отправки сообщения самому себе для проверки работы отправителя
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
        
        # Отправляем тестовое сообщение самому себе
        message = f"Тестовое сообщение от troubleshooter: {random.randint(1000, 9999)}"
        logger.info(f"Отправка тестового сообщения самому себе...")
        
        # Три метода отправки
        methods = ["me", "@" + me.username if me.username else None, me.phone]
        
        for method in methods:
            if not method:
                continue
                
            try:
                logger.info(f"Отправка методом: {method}")
                result = await client.send_message(method, message)
                logger.info(f"Сообщение отправлено: id={result.id}")
                
                # Если удалось отправить, возвращаем метод, который сработал
                return method
            except Exception as e:
                logger.error(f"Ошибка при отправке методом {method}: {str(e)}")
        
        logger.error("Все методы отправки не удались")
        return False
            
    except Exception as e:
        logger.error(f"Ошибка при тестировании отправки: {str(e)}")
        return False
    finally:
        await client.disconnect()
        logger.info("Отключение от Telegram API")

async def test_specific_recipient(recipient):
    """
    Тест отправки сообщения конкретному получателю для выявления проблем
    
    Args:
        recipient (str): Получатель (@username или телефон)
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
        
        # Отправляем тестовое сообщение указанному получателю
        message = f"Тестовое сообщение от troubleshooter: {random.randint(1000, 9999)}"
        logger.info(f"Отправка тестового сообщения получателю {recipient}...")
        
        try:
            # Пробуем сначала получить entity
            try:
                entity = await client.get_entity(recipient)
                logger.info(f"Получен entity типа {type(entity).__name__}")
                
                if isinstance(entity, User):
                    logger.info(f"Информация о пользователе: id={entity.id}, имя={entity.first_name} {entity.last_name if entity.last_name else ''}")
                    
                # Отправляем сообщение через entity
                try:
                    result = await client.send_message(entity, message)
                    logger.info(f"Сообщение отправлено через entity: id={result.id}")
                    return True
                except Exception as e:
                    logger.error(f"Ошибка при отправке через entity: {str(e)}")
            except Exception as e:
                logger.error(f"Ошибка при получении entity: {str(e)}")
            
            # Пробуем отправить напрямую
            logger.info("Пробуем отправить напрямую...")
            result = await client.send_message(recipient, message)
            logger.info(f"Сообщение отправлено напрямую: id={result.id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке получателю {recipient}: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при тестировании отправки: {str(e)}")
        return False
    finally:
        await client.disconnect()
        logger.info("Отключение от Telegram API")

async def main():
    """Основная функция для запуска тестирования"""
    print("Начинаем тестирование отправки сообщений...")
    
    # Сначала проверяем отправку самому себе
    print("\n--- Тест отправки самому себе ---")
    self_result = await test_self_messaging()
    
    if self_result:
        print(f"✅ Отправка самому себе работает методом: {self_result}")
    else:
        print("❌ Отправка самому себе не работает")
        print("Возможно, проблема с аккаунтом отправителя или API ключами.")
        return
    
    # Если указан конкретный получатель, тестируем отправку ему
    if len(sys.argv) > 1:
        recipient = sys.argv[1]
        print(f"\n--- Тест отправки получателю {recipient} ---")
        recipient_result = await test_specific_recipient(recipient)
        
        if recipient_result:
            print(f"✅ Отправка получателю {recipient} работает")
        else:
            print(f"❌ Отправка получателю {recipient} не работает")
            print("Возможно, проблема с этим конкретным получателем или форматом адреса.")
    else:
        print("\nДля тестирования отправки конкретному получателю укажите его в качестве аргумента:")
        print("python troubleshoot_sender.py @username")
        print("или")
        print("python troubleshoot_sender.py +79123456789")

if __name__ == "__main__":
    asyncio.run(main())