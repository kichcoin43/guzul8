import asyncio
import os
import sys
from telethon import TelegramClient

# Получаем API ключи из переменных окружения
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Оптимизированная функция для запуска рассылки 
# - максимальная скорость без блокировок
async def run_mailing(message, recipients, phone=None):
    """
    Запускает рассылку сообщений. Автоматически входит в аккаунт 
    или использует существующую сессию.
    """
    # Создаем имя сессии
    if phone:
        session_name = f"session_{phone.replace('+', '')}"
    else:
        session_name = 'mega_session'
    
    # Создаем клиент
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        # Подключаемся к API
        print("Подключение к Telegram API...")
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            print("Требуется авторизация")
            
            # Запрашиваем телефон если не передан
            if not phone:
                phone = input("Введите номер телефона (с '+', например +79001234567): ")
            
            # Отправляем запрос кода
            sent = await client.send_code_request(phone)
            
            # Запрашиваем код
            code = input(f"Введите код, отправленный на {phone}: ")
            
            # Пытаемся войти
            try:
                user = await client.sign_in(phone=phone, code=code)
                print(f"Успешный вход: {user.first_name}")
            except Exception as e:
                if "password" in str(e).lower() or "2fa" in str(e).lower():
                    # Обработка 2FA
                    password = input("Введите пароль двухфакторной аутентификации: ")
                    user = await client.sign_in(password=password)
                    print(f"Вход с 2FA выполнен успешно: {user.first_name}")
                else:
                    raise
        
        # Счетчики
        successful = 0
        failed = 0
        
        print(f"\nНачало отправки сообщений. Всего получателей: {len(recipients)}")
        
        # Основной цикл отправки сообщений
        for i, recipient in enumerate(recipients, 1):
            try:
                # Удаляем лишние пробелы
                recipient = recipient.strip()
                if not recipient:
                    continue
                
                print(f"[{i}/{len(recipients)}] Отправка сообщения для {recipient}...")
                
                # Отправляем сообщение
                await client.send_message(recipient, message)
                
                # Увеличиваем счетчик успешных отправок
                successful += 1
                print(f"✓ Успешно отправлено: {recipient}")
                
                # Небольшая пауза между отправками
                if i < len(recipients):
                    delay = min(3, 0.5 + (successful / 10)) # Увеличиваем паузу с ростом кол-ва сообщений
                    await asyncio.sleep(delay)
                
            except Exception as e:
                # Обрабатываем ошибку
                failed += 1
                print(f"✗ Ошибка отправки для {recipient}: {str(e)}")
                
                # Пауза после ошибки чуть больше
                await asyncio.sleep(3)
        
        # Выводим статистику
        print("\n===== РЕЗУЛЬТАТЫ ОТПРАВКИ СООБЩЕНИЙ =====")
        print(f"Всего получателей: {len(recipients)}")
        print(f"Успешно отправлено: {successful}")
        print(f"Не удалось отправить: {failed}")
        if recipients:
            print(f"Результативность: {successful / len(recipients) * 100:.1f}%")
        
        return successful, failed
        
    except Exception as main_error:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {str(main_error)}")
        return 0, len(recipients) if recipients else 0
        
    finally:
        # Отключаемся от API
        await client.disconnect()
        print("Сессия Telegram завершена")

# Загрузка получателей из файла
def load_recipients_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Читаем строки и удаляем пробелы
            recipients = [line.strip() for line in f if line.strip()]
        return recipients
    except Exception as e:
        print(f"Ошибка при чтении файла: {str(e)}")
        return []

# Основная функция
async def main():
    # Проверяем аргументы
    if len(sys.argv) < 2:
        print("Использование:")
        print("1. python mega_send.py 'текст сообщения' @username1 @username2")
        print("2. python mega_send.py 'текст сообщения' -f recipients.txt")
        print("")
        print("Параметры:")
        print("-f file.txt - загрузить получателей из файла")
        print("-y - запустить без подтверждения")
        return
    
    # Получаем текст сообщения (первый аргумент)
    message = sys.argv[1]
    
    # Проверяем режим работы (из файла или из аргументов)
    recipients = []
    auto_confirm = False
    
    # Обрабатываем аргументы
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '-f' and i+1 < len(sys.argv):
            # Загружаем из файла
            file_path = sys.argv[i+1]
            file_recipients = load_recipients_from_file(file_path)
            print(f"Загружено {len(file_recipients)} получателей из файла {file_path}")
            recipients.extend(file_recipients)
            i += 2
        elif arg == '-y':
            # Автоподтверждение
            auto_confirm = True
            i += 1
        else:
            # Добавляем получателя из аргумента
            recipients.append(arg)
            i += 1
    
    # Проверяем, есть ли получатели
    if not recipients:
        print("Не указаны получатели. Используйте список получателей или файл с получателями.")
        return
    
    # Выводим информацию о предстоящей рассылке
    print("\n===== ПАРАМЕТРЫ РАССЫЛКИ =====")
    print(f"Сообщение: {message}")
    print(f"Количество получателей: {len(recipients)}")
    if len(recipients) <= 5:
        print("Получатели:")
        for i, r in enumerate(recipients, 1):
            print(f"  {i}. {r}")
    else:
        print("Первые 5 получателей:")
        for i, r in enumerate(recipients[:5], 1):
            print(f"  {i}. {r}")
        print(f"  ... и еще {len(recipients) - 5}")
    
    # Подтверждение отправки
    if not auto_confirm:
        confirm = input("\nОтправить сообщения? (y/n): ").lower()
        if confirm != 'y' and confirm != 'yes' and confirm != 'да':
            print("Отправка отменена")
            return
    
    # Запускаем отправку
    await run_mailing(message, recipients)

# Точка входа
if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(main())