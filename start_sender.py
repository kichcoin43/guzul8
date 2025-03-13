import asyncio
import sys
import subprocess
import os
import glob

async def main():
    """
    Запуск срочной рассылки с текущей сессией Telegram
    """
    # Проверяем аргументы
    if len(sys.argv) < 3:
        print("Использование: python start_sender.py текст_сообщения получатель1 получатель2 ...")
        print("Пример: python start_sender.py 'Привет всем!' @username1 @username2")
        return
    
    # Получаем аргументы
    message = sys.argv[1]
    recipients = sys.argv[2:]
    
    # Находим текущую сессию
    session_files = glob.glob("session_*.session")
    if not session_files:
        print("ОШИБКА: Не найден файл сессии. Сначала выполните вход через веб-интерфейс.")
        return
    
    # Берем первую найденную сессию
    session_file = session_files[0]
    phone_number = session_file.replace("session_", "").replace(".session", "")
    
    print(f"ЗАПУСК СРОЧНОЙ РАССЫЛКИ:")
    print(f" - Телефон: +{phone_number}")
    print(f" - Получатели ({len(recipients)}): {', '.join(recipients[:5])}{'...' if len(recipients) > 5 else ''}")
    print(f" - Сообщение: {message[:50]}{'...' if len(message) > 50 else ''}")
    print()
    print("Выполняется отправка...")
    
    # Запускаем скрипт прямой отправки
    from direct_send_multiple import send_messages
    result = await send_messages(recipients, message)
    
    if result and len(result) >= 3:
        successful_count, failed_count, failed_users = result
        print("\nРЕЗУЛЬТАТЫ РАССЫЛКИ:")
        print(f" - Успешно отправлено: {successful_count}")
        print(f" - Ошибок при отправке: {failed_count}")
        
        if failed_count > 0 and failed_users:
            print("\nПолучатели с ошибками:")
            for user, error in list(failed_users.items())[:5]:
                print(f" - {user}: {error}")
            
            if len(failed_users) > 5:
                print(f"   ...и еще {len(failed_users) - 5} получателей")
    else:
        print("\nОШИБКА ПРИ ВЫПОЛНЕНИИ РАССЫЛКИ. Проверьте файл сессии и подключение к интернету.")

# Запускаем основную функцию
if __name__ == "__main__":
    asyncio.run(main())