import asyncio
import os
import sys
import logging
import random
from telethon import TelegramClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Авторизованная сессия
SESSION_FILE = "session_380664312381"

async def send_direct_message(recipient, message_text):
    """
    Простая функция для отправки сообщения одному получателю
    
    Args:
        recipient (str): Имя пользователя или телефон получателя
        message_text (str): Текст сообщения
    """
    if not API_ID or not API_HASH:
        logger.error("API_ID или API_HASH не найдены в переменных окружения")
        return False
        
    # Создаем клиент Telegram
    client = TelegramClient(SESSION_FILE, int(API_ID), API_HASH)
    
    try:
        # Подключаемся
        logger.info(f"Подключение к Telegram с сессией {SESSION_FILE}...")
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            logger.error("Пользователь не авторизован в этой сессии")
            return False
        
        # Получаем информацию о текущем пользователе
        me = await client.get_me()
        logger.info(f"Отправитель: id={me.id}, имя={me.first_name} {me.last_name if me.last_name else ''}, username={me.username}, phone={me.phone}")
        
        # Отправка сообщения
        logger.info(f"Попытка отправки сообщения получателю {recipient}...")
        
        try:
            # Пробуем получить информацию о получателе 
            try:
                user = await client.get_entity(recipient)
                logger.info(f"Найден получатель: {user.id}, {getattr(user, 'username', 'без имени')}")
            except Exception as user_error:
                logger.warning(f"Не удалось получить информацию о пользователе {recipient}: {str(user_error)}")
            
            # Отправляем сообщение
            result = await client.send_message(recipient, message_text)
            logger.info(f"Сообщение успешно отправлено! ID сообщения: {result.id}")
            return True
            
        except Exception as send_error:
            logger.error(f"Ошибка при отправке сообщения: {str(send_error)}")
            return False
    
    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}")
        return False
    
    finally:
        # Закрываем соединение
        await client.disconnect()
        logger.info("Отключение от Telegram API")

async def main():
    """Основная функция для запуска отправки сообщения"""
    # Проверяем количество аргументов
    if len(sys.argv) < 3:
        print("Использование: python telegram_direct.py <получатель> <сообщение>")
        print("          или: python telegram_direct.py --file recipients.txt <сообщение>")
        print("Пример: python telegram_direct.py @username 'Привет, это тестовое сообщение'")
        return
    
    # Режим отправки по списку из файла
    if sys.argv[1] == "--file" and len(sys.argv) >= 4:
        filename = sys.argv[2]
        message = sys.argv[3]
        
        try:
            # Читаем файл с получателями
            with open(filename, 'r') as f:
                recipients = [line.strip() for line in f.readlines() if line.strip()]
            
            if not recipients:
                print(f"❌ Файл {filename} пуст или не содержит получателей.")
                return
                
            print(f"📤 Отправка сообщения: '{message}' для {len(recipients)} получателей из файла {filename}")
            
            # Счетчики для статистики
            successful = 0
            failed = 0
            
            # Отправляем каждому получателю
            for idx, recipient in enumerate(recipients, 1):
                print(f"\n[{idx}/{len(recipients)}] Отправка для {recipient}...")
                
                # Отправляем сообщение
                result = await send_direct_message(recipient, message)
                
                if result:
                    successful += 1
                else:
                    failed += 1
                
                # Пауза между отправками, чтобы избежать блокировки
                if idx < len(recipients):
                    delay = random.uniform(1.5, 2.5)
                    print(f"Ожидание {delay:.1f} секунд перед следующей отправкой...")
                    await asyncio.sleep(delay)
            
            # Выводим статистику
            print(f"\n📊 Итоги отправки:")
            print(f"✅ Успешно отправлено: {successful}")
            print(f"❌ Не удалось отправить: {failed}")
            print(f"📋 Всего получателей: {len(recipients)}")
            
        except Exception as e:
            print(f"❌ Ошибка при чтении файла {filename}: {str(e)}")
            return
    
    # Режим отправки одному получателю
    else:
        recipient = sys.argv[1]
        message = sys.argv[2]
        
        print(f"📤 Отправка сообщения: '{message}' для получателя {recipient}")
        
        result = await send_direct_message(recipient, message)
        
        if result:
            print("✅ Сообщение успешно отправлено!")
        else:
            print("❌ Не удалось отправить сообщение. Проверьте логи для получения подробной информации.")

if __name__ == "__main__":
    asyncio.run(main())