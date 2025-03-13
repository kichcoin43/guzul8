#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
АВТОМАТИЧЕСКАЯ РАССЫЛКА СООБЩЕНИЙ В TELEGRAM
===========================================

ИСПОЛЬЗОВАНИЕ:
   python ЗАПУСТИТЬ_РАССЫЛКУ.py "Текст сообщения" +79001234567 12345 [пароль_2FA]
   python ЗАПУСТИТЬ_РАССЫЛКУ.py "Текст сообщения" +79001234567 12345 -f получатели.txt

ПАРАМЕТРЫ:
   1-й параметр: текст сообщения
   2-й параметр: номер телефона с '+' (например, +79001234567)
   3-й параметр: код подтверждения из Telegram
   4-й параметр (опционально): пароль 2FA или '-f файл_получателей.txt'
   
   Дополнительные опции:
   -f файл.txt - загрузить получателей из файла
   --delay=N   - установить базовую задержку между сообщениями (в секундах)
"""

import os
import sys
import time
import random
import logging
from telethon.sync import TelegramClient
from telethon.errors import (
    PhoneCodeExpiredError, PhoneCodeInvalidError, 
    SessionPasswordNeededError, FloodWaitError
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# API константы для Telegram
API_ID = 1079592
API_HASH = "4b3c8eeb47a62ecc941e61907f1a7bf0"

# Файл с получателями по умолчанию
DEFAULT_RECIPIENTS_FILE = "test_recipients.txt"

# Имя файла сессии
SESSION_NAME = "telegram_session"

def load_recipients(file_path):
    """Загрузка получателей из файла"""
    recipients = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                recipient = line.strip()
                if recipient:
                    recipients.append(recipient)
        logger.info(f"Загружено {len(recipients)} получателей из {file_path}")
        return recipients
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
        return []

def get_recipients():
    """Получение списка получателей из файла по умолчанию"""
    if os.path.exists(DEFAULT_RECIPIENTS_FILE):
        return load_recipients(DEFAULT_RECIPIENTS_FILE)
    else:
        logger.error(f"Файл получателей по умолчанию не найден: {DEFAULT_RECIPIENTS_FILE}")
        return []

def process_command_line():
    """Обработка аргументов командной строки"""
    # Показываем справку, если недостаточно аргументов
    if len(sys.argv) < 4:
        print(__doc__)
        return None
    
    # Получаем основные параметры
    message = sys.argv[1]
    phone = sys.argv[2]
    code = sys.argv[3]
    
    # Устанавливаем значения по умолчанию
    password = None
    recipients = []
    recipients_file = None
    delay = 2.0
    
    # Обрабатываем дополнительные аргументы
    for i in range(4, len(sys.argv)):
        arg = sys.argv[i]
        
        if arg.startswith('--delay='):
            try:
                delay = float(arg.split('=')[1])
            except:
                logger.warning(f"Неверный формат задержки: {arg}, используется значение по умолчанию")
                
        elif arg == '-f' and i+1 < len(sys.argv):
            recipients_file = sys.argv[i+1]
            i += 1
            
        elif not arg.startswith('-') and not password:
            password = arg
    
    # Загружаем получателей из файла, если указан
    if recipients_file:
        file_recipients = load_recipients(recipients_file)
        recipients.extend(file_recipients)
    
    # Если получателей нет, пробуем использовать файл по умолчанию
    if not recipients:
        recipients = get_recipients()
    
    # Проверяем наличие основных параметров
    if not message or not message.strip():
        logger.error("Сообщение не может быть пустым")
        return None
        
    if not phone or not phone.startswith('+'):
        logger.error("Номер телефона должен начинаться с '+' (например, +79001234567)")
        return None
        
    if not code or not code.strip():
        logger.error("Код подтверждения не может быть пустым")
        return None
        
    if not recipients:
        logger.error("Список получателей пуст")
        return None
    
    # Возвращаем параметры в виде словаря
    return {
        'message': message,
        'phone': phone,
        'code': code,
        'password': password,
        'recipients': recipients,
        'delay': delay
    }

async def login_telegram(phone, code, password=None):
    """
    Вход в аккаунт Telegram с использованием указанных параметров
    
    Args:
        phone (str): Номер телефона
        code (str): Код подтверждения
        password (str, optional): Пароль двухфакторной аутентификации
        
    Returns:
        TelegramClient: Клиент Telegram или None в случае ошибки
    """
    client = None
    
    try:
        # Создаем и подключаем клиент
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.connect()
        
        # Если уже авторизованы, просто возвращаем клиент
        if await client.is_user_authorized():
            logger.info("Уже авторизован в Telegram")
            return client
            
        # Пытаемся войти с кодом
        try:
            logger.info(f"Вход в Telegram с номером {phone}")
            await client.sign_in(phone=phone, code=code)
            logger.info("Успешный вход!")
            return client
            
        except PhoneCodeInvalidError:
            logger.error("Введен неверный код подтверждения")
            await client.disconnect()
            return None
            
        except PhoneCodeExpiredError:
            logger.error("Код подтверждения истек")
            
            # Пытаемся запросить новый код и предупреждаем пользователя
            try:
                sent_code = await client.send_code_request(phone)
                new_code_hash = sent_code.phone_code_hash
                logger.info(f"Запрошен новый код. Запустите программу снова с новым кодом")
                logger.info(f"Новый хеш кода: {new_code_hash}")
            except Exception as e:
                logger.error(f"Ошибка при запросе нового кода: {e}")
                
            await client.disconnect()
            return None
            
        except SessionPasswordNeededError:
            # Требуется двухфакторная аутентификация
            logger.info("Требуется пароль двухфакторной аутентификации")
            
            if not password:
                logger.error("Пароль 2FA не указан, но требуется для входа")
                await client.disconnect()
                return None
                
            try:
                # Пытаемся войти с паролем
                await client.sign_in(password=password)
                logger.info("Успешный вход с двухфакторной аутентификацией!")
                return client
            except Exception as e:
                logger.error(f"Ошибка при входе с паролем 2FA: {e}")
                await client.disconnect()
                return None
                
    except Exception as e:
        logger.error(f"Ошибка при подключении к Telegram: {e}")
        if client:
            await client.disconnect()
        return None

async def send_messages(client, recipients, message, base_delay=2.0):
    """
    Отправка сообщений списку получателей
    
    Args:
        client: Клиент Telegram
        recipients (list): Список получателей
        message (str): Текст сообщения
        base_delay (float): Базовая задержка между сообщениями
        
    Returns:
        tuple: (успешных, неуспешных)
    """
    if not client or not recipients or not message:
        return 0, 0
    
    # Счетчики
    successful = 0
    failed = 0
    errors = {}
    
    # Получаем информацию о пользователе
    try:
        me = await client.get_me()
        logger.info(f"Отправка от имени: {me.first_name} {me.last_name or ''} (@{me.username or 'нет'})")
    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе: {e}")
    
    # Отправляем сообщения
    logger.info(f"\n===== НАЧАЛО ОТПРАВКИ =====")
    logger.info(f"Всего получателей: {len(recipients)}")
    
    start_time = time.time()
    
    for i, recipient in enumerate(recipients, 1):
        # Очищаем имя получателя
        recipient = recipient.strip()
        if not recipient:
            continue
        
        # Прогресс
        logger.info(f"[{i}/{len(recipients)}] Отправка для {recipient}...")
        
        try:
            # Отправляем сообщение
            await client.send_message(recipient, message)
            
            # Учитываем успех
            successful += 1
            logger.info(f"✓ Успешно отправлено: {recipient}")
            
            # Умная пауза между сообщениями
            if i < len(recipients):
                # Базовая пауза
                delay = base_delay
                
                # Увеличиваем паузу с ростом количества сообщений
                if successful > 10:
                    delay += 0.5
                if successful > 20:
                    delay += 0.5
                    
                # Добавляем случайность для обхода анти-спам систем
                delay += random.uniform(0.5, 1.5)
                
                logger.debug(f"Пауза {delay:.1f} сек...")
                await client.loop.run_in_executor(None, time.sleep, delay)
                
        except FloodWaitError as e:
            # Ограничение частоты
            wait_time = e.seconds
            
            if wait_time <= 30:
                # Короткое ожидание, можем подождать
                logger.warning(f"⚠️ Telegram требует паузу {wait_time} сек...")
                await client.loop.run_in_executor(None, time.sleep, wait_time)
                
                # Пробуем еще раз
                try:
                    await client.send_message(recipient, message)
                    successful += 1
                    logger.info(f"✓ Успешно отправлено после паузы: {recipient}")
                    continue
                except Exception as e2:
                    logger.error(f"✗ Ошибка после паузы: {e2}")
            else:
                logger.error(f"✗ Требуется слишком долгая пауза ({wait_time} сек)")
            
            # Учитываем ошибку
            failed += 1
            errors[recipient] = f"FloodWaitError: {wait_time} сек"
            
        except Exception as e:
            # Другие ошибки
            failed += 1
            errors[recipient] = str(e)
            logger.error(f"✗ Ошибка отправки для {recipient}: {e}")
            
            # Короткая пауза после ошибки
            await client.loop.run_in_executor(None, time.sleep, 2)
    
    # Вычисляем общее время
    total_time = time.time() - start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    # Выводим статистику
    logger.info("\n===== РЕЗУЛЬТАТЫ ОТПРАВКИ =====")
    logger.info(f"Всего получателей: {len(recipients)}")
    logger.info(f"Успешно отправлено: {successful}")
    logger.info(f"Не удалось отправить: {failed}")
    logger.info(f"Время отправки: {minutes} мин {seconds} сек")
    
    # Процент успешных отправок
    if recipients:
        success_rate = (successful / len(recipients)) * 100
        logger.info(f"Процент успеха: {success_rate:.1f}%")
    
    # Детали ошибок
    if errors:
        logger.info("\nОшибки отправки:")
        for i, (recipient, error) in enumerate(list(errors.items())[:5], 1):
            logger.info(f"  {i}. {recipient}: {error}")
        
        if len(errors) > 5:
            logger.info(f"  ... и еще {len(errors) - 5} ошибок")
    
    return successful, failed

async def main():
    """Основная функция программы"""
    
    # Получаем параметры из командной строки
    params = process_command_line()
    if not params:
        return
    
    # Выводим информацию
    logger.info("\n===== ИНФОРМАЦИЯ О РАССЫЛКЕ =====")
    logger.info(f"Сообщение: {params['message'][:50]}{'...' if len(params['message']) > 50 else ''}")
    logger.info(f"Телефон: {params['phone']}")
    logger.info(f"Получателей: {len(params['recipients'])}")
    
    # Показываем первых получателей
    if len(params['recipients']) <= 5:
        for i, recipient in enumerate(params['recipients'], 1):
            logger.info(f"  {i}. {recipient}")
    else:
        for i, recipient in enumerate(params['recipients'][:5], 1):
            logger.info(f"  {i}. {recipient}")
        logger.info(f"  ... и еще {len(params['recipients']) - 5}")
    
    # Авторизация в Telegram
    client = await login_telegram(
        params['phone'], 
        params['code'], 
        params['password']
    )
    
    # Проверяем успешность входа
    if not client:
        logger.error("Не удалось войти в Telegram")
        return
    
    try:
        # Отправляем сообщения
        await send_messages(
            client, 
            params['recipients'], 
            params['message'], 
            params['delay']
        )
    except KeyboardInterrupt:
        logger.info("\nОтправка прервана пользователем")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
    finally:
        # Отключаемся от API
        if client:
            await client.disconnect()
            logger.info("Отключено от Telegram API")

if __name__ == "__main__":
    import asyncio
    
    try:
        # Запускаем основную функцию
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nПрограмма прервана пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    
    # Задержка в конце для просмотра результатов
    print("\nНажмите Enter для выхода...")