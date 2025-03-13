#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ОТПРАВКА СООБЩЕНИЙ В TELEGRAM
=============================
Простой и надежный скрипт для отправки сообщений в Telegram
без проблем с истекающими кодами подтверждения.

Автоматически обрабатывает:
- Истекающие коды подтверждения
- Двухфакторную аутентификацию
- Ограничения на отправку (FloodWait)
- Умные паузы между сообщениями

ИСПОЛЬЗОВАНИЕ:
  python отправить_сообщения.py "Текст сообщения"
  python отправить_сообщения.py "Текст сообщения" @username1 @username2
  python отправить_сообщения.py "Текст сообщения" -f список_получателей.txt
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

# API константы для Telegram - не менять!
API_ID = 1079592
API_HASH = "4b3c8eeb47a62ecc941e61907f1a7bf0"

# Имя сессии по умолчанию
SESSION_NAME = "session_telegram"

# Файл с получателями по умолчанию
DEFAULT_RECIPIENTS_FILE = "test_recipients.txt"

class TelegramSender:
    """Класс для отправки сообщений в Telegram"""
    
    def __init__(self, session_name=SESSION_NAME):
        """Инициализация с указанным именем сессии"""
        self.session_name = session_name
        self.client = None
    
    def connect(self):
        """Подключение к Telegram"""
        try:
            self.client = TelegramClient(self.session_name, API_ID, API_HASH)
            self.client.connect()
            logger.info("Подключено к Telegram API")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к Telegram: {e}")
            return False
    
    def is_authorized(self):
        """Проверка авторизации"""
        if not self.client:
            return False
        return self.client.is_user_authorized()
    
    def login(self, phone_number=None):
        """
        Вход в аккаунт Telegram
        
        Args:
            phone_number (str, optional): Номер телефона для входа
                
        Returns:
            bool: Успешность входа
        """
        if self.is_authorized():
            logger.info("Уже авторизован")
            return True
            
        # Запрашиваем номер телефона, если не указан
        if not phone_number:
            try:
                phone_number = input("Введите номер телефона (с '+', например +79001234567): ")
            except EOFError:
                logger.error("Ошибка ввода номера телефона")
                return False
        
        try:
            # Отправляем запрос на код подтверждения
            logger.info(f"Запрашиваем код подтверждения на номер {phone_number}")
            sent_code = self.client.send_code_request(phone_number)
            
            # Запрашиваем код
            try:
                code = input("Введите код подтверждения из Telegram: ")
            except EOFError:
                logger.error("Ошибка ввода кода")
                return False
                
            # Пытаемся войти с полученным кодом
            try:
                logger.info("Выполняем вход с кодом...")
                self.client.sign_in(phone=phone_number, code=code)
                logger.info("Успешный вход!")
                return True
                
            except PhoneCodeInvalidError:
                # Код неверный
                logger.error("Введен неверный код подтверждения")
                return False
                
            except PhoneCodeExpiredError:
                # Код истек, запрашиваем новый
                logger.warning("Код подтверждения истек, запрашиваем новый...")
                sent_code = self.client.send_code_request(phone_number)
                
                try:
                    code = input("Код истек. Введите новый код подтверждения: ")
                except EOFError:
                    logger.error("Ошибка ввода нового кода")
                    return False
                
                try:
                    self.client.sign_in(phone=phone_number, code=code)
                    logger.info("Успешный вход с новым кодом!")
                    return True
                except Exception as e:
                    logger.error(f"Ошибка входа с новым кодом: {e}")
                    return False
                    
            except SessionPasswordNeededError:
                # Требуется двухфакторная аутентификация
                logger.info("Требуется пароль двухфакторной аутентификации")
                
                try:
                    password = input("Введите пароль двухфакторной аутентификации: ")
                except EOFError:
                    logger.error("Ошибка ввода пароля 2FA")
                    return False
                
                try:
                    self.client.sign_in(password=password)
                    logger.info("Успешный вход с двухфакторной аутентификацией!")
                    return True
                except Exception as e:
                    logger.error(f"Ошибка при вводе пароля 2FA: {e}")
                    return False
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при входе: {e}")
            return False
    
    def disconnect(self):
        """Отключение от Telegram API"""
        if self.client:
            self.client.disconnect()
            logger.info("Отключено от Telegram API")
    
    def get_user_info(self):
        """Получение информации о текущем пользователе"""
        if not self.is_authorized():
            logger.error("Не авторизован")
            return None
            
        try:
            me = self.client.get_me()
            return me
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе: {e}")
            return None
    
    def send_message(self, recipient, message):
        """
        Отправка одного сообщения указанному получателю
        
        Args:
            recipient (str): Получатель (@username или телефон)
            message (str): Текст сообщения
            
        Returns:
            bool: Успешность отправки
        """
        if not self.is_authorized():
            logger.error("Не авторизован, сообщение не отправлено")
            return False
            
        try:
            # Отправляем сообщение
            self.client.send_message(recipient, message)
            return True
        except FloodWaitError as e:
            # Ограничение на отправку
            wait_seconds = e.seconds
            logger.warning(f"Ограничение отправки, ожидание {wait_seconds} сек")
            
            if wait_seconds <= 30:
                # Если ожидание небольшое, ждем и пробуем снова
                time.sleep(wait_seconds)
                try:
                    self.client.send_message(recipient, message)
                    return True
                except Exception as e2:
                    logger.error(f"Ошибка при повторной отправке: {e2}")
                    return False
            else:
                # Слишком долгое ожидание
                logger.error(f"Слишком долгое ожидание: {wait_seconds} сек")
                return False
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return False
    
    def send_bulk_messages(self, recipients, message):
        """
        Отправка сообщений списку получателей
        
        Args:
            recipients (list): Список получателей
            message (str): Текст сообщения
            
        Returns:
            tuple: (успешно_отправлено, ошибки)
        """
        if not self.is_authorized():
            logger.error("Не авторизован, сообщения не отправлены")
            return 0, len(recipients)
        
        # Счетчики для статистики
        successful = 0
        failed = 0
        failed_details = {}
        
        # Информация о пользователе
        me = self.get_user_info()
        if me:
            logger.info(f"Отправка сообщений как: {me.first_name} {me.last_name or ''} (@{me.username or 'нет'})")
        
        # Отправляем сообщения
        logger.info(f"Начало отправки {len(recipients)} сообщений")
        for i, recipient in enumerate(recipients, 1):
            # Очищаем имя получателя от лишних пробелов
            recipient = recipient.strip()
            if not recipient:
                continue
                
            # Выводим прогресс
            logger.info(f"[{i}/{len(recipients)}] Отправка сообщения для {recipient}")
            
            try:
                # Отправляем сообщение
                self.client.send_message(recipient, message)
                
                # Отмечаем успех
                successful += 1
                logger.info(f"✓ Успешно отправлено: {recipient}")
                
                # Умная пауза между сообщениями
                if i < len(recipients):
                    # Базовая пауза зависит от количества успешных отправок
                    delay = min(2.5, 1 + (successful / 10))
                    
                    # Добавляем случайность для обхода анти-спам систем
                    delay += random.uniform(0.5, 1.5)
                    
                    # Увеличиваем паузу если много успешных отправок
                    if successful > 10:
                        delay += 0.5
                    
                    logger.debug(f"Пауза {delay:.1f} сек...")
                    time.sleep(delay)
                    
            except FloodWaitError as e:
                # Обрабатываем ограничение частоты
                wait_seconds = e.seconds
                
                if wait_seconds <= 30:
                    # Если ожидание небольшое, ждем и пробуем снова
                    logger.warning(f"⚠️ Требуется пауза {wait_seconds} сек")
                    time.sleep(wait_seconds)
                    
                    # Повторная попытка
                    try:
                        self.client.send_message(recipient, message)
                        successful += 1
                        logger.info(f"✓ Успешно отправлено после паузы: {recipient}")
                        continue
                    except Exception as e2:
                        logger.error(f"✗ Ошибка после паузы: {e2}")
                else:
                    logger.error(f"✗ Требуется слишком долгая пауза ({wait_seconds} сек)")
                
                # Считаем как ошибку
                failed += 1
                failed_details[recipient] = f"FloodWaitError: {wait_seconds} сек"
                
            except Exception as e:
                # Другие ошибки
                failed += 1
                failed_details[recipient] = str(e)
                logger.error(f"✗ Ошибка отправки для {recipient}: {e}")
                
                # Короткая пауза после ошибки
                time.sleep(2)
        
        # Выводим статистику
        logger.info("\n===== РЕЗУЛЬТАТЫ ОТПРАВКИ =====")
        logger.info(f"Всего получателей: {len(recipients)}")
        logger.info(f"Успешно отправлено: {successful}")
        logger.info(f"Не удалось отправить: {failed}")
        
        # Процент успешных отправок
        if recipients:
            success_rate = (successful / len(recipients)) * 100
            logger.info(f"Процент успеха: {success_rate:.1f}%")
        
        # Выводим детали ошибок
        if failed_details:
            logger.info("\nПолучатели с ошибками:")
            for i, (recipient, error) in enumerate(list(failed_details.items())[:5], 1):
                logger.info(f"  {i}. {recipient}: {error}")
            
            if len(failed_details) > 5:
                logger.info(f"  ... и еще {len(failed_details) - 5} ошибок")
        
        return successful, failed

def load_recipients(file_path):
    """
    Загрузка списка получателей из файла
    
    Args:
        file_path (str): Путь к файлу
        
    Returns:
        list: Список получателей
    """
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

def parse_arguments():
    """
    Разбор аргументов командной строки
    
    Returns:
        tuple: (сообщение, получатели, автоподтверждение)
    """
    message = None
    recipients = []
    recipients_file = None
    auto_confirm = False
    
    # Проверяем наличие аргументов
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h', '/?']:
        print(__doc__)
        return None, [], False
    
    # Первый аргумент - сообщение
    message = sys.argv[1]
    
    # Остальные аргументы - получатели или опции
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '-f' and i+1 < len(sys.argv):
            # Загрузка из файла
            recipients_file = sys.argv[i+1]
            i += 2
        elif arg == '-y':
            # Автоподтверждение
            auto_confirm = True
            i += 1
        else:
            # Обычный получатель
            recipients.append(arg)
            i += 1
    
    # Загружаем получателей из файла, если указан
    if recipients_file:
        file_recipients = load_recipients(recipients_file)
        recipients.extend(file_recipients)
    
    # Если получателей всё ещё нет, пробуем файл по умолчанию
    if not recipients:
        if os.path.exists(DEFAULT_RECIPIENTS_FILE):
            default_recipients = load_recipients(DEFAULT_RECIPIENTS_FILE)
            recipients.extend(default_recipients)
    
    return message, recipients, auto_confirm

def main():
    """Основная функция программы"""
    
    # Разбор аргументов
    message, recipients, auto_confirm = parse_arguments()
    
    # Проверяем наличие сообщения
    if not message:
        logger.error("Сообщение не указано")
        return
    
    # Проверяем наличие получателей
    if not recipients:
        logger.error("Список получателей пуст")
        return
    
    # Выводим информацию
    logger.info("\n===== ИНФОРМАЦИЯ О РАССЫЛКЕ =====")
    logger.info(f"Сообщение: {message[:50]}{'...' if len(message) > 50 else ''}")
    logger.info(f"Количество получателей: {len(recipients)}")
    
    # Показываем первых получателей
    if len(recipients) <= 5:
        for i, recipient in enumerate(recipients, 1):
            logger.info(f"  {i}. {recipient}")
    else:
        for i, recipient in enumerate(recipients[:5], 1):
            logger.info(f"  {i}. {recipient}")
        logger.info(f"  ... и еще {len(recipients) - 5}")
    
    # Запрашиваем подтверждение
    if not auto_confirm:
        try:
            confirm = input("\nНачать отправку сообщений? (y/n): ").lower()
            if not (confirm.startswith('y') or confirm.startswith('д')):
                logger.info("Отправка отменена")
                return
        except EOFError:
            logger.error("Ошибка ввода подтверждения")
            return
    
    # Создаем отправитель
    sender = TelegramSender()
    
    try:
        # Подключаемся к API
        if not sender.connect():
            logger.error("Ошибка подключения к Telegram API")
            return
        
        # Выполняем вход, если нужно
        if not sender.is_authorized():
            if not sender.login():
                logger.error("Ошибка авторизации в Telegram")
                return
        
        # Отправляем сообщения
        sender.send_bulk_messages(recipients, message)
        
    except KeyboardInterrupt:
        logger.info("\nОтправка прервана пользователем")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
    finally:
        # Отключаемся от API
        sender.disconnect()
    
    # Вывод в конце программы
    logger.info("\nОтправка сообщений завершена")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nПрограмма прервана пользователем")
    
    # Задержка в конце для просмотра результатов
    try:
        input("\nНажмите Enter для выхода...")
    except EOFError:
        pass