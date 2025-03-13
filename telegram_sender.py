import os
import logging
import asyncio
import random
import time
from datetime import datetime
from telethon.client.telegramclient import TelegramClient
from telethon.errors.rpcerrorlist import (
    FloodWaitError, 
    SessionPasswordNeededError, 
    PhoneCodeInvalidError,
    PhoneCodeExpiredError
)
from telethon.tl.types import User, Channel
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
import glob

from anti_spam import AntiSpamThrottler
from utils import create_session_name, format_phone
from models import MessageLog, BroadcastSession
from app import db

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')

class TelegramSender:
    def __init__(self):
        self.client = None
        self.phone_number = None
        self.phone_code_hash = None
        self.throttler = AntiSpamThrottler()
        self.current_broadcast_session = None

    def _get_session_name(self):
        """Get session name for current phone number"""
        if not self.phone_number:
            raise ValueError("Phone number not set")
        return f"session_{self.phone_number.replace('+', '')}"

    def _cleanup_session(self):
        """Clean up session files"""
        try:
            session_name = self._get_session_name()
            session_files = glob.glob(f"{session_name}.*")
            for file in session_files:
                try:
                    os.remove(file)
                    logger.info(f"Removed session file: {file}")
                except Exception as e:
                    logger.error(f"Error removing session file {file}: {e}")
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")

    async def _create_client(self):
        """Create and connect a new client"""
        if not API_ID or not API_HASH:
            raise ValueError("API credentials missing")

        # Clean up old session first
        self._cleanup_session()

        session_name = self._get_session_name()
        logger.info(f"Creating new client with session: {session_name}")

        client = TelegramClient(session_name, int(API_ID), API_HASH)
        await client.connect()
        logger.info("Client connected successfully")
        return client

    def login(self, phone_number):
        """First step of login - request verification code"""
        self.phone_number = format_phone(phone_number)
        logger.info(f"Starting login process for {self.phone_number}")

        loop = asyncio.get_event_loop()
        try:
            result = loop.run_until_complete(self._login_process())
            return result
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise

    async def _login_process(self):
        """Async login implementation"""
        try:
            self.client = await self._create_client()
            logger.info("Client created successfully")

            if await self.client.is_user_authorized():
                logger.info("Already authorized")
                return True

            logger.info("Sending code request")
            sent_code = await self.client.send_code_request(self.phone_number)
            self.phone_code_hash = sent_code.phone_code_hash
            logger.info(f"Code sent, hash: {self.phone_code_hash}")
            return False

        except Exception as e:
            logger.error(f"Login process error: {str(e)}")
            raise

    def verify_code(self, verification_code, two_factor_password=None):
        """Second step of login - verify code and handle 2FA"""
        if not self.phone_number or not self.phone_code_hash:
            raise ValueError("Login process not properly initialized")

        loop = asyncio.get_event_loop()
        try:
            result = loop.run_until_complete(
                self._verify_code_process(verification_code, two_factor_password)
            )
            return result
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            raise

    async def _verify_code_process(self, verification_code, two_factor_password=None):
        """Async verification implementation"""
        try:
            if not self.client or not self.client.is_connected():
                self.client = await self._create_client()

            try:
                logger.info("Attempting to sign in with code")
                # Пробуем войти с предоставленным кодом
                await self.client.sign_in(
                    phone=self.phone_number,
                    code=verification_code,
                    phone_code_hash=self.phone_code_hash
                )
                logger.info("Sign in successful")
                return True

            except SessionPasswordNeededError:
                logger.info("2FA required")
                if not two_factor_password:
                    return "2FA_REQUIRED"

                try:
                    logger.info("Attempting 2FA login")
                    await self.client.sign_in(password=two_factor_password)
                    logger.info("2FA login successful")
                    return True
                except Exception as e:
                    logger.error(f"2FA error: {str(e)}")
                    return False

            except PhoneCodeExpiredError:
                logger.error("Verification code has expired")
                # Пытаемся автоматически запросить новый код вместо вызова исключения
                try:
                    # Сначала отключаемся и очищаем клиент
                    if self.client:
                        await self.client.disconnect()
                        self.client = None
                        
                    # Создаем новый клиент
                    self.client = await self._create_client()
                    
                    # Запрашиваем новый код
                    sent_code = await self.client.send_code_request(self.phone_number)
                    self.phone_code_hash = sent_code.phone_code_hash
                    logger.info(f"Автоматически запрошен новый код, hash: {self.phone_code_hash}")
                    
                    # Возвращаем специальный статус для обновления UI
                    return "CODE_EXPIRED_NEW_SENT"
                except Exception as exp:
                    logger.error(f"Failed to automatically request new code: {exp}")
                    raise ValueError("Код подтверждения истёк и не удалось запросить новый автоматически. Пожалуйста, вернитесь на главную страницу.")

            except PhoneCodeInvalidError:
                logger.error("Invalid verification code")
                raise ValueError("Неверный код подтверждения")

        except Exception as e:
            logger.error(f"Verification process error: {str(e)}")
            raise

    async def send_message(self, recipient, message):
        """Send a message to a recipient"""
        try:
            # Убедимся, что клиент создан и подключен
            if not self.client or not self.client.is_connected():
                self.client = await self._create_client()
                
            if not await self.client.is_user_authorized():
                raise ValueError("Not authorized")
                
            # Check if recipient is a phone number
            is_phone = recipient.startswith('+') or recipient.replace(' ', '').isdigit()

            if is_phone:
                # Format phone number
                formatted_phone = format_phone(recipient)
                logger.info(f"Sending to phone number: {formatted_phone}")

                try:
                    # Try to import contact first
                    contact = InputPhoneContact(
                        client_id=random.randint(1, 100000),
                        phone=formatted_phone,
                        first_name="Contact"
                    )
                    imported = await self.client(ImportContactsRequest([contact]))

                    if imported.users:
                        entity = imported.users[0]
                        logger.info(f"Found user for phone {formatted_phone}")
                    else:
                        entity = formatted_phone
                        logger.info(f"User not found, trying direct send to {formatted_phone}")

                except Exception as e:
                    logger.error(f"Error finding user by phone: {e}")
                    entity = formatted_phone
            else:
                # For username
                if not recipient.startswith('@'):
                    recipient = '@' + recipient
                entity = await self.client.get_entity(recipient)

            # Send message
            result = await self.client.send_message(entity, message)
            if result:
                logger.info(f"Successfully sent message to {recipient}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error sending message to {recipient}: {e}")
            return False

    async def send_bulk_messages(self, recipients, message):
        """Send messages to multiple recipients"""
        if not self.phone_number:
            raise ValueError("Not logged in")

        # Create broadcast session
        with db.app.app_context():
            broadcast_session = BroadcastSession(
                phone_number=self.phone_number,
                recipient_count=len(recipients),
                start_time=datetime.utcnow(),
                status='in_progress'
            )
            db.session.add(broadcast_session)
            db.session.commit()
            self.current_broadcast_session = broadcast_session

        try:
            successful, failed = await self._send_bulk_messages_async(recipients, message)

            # Update session status
            with db.app.app_context():
                broadcast_session.end_time = datetime.utcnow()
                broadcast_session.status = 'completed'
                broadcast_session.successful_count = successful
                broadcast_session.failed_count = failed
                db.session.commit()

            return True, successful, failed

        except Exception as e:
            logger.error(f"Bulk sending failed: {str(e)}")

            # Update session status
            with db.app.app_context():
                broadcast_session.end_time = datetime.utcnow()
                broadcast_session.status = 'failed'
                db.session.commit()

            raise

    async def _send_bulk_messages_async(self, recipients, message):
        """Async implementation of bulk messaging"""
        # Убедимся, что клиент создан и подключен
        if not self.client or not self.client.is_connected():
            self.client = await self._create_client()
            
        if not await self.client.is_user_authorized():
            raise ValueError("Not authorized")

        successful = 0
        failed = 0

        # Get sender info for logging
        me = await self.client.get_me()
        logger.info(f"Sending as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")

        for recipient in recipients:
            try:
                # Apply smart delay
                await self.throttler.smart_delay()

                # Send message
                success = await self.send_message(recipient, message)

                if success:
                    successful += 1
                    self.throttler.record_success()

                    # Log success
                    with db.app.app_context():
                        log = MessageLog(
                            phone_number=self.phone_number,
                            recipient=recipient,
                            message_preview=message[:50] + ('...' if len(message) > 50 else ''),
                            status='success'
                        )
                        db.session.add(log)
                        db.session.commit()
                else:
                    failed += 1
                    self.throttler.record_failure()

                    # Log failure
                    with db.app.app_context():
                        log = MessageLog(
                            phone_number=self.phone_number,
                            recipient=recipient,
                            message_preview=message[:50] + ('...' if len(message) > 50 else ''),
                            status='failed',
                            error_message="Failed to send message"
                        )
                        db.session.add(log)
                        db.session.commit()

            except Exception as e:
                logger.error(f"Error sending to {recipient}: {str(e)}")
                failed += 1
                self.throttler.record_failure()

        return successful, failed