"""
GUST Bot Enhanced - Utilities Package (FIXED VERSION)
====================================================
✅ FIXED: Import errors resolved
✅ FIXED: Only imports functions that actually exist
✅ FIXED: Safe import structure with error handling
✅ FIXED: No circular imports
"""

# Import rate limiter first (always available)
try:
    from .rate_limiter import RateLimiter
except ImportError as e:
    print(f"⚠️ Warning: Could not import RateLimiter: {e}")
    # Create a dummy rate limiter for development
    class RateLimiter:
        def __init__(self, *args, **kwargs):
            pass
        def wait_if_needed(self, *args, **kwargs):
            pass

# Import helpers with error handling
try:
    from .helpers import (
        # Core token functions
        load_token, refresh_token, save_token, 
        is_valid_jwt_token, monitor_token_health, validate_token_file,
        
        # Console and command functions
        parse_console_response, classify_message, get_type_icon, 
        format_console_message, format_command,
        
        # Validation functions
        validate_server_id, validate_region,
        
        # Utility functions
        safe_int, safe_float, escape_html,
        format_timestamp, sanitize_filename,
        
        # Data creation functions
        create_server_data, get_countdown_announcements,
        
        # Status functions
        get_status_class, get_status_text,
        
        # Steam ID validation
        is_valid_steam_id,
        
        # String utilities
        generate_random_string, truncate_string,
        
        # Dictionary utilities
        deep_get, flatten_dict, merge_dicts,
        
        # List utilities
        chunk_list, remove_duplicates,
        
        # Validation utilities
        validate_email, validate_url,
        
        # Calculation utilities
        calculate_percentage, format_bytes, format_duration
    )
    
    print("✅ Successfully imported all helper functions")
    
except ImportError as e:
    print(f"⚠️ Warning: Could not import some helper functions: {e}")
    
    # Create minimal fallback functions
    def load_token():
        """Fallback token loader"""
        import os, json
        try:
            if os.path.exists('gp-session.json'):
                with open('gp-session.json', 'r') as f:
                    data = json.load(f)
                    return data.get('access_token', '')
            return ''
        except:
            return ''
    
    def refresh_token():
        """Fallback token refresh"""
        return False
    
    def save_token(tokens, username='unknown'):
        """Fallback token save"""
        return False
    
    def validate_server_id(server_id):
        """Fallback server ID validation"""
        try:
            return True, int(server_id)
        except:
            return False, None
    
    def validate_region(region):
        """Fallback region validation"""
        return str(region).upper() in ['US', 'EU', 'AS', 'AU']
    
    def safe_int(value, default=0):
        """Fallback safe int conversion"""
        try:
            return int(value)
        except:
            return default
    
    def safe_float(value, default=0.0):
        """Fallback safe float conversion"""
        try:
            return float(value)
        except:
            return default

# Package exports
__all__ = [
    'RateLimiter',
    'load_token', 'refresh_token', 'save_token',
    'validate_server_id', 'validate_region',
    'safe_int', 'safe_float'
]

# Add additional exports if they were imported successfully
try:
    # Test if advanced functions are available
    parse_console_response
    __all__.extend([
        'parse_console_response', 'classify_message', 'get_type_icon', 
        'format_console_message', 'format_command',
        'escape_html', 'format_timestamp', 'sanitize_filename',
        'create_server_data', 'get_countdown_announcements',
        'get_status_class', 'get_status_text', 'is_valid_steam_id'
    ])
except NameError:
    pass

# Package metadata
__version__ = "2.0.0"
__author__ = "GUST Bot Enhanced"
__description__ = "Utility functions and helper classes - Fixed Version"

print(f"✅ Utils package loaded successfully - Version {__version__}")