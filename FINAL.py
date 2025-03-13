#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ФИНАЛЬНАЯ ВЕРСИЯ ОТПРАВЩИКА СООБЩЕНИЙ TELEGRAM
============================================

Самая простая версия скрипта для отправки сообщений Telegram, 
используя существующий файл сессии без интерактивного ввода.

Если вы уже выполнили вход в Telegram через другой скрипт,
эта программа позволит быстро отправить сообщения без
необходимости вводить коды подтверждения.

ИСПОЛЬЗОВАНИЕ:
  python FINAL.py "Текст сообщения"
"""

import os
import sys
import time
import random
import logging
from telethon.sync import TelegramClient
from telethon.errors import FloodWaitError

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

# Константы для API
API_ID = 1079592
API_HASH = "4b3c8eeb47a62ecc941e61907f1a7bf0"

# Список возможных файлов сессий
SESSION_FILES = [
    'session', 'telegram_session', 'mega_session', 'direct_session',
    'direct_login', 'session_telegram'
]

# Файл с получателями
RECIPIENTS_FILE = "test_recipients.txt"

def find_session_file():
    """Поиск существующего файла сессии"""
    for session in SESSION_FILES:
        if os.path.exists(f"{session}.session"):
            return session
    return None

def load_recipients():
    """Загрузка получателей из файла"""
    try:
        with open(RECIPIENTS_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Ошибка загрузки получателей: {e}")
        return []

def main():
    """Основная функция программы"""
    # Проверяем наличие сообщения
    if len(sys.argv) < 2:
        print(__doc__)
        return
        
    # Получаем сообщение
    message = sys.argv[1]
    
    # Ищем существующий файл сессии
    session_file = find_session_file()
    if not session_file:
        logger.error("Не найден файл сессии Telegram. Сначала войдите в аккаунт.")
        return
    
    # Загружаем получателей
    recipients = load_recipients()
    if not recipients:
        logger.error(f"Не удалось загрузить получателей из {RECIPIENTS_FILE}")
        return
    
    logger.info(f"Найден файл сессии: {session_file}.session")
    logger.info(f"Загружено {len(recipients)} получателей")
    logger.info(f"Сообщение: {message[:50]}{'...' if len(message) > 50 else ''}")
    
    # Создаем клиент
    client = TelegramClient(session_file, API_ID, API_HASH)
    
    try:
        # Подключаемся
        client.connect()
        
        # Проверяем авторизацию
        if not client.is_user_authorized():
            logger.error("Сессия недействительна. Требуется повторный вход в аккаунт.")
            return
        
        # Получаем информацию о пользователе
        me = client.get_me()
        logger.info(f"Авторизован как: {me.first_name} {me.last_name or ''} (@{me.username or 'нет'})")
        
        # Отправка сообщений
        successful = 0
        failed = 0
        
        logger.info(f"\n===== НАЧАЛО ОТПРАВКИ =====")
        
        for i, recipient in enumerate(recipients, 1):
            try:
                # Отправляем сообщение
                client.send_message(recipient, message)
                
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
                        client.send_message(recipient, message)
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
        if client:
            client.disconnect()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nПрограмма прервана пользователем")
    
    # Задержка перед выходом
    print("\nГотово! Нажмите Ctrl+C для выхода.")