import os
import sys
import logging
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError, PhoneCodeInvalidError

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

async def check_session(session_file):
    """
    Проверка существующей сессии Telegram
    
    Args:
        session_file (str): Путь к файлу сессии
    """
    if not API_ID or not API_HASH:
        logger.error("API_ID или API_HASH не найдены в переменных окружения")
        return False
        
    if not os.path.exists(session_file):
        logger.error(f"Файл сессии {session_file} не существует")
        return False
        
    # Создаем клиент с указанной сессией
    client = TelegramClient(session_file.replace('.session', ''), int(API_ID), API_HASH)
    
    try:
        # Подключаемся
        logger.info(f"Подключение к Telegram с сессией {session_file}...")
        await client.connect()
        
        # Проверяем авторизацию
        if await client.is_user_authorized():
            logger.info("Сессия активна, пользователь авторизован")
            
            # Получаем информацию о текущем пользователе
            me = await client.get_me()
            logger.info(f"Текущий пользователь: id={me.id}, имя={me.first_name} {me.last_name if me.last_name else ''}, phone={me.phone}")
            
            # Получаем список диалогов
            logger.info("Получение списка последних диалогов...")
            dialogs = await client.get_dialogs(limit=5)
            
            for dialog in dialogs:
                logger.info(f"Диалог: {dialog.name}, ID: {dialog.id}, entity_type: {type(dialog.entity).__name__}")
                
            return True
        else:
            logger.error("Сессия есть, но пользователь не авторизован")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при проверке сессии: {str(e)}")
        return False
    finally:
        await client.disconnect()
        logger.info("Отключение от Telegram API")

async def main():
    """Основная функция для проверки сессий"""
    if len(sys.argv) < 2:
        # Если файл не указан, проверяем все .session файлы
        session_files = [f for f in os.listdir('.') if f.endswith('.session')]
        if not session_files:
            print("Сессионные файлы не найдены.")
            return
            
        print(f"Найдено {len(session_files)} сессий. Проверяем...")
        
        for sess_file in session_files:
            print(f"\n--- Проверка сессии {sess_file} ---")
            await check_session(sess_file)
    else:
        # Проверяем указанный файл
        session_file = sys.argv[1]
        await check_session(session_file)

if __name__ == "__main__":
    asyncio.run(main())