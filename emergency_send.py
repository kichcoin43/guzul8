"""
ЭКСТРЕННАЯ РАССЫЛКА TELEGRAM
==============================
Скрипт для срочного запуска рассылки сообщений в Telegram 
с использованием существующей сессии.

Использование: python emergency_send.py
"""

import asyncio
import os
import glob
import sys
import logging
import time
from telethon import TelegramClient
from telethon.errors import FloodWaitError

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получаем API ключи
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Функция умной задержки
async def smart_delay(success_count):
    # Базовая задержка увеличивается с каждым отправленным сообщением
    base_delay = 1.0 + min(success_count * 0.05, 3.0)
    # Добавляем случайную компоненту
    import random
    jitter = random.uniform(-0.5, 0.5)
    delay = max(0.5, base_delay + jitter)
    await asyncio.sleep(delay)

# Основная функция отправки
async def emergency_send(session_file, message, recipients):
    """
    Функция для экстренной рассылки сообщений
    
    Args:
        session_file (str): Путь к файлу сессии
        message (str): Текст сообщения для отправки
        recipients (list): Список получателей (@username или телефоны)
    """
    # Имя сессии без расширения
    session_name = session_file.replace('.session', '')
    
    # Создаем клиент
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        # Подключаемся к API
        logger.info("Подключение к Telegram API...")
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            logger.error("ОШИБКА: Сессия недействительна!")
            return False, 0, len(recipients)
        
        # Получаем данные аккаунта
        me = await client.get_me()
        logger.info(f"Авторизован как: {me.first_name} {me.last_name or ''} (@{me.username or 'нет username'})")
        
        # Счетчики для статистики
        success_count = 0
        failure_count = 0
        error_details = {}
        
        # Запускаем отправку
        logger.info(f"Начинаем отправку {len(recipients)} сообщений...")
        
        # Основной цикл отправки
        for idx, recipient in enumerate(recipients, 1):
            # Очищаем получателя от лишних пробелов
            recipient = recipient.strip()
            
            # Пропускаем пустые строки
            if not recipient:
                continue
            
            # Выводим прогресс
            logger.info(f"[{idx}/{len(recipients)}] Отправка: {recipient}")
            
            try:
                # Отправляем сообщение
                await client.send_message(recipient, message)
                
                # Отмечаем успех
                success_count += 1
                logger.info(f"✓ Успешно отправлено: {recipient}")
                
                # Применяем умную задержку после успешной отправки
                if idx < len(recipients):
                    await smart_delay(success_count)
                
            except FloodWaitError as e:
                # Телеграм требует подождать
                wait_seconds = e.seconds
                
                if wait_seconds <= 60:  # Если ждать не более минуты
                    logger.warning(f"⚠️ Требуется пауза на {wait_seconds} секунд")
                    await asyncio.sleep(wait_seconds)
                    
                    # Повторная попытка
                    try:
                        await client.send_message(recipient, message)
                        success_count += 1
                        logger.info(f"✓ Успешно отправлено после паузы: {recipient}")
                        continue
                    except Exception as e2:
                        logger.error(f"✗ Повторная попытка не удалась: {str(e2)}")
                else:
                    logger.error(f"✗ Слишком долгая пауза ({wait_seconds} сек), пропускаем")
                
                failure_count += 1
                error_details[recipient] = f"FloodWaitError: {wait_seconds} сек"
                
            except Exception as e:
                # Прочие ошибки
                failure_count += 1
                error_msg = str(e)
                error_details[recipient] = error_msg
                logger.error(f"✗ Ошибка отправки {recipient}: {error_msg}")
                
                # Дополнительная пауза после ошибки
                await asyncio.sleep(2)
        
        # Выводим статистику
        logger.info("\n===== РЕЗУЛЬТАТЫ РАССЫЛКИ =====")
        logger.info(f"Всего получателей: {len(recipients)}")
        logger.info(f"Успешно отправлено: {success_count}")
        logger.info(f"Не удалось отправить: {failure_count}")
        
        if len(recipients) > 0:
            success_rate = success_count / len(recipients) * 100
            logger.info(f"Процент успеха: {success_rate:.1f}%")
        
        # Выводим детали ошибок, если есть
        if error_details:
            logger.info("\nОшибки отправки:")
            for recipient, error in list(error_details.items())[:5]:
                logger.info(f"   - {recipient}: {error}")
            
            if len(error_details) > 5:
                logger.info(f"   ... и еще {len(error_details) - 5} ошибок")
        
        return True, success_count, failure_count
        
    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        return False, 0, len(recipients)
        
    finally:
        # Закрываем соединение
        await client.disconnect()
        logger.info("Сессия Telegram завершена")

# Загрузка получателей из файла
def load_recipients(file_path):
    """Загружает список получателей из текстового файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Читаем строки, удаляем пробелы и пустые строки
            recipients = [line.strip() for line in f if line.strip()]
        return recipients
    except Exception as e:
        logger.error(f"Ошибка при чтении {file_path}: {str(e)}")
        return []

# Поиск файла сессии Telegram
def find_session_file():
    """Ищет файл сессии Telegram в текущей директории"""
    sessions = glob.glob("*.session")
    return sessions[0] if sessions else None

# Главная функция
async def main():
    try:
        print("\n===== ЭКСТРЕННАЯ РАССЫЛКА TELEGRAM =====\n")
        
        # Проверяем ключи API
        if not API_ID or not API_HASH:
            logger.error("Отсутствуют ключи API Telegram!")
            logger.error("Установите переменные окружения TELEGRAM_API_ID и TELEGRAM_API_HASH")
            return
        
        # Ищем файл сессии
        session_file = find_session_file()
        if not session_file:
            logger.error("Не найдены файлы сессии Telegram!")
            logger.error("Сначала войдите в аккаунт через основное приложение")
            return
        
        logger.info(f"Найден файл сессии: {session_file}")
        
        # Запрашиваем текст сообщения
        print("\nВведите текст сообщения для рассылки (Ctrl+D для завершения ввода):")
        message_lines = []
        
        try:
            while True:
                line = input()
                message_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            # Завершение ввода
            pass
        
        message = "\n".join(message_lines)
        
        if not message.strip():
            logger.error("Сообщение не может быть пустым!")
            return
        
        # Получатели
        recipients = []
        
        # Спрашиваем про источник получателей
        print("\nКак вы хотите указать получателей?")
        print("1. Ввести получателей вручную")
        print("2. Загрузить из файла")
        
        try:
            choice = input("Выберите опцию (1/2): ").strip()
            
            if choice == "1":
                # Ручной ввод
                print("\nВведите получателей по одному на строку (Ctrl+D для завершения):")
                try:
                    while True:
                        recipient = input().strip()
                        if recipient:
                            recipients.append(recipient)
                except (EOFError, KeyboardInterrupt):
                    pass
            elif choice == "2":
                # Загрузка из файла
                file_path = input("Введите путь к файлу со списком получателей: ").strip()
                recipients = load_recipients(file_path)
                logger.info(f"Загружено {len(recipients)} получателей из файла {file_path}")
            else:
                logger.error("Неверный выбор!")
                return
                
        except (EOFError, KeyboardInterrupt):
            logger.error("Операция отменена пользователем")
            return
        
        # Проверяем список получателей
        if not recipients:
            logger.error("Список получателей пуст!")
            return
        
        # Выводим информацию о рассылке
        print("\n===== ИНФОРМАЦИЯ О РАССЫЛКЕ =====")
        print(f"Сообщение: {message[:50]}{'...' if len(message) > 50 else ''}")
        print(f"Количество получателей: {len(recipients)}")
        
        # Показываем первых 5 получателей
        if len(recipients) <= 5:
            print("Получатели:")
            for i, recipient in enumerate(recipients, 1):
                print(f"  {i}. {recipient}")
        else:
            print("Первые 5 получателей:")
            for i, recipient in enumerate(recipients[:5], 1):
                print(f"  {i}. {recipient}")
            print(f"  ... и еще {len(recipients) - 5}")
        
        # Подтверждение
        try:
            confirm = input("\nНачать рассылку? (y/n): ").lower()
            if confirm != 'y' and confirm != 'yes' and confirm != 'да':
                logger.info("Рассылка отменена пользователем")
                return
        except (EOFError, KeyboardInterrupt):
            logger.error("Операция отменена пользователем")
            return
            
        # Запускаем рассылку
        success, success_count, failure_count = await emergency_send(
            session_file, message, recipients
        )
        
        # Выводим итог
        if success:
            logger.info("Рассылка завершена!\n")
        else:
            logger.error("Ошибка при выполнении рассылки!\n")
            
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
    
    finally:
        # Задержка перед выходом, чтобы пользователь успел прочитать сообщения
        print("\nНажмите Enter для выхода...")
        try:
            input()
        except:
            pass

# Точка входа
if __name__ == "__main__":
    # Запускаем основную функцию
    asyncio.run(main())