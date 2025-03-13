"""
АВТОМАТИЧЕСКАЯ ОТПРАВКА СООБЩЕНИЙ В TELEGRAM
============================================
Скрипт для автоматической отправки сообщений без интерактивного взаимодействия
"""

import asyncio
import os
import sys
import logging
import glob
from telethon import TelegramClient
from telethon.errors import FloodWaitError

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Telegram
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

async def send_batch(message, recipients, phone=None):
    """
    Отправка сообщений группе получателей
    
    Args:
        message (str): Сообщение для отправки
        recipients (list): Список получателей
        phone (str, optional): Номер телефона для инициализации сессии
    """
    # Создаем или используем существующую сессию
    session_file = None
    
    # Если нет телефона, ищем существующие сессии
    if not phone:
        existing_sessions = glob.glob('*.session')
        if existing_sessions:
            session_file = existing_sessions[0].replace('.session', '')
            logger.info(f"Используем существующую сессию: {session_file}")
        else:
            # Создаем временную сессию
            session_file = "temp_session"
            logger.info("Создаем временную сессию")
    else:
        # Создаем сессию для указанного телефона
        session_file = f"session_{phone.replace('+', '')}"
        logger.info(f"Используем сессию для номера {phone}")
    
    # Создаем клиент Telegram
    client = TelegramClient(session_file, API_ID, API_HASH)
    
    try:
        # Подключаемся
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            if not phone:
                logger.error("Ошибка: требуется авторизация, но номер телефона не указан")
                return 0, len(recipients)
            
            # Запрашиваем код
            await client.send_code_request(phone)
            logger.info(f"Код подтверждения отправлен на номер {phone}")
            
            # Требуется интерактивная авторизация - возвращаем ошибку
            logger.error("Требуется авторизация. Запустите веб-приложение и войдите в аккаунт")
            return 0, len(recipients)
        
        # Отправка сообщений
        successful = 0
        failed = 0
        
        for i, recipient in enumerate(recipients, 1):
            try:
                # Удаляем лишние пробелы
                recipient = recipient.strip()
                if not recipient:
                    continue
                
                # Отправляем сообщение
                logger.info(f"[{i}/{len(recipients)}] Отправка: {recipient}")
                await client.send_message(recipient, message)
                
                # Увеличиваем счетчик
                successful += 1
                logger.info(f"✓ Отправлено: {recipient}")
                
                # Пауза между отправками
                if i < len(recipients):
                    import random
                    await asyncio.sleep(random.uniform(1.0, 3.0))
                
            except FloodWaitError as e:
                # Обрабатываем ограничение частоты
                wait_time = e.seconds
                
                if wait_time <= 30:
                    logger.warning(f"⚠️ Telegram требует паузу {wait_time} сек. Ожидаем...")
                    await asyncio.sleep(wait_time)
                    
                    # Повторная попытка
                    try:
                        await client.send_message(recipient, message)
                        successful += 1
                        logger.info(f"✓ Отправлено после паузы: {recipient}")
                        continue
                    except Exception as e2:
                        logger.error(f"✗ Повторная попытка не удалась: {str(e2)}")
                else:
                    logger.error(f"✗ Слишком долгая пауза {wait_time} сек. Пропускаем.")
                
                failed += 1
                
            except Exception as e:
                # Другие ошибки
                failed += 1
                logger.error(f"✗ Ошибка: {str(e)}")
                
                # Пауза после ошибки
                await asyncio.sleep(2)
        
        return successful, failed
        
    finally:
        # Закрываем соединение
        await client.disconnect()

async def main():
    # Проверяем аргументы
    if len(sys.argv) < 3:
        print("Использование:")
        print("  1) python auto_send.py 'сообщение' @username1 @username2 ...")
        print("  2) python auto_send.py 'сообщение' -f recipients.txt")
        print("  3) python auto_send.py 'сообщение' -f recipients.txt -p +79001234567")
        print("")
        print("Параметры:")
        print("  -f файл.txt     Загрузить получателей из файла")
        print("  -p телефон      Использовать указанный номер телефона для входа")
        return
    
    # Получаем текст сообщения
    message = sys.argv[1]
    
    # Получатели и телефон
    recipients = []
    phone = None
    
    # Разбор аргументов
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '-f' and i+1 < len(sys.argv):
            # Загрузка получателей из файла
            file_path = sys.argv[i+1]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    recipients = [line.strip() for line in f if line.strip()]
                logger.info(f"Загружено {len(recipients)} получателей из {file_path}")
            except Exception as e:
                logger.error(f"Ошибка при чтении файла {file_path}: {str(e)}")
            i += 2
            
        elif arg == '-p' and i+1 < len(sys.argv):
            # Номер телефона
            phone = sys.argv[i+1]
            logger.info(f"Используем номер телефона: {phone}")
            i += 2
            
        else:
            # Обычный получатель
            recipients.append(arg)
            i += 1
    
    # Проверяем наличие получателей
    if not recipients:
        logger.error("Ошибка: не указаны получатели")
        return
    
    # Выводим информацию
    logger.info(f"Сообщение для отправки: {message[:50]}{'...' if len(message) > 50 else ''}")
    logger.info(f"Количество получателей: {len(recipients)}")
    
    # Запускаем отправку
    successful, failed = await send_batch(message, recipients, phone)
    
    # Выводим итоги
    logger.info("\n===== РЕЗУЛЬТАТЫ =====")
    logger.info(f"Всего получателей: {len(recipients)}")
    logger.info(f"Успешно отправлено: {successful}")
    logger.info(f"Не удалось отправить: {failed}")
    if len(recipients) > 0:
        logger.info(f"Процент успеха: {successful / len(recipients) * 100:.1f}%")

# Запускаем скрипт
if __name__ == "__main__":
    asyncio.run(main())