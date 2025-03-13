import os
import sys
import logging
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError, PhoneCodeInvalidError
from telethon.tl.types import InputPhoneContact
from telethon.tl.functions.contacts import ImportContactsRequest

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Тестовое сообщение
TEST_MESSAGE = "Это тестовое сообщение от системы проверки API Telegram."

# Путь к сессии
SESSION_FILE = "test_session"  # Имя файла для сессии

# Прямое тестирование отправки сообщений
async def test_telegram_api(phone_number=None, test_recipient=None):
    """
    Тестирует подключение к API Telegram и отправку сообщения
    
    Args:
        phone_number (str): Номер телефона для входа
        test_recipient (str): Получатель тестового сообщения (@username или телефон)
    """
    if not API_ID or not API_HASH:
        logger.error("API_ID или API_HASH не найдены в переменных окружения")
        return False
        
    logger.info(f"Тестирование API с API_ID={API_ID}")
    
    # Создаем клиент
    client = TelegramClient(SESSION_FILE, int(API_ID), API_HASH)
    
    try:
        # Подключаемся
        logger.info("Подключение к Telegram...")
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            if not phone_number:
                logger.error("Требуется номер телефона для авторизации")
                return False
                
            logger.info(f"Отправка кода на номер {phone_number}...")
            sent = await client.send_code_request(phone_number)
            
            # Запрашиваем код подтверждения
            verification_code = input("Введите код подтверждения: ")
            
            # Входим с кодом
            try:
                await client.sign_in(phone_number, verification_code, phone_code_hash=sent.phone_code_hash)
                logger.info("Авторизация успешна")
            except (PhoneCodeInvalidError, SessionPasswordNeededError) as e:
                logger.error(f"Ошибка при входе: {str(e)}")
                return False
        else:
            logger.info("Уже авторизован")
        
        # Отправка тестового сообщения
        if test_recipient:
            try:
                logger.info(f"Получение информации о пользователе {test_recipient}...")
                
                # Для телефонных номеров
                if test_recipient.startswith('+'):
                    logger.info(f"Получатель - телефонный номер: {test_recipient}")
                    
                    # Создаем контакт для импорта
                    contact = InputPhoneContact(
                        client_id=0,
                        phone=test_recipient,
                        first_name="TestContact",
                        last_name=""
                    )
                    
                    # Импортируем контакт
                    import_result = await client(ImportContactsRequest([contact]))
                    logger.info(f"Результат импорта контакта: {import_result}")
                    
                    if import_result.users:
                        entity = import_result.users[0]
                        logger.info(f"Найден пользователь для номера {test_recipient}")
                    else:
                        logger.warning(f"Пользователь не найден для номера {test_recipient}, пробуем прямую отправку")
                        entity = test_recipient
                else:
                    # Для имен пользователей
                    if not test_recipient.startswith('@'):
                        test_recipient = '@' + test_recipient
                    
                    entity = await client.get_entity(test_recipient)
                    logger.info(f"Найден пользователь: {entity}")
                
                # Отправляем сообщение
                logger.info(f"Отправка тестового сообщения пользователю {test_recipient}...")
                result = await client.send_message(entity, TEST_MESSAGE)
                logger.info(f"Сообщение отправлено, результат: {result}")
                return True
                
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения: {str(e)}")
                return False
        else:
            logger.info("Тест подключения успешен, но получатель не указан для тестового сообщения")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка при тестировании API: {str(e)}")
        return False
    finally:
        await client.disconnect()
        logger.info("Отключение от Telegram API")

async def main():
    """Основная функция для запуска тестов"""
    # Проверяем аргументы командной строки
    if len(sys.argv) < 2:
        print("Использование: python test_telegram_api.py <phone_number> [test_recipient]")
        return
        
    phone_number = sys.argv[1]
    test_recipient = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = await test_telegram_api(phone_number, test_recipient)
    if result:
        print("Тест успешно завершен")
    else:
        print("Тест завершился с ошибкой")

if __name__ == "__main__":
    asyncio.run(main())