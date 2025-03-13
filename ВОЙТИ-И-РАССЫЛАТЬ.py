"""
СРОЧНАЯ РАССЫЛКА TELEGRAM С АВТОМАТИЧЕСКОЙ АВТОРИЗАЦИЕЙ
======================================================
Скрипт, который решает проблему истекающих кодов путем прямой авторизации
"""

import os
import sys
import logging
from telethon.sync import TelegramClient
from telethon.errors import FloodWaitError
import time
import random

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константы для входа - не менять!
API_ID = 1079592
API_HASH = "4b3c8eeb47a62ecc941e61907f1a7bf0"

# Файл получателей по умолчанию
DEFAULT_RECIPIENTS_FILE = "test_recipients.txt"

def load_recipients(file_path):
    """Загружает получателей из файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            recipients = [line.strip() for line in f if line.strip()]
        return recipients
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {str(e)}")
        return []

def main():
    # Проверяем аргументы
    message = None
    recipients = []
    recipients_file = None
    
    # Обрабатываем аргументы
    if len(sys.argv) > 1:
        message = sys.argv[1]
        
        # Проверяем другие аргументы
        for i in range(2, len(sys.argv)):
            arg = sys.argv[i]
            if arg == '-f' and i+1 < len(sys.argv):
                recipients_file = sys.argv[i+1]
            elif not arg.startswith('-'):
                recipients.append(arg)
    
    # Если не указан файл получателей, используем дефолтный
    if not recipients and not recipients_file:
        recipients_file = DEFAULT_RECIPIENTS_FILE
    
    # Загружаем получателей из файла, если указан
    if recipients_file:
        file_recipients = load_recipients(recipients_file)
        recipients.extend(file_recipients)
    
    # Запрашиваем сообщение, если не указано
    if not message:
        print("\nВведите текст сообщения для рассылки:")
        message_lines = []
        try:
            while True:
                line = input()
                if not line:
                    break
                message_lines.append(line)
        except EOFError:
            pass
        
        message = "\n".join(message_lines)
    
    # Проверяем наличие сообщения
    if not message or not message.strip():
        logger.error("Сообщение не может быть пустым!")
        return
    
    # Если список получателей пуст, запрашиваем их
    if not recipients:
        print("\nСписок получателей пуст. Введите получателей (по одному на строку):")
        try:
            while True:
                recipient = input()
                if not recipient:
                    break
                recipients.append(recipient.strip())
        except EOFError:
            pass
    
    # Проверяем наличие получателей
    if not recipients:
        logger.error("Список получателей пуст!")
        return
    
    # Выводим информацию
    logger.info(f"\n===== ИНФОРМАЦИЯ О РАССЫЛКЕ =====")
    logger.info(f"Сообщение: {message[:50]}{'...' if len(message) > 50 else ''}")
    logger.info(f"Количество получателей: {len(recipients)}")
    
    if len(recipients) <= 5:
        for i, recipient in enumerate(recipients, 1):
            logger.info(f"  {i}. {recipient}")
    else:
        for i, recipient in enumerate(recipients[:5], 1):
            logger.info(f"  {i}. {recipient}")
        logger.info(f"  ... и еще {len(recipients) - 5}")
    
    # Процесс авторизации и отправки
    logger.info("\n===== НАЧАЛО ПРОЦЕССА АВТОРИЗАЦИИ =====")
    
    # Авторизация
    session_name = "direct_login"
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        # Подключаемся
        client.connect()
        
        # Проверяем авторизацию
        if not client.is_user_authorized():
            print("\nДля продолжения необходимо войти в аккаунт Telegram.")
            phone = input("Введите номер телефона (с '+', например +79001234567): ")
            
            # Отправляем запрос на код
            client.send_code_request(phone)
            
            # Запрашиваем код
            code = input("Введите код подтверждения из Telegram: ")
            
            try:
                # Пытаемся войти
                client.sign_in(phone=phone, code=code)
                logger.info("Успешный вход!")
            except Exception as e:
                # Проверяем на 2FA
                if "password" in str(e).lower() or "2fa" in str(e).lower():
                    password = input("Введите пароль двухфакторной аутентификации: ")
                    client.sign_in(password=password)
                    logger.info("Успешный вход с 2FA!")
                else:
                    raise
        
        # Получаем информацию о пользователе
        me = client.get_me()
        logger.info(f"Авторизован как: {me.first_name} {me.last_name or ''} (@{me.username or 'нет username'})")
        
        # Начинаем отправку
        logger.info("\n===== НАЧАЛО ОТПРАВКИ СООБЩЕНИЙ =====")
        
        # Счетчики
        success_count = 0
        fail_count = 0
        
        # Отправляем сообщения
        for i, recipient in enumerate(recipients, 1):
            try:
                # Выводим прогресс
                logger.info(f"[{i}/{len(recipients)}] Отправка сообщения для: {recipient}")
                
                # Отправляем
                client.send_message(recipient, message)
                
                # Отмечаем успех
                success_count += 1
                logger.info(f"✓ Успешно отправлено: {recipient}")
                
                # Делаем паузу для избежания блокировки
                if i < len(recipients):
                    delay = random.uniform(1.5, 3.0)
                    time.sleep(delay)
                
            except FloodWaitError as e:
                # Обрабатываем ограничение частоты
                wait_time = e.seconds
                
                if wait_time <= 30:
                    logger.warning(f"⚠️ Telegram требует паузу {wait_time} сек...")
                    time.sleep(wait_time)
                    
                    # Повторная попытка
                    try:
                        client.send_message(recipient, message)
                        success_count += 1
                        logger.info(f"✓ Успешно отправлено после паузы: {recipient}")
                        continue
                    except Exception as e2:
                        logger.error(f"✗ Ошибка после паузы: {str(e2)}")
                else:
                    logger.error(f"✗ Слишком долгая пауза ({wait_time} сек), пропускаем получателя")
                
                fail_count += 1
                
            except Exception as e:
                # Прочие ошибки
                fail_count += 1
                logger.error(f"✗ Ошибка отправки для {recipient}: {str(e)}")
                
                # Пауза после ошибки
                time.sleep(2)
        
        # Выводим итоги
        logger.info("\n===== РЕЗУЛЬТАТЫ РАССЫЛКИ =====")
        logger.info(f"Всего получателей: {len(recipients)}")
        logger.info(f"Успешно отправлено: {success_count}")
        logger.info(f"Не удалось отправить: {fail_count}")
        
        if len(recipients) > 0:
            success_rate = success_count / len(recipients) * 100
            logger.info(f"Процент успеха: {success_rate:.1f}%")
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
    
    finally:
        # Отключаемся от API
        client.disconnect()
        logger.info("Сеанс Telegram завершен.")

# Запуск программы
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nПрограмма прервана пользователем.")
    
    # Задержка в конце
    try:
        input("\nНажмите Enter для выхода...")
    except EOFError:
        pass