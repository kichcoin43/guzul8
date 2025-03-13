import asyncio
import os
import sys
import logging
from telethon import TelegramClient
from anti_spam import AntiSpamThrottler

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('telegram_sender')

# Telegram API данные
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

async def send_messages(phone_number, recipients, message):
    """
    Отправляет сообщения списку получателей
    
    Args:
        phone_number (str): Номер телефона отправителя
        recipients (list): Список получателей (usernames или номера телефонов)
        message (str): Текст сообщения
    """
    logger.info(f"Отправка сообщений {len(recipients)} получателям")
    
    # Создаем сессию из существующего файла
    session_name = f"session_{phone_number.replace('+', '')}"
    
    # Создаем клиент
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    # Инициализируем анти-спам систему
    throttler = AntiSpamThrottler()
    
    try:
        # Подключаемся к Telegram
        await client.connect()
        
        if not await client.is_user_authorized():
            logger.error("Не авторизован в Telegram. Пожалуйста, сначала выполните вход через веб-интерфейс.")
            return False, 0, len(recipients)
        
        successful_count = 0
        failed_count = 0
        failed_recipients = {}
        
        for recipient in recipients:
            try:
                # Применяем умную задержку для избежания блокировки
                await throttler.smart_delay()
                
                try:
                    # Отправляем сообщение
                    entity = await client.get_entity(recipient)
                    await client.send_message(entity, message)
                    
                    # Отмечаем успешную отправку
                    throttler.record_success()
                    successful_count += 1
                    logger.info(f"Успешно отправлено {recipient}")
                
                except Exception as e:
                    throttler.record_failure()
                    failed_count += 1
                    failed_recipients[recipient] = str(e)
                    logger.error(f"Ошибка при отправке {recipient}: {str(e)}")
            
            except Exception as e:
                logger.error(f"Ошибка при обработке получателя {recipient}: {str(e)}")
                failed_count += 1
                failed_recipients[recipient] = str(e)
                
        success_rate = successful_count / len(recipients) if recipients else 0
        logger.info(f"Отправка завершена. Успешно: {successful_count}, Неудачно: {failed_count}, Успешность: {success_rate:.2%}")
        
        return True, successful_count, failed_count
        
    except Exception as e:
        logger.error(f"Критическая ошибка при отправке сообщений: {str(e)}")
        return False, 0, len(recipients)
        
    finally:
        await client.disconnect()


async def main():
    # Проверяем количество аргументов
    if len(sys.argv) < 3:
        print("Использование: python run_sender.py сообщение получатель1 получатель2 ...")
        return
    
    # Используем текущий номер телефона из сессии
    # Ищем любой файл сессии
    import glob
    session_files = glob.glob("session_*.session")
    
    if not session_files:
        print("Ошибка: Файл сессии не найден. Сначала выполните вход через веб-интерфейс.")
        return
    
    # Берем первый найденный файл сессии
    session_file = session_files[0]
    phone_number = session_file.replace("session_", "").replace(".session", "")
    phone_number = f"+{phone_number}"
    
    message = sys.argv[1]
    recipients = sys.argv[2:]
    
    print(f"Телефон отправителя: {phone_number}")
    print(f"Получатели ({len(recipients)}): {', '.join(recipients[:5])}{'...' if len(recipients) > 5 else ''}")
    print(f"Сообщение: {message[:50]}{'...' if len(message) > 50 else ''}")
    
    # Запускаем отправку
    result, successful, failed = await send_messages(phone_number, recipients, message)
    
    if result:
        print(f"Рассылка завершена. Успешно: {successful}, Неудачно: {failed}")
    else:
        print("Ошибка при выполнении рассылки")

if __name__ == "__main__":
    asyncio.run(main())