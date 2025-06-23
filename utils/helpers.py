"""
GUST Bot Utils - Main Helpers Compatibility Shim
===============================================
This file provides backwards compatibility by importing all functions
from the new organized core/helpers.py location.
"""

# Import everything from the new core location
try:
    from .core.helpers import *
    print("✅ Main helpers loaded from core/helpers.py")
except ImportError as e:
    print(f"❌ Failed to import from core/helpers: {e}")
    
    # Provide minimal fallback functions if core helpers fails
    def safe_int(value, default=0):
        """Safe integer conversion with fallback"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def safe_str(value, default=""):
        """Safe string conversion with fallback"""
        try:
            return str(value) if value is not None else default
        except:
            return default
    
    def load_token():
        """Fallback token loader"""
        return "fallback_token"
    
    print("⚠️ Using minimal fallback functions")

# Ensure all core functions are available for backwards compatibility
__all__ = [
    'safe_int', 'safe_str', 'load_token', 'save_token', 'refresh_token',
    'get_auth_headers', 'validate_server_id', 'format_command', 
    'parse_console_response', 'classify_message', 'format_bytes'
]
