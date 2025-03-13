import asyncio
import logging
import random
import time
import os
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AntiSpamThrottler:
    """
    Class that handles smart throttling to avoid Telegram's spam detection
    """
    def __init__(self):
        # Initialize with conservative values
        self.min_delay = float(os.environ.get('MIN_DELAY', '1.5'))  # Minimum delay between messages in seconds
        self.max_delay = float(os.environ.get('MAX_DELAY', '5.5'))  # Maximum delay between messages in seconds
        self.consecutive_successes = 0  # Counter for consecutive successful sends
        self.consecutive_failures = 0  # Counter for consecutive failures
        self.last_flood_wait = 0  # Last flood wait time imposed by Telegram
        self.total_messages_sent = 0  # Total messages sent in current session
        self.session_start_time = datetime.now()  # Start time of current session
        
        # Advanced parameters
        self.adaptive_factor = 1.0  # Multiplier for delays, increases with failures
        self.max_adaptive_factor = 5.0  # Maximum adaptive factor
        self.recovery_threshold = 10  # Number of successful messages before reducing adaptive factor
        
        # Rate limiting
        self.hourly_limit = int(os.environ.get('MAX_HOURLY_MESSAGES', '40'))  # Configurable limit for messages per hour
        self.daily_limit = int(os.environ.get('MAX_DAILY_MESSAGES', '200'))  # Configurable limit for messages per day
        self.hourly_sent = 0  # Counter for messages sent in the last hour
        self.daily_sent = 0  # Counter for messages sent in the last day
        self.last_hour_reset = datetime.now()  # Timestamp of last hourly counter reset
        self.last_day_reset = datetime.now()  # Timestamp of last daily counter reset
    
    async def smart_delay(self):
        """Apply a smart delay before sending the next message"""
        # Reset counters if needed
        self._reset_counters_if_needed()
        
        # Check rate limits
        if self._is_rate_limited():
            logger.warning("Rate limit reached, applying additional delay")
            await asyncio.sleep(60)  # Wait a minute if we're close to rate limits
        
        # Calculate base delay
        current_delay = random.uniform(
            self.min_delay * self.adaptive_factor, 
            self.max_delay * self.adaptive_factor
        )
        
        # Add jitter for more natural behavior (±15%)
        jitter = random.uniform(-0.15, 0.15) * current_delay
        final_delay = max(0.5, current_delay + jitter)  # Ensure minimum delay of 0.5s
        
        logger.debug(f"Applying delay of {final_delay:.2f}s before next message")
        await asyncio.sleep(final_delay)
        return final_delay
    
    def record_success(self):
        """Record a successful message send"""
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.total_messages_sent += 1
        self.hourly_sent += 1
        self.daily_sent += 1
        
        # Gradually reduce adaptive factor after consecutive successes
        if self.consecutive_successes >= self.recovery_threshold and self.adaptive_factor > 1.0:
            self.adaptive_factor = max(1.0, self.adaptive_factor * 0.9)
            logger.debug(f"Reducing adaptive factor to {self.adaptive_factor:.2f}")
    
    def record_failure(self):
        """Record a failed message send"""
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        
        # Increase adaptive factor on failure
        self.adaptive_factor = min(
            self.max_adaptive_factor, 
            self.adaptive_factor * (1.0 + 0.5 * self.consecutive_failures)
        )
        logger.debug(f"Increasing adaptive factor to {self.adaptive_factor:.2f}")
    
    def adjust_for_flood_wait(self, wait_seconds):
        """
        Adjust parameters after a FloodWaitError
        
        Args:
            wait_seconds (int): The wait time imposed by Telegram
        """
        self.last_flood_wait = wait_seconds
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        
        # Adjust adaptive factor based on wait time
        factor_increase = min(3.0, wait_seconds / 10.0)
        self.adaptive_factor = min(
            self.max_adaptive_factor,
            self.adaptive_factor * (1.0 + factor_increase)
        )
        
        # Adjust limits if the wait is significant
        if wait_seconds > 60:
            self.hourly_limit = max(10, int(self.hourly_limit * 0.7))
            logger.warning(f"Reducing hourly limit to {self.hourly_limit} messages")
        
        logger.debug(f"Adjusted for flood wait: {wait_seconds}s, new adaptive factor: {self.adaptive_factor:.2f}")
    
    def _reset_counters_if_needed(self):
        """Reset hour and day counters if needed"""
        now = datetime.now()
        
        # Reset hourly counter if an hour has passed
        if now - self.last_hour_reset > timedelta(hours=1):
            logger.debug(f"Resetting hourly counter. Sent {self.hourly_sent} messages in the last hour")
            self.hourly_sent = 0
            self.last_hour_reset = now
        
        # Reset daily counter if a day has passed
        if now - self.last_day_reset > timedelta(days=1):
            logger.debug(f"Resetting daily counter. Sent {self.daily_sent} messages in the last day")
            self.daily_sent = 0
            self.last_day_reset = now
    
    def _is_rate_limited(self):
        """Check if we're approaching rate limits"""
        # Conservative approach: stay 20% below limits
        hourly_threshold = int(self.hourly_limit * 0.8)
        daily_threshold = int(self.daily_limit * 0.8)
        
        if self.hourly_sent >= hourly_threshold:
            logger.warning(f"Approaching hourly limit: {self.hourly_sent}/{self.hourly_limit}")
            return True
        
        if self.daily_sent >= daily_threshold:
            logger.warning(f"Approaching daily limit: {self.daily_sent}/{self.daily_limit}")
            return True
        
        return False
    
    def get_status(self):
        """Return current status as a dictionary"""
        return {
            "adaptive_factor": round(self.adaptive_factor, 2),
            "messages_sent": self.total_messages_sent,
            "hourly_sent": self.hourly_sent,
            "daily_sent": self.daily_sent,
            "hourly_limit": self.hourly_limit,
            "daily_limit": self.daily_limit,
            "session_duration": str(datetime.now() - self.session_start_time).split('.')[0]  # Format as HH:MM:SS
        }