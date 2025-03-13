"""
СРОЧНАЯ РАССЫЛКА TELEGRAM
========================
Скрипт для срочной рассылки, который решает проблему истекающих кодов
"""

import asyncio
import os
import sys
import logging
import time
from telethon import TelegramClient, functions, types
from telethon.errors import FloodWaitError

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константы - не трогать!
API_ID = 1079592
API_HASH = "4b3c8eeb47a62ecc941e61907f1a7bf0"

async def login_bot():
    """Альтернативный вход через бота"""
    session_name = "direct_session"
    
    logger.info("Создаю новую сессию напрямую...")
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            # Запрашиваем телефон
            phone = input("Введите номер телефона (с '+', например +7...): ")
            
            # Отправляем запрос кода
            await client.send_code_request(phone)
            logger.info(f"Код отправлен на номер {phone}")
            
            # Запрашиваем код
            code = input("Введите код из Telegram (5 цифр): ")
            
            try:
                # Пытаемся войти
                await client.sign_in(phone=phone, code=code)
                logger.info("Успешный вход!")
            except Exception as e:
                if "password" in str(e) or "2fa" in str(e).lower():
                    # Двухфакторная аутентификация
                    password = input("Требуется пароль 2FA: ")
                    await client.sign_in(password=password)
                    logger.info("Успешный вход с 2FA!")
                else:
                    raise
        
        # Выводим информацию о пользователе
        me = await client.get_me()
        logger.info(f"Вход выполнен как: {me.first_name} {me.last_name or ''} (@{me.username or ''})")
        
        return client
    except Exception as e:
        logger.error(f"Ошибка при входе: {str(e)}")
        if client:
            await client.disconnect()
        return None

async def send_messages(client, message, recipients):
    """Отправка сообщений"""
    successful = 0
    failed = 0
    failed_details = {}
    
    for i, recipient in enumerate(recipients, 1):
        # Очищаем получателя от пробелов
        recipient = recipient.strip()
        if not recipient:
            continue
        
        # Выводим прогресс
        logger.info(f"[{i}/{len(recipients)}] Отправка для {recipient}")
        
        try:
            # Отправляем сообщение
            await client.send_message(recipient, message)
            
            # Отмечаем успех
            successful += 1
            logger.info(f"✓ Успешно отправлено: {recipient}")
            
            # Умная задержка для избежания блокировки
            delay = min(3, 1 + (successful / 10))
            if i < len(recipients):
                await asyncio.sleep(delay)
            
        except FloodWaitError as e:
            # Обрабатываем ограничение частоты
            wait_time = e.seconds
            
            if wait_time <= 30:
                logger.warning(f"⚠️ Требуется пауза {wait_time} сек...")
                await asyncio.sleep(wait_time)
                
                # Повторная попытка
                try:
                    await client.send_message(recipient, message)
                    successful += 1
                    logger.info(f"✓ Успешно отправлено после паузы: {recipient}")
                    continue
                except Exception as e2:
                    logger.error(f"✗ Ошибка после паузы: {str(e2)}")
            else:
                logger.error(f"✗ Слишком долгая пауза ({wait_time} сек), пропускаем")
            
            failed += 1
            failed_details[recipient] = f"FloodWaitError: {wait_time} сек"
            
        except Exception as e:
            # Другие ошибки
            failed += 1
            failed_details[recipient] = str(e)
            logger.error(f"✗ Ошибка отправки {recipient}: {str(e)}")
            
            # Пауза после ошибки
            await asyncio.sleep(2)
    
    # Выводим статистику
    logger.info("\n===== РЕЗУЛЬТАТЫ РАССЫЛКИ =====")
    logger.info(f"Всего получателей: {len(recipients)}")
    logger.info(f"Успешно отправлено: {successful}")
    logger.info(f"Не удалось отправить: {failed}")
    
    if len(recipients) > 0:
        success_rate = successful / len(recipients) * 100
        logger.info(f"Процент успеха: {success_rate:.1f}%")
    
    # Выводим детали ошибок
    if failed_details:
        logger.info("\nПолучатели с ошибками:")
        for i, (recipient, error) in enumerate(list(failed_details.items())[:5], 1):
            logger.info(f"  {i}. {recipient}: {error}")
        
        if len(failed_details) > 5:
            logger.info(f"  ... и еще {len(failed_details) - 5} получателей")
    
    return successful, failed

async def main():
    # Проверяем аргументы
    if len(sys.argv) < 3:
        print("""
СРОЧНАЯ РАССЫЛКА TELEGRAM
========================
Использование:
  python СРОЧНАЯ_РАССЫЛКА.py "текст сообщения" @username1 @username2 ...
  python СРОЧНАЯ_РАССЫЛКА.py "текст сообщения" -f recipients.txt

Параметры:
  -f file.txt     загрузить получателей из файла
  -y              подтвердить отправку автоматически
""")
        return
    
    # Получаем текст сообщения
    message = sys.argv[1]
    
    # Обрабатываем аргументы
    recipients = []
    auto_confirm = False
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '-f' and i+1 < len(sys.argv):
            # Загрузка из файла
            file_path = sys.argv[i+1]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded = [line.strip() for line in f if line.strip()]
                    recipients.extend(loaded)
                logger.info(f"Загружено {len(loaded)} получателей из {file_path}")
            except Exception as e:
                logger.error(f"Ошибка при чтении файла {file_path}: {str(e)}")
            i += 2
            
        elif arg == '-y':
            # Автоподтверждение
            auto_confirm = True
            i += 1
            
        else:
            # Обычный получатель
            recipients.append(arg)
            i += 1
    
    # Проверяем наличие получателей
    if not recipients:
        logger.error("Не указаны получатели!")
        return
    
    # Выводим информацию
    logger.info("\n===== СРОЧНАЯ РАССЫЛКА TELEGRAM =====")
    logger.info(f"Сообщение: {message[:50]}{'...' if len(message) > 50 else ''}")
    logger.info(f"Количество получателей: {len(recipients)}")
    
    # Показываем получателей
    if len(recipients) <= 5:
        for i, recipient in enumerate(recipients, 1):
            logger.info(f"  {i}. {recipient}")
    else:
        for i, recipient in enumerate(recipients[:5], 1):
            logger.info(f"  {i}. {recipient}")
        logger.info(f"  ... и еще {len(recipients) - 5}")
    
    # Подтверждение
    if not auto_confirm:
        confirm = input("\nНачать отправку сообщений? (y/n): ").lower()
        if not (confirm == 'y' or confirm == 'yes' or confirm == 'да'):
            logger.info("Отправка отменена.")
            return
    
    # Авторизация и отправка
    client = await login_bot()
    
    if client:
        try:
            # Отправляем сообщения
            await send_messages(client, message, recipients)
        finally:
            # Закрываем соединение
            await client.disconnect()
    else:
        logger.error("Не удалось выполнить вход. Рассылка отменена.")

# Запуск программы
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nОтправка прервана пользователем.")
    
    # Задержка чтобы увидеть финальные логи
    input("\nНажмите Enter для выхода...")