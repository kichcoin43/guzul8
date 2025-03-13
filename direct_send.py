import asyncio
import os
import sys
import logging
from telethon import TelegramClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Авторизованная сессия
SESSION_FILE = "session_380664312381"

async def send_direct_message(recipient, message_text):
    """
    Простая функция для отправки сообщения одному получателю
    
    Args:
        recipient (str): Имя пользователя или телефон получателя
        message_text (str): Текст сообщения
    """
    if not API_ID or not API_HASH:
        logger.error("API_ID или API_HASH не найдены в переменных окружения")
        return False
        
    # Создаем клиент Telegram
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
        logger.info(f"Отправитель: id={me.id}, имя={me.first_name} {me.last_name if me.last_name else ''}, username={me.username}, phone={me.phone}")
        
        # Отправка сообщения
        logger.info(f"Попытка отправки сообщения получателю {recipient}...")
        
        try:
            # Пробуем получить информацию о получателе 
            try:
                user = await client.get_entity(recipient)
                logger.info(f"Найден получатель: {user.id}, {getattr(user, 'username', 'без имени')}")
            except Exception as user_error:
                logger.warning(f"Не удалось получить информацию о пользователе {recipient}: {str(user_error)}")
            
            # Отправляем сообщение
            result = await client.send_message(recipient, message_text)
            logger.info(f"Сообщение успешно отправлено! ID сообщения: {result.id}")
            return True
            
        except Exception as send_error:
            logger.error(f"Ошибка при отправке сообщения: {str(send_error)}")
            return False
    
    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}")
        return False
    
    finally:
        # Закрываем соединение
        await client.disconnect()
        logger.info("Отключение от Telegram API")

async def main():
    """Основная функция для запуска отправки сообщения"""
    if len(sys.argv) < 3:
        print("Использование: python direct_send.py <получатель> <сообщение>")
        print("Пример: python direct_send.py @username 'Привет, это тестовое сообщение'")
        return
    
    recipient = sys.argv[1]
    message = sys.argv[2]
    
    print(f"Отправка сообщения: '{message}' для получателя {recipient}")
    
    result = await send_direct_message(recipient, message)
    
    if result:
        print("✅ Сообщение успешно отправлено!")
    else:
        print("❌ Не удалось отправить сообщение. Проверьте логи для получения подробной информации.")

if __name__ == "__main__":
    asyncio.run(main())