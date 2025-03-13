#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ПРОСТОЙ ОТПРАВЩИК СООБЩЕНИЙ TELEGRAM
===================================

Этот скрипт является максимально простой версией отправщика сообщений,
который принимает все необходимые параметры через командную строку, 
избегая необходимости в интерактивном вводе.

ИСПОЛЬЗОВАНИЕ:
  python запустить.py "Текст сообщения" +79001234567 12345
  
АРГУМЕНТЫ:
  1. Текст сообщения (в кавычках)
  2. Номер телефона (с + в начале)
  3. Код подтверждения из Telegram
  4. (опционально) Пароль двухфакторной аутентификации
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

# Константы для API
API_ID = 1079592
API_HASH = "4b3c8eeb47a62ecc941e61907f1a7bf0"

# Проверка аргументов
if len(sys.argv) < 4:
    print(__doc__)
    sys.exit(1)

# Получаем аргументы
MESSAGE = sys.argv[1]
PHONE = sys.argv[2]
CODE = sys.argv[3]
PASSWORD = sys.argv[4] if len(sys.argv) > 4 else None

# Файл с получателями
RECIPIENTS_FILE = "test_recipients.txt"

def load_recipients():
    """Загрузка списка получателей из файла"""
    try:
        with open(RECIPIENTS_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Ошибка загрузки получателей: {e}")
        return []

def main():
    """Основная функция программы"""
    # Загружаем получателей
    recipients = load_recipients()
    if not recipients:
        logger.error(f"Не удалось загрузить получателей из {RECIPIENTS_FILE}")
        return
    
    # Выводим информацию
    logger.info(f"Отправка сообщения: {MESSAGE[:50]}{'...' if len(MESSAGE) > 50 else ''}")
    logger.info(f"Телефон: {PHONE}")
    logger.info(f"Получателей: {len(recipients)}")
    
    # Создаем клиент Telegram
    client = TelegramClient('session', API_ID, API_HASH)
    
    try:
        # Подключаемся
        client.connect()
        
        # Проверяем авторизацию
        if not client.is_user_authorized():
            # Пытаемся войти
            try:
                client.sign_in(phone=PHONE, code=CODE)
                logger.info("Успешный вход!")
            except SessionPasswordNeededError:
                # Требуется двухфакторная аутентификация
                if not PASSWORD:
                    logger.error("Требуется пароль двухфакторной аутентификации")
                    return
                
                client.sign_in(password=PASSWORD)
                logger.info("Успешный вход с 2FA!")
            except PhoneCodeInvalidError:
                logger.error("Неверный код подтверждения")
                return
            except PhoneCodeExpiredError:
                logger.error("Код подтверждения истек")
                return
            except Exception as e:
                logger.error(f"Ошибка входа: {e}")
                return
        
        # Показываем информацию о пользователе
        me = client.get_me()
        logger.info(f"Вход выполнен как: {me.first_name} {me.last_name or ''} (@{me.username or 'нет юзернейма'})")
        
        # Отправка сообщений
        successful = 0
        failed = 0
        
        for i, recipient in enumerate(recipients, 1):
            try:
                # Отправляем сообщение
                client.send_message(recipient, MESSAGE)
                
                # Отмечаем успех
                successful += 1
                logger.info(f"✓ [{i}/{len(recipients)}] Отправлено: {recipient}")
                
                # Делаем паузу
                if i < len(recipients):
                    delay = 2 + random.uniform(0.5, 1.5)
                    time.sleep(delay)
                    
            except FloodWaitError as e:
                # Ограничение на частоту отправки
                wait_seconds = e.seconds
                
                if wait_seconds <= 30:
                    logger.warning(f"⚠️ Пауза {wait_seconds} сек...")
                    time.sleep(wait_seconds)
                    
                    # Повторная попытка
                    try:
                        client.send_message(recipient, MESSAGE)
                        successful += 1
                        logger.info(f"✓ [{i}/{len(recipients)}] Отправлено (после паузы): {recipient}")
                        continue
                    except Exception as e2:
                        pass
                
                failed += 1
                logger.error(f"✗ [{i}/{len(recipients)}] Ошибка (FloodWait {wait_seconds}с): {recipient}")
                
            except Exception as e:
                # Прочие ошибки
                failed += 1
                logger.error(f"✗ [{i}/{len(recipients)}] Ошибка: {recipient} - {str(e)}")
                time.sleep(2)
        
        # Итоги
        logger.info("\n===== РЕЗУЛЬТАТЫ =====")
        logger.info(f"Всего получателей: {len(recipients)}")
        logger.info(f"Успешно отправлено: {successful}")
        logger.info(f"Ошибок: {failed}")
        
        if recipients:
            success_rate = (successful / len(recipients)) * 100
            logger.info(f"Процент успеха: {success_rate:.1f}%")
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        # Отключаемся
        client.disconnect()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nПрограмма прервана пользователем")
    
    # Задержка перед выходом
    print("\nГотово! Проверьте результаты выше.")