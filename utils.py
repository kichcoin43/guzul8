import logging
import re
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def is_phone_number(text):
    """
    Check if a given text represents a phone number
    
    Args:
        text (str): The text to check
        
    Returns:
        bool: True if it's a phone number, False otherwise
    """
    # Basic check for international format: +[country code][number]
    # This is a simplified pattern, real validation would be more complex
    pattern = r'^\+[0-9]{7,15}$'
    return bool(re.match(pattern, text))

def format_phone(phone_number):
    """
    Format a phone number for Telegram (with country code)
    
    Args:
        phone_number (str): The phone number to format
        
    Returns:
        str: Formatted phone number
    """
    # Remove any non-digit characters except the plus sign
    formatted = re.sub(r'[^0-9+]', '', phone_number)
    
    # Ensure it starts with a plus sign
    if not formatted.startswith('+'):
        formatted = '+' + formatted
    
    return formatted

def create_session_name(phone_number):
    """
    Create a safe session file name from a phone number
    
    Args:
        phone_number (str): The phone number
        
    Returns:
        str: Safe session name
    """
    # Remove the plus sign and any other non-alphanumeric characters
    safe_name = re.sub(r'[^0-9a-zA-Z]', '', phone_number)
    return f"session_{safe_name}"

def validate_recipients(recipients):
    """
    Validate a list of recipient usernames or phone numbers
    
    Args:
        recipients (list): List of recipient identifiers
        
    Returns:
        tuple: (valid_recipients, invalid_recipients)
    """
    valid = []
    invalid = []
    
    for recipient in recipients:
        # Clean up the recipient identifier
        clean_recipient = recipient.strip()
        
        # Skip empty entries
        if not clean_recipient:
            continue
        
        # Check if it's a username or phone number based on format
        format_valid = False
        error_reason = "Неизвестный формат"
        
        if clean_recipient.startswith('@'):
            # Username format validation
            username = clean_recipient[1:]  # Remove @ symbol
            if re.match(r'^[a-zA-Z][a-zA-Z0-9_]{3,30}$', username):
                format_valid = True
            else:
                error_reason = "Некорректный формат имени пользователя. Допустимы буквы, цифры и знак подчеркивания."
        elif is_phone_number(clean_recipient):
            # Phone number format
            format_valid = True 
        else:
            # Try to handle usernames without @
            if re.match(r'^[a-zA-Z][a-zA-Z0-9_]{3,30}$', clean_recipient):
                clean_recipient = '@' + clean_recipient
                format_valid = True
            else:
                error_reason = "Ни имя пользователя, ни телефонный номер. Проверьте формат."
        
        # Add to appropriate list
        if format_valid:
            valid.append(clean_recipient)
            logger.info(f"Recipient {clean_recipient} passed format validation")
        else:
            invalid.append((clean_recipient, error_reason))
            logger.warning(f"Recipient {clean_recipient} failed validation: {error_reason}")
    
    logger.info(f"Validated {len(valid)} recipients, found {len(invalid)} invalid")
    return valid, invalid

def get_session_files():
    """
    Get a list of all session files in the current directory
    
    Returns:
        list: List of session files
    """
    session_files = []
    for file in os.listdir('.'):
        if file.startswith('session_') and file.endswith('.session'):
            session_files.append(file)
    return session_files