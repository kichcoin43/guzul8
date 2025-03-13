import asyncio
import sys
import os
import datetime
import random
from telethon import TelegramClient
from telethon.errors import FloodWaitError

# Данные API (берём из переменных окружения)
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Функция паузы между сообщениями для избежания блокировки
async def smart_delay():
    base_delay = random.uniform(1.5, 3.0)
    await asyncio.sleep(base_delay)

# Функция отправки сообщений
async def send_messages(message, recipients):
    # Создаем новую сессию
    client = TelegramClient('fast_session', API_ID, API_HASH)
    
    try:
        # Подключаемся
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Подключение к Telegram...")
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            print("ОШИБКА: Не авторизован!")
            print("Необходимо авторизоваться. Введите номер телефона (с +):")
            phone = input()
            
            # Отправляем запрос на код
            await client.send_code_request(phone)
            
            # Запрашиваем код
            print("Введите код, который был отправлен в Telegram:")
            code = input()
            
            try:
                await client.sign_in(phone=phone, code=code)
            except Exception as e:
                if "2FA" in str(e) or "password" in str(e).lower():
                    print("Требуется двухфакторная аутентификация.")
                    password = input("Введите пароль 2FA: ")
                    await client.sign_in(password=password)
                else:
                    raise e
            
            print("Авторизация успешна!")
        
        # Статистика для вывода
        total = len(recipients)
        success = 0
        failed = 0
        
        # Основной цикл отправки
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Начинаем отправку {total} сообщений...")
        
        for i, recipient in enumerate(recipients, 1):
            try:
                # Применяем задержку перед отправкой
                if i > 1:  # Не ждем перед первым сообщением
                    await smart_delay()
                
                # Очищаем имя получателя от пробелов
                recipient = recipient.strip()
                
                # Пропускаем пустые строки
                if not recipient:
                    continue
                
                # Отправляем сообщение
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Отправка {i}/{total}: {recipient}...")
                await client.send_message(recipient, message)
                
                # Увеличиваем счетчик успешных
                success += 1
                print(f"✓ Отправлено: {recipient}")
                
            except FloodWaitError as e:
                # Обработка ограничения частоты отправки
                print(f"⚠️ Telegram требует паузу на {e.seconds} секунд")
                
                # Если пауза меньше 60 секунд, ждем
                if e.seconds < 300:  # Максимум 5 минут ожидания
                    print(f"Ожидаем {e.seconds} секунд...")
                    await asyncio.sleep(e.seconds)
                    
                    # Повторная попытка
                    try:
                        await client.send_message(recipient, message)
                        success += 1
                        print(f"✓ Отправлено после ожидания: {recipient}")
                        continue
                    except Exception as e2:
                        print(f"✗ Ошибка после ожидания: {str(e2)}")
                else:
                    print("Слишком долгая пауза, пропускаем получателя")
                
                failed += 1
                
            except Exception as e:
                # Другие ошибки
                failed += 1
                error_msg = str(e)
                print(f"✗ Ошибка при отправке {recipient}: {error_msg}")
                
                # Пауза при ошибке для безопасности
                await asyncio.sleep(2)
        
        # Показываем итоги
        print("\n========== РЕЗУЛЬТАТЫ РАССЫЛКИ ==========")
        print(f"Всего получателей: {total}")
        print(f"Успешно отправлено: {success}")
        print(f"Не удалось отправить: {failed}")
        if total > 0:
            print(f"Процент успешных: {success / total * 100:.1f}%")
        print("==========================================")
        
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
    finally:
        # Закрываем соединение
        await client.disconnect()
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Рассылка завершена.")

# Основная функция
async def main():
    # Проверяем аргументы
    if len(sys.argv) < 3:
        print("Использование: python fast_send.py \"текст сообщения\" получатель1 получатель2 ...")
        print("Пример: python fast_send.py \"Привет, это тестовое сообщение\" @username +79001234567")
        return
    
    # Получаем сообщение и получателей
    message = sys.argv[1]
    recipients = sys.argv[2:]
    
    # Если передан слишком короткий список получателей
    if len(recipients) < 1:
        print("Требуется указать хотя бы одного получателя!")
        return
        
    # Выводим информацию
    print(f"Сообщение для отправки: {message}")
    print(f"Количество получателей: {len(recipients)}")
    print("Первые получатели из списка:")
    for i, recipient in enumerate(recipients[:5], 1):
        print(f"{i}. {recipient}")
    if len(recipients) > 5:
        print(f"...и еще {len(recipients) - 5}")
        
    # Подтверждение
    print("\nВы уверены, что хотите начать рассылку? (y/n)")
    confirm = input().lower()
    
    if confirm == 'y' or confirm == 'yes' or confirm == 'да':
        await send_messages(message, recipients)
    else:
        print("Отмена рассылки.")

# Запуск программы
if __name__ == "__main__":
    asyncio.run(main())