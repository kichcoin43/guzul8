import os
import logging
from typing import Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения информации о подключении к Twilio
twilio_available = False

# Попытка импорта библиотеки Twilio
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    twilio_available = True
except ImportError:
    logger.warning("Twilio library not installed. SMS notifications will not be available.")

# Константы для доступа к переменным окружения
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

def check_twilio_config() -> bool:
    """
    Проверяет наличие настроек Twilio в переменных окружения
    
    Returns:
        bool: True если все настройки найдены, False иначе
    """
    if not twilio_available:
        return False
        
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        logger.warning("Missing Twilio configuration in environment variables")
        return False
        
    return True

def send_sms_notification(to_phone: str, message: str) -> tuple[bool, Optional[str]]:
    """
    Отправляет SMS-уведомление через Twilio API
    
    Args:
        to_phone (str): Номер телефона получателя в международном формате (+1XXXYYYZZZZ)
        message (str): Текст сообщения
        
    Returns:
        tuple: (успех, сообщение об ошибке или None)
    """
    # Проверка конфигурации
    if not check_twilio_config():
        return False, "Twilio not configured properly. Check environment variables."
    
    # Проверка номера телефона
    if not to_phone or not to_phone.startswith('+'):
        return False, "Invalid phone number format. Must start with + and country code."
    
    # Проверка сообщения
    if not message or len(message) == 0:
        return False, "Message cannot be empty"
    
    # Инициализация клиента Twilio
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Отправка сообщения
        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        logger.info(f"SMS sent successfully to {to_phone}. SID: {sms.sid}")
        return True, None
        
    except TwilioRestException as e:
        error_msg = f"Twilio error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error sending SMS: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def send_broadcast_notification(admin_phone: str, message_count: int, success_count: int) -> None:
    """
    Отправляет уведомление администратору о завершении рассылки
    
    Args:
        admin_phone (str): Номер телефона администратора
        message_count (int): Общее количество сообщений в рассылке
        success_count (int): Количество успешно отправленных сообщений
    """
    if not check_twilio_config():
        logger.warning("Cannot send broadcast notification: Twilio not configured")
        return
        
    message = (
        f"Broadcast completed!\n"
        f"Total messages: {message_count}\n"
        f"Successfully sent: {success_count}\n"
        f"Failed: {message_count - success_count}"
    )
    
    success, error = send_sms_notification(admin_phone, message)
    if not success:
        logger.warning(f"Failed to send broadcast notification: {error}")