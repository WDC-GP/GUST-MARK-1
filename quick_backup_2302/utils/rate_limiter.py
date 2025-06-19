"""
"""
"""
GUST Bot Enhanced - Rate Limiter
===============================
Simple rate limiter implementation for G-Portal API
"""

# Standard library imports
from collections import defaultdict
import time



class RateLimiter:
    """Simple rate limiter implementation for G-Portal API"""
    
    def __init__(self, max_calls=5, time_window=1):
        """
        Initialize rate limiter
        
        Args:
            max_calls (int): Maximum number of calls allowed in time window
            time_window (int): Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = defaultdict(list)
    
    def is_allowed(self, key="default"):
        """
        Check if a call is allowed for the given key
        
        Args:
            key (str): Identifier for rate limiting (e.g., user ID, API endpoint)
            
        Returns:
            bool: True if call is allowed, False otherwise
        """
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls[key] = [call_time for call_time in self.calls[key] 
                          if now - call_time < self.time_window]
        
        # Check if we can make a new call
        if len(self.calls[key]) < self.max_calls:
            self.calls[key].append(now)
            return True
        return False
    
    def wait_if_needed(self, key="default"):
        """
        Wait if necessary to respect rate limits
        
        Args:
            key (str): Identifier for rate limiting
        """
        while not self.is_allowed(key):
            time.sleep(0.1)
    
    def get_remaining_calls(self, key="default"):
        """
        Get remaining calls for the given key
        
        Args:
            key (str): Identifier for rate limiting
            
        Returns:
            int: Number of remaining calls in current window
        """
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls[key] = [call_time for call_time in self.calls[key] 
                          if now - call_time < self.time_window]
        
        return max(0, self.max_calls - len(self.calls[key]))
    
    def get_reset_time(self, key="default"):
        """
        Get time until rate limit resets for the given key
        
        Args:
            key (str): Identifier for rate limiting
            
        Returns:
            float: Seconds until rate limit resets
        """
        if key not in self.calls or not self.calls[key]:
            return 0.0
        
        now = time.time()
        oldest_call = min(self.calls[key])
        reset_time = oldest_call + self.time_window - now
        
        return max(0.0, reset_time)
    
    def clear_key(self, key):
        """
        Clear rate limiting history for a specific key
        
        Args:
            key (str): Key to clear
        """
        if key in self.calls:
            del self.calls[key]
    
    def clear_all(self):
        """Clear all rate limiting history"""
        self.calls.clear()
    
    def get_status(self, key="default"):
        """
        Get comprehensive status for a key
        
        Args:
            key (str): Identifier for rate limiting
            
        Returns:
            dict: Status information including remaining calls, reset time, etc.
        """
        return {
            "key": key,
            "max_calls": self.max_calls,
            "time_window": self.time_window,
            "remaining_calls": self.get_remaining_calls(key),
            "reset_time": self.get_reset_time(key),
            "is_allowed": self.get_remaining_calls(key) > 0
        }
