import asyncio
import os
import sys
import logging
from telethon import TelegramClient
from telethon.errors import FloodWaitError

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

async def send_message(client, recipient, message_text):
    """
    Отправляет сообщение конкретному получателю
    
    Args:
        client: TelegramClient
        recipient: str - получатель (@username или номер телефона)
        message_text: str - текст сообщения
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        # Пробуем получить информацию о получателе 
        try:
            user = await client.get_entity(recipient)
            logger.info(f"Найден получатель: {user.id}, {getattr(user, 'username', 'без имени')}")
        except Exception as user_error:
            logger.warning(f"Не удалось получить информацию о пользователе {recipient}: {str(user_error)}")
            return False, f"Ошибка получения данных пользователя: {str(user_error)}"
        
        # Отправляем сообщение
        result = await client.send_message(recipient, message_text)
        logger.info(f"Сообщение успешно отправлено! ID сообщения: {result.id}")
        return True, None
        
    except FloodWaitError as flood_error:
        # Обработка ошибки флуда (слишком много запросов)
        wait_time = flood_error.seconds
        logger.error(f"Сработала защита от флуда, требуется ожидание {wait_time} секунд")
        return False, f"Ограничение Telegram: требуется подождать {wait_time} секунд"
    
    except Exception as send_error:
        logger.error(f"Ошибка при отправке сообщения: {str(send_error)}")
        return False, str(send_error)

async def send_messages(recipients_list, message_text):
    """
    Отправляет сообщение списку получателей
    
    Args:
        recipients_list (list): Список получателей
        message_text (str): Текст сообщения
        
    Returns:
        tuple: (successful_count, failed_count, {failed_user: error_message})
    """
    if not API_ID or not API_HASH:
        logger.error("API_ID или API_HASH не найдены в переменных окружения")
        return 0, len(recipients_list), {"all": "API_ID или API_HASH не настроены"}
        
    # Создаем клиент Telegram
    client = TelegramClient(SESSION_FILE, int(API_ID), API_HASH)
    
    successful_count = 0
    failed_count = 0
    failed_recipients = {}
    
    try:
        # Подключаемся
        logger.info(f"Подключение к Telegram с сессией {SESSION_FILE}...")
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            logger.error("Пользователь не авторизован в этой сессии")
            return 0, len(recipients_list), {"all": "Сессия не авторизована"}
        
        # Получаем информацию о текущем пользователе
        me = await client.get_me()
        logger.info(f"Отправитель: id={me.id}, имя={me.first_name} {me.last_name if me.last_name else ''}, username={me.username}, phone={me.phone}")
        
        # Отправляем сообщения каждому получателю
        for recipient in recipients_list:
            logger.info(f"Отправка сообщения для {recipient}...")
            success, error = await send_message(client, recipient, message_text)
            
            if success:
                successful_count += 1
                # Небольшая задержка между сообщениями для избежания флуда
                await asyncio.sleep(1.5)
            else:
                failed_count += 1
                failed_recipients[recipient] = error
                
                # Если возникла ошибка FloodWaitError, нужно подождать дольше
                if "требуется подождать" in error:
                    wait_time = int(error.split("подождать ")[1].split(" ")[0])
                    logger.info(f"Ожидание {wait_time} секунд из-за ограничения Telegram...")
                    await asyncio.sleep(min(wait_time, 60))  # Ждем не более 60 секунд
                else:
                    # Обычная задержка между попытками
                    await asyncio.sleep(2)
    
    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}")
        return successful_count, failed_count + (len(recipients_list) - successful_count - failed_count), failed_recipients
    
    finally:
        # Закрываем соединение
        await client.disconnect()
        logger.info("Отключение от Telegram API")
    
    return successful_count, failed_count, failed_recipients

async def main():
    """Основная функция для запуска отправки сообщений"""
    if len(sys.argv) < 3:
        print("Использование: python direct_send_multiple.py <сообщение> <получатель1> [получатель2] ...")
        print("Пример: python direct_send_multiple.py 'Привет, это тестовое сообщение' @username1 @username2")
        return
    
    message = sys.argv[1]
    recipients = sys.argv[2:]
    
    print(f"Отправка сообщения: '{message}' для {len(recipients)} получателей: {', '.join(recipients)}")
    
    successful, failed, failures = await send_messages(recipients, message)
    
    print(f"\n✅ Успешно отправлено: {successful}")
    print(f"❌ Ошибок отправки: {failed}")
    
    if failed > 0:
        print("\nДетали ошибок:")
        for recipient, error in failures.items():
            print(f"  - {recipient}: {error}")

if __name__ == "__main__":
    asyncio.run(main())