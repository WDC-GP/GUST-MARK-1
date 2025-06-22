"""
GUST Bot Enhanced - Data Utilities Module (FIXED VERSION)
=========================================================
✅ CRITICAL FIX: validate_server_id now properly handles int/string input
✅ CRITICAL FIX: All validation functions handle type conversion safely
✅ PRESERVED: All existing functionality from monolithic helpers.py
✅ ENHANCED: Better error handling and type safety

This fixes the 'int' object has no attribute 'strip' error in console commands.
"""

import os
import json
import math
import random
import string
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any
import logging

logger = logging.getLogger(__name__)

# ================================================================
# ✅ CRITICAL FIX: VALIDATION UTILITIES
# ================================================================

def validate_server_id(server_id):
    """
    ✅ FIXED: Validate server ID format with proper type handling
    
    This function now properly handles both integer and string inputs,
    fixing the 'int' object has no attribute 'strip' error.
    
    Args:
        server_id: Server ID to validate (int, str, or other)
        
    Returns:
        tuple: (is_valid, validated_id)
    """
    try:
        # ✅ CRITICAL FIX: Handle None input
        if server_id is None:
            return False, None
        
        # ✅ CRITICAL FIX: Convert to string first, then validate
        if isinstance(server_id, int):
            # Integer server IDs are valid - convert to string for processing
            server_id_str = str(server_id)
        elif isinstance(server_id, str):
            # String input - use as-is but strip whitespace
            server_id_str = server_id.strip()
        else:
            # Other types - try to convert to string
            try:
                server_id_str = str(server_id).strip()
            except Exception:
                return False, None
        
        # ✅ CRITICAL FIX: Validate the string representation
        if not server_id_str:
            return False, None
        
        # Handle test server IDs and extract base ID
        if '_test' in server_id_str.lower():
            server_id_str = server_id_str.split('_')[0]
        
        # ✅ CRITICAL FIX: Return appropriate type based on input
        if server_id_str.isdigit():
            server_id_int = int(server_id_str)
            if server_id_int > 0:
                # Return integer for numeric server IDs (this is what the original expected)
                return True, server_id_int
            else:
                return False, None
        elif server_id_str.isalnum() and len(server_id_str) > 0:
            # Return string for alphanumeric server IDs
            return True, server_id_str
        else:
            return False, None
            
    except (ValueError, TypeError) as e:
        logger.debug(f"Server ID validation error: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error validating server ID: {e}")
        return False, None

def validate_region(region):
    """
    ✅ FIXED: Validate server region with proper type handling
    
    Args:
        region: Region to validate (str or other)
        
    Returns:
        bool: True if valid region
    """
    try:
        if not region:
            return False
        
        # ✅ CRITICAL FIX: Convert to string if needed
        if not isinstance(region, str):
            try:
                region = str(region)
            except Exception:
                return False
        
        region_clean = region.strip().upper()
        valid_regions = ['US', 'EU', 'AS', 'AU', 'OCE', 'SA']
        return region_clean in valid_regions
        
    except Exception as e:
        logger.debug(f"Region validation error: {e}")
        return False

def get_server_region(server_id):
    """
    ✅ PRESERVED: Extract region from server ID (original functionality)
    
    Args:
        server_id: Server ID (int or str)
        
    Returns:
        str: Server region
    """
    try:
        if not server_id:
            return 'US'
        
        # ✅ CRITICAL FIX: Convert to string safely
        server_id_str = str(server_id).lower()
        
        # Common G-Portal region patterns
        if server_id_str.startswith('us-'):
            return 'US'
        elif server_id_str.startswith('eu-'):
            return 'EU'
        elif server_id_str.startswith('as-'):
            return 'AS'
        else:
            return 'US'  # Default fallback
            
    except Exception:
        return 'US'

# ================================================================
# ✅ PRESERVED: SAFE TYPE CONVERSION UTILITIES
# ================================================================

def safe_int(value, default=0):
    """✅ PRESERVED: Safe integer conversion with fallback"""
    try:
        if value is None:
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """✅ PRESERVED: Safe float conversion with fallback"""
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
        return float(value)
    except (ValueError, TypeError):
        return default

# ================================================================
# ✅ CRITICAL FIX: SERVER DATA CREATION
# ================================================================

def create_server_data(server_info):
    """
    ✅ FIXED: Create standardized server data structure
    
    This function now properly handles the server_info parameter that was 
    causing issues in the modular version.
    
    Args:
        server_info (dict): Raw server information
        
    Returns:
        dict: Standardized server data
    """
    try:
        # ✅ CRITICAL FIX: Validate input parameter
        if not isinstance(server_info, dict):
            raise ValueError(f"server_info must be a dictionary, got {type(server_info)}")
        
        # ✅ CRITICAL FIX: Extract and validate required fields
        server_id = server_info.get('serverId')
        if not server_id:
            raise ValueError("serverId is required in server_info")
        
        # ✅ CRITICAL FIX: Use the fixed validate_server_id function
        is_valid, validated_server_id = validate_server_id(server_id)
        if not is_valid:
            raise ValueError(f"Invalid serverId: {server_id}")
        
        server_name = server_info.get('serverName', '')
        if isinstance(server_name, str):
            server_name = server_name.strip()
        else:
            server_name = str(server_name).strip() if server_name else ''
        
        server_region = server_info.get('serverRegion', 'US')
        if not validate_region(server_region):
            logger.warning(f"Invalid region '{server_region}', using US")
            server_region = 'US'
        
        # ✅ CRITICAL FIX: Create standardized structure (matching original)
        return {
            'serverId': validated_server_id,  # This will be int or str as appropriate
            'serverName': server_name,
            'serverRegion': server_region.upper(),
            'serverType': server_info.get('serverType', 'Standard'),
            'description': server_info.get('description', ''),
            'guildId': server_info.get('guildId', ''),
            'channelId': server_info.get('channelId', ''),
            'status': 'unknown',
            'lastPing': None,
            'playerCount': 0,
            'maxPlayers': 0,
            'isActive': True,
            'isFavorite': False,
            'added_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating server data: {e}")
        # Return minimal valid structure
        return {
            'serverId': server_info.get('serverId', 'unknown'),
            'serverName': server_info.get('serverName', 'Unknown Server'),
            'serverRegion': 'US',
            'serverType': 'Standard',
            'description': '',
            'guildId': '',
            'channelId': '',
            'status': 'unknown',
            'lastPing': None,
            'playerCount': 0,
            'maxPlayers': 0,
            'isActive': True,
            'isFavorite': False,
            'added_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }

# ================================================================
# ✅ PRESERVED: STRING AND TEXT UTILITIES
# ================================================================

def escape_html(text):
    """✅ PRESERVED: Escape HTML characters in text"""
    if not text:
        return ''
    
    # ✅ CRITICAL FIX: Handle non-string input
    if not isinstance(text, str):
        text = str(text)
    
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        ">": "&gt;",
        "<": "&lt;",
    }
    
    return "".join(html_escape_table.get(c, c) for c in text)

def truncate_string(text, length=100, suffix='...'):
    """✅ PRESERVED: Truncate string to specified length"""
    if not text:
        return ''
    
    # ✅ CRITICAL FIX: Handle non-string input
    if not isinstance(text, str):
        text = str(text)
    
    if len(text) <= length:
        return text
    
    return text[:length - len(suffix)] + suffix

def sanitize_filename(filename):
    """✅ PRESERVED: Sanitize filename for safe filesystem usage"""
    if not filename:
        return 'untitled'
    
    # ✅ CRITICAL FIX: Handle non-string input
    if not isinstance(filename, str):
        filename = str(filename)
    
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '_', filename)
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_len = 255 - len(ext)
        filename = name[:max_name_len] + ext
    
    if not filename:
        filename = 'untitled'
    
    return filename

# ================================================================
# ✅ PRESERVED: DATE AND TIME UTILITIES
# ================================================================

def format_timestamp(timestamp=None, format_str='%Y-%m-%d %H:%M:%S'):
    """✅ PRESERVED: Format timestamp with optional custom format"""
    try:
        if timestamp is None:
            timestamp = datetime.now()
        elif isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str):
            # Try common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    timestamp = datetime.strptime(timestamp, fmt)
                    break
                except ValueError:
                    continue
            else:
                return timestamp  # Return original if can't parse
        
        return timestamp.strftime(format_str)
        
    except Exception as e:
        logger.error(f"Error formatting timestamp: {e}")
        return str(timestamp) if timestamp is not None else datetime.now().strftime(format_str)

# ================================================================
# ✅ PRESERVED: VALIDATION UTILITIES
# ================================================================

def is_valid_steam_id(steam_id):
    """✅ PRESERVED: Validate Steam ID format"""
    try:
        if not steam_id:
            return False
        steam_id_str = str(steam_id).strip()
        # Steam ID should be 17 digits starting with 7656119
        return re.match(r'^7656119[0-9]{10}$', steam_id_str) is not None
    except Exception:
        return False

def validate_email(email):
    """✅ PRESERVED: Basic email validation"""
    try:
        if not email or not isinstance(email, str):
            return False
        email = email.strip().lower()
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None
    except Exception:
        return False

def validate_url(url):
    """✅ PRESERVED: Basic URL validation"""
    try:
        if not url or not isinstance(url, str):
            return False
        url = url.strip()
        return re.match(r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$', url) is not None
    except Exception:
        return False

# ================================================================
# ✅ PRESERVED: UTILITY FUNCTIONS
# ================================================================

def generate_random_string(length=10):
    """✅ PRESERVED: Generate random string for various purposes"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def deep_get(dictionary, keys, default=None):
    """✅ PRESERVED: Get nested dictionary value safely"""
    try:
        # Handle both dot notation strings and lists
        if isinstance(keys, str):
            keys = keys.split('.')
        
        for key in keys:
            dictionary = dictionary[key]
        return dictionary
    except (KeyError, TypeError, AttributeError):
        return default

def flatten_dict(d, parent_key='', sep='_'):
    """✅ PRESERVED: Flatten nested dictionary"""
    items = []
    if not isinstance(d, dict):
        return {parent_key: d} if parent_key else {}
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def merge_dicts(dict1, dict2):
    """✅ PRESERVED: Merge two dictionaries safely"""
    if not isinstance(dict1, dict):
        dict1 = {}
    if not isinstance(dict2, dict):
        dict2 = {}
    
    result = dict1.copy()
    result.update(dict2)
    return result

def chunk_list(lst, chunk_size):
    """✅ PRESERVED: Split list into chunks of specified size"""
    if not isinstance(lst, list):
        lst = list(lst)
    
    chunk_size = max(1, int(chunk_size))  # Ensure positive chunk size
    
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def remove_duplicates(lst, key=None):
    """✅ PRESERVED: Remove duplicates from list"""
    if not isinstance(lst, list):
        return []
    
    if key is None:
        return list(dict.fromkeys(lst))
    else:
        seen = set()
        result = []
        for item in lst:
            try:
                k = key(item)
                if k not in seen:
                    seen.add(k)
                    result.append(item)
            except Exception:
                continue  # Skip items that cause errors
        return result

# ================================================================
# ✅ PRESERVED: CALCULATION UTILITIES
# ================================================================

def calculate_percentage(part, total):
    """✅ PRESERVED: Calculate percentage safely"""
    try:
        part = safe_float(part, 0)
        total = safe_float(total, 0)
        
        if total == 0:
            return 0
        return (part / total) * 100
    except Exception:
        return 0

def format_bytes(bytes_value):
    """✅ PRESERVED: Format bytes to human-readable format"""
    try:
        bytes_value = safe_float(bytes_value, 0)
        
        if bytes_value == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(bytes_value, 1024)))
        i = min(i, len(size_names) - 1)  # Prevent index error
        p = math.pow(1024, i)
        s = round(bytes_value / p, 2)
        return f"{s} {size_names[i]}"
    except Exception:
        return "0B"

def format_duration(seconds):
    """✅ PRESERVED: Format duration in seconds to human-readable format"""
    try:
        seconds = safe_int(seconds, 0)
        
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    except Exception:
        return "0s"

# ================================================================
# ✅ PRESERVED: STATUS AND DISPLAY UTILITIES
# ================================================================

def get_countdown_announcements(seconds_left):
    """✅ PRESERVED: Get countdown announcements for events"""
    try:
        seconds_left = safe_int(seconds_left, 0)
        announcements = []
        
        if seconds_left <= 0:
            announcements.append("Event starting now!")
        elif seconds_left <= 30:
            announcements.append(f"Event starting in {seconds_left} seconds!")
        elif seconds_left <= 60:
            announcements.append(f"Event starting in 1 minute!")
        elif seconds_left <= 300:  # 5 minutes
            minutes = seconds_left // 60
            announcements.append(f"Event starting in {minutes} minutes!")
        
        return announcements
    except Exception:
        return []

def get_status_class(status):
    """✅ PRESERVED: Get CSS class for status"""
    if not status:
        return 'status-unknown'
    
    status_str = str(status).lower()
    status_classes = {
        'online': 'status-online',
        'offline': 'status-offline',
        'starting': 'status-starting',
        'stopping': 'status-stopping',
        'error': 'status-error',
        'unknown': 'status-unknown'
    }
    return status_classes.get(status_str, 'status-unknown')

def get_status_text(status):
    """✅ PRESERVED: Get human-readable status text"""
    if not status:
        return 'Unknown'
    
    status_str = str(status).lower()
    status_texts = {
        'online': 'Online',
        'offline': 'Offline',
        'starting': 'Starting',
        'stopping': 'Stopping',
        'error': 'Error',
        'unknown': 'Unknown'
    }
    return status_texts.get(status_str, 'Unknown')

# ================================================================
# MODULE EXPORTS
# ================================================================

__all__ = [
    # Validation functions (FIXED)
    'validate_server_id', 'validate_region', 'is_valid_steam_id',
    'validate_email', 'validate_url',
    
    # Server utilities (FIXED)
    'get_server_region', 'create_server_data',
    
    # Type conversion utilities
    'safe_int', 'safe_float',
    
    # String and text utilities
    'escape_html', 'truncate_string', 'sanitize_filename',
    
    # Date and time utilities
    'format_timestamp',
    
    # Data manipulation functions
    'deep_get', 'flatten_dict', 'merge_dicts',
    'chunk_list', 'remove_duplicates',
    
    # Calculation utilities
    'calculate_percentage', 'format_bytes', 'format_duration',
    
    # Utility functions
    'generate_random_string',
    
    # Status and display utilities
    'get_countdown_announcements', 'get_status_class', 'get_status_text'
]

logger.info("✅ FIXED data_helpers module loaded with critical type handling fixes")