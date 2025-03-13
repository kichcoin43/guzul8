"""
ГОТОВЫЙ ОТПРАВЩИК СООБЩЕНИЙ В TELEGRAM
=====================================

ИСПОЛЬЗОВАНИЕ:
   python ГОТОВО-ЗАПУСТИТЬ-ЭТО.py "Текст сообщения" @username1 @username2
   python ГОТОВО-ЗАПУСТИТЬ-ЭТО.py "Текст сообщения" -f test_recipients.txt

ПАРАМЕТРЫ:
   -f file.txt - загрузить получателей из файла
   -y - автоматический запуск без подтверждения
"""

import os
import sys
import asyncio
import logging
from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError, PhoneCodeExpiredError, PhoneCodeInvalidError, 
    SessionPasswordNeededError
)
import time
import random

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константы для API - не менять!
API_ID = 1079592
API_HASH = "4b3c8eeb47a62ecc941e61907f1a7bf0"

# Константа для автоподтверждения
AUTO_CONFIRM = False

# Файл сессии по умолчанию
DEFAULT_SESSION_FILE = "mega_session"

# Интерактивная функция для ввода данных
def prompt(message):
    """Запрашивает ввод от пользователя с обработкой ошибок"""
    print(message, end='', flush=True)
    try:
        return input()
    except EOFError:
        print("\nОшибка ввода. Используется пустая строка.")
        return ""

async def send_messages_now(message, recipients, session_file='mega_session'):
    """Отправка сообщений получателям"""
    
    # Счетчики для статистики
    sent_count = 0
    error_count = 0
    error_details = {}
    
    # Создаем клиент с указанным файлом сессии
    client = TelegramClient(session_file, API_ID, API_HASH)
    
    try:
        # Подключаемся к API
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            logger.info("Сессия не найдена, требуется авторизация...")
            
            # Запрашиваем телефон
            phone = prompt("Введите номер телефона (с '+', например +79001234567): ")
            if not phone:
                logger.error("Номер телефона не введен.")
                return 0, len(recipients)
                
            # Отправляем запрос на код
            sent_code = await client.send_code_request(phone)
            
            # Запрашиваем код подтверждения
            code = prompt("Введите код подтверждения из Telegram: ")
            if not code:
                logger.error("Код не введен.")
                return 0, len(recipients)
            
            try:
                # Пытаемся войти с кодом
                await client.sign_in(phone=phone, code=code)
                logger.info("Успешный вход!")
                
            except PhoneCodeInvalidError:
                logger.error("Неверный код подтверждения!")
                return 0, len(recipients)
                
            except PhoneCodeExpiredError:
                logger.error("Код подтверждения истек!")
                # Автоматически запрашиваем новый
                sent_code = await client.send_code_request(phone)
                code = prompt("Отправлен новый код. Введите его: ")
                if not code:
                    logger.error("Код не введен.")
                    return 0, len(recipients)
                
                try:
                    await client.sign_in(phone=phone, code=code)
                    logger.info("Успешный вход с новым кодом!")
                except Exception as e:
                    logger.error(f"Ошибка при входе: {str(e)}")
                    return 0, len(recipients)
                
            except SessionPasswordNeededError:
                # Необходима двухфакторная аутентификация
                password = prompt("Требуется пароль двухфакторной аутентификации: ")
                await client.sign_in(password=password)
                logger.info("Успешный вход с двухфакторной аутентификацией!")
                
            except Exception as e:
                logger.error(f"Ошибка при входе: {str(e)}")
                return 0, len(recipients)
        
        # Получаем информацию о пользователе
        me = await client.get_me()
        logger.info(f"Авторизован как: {me.first_name} {me.last_name or ''} (@{me.username or 'нет юзернейма'})")
        
        # Отправляем сообщения
        logger.info(f"\n===== НАЧАЛО ОТПРАВКИ СООБЩЕНИЙ =====")
        logger.info(f"Всего получателей: {len(recipients)}")
        
        for i, recipient in enumerate(recipients, 1):
            # Выводим прогресс
            logger.info(f"[{i}/{len(recipients)}] Отправка сообщения для {recipient}...")
            
            try:
                # Отправляем сообщение
                await client.send_message(recipient, message)
                
                # Отмечаем успех
                sent_count += 1
                logger.info(f"✓ Успешно отправлено: {recipient}")
                
                # Делаем умную паузу
                if i < len(recipients):
                    delay = min(2.5, 1 + (sent_count / 10))
                    delay += random.uniform(0.5, 1.5)  # Добавляем случайность
                    
                    # Корректируем если много успешных
                    if sent_count > 10:
                        delay += 0.5
                    
                    logger.debug(f"Пауза {delay:.1f} сек...")
                    await asyncio.sleep(delay)
                
            except FloodWaitError as e:
                # Обрабатываем ограничение частоты
                wait_time = e.seconds
                
                if wait_time <= 30:
                    # Короткое ожидание, можем подождать
                    logger.warning(f"⚠️ Telegram требует паузу {wait_time} сек...")
                    await asyncio.sleep(wait_time)
                    
                    # Пробуем еще раз после паузы
                    try:
                        await client.send_message(recipient, message)
                        sent_count += 1
                        logger.info(f"✓ Успешно отправлено после паузы: {recipient}")
                        continue
                    except Exception as e2:
                        logger.error(f"✗ Ошибка после паузы: {str(e2)}")
                else:
                    logger.error(f"✗ Требуется слишком долгая пауза ({wait_time} сек), пропускаем получателя")
                
                # Считаем как ошибку
                error_count += 1
                error_details[recipient] = f"FloodWaitError: {wait_time} сек"
                
            except Exception as e:
                # Прочие ошибки
                error_count += 1
                error_details[recipient] = str(e)
                logger.error(f"✗ Ошибка отправки для {recipient}: {str(e)}")
                
                # Короткая пауза после ошибки
                await asyncio.sleep(2)
        
        # Выводим итоги
        logger.info("\n===== ИТОГИ РАССЫЛКИ =====")
        logger.info(f"Всего получателей: {len(recipients)}")
        logger.info(f"Успешно отправлено: {sent_count}")
        logger.info(f"Не удалось отправить: {error_count}")
        
        if error_details:
            logger.info("\nОшибки отправки:")
            for recipient, error in list(error_details.items())[:5]:
                logger.info(f"  {recipient}: {error}")
            
            if len(error_details) > 5:
                logger.info(f"  ... и еще {len(error_details) - 5} ошибок")
        
        return sent_count, error_count
        
    finally:
        # Закрываем соединение
        await client.disconnect()

async def main():
    global AUTO_CONFIRM
    
    # Анализируем аргументы
    if len(sys.argv) < 2:
        logger.info(__doc__)
        return
    
    # Получаем сообщение
    message = sys.argv[1]
    
    # Получаем список получателей
    recipients = []
    recipients_file = None
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '-f' and i+1 < len(sys.argv):
            # Загрузка из файла
            recipients_file = sys.argv[i+1]
            i += 2
        elif arg == '-y':
            # Автоматическое подтверждение
            AUTO_CONFIRM = True
            i += 1
        else:
            # Обычный получатель
            recipients.append(arg)
            i += 1
    
    # Загружаем получателей из файла, если указан
    if recipients_file:
        try:
            with open(recipients_file, 'r', encoding='utf-8') as f:
                file_recipients = [line.strip() for line in f if line.strip()]
                recipients.extend(file_recipients)
            logger.info(f"Загружено {len(file_recipients)} получателей из файла {recipients_file}")
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {recipients_file}: {str(e)}")
    
    # Проверяем наличие сообщения
    if not message:
        logger.error("Сообщение не указано!")
        return
    
    # Проверяем наличие получателей
    if not recipients:
        # Если получатели не указаны, пробуем загрузить из файла по умолчанию
        default_file = "test_recipients.txt"
        try:
            with open(default_file, 'r', encoding='utf-8') as f:
                recipients = [line.strip() for line in f if line.strip()]
            logger.info(f"Загружено {len(recipients)} получателей из файла по умолчанию")
        except:
            logger.error("Не указаны получатели и не найден файл по умолчанию!")
            return
    
    # Выводим информацию
    logger.info(f"\n===== ИНФОРМАЦИЯ О РАССЫЛКЕ =====")
    logger.info(f"Текст сообщения: {message[:50]}{'...' if len(message) > 50 else ''}")
    logger.info(f"Количество получателей: {len(recipients)}")
    
    # Показываем первых получателей
    if len(recipients) <= 5:
        for i, recipient in enumerate(recipients, 1):
            logger.info(f"  {i}. {recipient}")
    else:
        for i, recipient in enumerate(recipients[:5], 1):
            logger.info(f"  {i}. {recipient}")
        logger.info(f"  ... и еще {len(recipients) - 5}")
    
    # Запрашиваем подтверждение, если не указан флаг -y
    if not AUTO_CONFIRM:
        confirm = prompt("\nНачать отправку сообщений? (y/n): ").lower()
        if not confirm.startswith('y') and not confirm.startswith('д'):
            logger.info("Отправка отменена.")
            return
    
    # Отправляем сообщения
    sent, failed = await send_messages_now(message, recipients, DEFAULT_SESSION_FILE)
    
    # Выводим процент успеха
    if len(recipients) > 0:
        success_rate = sent / len(recipients) * 100
        logger.info(f"Процент успеха: {success_rate:.1f}%")

# Запуск программы
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nПрограмма прервана пользователем.")
    
    # Задержка для просмотра результатов
    try:
        input("\nНажмите Enter для выхода...")
    except:
        pass