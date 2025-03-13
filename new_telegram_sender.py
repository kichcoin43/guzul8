import asyncio
import logging
import os
import sys
import random
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Conditional import for Telethon
try:
    from telethon import TelegramClient, events, functions
    from telethon.errors import FloodWaitError, SessionPasswordNeededError, PhoneCodeInvalidError
    from telethon.tl.types import User, Channel
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    logger.warning("Telethon not available. Running in demo mode.")

from anti_spam import AntiSpamThrottler
from utils import create_session_name, format_phone
# Импортируем модели только если не работаем в изолированном режиме
try:
    from models import MessageLog, BroadcastSession
    from app import db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logger.warning("Database models not available. Running without database logging.")

# Telegram API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# Demo mode flag
DEMO_MODE = os.environ.get('TELEGRAM_DEMO_MODE', 'False').lower() == 'true'
logger.info(f"DEMO_MODE is set to: {DEMO_MODE}")

class TelegramSender:
    def __init__(self):
        self.demo_mode = DEMO_MODE or not TELETHON_AVAILABLE
        
        if self.demo_mode:
            logger.info("Running in DEMO MODE - no actual messages will be sent")
            self.api_id = 12345  # Dummy values
            self.api_hash = '0123456789abcdef0123456789abcdef'  # Dummy values
        else:
            # Check if API credentials are available
            if not API_ID or not API_HASH:
                logger.warning("Telegram API credentials not found in environment variables.")
                self.api_id = None
                self.api_hash = None
            else:
                self.api_id = int(API_ID)
                self.api_hash = API_HASH
                
        # Will be set during login
        self.phone_number = None
        self.phone_code_hash = None
        
    def login(self, phone_number):
        """
        Login to Telegram with a phone number - first step (requesting verification code)
        
        Args:
            phone_number (str): The phone number with country code
            
        Returns:
            bool: True if already logged in, False if verification code needed
        """
        self.phone_number = format_phone(phone_number)
        
        if self.demo_mode:
            # Simulate login process in demo mode
            logger.info(f"[DEMO] Initiating login for {self.phone_number}")
            # Random choice if we need verification or are already authorized
            already_authorized = random.choice([True, False])
            if already_authorized:
                logger.info("[DEMO] Already authorized, no verification needed")
                return True
            else:
                logger.info("[DEMO] Verification code needed")
                # Generate a fake phone_code_hash
                self.phone_code_hash = ''.join(random.choices('abcdef0123456789', k=32))
                return False
                
        else:
            # Real login process
            logger.info(f"Initiating login for {self.phone_number}")
            
            # Run async login process
            result = asyncio.run(self._login_process(self.phone_number))
            
            if isinstance(result, tuple):
                # Need verification
                _, self.phone_code_hash = result
                return False
            else:
                # Already logged in
                return True
    
    def verify_code(self, verification_code):
        """
        Verify the Telegram code (second step of login process)
        
        Args:
            verification_code (str): The verification code sent to the phone
            
        Returns:
            bool: True if verification successful
        """
        if self.demo_mode:
            # Simulate verification in demo mode
            logger.info(f"[DEMO] Verifying code for {self.phone_number}")
            # Usually succeed in demo mode
            success = random.random() < 0.9
            if success:
                logger.info("[DEMO] Verification successful")
                return True
            else:
                logger.error("[DEMO] Verification failed")
                return False
                
        else:
            # Real verification process
            logger.info(f"Verifying code for {self.phone_number}")
            
            if not self.phone_code_hash:
                logger.error("Cannot verify code without phone_code_hash")
                return False
                
            # Run async verification process
            return asyncio.run(self._verify_code_process(verification_code))
    
    async def _verify_code_process(self, verification_code):
        """
        Async implementation of code verification
        
        Args:
            verification_code (str): The verification code sent to the phone
        """
        if not self.phone_number or not self.phone_code_hash:
            logger.error("Phone number or phone_code_hash is missing")
            return False
            
        session_name = create_session_name(self.phone_number)
        client = TelegramClient(session_name, self.api_id, self.api_hash)
        
        try:
            await client.connect()
            
            try:
                # Try to sign in with the code
                await client.sign_in(
                    phone=self.phone_number,
                    code=verification_code,
                    phone_code_hash=self.phone_code_hash
                )
                
                # Check if it worked
                if await client.is_user_authorized():
                    logger.info("Verification successful")
                    return True
                else:
                    logger.error("Verification did not result in authorization")
                    return False
            
            except SessionPasswordNeededError:
                logger.error("Two-factor authentication (2FA) is enabled but not supported in this app yet")
                return False
                
            except PhoneCodeInvalidError:
                logger.error("Invalid verification code")
                return False
                
            except Exception as e:
                logger.error(f"Error during verification: {e}")
                return False
        
        finally:
            await client.disconnect()
    
    async def _login_process(self, phone_number):
        """
        Async login process
        
        Args:
            phone_number (str): The phone number with country code
            
        Returns:
            bool or tuple: True if already authorized, otherwise (False, phone_code_hash)
        """
        session_name = create_session_name(phone_number)
        client = TelegramClient(session_name, self.api_id, self.api_hash)
        
        try:
            await client.connect()
            
            # Check if already authorized
            if await client.is_user_authorized():
                logger.info(f"Session {session_name} is already authorized")
                return True
                
            # Send code request
            result = await client.send_code_request(phone_number)
            logger.info(f"Code request sent to {phone_number}, phone_code_hash: {result.phone_code_hash}")
            
            # Return phone_code_hash for later verification
            return False, result.phone_code_hash
        
        finally:
            await client.disconnect()
    
    def send_bulk_messages(self, recipients, message):
        """
        Send messages to multiple recipients with anti-spam measures
        
        Args:
            recipients (list): List of recipient usernames or phone numbers
            message (str): Message to send
            
        Returns:
            tuple: (success_status, successful_count, failed_count)
        """
        if self.demo_mode:
            # Simulate bulk messaging in demo mode
            return self._send_demo_messages(recipients, message)
        else:
            # Real sending process
            logger.info(f"Starting bulk sending to {len(recipients)} recipients")
            return asyncio.run(self._send_bulk_messages_async(recipients, message))
    
    def _send_demo_messages(self, recipients, message):
        """
        Simulate sending messages in demo mode
        
        Args:
            recipients (list): List of recipient usernames or phone numbers
            message (str): Message to send
            
        Returns:
            tuple: (successful, failed) counts
        """
        # Run the async implementation in a sync context for demo mode
        return asyncio.run(self._send_demo_messages_async(recipients, message))
    
    async def _send_demo_messages_async(self, recipients, message):
        """
        Simulate sending messages in demo mode
        
        Args:
            recipients (list): List of recipient usernames or phone numbers
            message (str): Message to send
            
        Returns:
            tuple: (successful, failed) counts
        """
        logger.info(f"[DEMO] Sending message to {len(recipients)} recipients")
        
        # Create a broadcast session record if DB is available
        if DB_AVAILABLE:
            broadcast_session = BroadcastSession(
                phone_number=self.phone_number or "demo",
                recipient_count=len(recipients),
                start_time=datetime.utcnow()
            )
            db.session.add(broadcast_session)
            db.session.commit()
        
        successful = 0
        failed = 0
        
        # Simulate processing delay and success/failure
        total_wait_time = min(len(recipients) * 0.5, 3)  # Cap at 3 seconds
        await asyncio.sleep(total_wait_time)
        
        for recipient in recipients:
            # 90% chance of success in demo mode
            if random.random() < 0.9:
                successful += 1
                logger.info(f"[DEMO] ✅ Message to {recipient} sent successfully")
                
                # Log success if DB is available
                if DB_AVAILABLE:
                    log_entry = MessageLog(
                        phone_number=self.phone_number or "demo",
                        recipient=recipient,
                        message_preview=message[:50] + ('...' if len(message) > 50 else ''),
                        status='success'
                    )
                    db.session.add(log_entry)
            else:
                failed += 1
                error_message = random.choice([
                    "User not found",
                    "User has blocked messages",
                    "Rate limited by Telegram"
                ])
                logger.warning(f"[DEMO] ❌ Failed to send to {recipient}: {error_message}")
                
                # Log failure if DB is available
                if DB_AVAILABLE:
                    log_entry = MessageLog(
                        phone_number=self.phone_number or "demo",
                        recipient=recipient,
                        message_preview=message[:50] + ('...' if len(message) > 50 else ''),
                        status='failed',
                        error_message=error_message
                    )
                    db.session.add(log_entry)
        
        # Update broadcast session if DB is available
        if DB_AVAILABLE:
            broadcast_session.status = 'completed'
            broadcast_session.end_time = datetime.utcnow()
            broadcast_session.successful_count = successful
            broadcast_session.failed_count = failed
            db.session.commit()
        
        logger.info(f"[DEMO] Bulk sending completed. Success: {successful}, Failed: {failed}")
        return 'completed', successful, failed
        
    async def _send_bulk_messages_async(self, recipients, message):
        """
        Async implementation of bulk messaging - использует упрощенный подход, который точно работает
        
        Args:
            recipients (list): List of recipient usernames or phone numbers
            message (str): Message to send
        """
        # Create and initialize client
        session_name = create_session_name(self.phone_number)
        client = TelegramClient(session_name, self.api_id, self.api_hash)
        
        # Anti-spam throttler for smart delays
        throttler = AntiSpamThrottler()
        
        # Statistics
        successful_count = 0
        failed_count = 0
        errors = {}
        
        # Create broadcast session record if DB is available
        if DB_AVAILABLE:
            broadcast_session = BroadcastSession(
                phone_number=self.phone_number,
                recipient_count=len(recipients),
                start_time=datetime.utcnow()
            )
            db.session.add(broadcast_session)
            db.session.commit()
        
        try:
            # Connect and check auth
            logger.info(f"Connecting to Telegram with session {session_name}...")
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.error(f"Session {session_name} is not authorized")
                if DB_AVAILABLE:
                    broadcast_session.status = 'failed'
                    broadcast_session.end_time = datetime.utcnow()
                    db.session.commit()
                return 'failed', 0, len(recipients)
                
            # Log sender information
            me = await client.get_me()
            logger.info(f"Sending as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'}) Phone: {me.phone}")
            
            # Process each recipient
            for recipient in recipients:
                logger.info(f"Sending message to {recipient}...")
                
                try:
                    # Apply smart delay to avoid Telegram rate limits
                    await throttler.smart_delay()
                    
                    # Простой способ отправки сообщения, который работает в direct_send.py
                    try:
                        # Пробуем найти получателя
                        entity = await client.get_entity(recipient)
                        logger.info(f"Found recipient: {entity.id}, {getattr(entity, 'username', 'no username')}")
                    except Exception as user_error:
                        logger.warning(f"Could not find recipient {recipient}: {str(user_error)}")
                        raise
                    
                    # Отправляем сообщение напрямую
                    result = await client.send_message(entity, message)
                    logger.info(f"✅ Message to {recipient} sent successfully! Message ID: {result.id}")
                    
                    # Record success
                    successful_count += 1
                    throttler.record_success()
                    
                    # Create successful message log if DB is available
                    if DB_AVAILABLE:
                        message_log = MessageLog(
                            phone_number=self.phone_number,
                            recipient=recipient,
                            message_preview=message[:50] + ('...' if len(message) > 50 else ''),
                            status='success'
                        )
                        db.session.add(message_log)
                        db.session.commit()
                    
                except FloodWaitError as flood_error:
                    # Handle Telegram's flood wait restriction
                    wait_seconds = flood_error.seconds
                    logger.warning(f"⚠️ Hit FloodWaitError, need to wait {wait_seconds} seconds")
                    
                    # Adjust throttling params
                    throttler.adjust_for_flood_wait(wait_seconds)
                    
                    # Record the error
                    errors[recipient] = f"Rate limit exceeded, waiting {wait_seconds}s"
                    failed_count += 1
                    
                    # Create failed message log if DB is available
                    if DB_AVAILABLE:
                        message_log = MessageLog(
                            phone_number=self.phone_number,
                            recipient=recipient,
                            message_preview=message[:50] + ('...' if len(message) > 50 else ''),
                            status='failed',
                            error_message=f"Rate limit exceeded, waiting {wait_seconds}s"
                        )
                        db.session.add(message_log)
                        db.session.commit()
                    
                    # Wait according to Telegram's restriction
                    if wait_seconds < 60:  # Only wait for short delays
                        await asyncio.sleep(wait_seconds)
                    else:
                        # For longer waits, update broadcast session and exit
                        if DB_AVAILABLE:
                            broadcast_session.status = 'failed'
                            broadcast_session.end_time = datetime.utcnow()
                            broadcast_session.successful_count = successful_count
                            broadcast_session.failed_count = failed_count
                            db.session.commit()
                        return 'flood_limited', successful_count, failed_count
                
                except Exception as e:
                    # Handle other errors
                    error_message = str(e)
                    logger.error(f"❌ Error sending to {recipient}: {error_message}")
                    
                    # Record the error
                    errors[recipient] = error_message
                    failed_count += 1
                    throttler.record_failure()
                    
                    # Create failed message log if DB is available
                    if DB_AVAILABLE:
                        message_log = MessageLog(
                            phone_number=self.phone_number,
                            recipient=recipient,
                            message_preview=message[:50] + ('...' if len(message) > 50 else ''),
                            status='failed',
                            error_message=error_message
                        )
                        db.session.add(message_log)
                        db.session.commit()
        
        except Exception as e:
            # Handle general errors
            logger.error(f"General error in bulk sending: {e}")
            if DB_AVAILABLE:
                broadcast_session.status = 'failed'
                broadcast_session.end_time = datetime.utcnow()
                broadcast_session.successful_count = successful_count
                broadcast_session.failed_count = failed_count
                db.session.commit()
            return 'error', successful_count, failed_count
        
        finally:
            # Disconnect client
            await client.disconnect()
            logger.info("Disconnected from Telegram API")
        
        # Update broadcast session record if DB is available
        if DB_AVAILABLE:
            broadcast_session.status = 'completed'
            broadcast_session.end_time = datetime.utcnow()
            broadcast_session.successful_count = successful_count
            broadcast_session.failed_count = failed_count
            db.session.commit()
        
        logger.info(f"Bulk messaging completed. Success: {successful_count}, Failed: {failed_count}")
        return 'completed', successful_count, failed_count

# Function to send a single message - convenience method
async def send_single_message(recipient, message, session_name=None):
    """
    Отправляет одно сообщение указанному получателю
    
    Args:
        recipient (str): Username или телефон получателя
        message (str): Текст сообщения
        session_name (str): Имя файла сессии для использования
    
    Returns:
        bool: True если сообщение отправлено успешно
    """
    if not API_ID or not API_HASH:
        logger.error("API_ID or API_HASH not found in environment variables")
        return False
    
    # Используем существующую сессию или берем из списка доступных
    if not session_name:
        from utils import get_session_files
        session_files = get_session_files()
        if not session_files:
            logger.error("No session files found")
            return False
        session_name = session_files[0].split('.')[0]  # Берем первую доступную сессию
    
    # Создаем клиент Telegram
    client = TelegramClient(session_name, int(API_ID), API_HASH)
    
    try:
        # Подключаемся
        logger.info(f"Connecting to Telegram with session {session_name}...")
        await client.connect()
        
        # Проверяем авторизацию
        if not await client.is_user_authorized():
            logger.error(f"Session {session_name} is not authorized")
            return False
        
        # Информация об отправителе
        me = await client.get_me()
        logger.info(f"Sending as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'}) Phone: {me.phone}")
        
        # Отправляем сообщение
        logger.info(f"Sending message to {recipient}...")
        
        try:
            # Получаем данные о получателе
            entity = await client.get_entity(recipient)
            logger.info(f"Found recipient: {entity.id}, {getattr(entity, 'username', 'no username')}")
            
            # Отправляем сообщение
            result = await client.send_message(entity, message)
            logger.info(f"✅ Message sent successfully! Message ID: {result.id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending message: {str(e)}")
            return False
    
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return False
    
    finally:
        # Отключаемся
        await client.disconnect()
        logger.info("Disconnected from Telegram API")

# Если скрипт запущен напрямую
if __name__ == "__main__":
    # Проверить аргументы командной строки
    if len(sys.argv) < 3:
        print("Usage: python telegram_sender.py RECIPIENT MESSAGE")
        print("Example: python telegram_sender.py @username 'Hello world'")
        sys.exit(1)
    
    recipient = sys.argv[1]
    message = sys.argv[2]
    
    # Отправить сообщение
    success = asyncio.run(send_single_message(recipient, message))
    
    if success:
        print("Message sent successfully!")
    else:
        print("Failed to send message.")
        sys.exit(1)