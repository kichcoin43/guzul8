#!/usr/bin/env python3
import os
import sys
import logging
from telethon import TelegramClient
from telethon.errors import FloodWaitError, UserNotMutualContactError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

async def send_message(client, recipient, message):
    """
    Отправляет сообщение конкретному получателю

    Args:
        client: TelegramClient
        recipient: str - получатель (@username или номер телефона)
        message: str - текст сообщения

    Returns:
        bool - успешность отправки
    """
    try:
        print(f"Trying to resolve entity for {recipient}...")
        entity = await client.get_entity(recipient)
        print(f"Entity found: {entity.username if hasattr(entity, 'username') else entity.phone if hasattr(entity, 'phone') else entity}")

        # Отправляем сообщение
        result = await client.send_message(entity, message)
        print(f"Message sent successfully to {recipient}, message ID: {result.id}")
        return True

    except UserNotMutualContactError:
        # Пользователь не добавил нас в контакты, но это частая ошибка
        # Попробуем отправить сообщение напрямую по username
        try:
            print("User not mutual contact error, trying direct send...")
            result = await client.send_message(recipient, message)
            print(f"Direct message sent successfully to {recipient}, message ID: {result.id}")
            return True
        except Exception as inner_e:
            print(f"Direct send failed: {inner_e}")
            return False

    except FloodWaitError as flood_err:
        wait_time = flood_err.seconds
        print(f"Flood wait error! Need to wait {wait_time} seconds. Telegram is rate limiting us.")
        return False

    except Exception as e:
        print(f"Error sending message to {recipient}: {str(e)}")
        return False

async def main():
    if len(sys.argv) < 2:
        print("Usage: python enhanced_send.py @username1,@username2 'Your message text'")
        print("  Or:  python enhanced_send.py @username 'Text'")
        return

    # Разбираем получателей (можно указать несколько через запятую)
    recipients = sys.argv[1].split(',')
    message = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Тестовое сообщение"

    print(f"Starting to send message to {len(recipients)} recipient(s)")
    print(f"Message: {message}")

    # Connect to Telegram using the session name based on phone number
    phone_number = os.environ.get('TELEGRAM_PHONE_NUMBER')
    if not phone_number:
        print("Error: TELEGRAM_PHONE_NUMBER environment variable not set")
        return

    session_name = f"session_{phone_number.replace('+', '')}"
    client = TelegramClient(session_name, int(API_ID), API_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print(f"Error: Not authorized. Session file {session_name} may be invalid.")
            return

        # Получаем информацию о своём аккаунте
        me = await client.get_me()
        print(f"Sending from: {me.first_name} {me.last_name or ''}, ID: {me.id}, Phone: {me.phone}")

        # Отправляем сообщения всем получателям
        success_count = 0
        fail_count = 0

        for recipient in recipients:
            recipient = recipient.strip()
            if not recipient:
                continue

            print(f"\n=== Sending to {recipient} ===")
            success = await send_message(client, recipient, message)

            if success:
                success_count += 1
            else:
                fail_count += 1

        # Выводим итоги
        print(f"\n--- Summary ---")
        print(f"Total recipients: {len(recipients)}")
        print(f"Successfully sent: {success_count}")
        print(f"Failed: {fail_count}")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Disconnect
        await client.disconnect()
        print("Disconnected from Telegram")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())