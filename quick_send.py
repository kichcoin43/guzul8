import asyncio
import sys
import os
from telethon import TelegramClient

# API-ключи Telegram
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Скрипт для срочной отправки сообщений
async def main():
    # Проверяем наличие аргументов
    if len(sys.argv) < 3:
        print("Использование: python quick_send.py СООБЩЕНИЕ ПОЛУЧАТЕЛЬ1 ПОЛУЧАТЕЛЬ2 ...")
        return

    # Создаем новую сессию (no-cache режим)
    session_file = "quick_session"
    client = TelegramClient(session_file, API_ID, API_HASH)
    
    try:
        # Подключаемся
        print("Подключение к Telegram...")
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            print("ОШИБКА: Требуется авторизация!")
            print("Пожалуйста, введите свой номер телефона:")
            phone = input("+")
            
            # Отправляем запрос на код
            await client.send_code_request(f"+{phone}")
            
            # Запрашиваем код подтверждения
            print("Введите код подтверждения, который был отправлен в Telegram:")
            code = input("Код: ")
            
            try:
                await client.sign_in(phone=f"+{phone}", code=code)
            except Exception as e:
                if "2FA" in str(e):
                    print("Требуется двухфакторная аутентификация.")
                    password = input("Введите ваш пароль 2FA: ")
                    await client.sign_in(password=password)
                else:
                    raise e
        
        # Получаем сообщение и получателей
        message = sys.argv[1]
        recipients = sys.argv[2:]
        
        print(f"Отправляем сообщение: {message[:30]}...")
        print(f"Количество получателей: {len(recipients)}")
        
        # Отправляем сообщения
        success_count = 0
        
        for recipient in recipients:
            try:
                print(f"Отправка сообщения для {recipient}...")
                await client.send_message(recipient, message)
                success_count += 1
                print(f"✓ Отправлено успешно: {recipient}")
                
                # Пауза для избежания блокировки
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"✗ Ошибка при отправке {recipient}: {str(e)}")
        
        # Выводим результаты
        print("\n=== РЕЗУЛЬТАТЫ РАССЫЛКИ ===")
        print(f"Всего получателей: {len(recipients)}")
        print(f"Успешно отправлено: {success_count}")
        print(f"Не удалось отправить: {len(recipients) - success_count}")
        print(f"Процент успеха: {success_count / len(recipients) * 100:.1f}%")
        
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
    finally:
        print("Завершение сессии...")
        await client.disconnect()
        print("Готово.")

if __name__ == "__main__":
    asyncio.run(main())