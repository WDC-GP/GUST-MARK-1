"""
GUST Bot Enhanced - Data Helper Functions (MODULAR VERSION)
=====================================================================
✅ EXTRACTED: Data manipulation & utility functions from helpers.py
✅ ENHANCED: Better error handling and validation
✅ MODULAR: Clean separation of data processing functionality
"""

import os
import json
import math
import random
import string
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any
import logging

logger = logging.getLogger(__name__)

# ================================================================
# DICTIONARY AND DATA MANIPULATION
# ================================================================

def deep_get(dictionary, keys, default=None):
    """
    Get nested dictionary value safely using dot notation or key list
    
    Args:
        dictionary (dict): Dictionary to search
        keys (str or list): Key path (dot notation string or list of keys)
        default: Default value if key path not found
        
    Returns:
        Any: Value at key path or default
    """
    try:
        if not isinstance(dictionary, dict):
            return default
        
        if isinstance(keys, str):
            keys = keys.split('.')
        elif not isinstance(keys, list):
            keys = [keys]
        
        current = dictionary
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
        
    except Exception as e:
        logger.error(f"Error in deep_get: {e}")
        return default

def flatten_dict(dictionary, parent_key='', separator='.'):
    """
    Flatten nested dictionary into single level with dot notation keys
    
    Args:
        dictionary (dict): Dictionary to flatten
        parent_key (str): Parent key prefix
        separator (str): Key separator character
        
    Returns:
        dict: Flattened dictionary
    """
    try:
        items = []
        
        if not isinstance(dictionary, dict):
            return {parent_key: dictionary} if parent_key else {}
        
        for key, value in dictionary.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            
            if isinstance(value, dict):
                items.extend(flatten_dict(value, new_key, separator).items())
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    list_key = f"{new_key}{separator}{i}"
                    if isinstance(item, dict):
                        items.extend(flatten_dict(item, list_key, separator).items())
                    else:
                        items.append((list_key, item))
            else:
                items.append((new_key, value))
        
        return dict(items)
        
    except Exception as e:
        logger.error(f"Error flattening dictionary: {e}")
        return {}

def merge_dicts(*dicts, deep=True):
    """
    Merge multiple dictionaries with optional deep merging
    
    Args:
        *dicts: Dictionaries to merge
        deep (bool): Whether to perform deep merge on nested dicts
        
    Returns:
        dict: Merged dictionary
    """
    try:
        if not dicts:
            return {}
        
        result = {}
        
        for dictionary in dicts:
            if not isinstance(dictionary, dict):
                continue
            
            if not deep:
                result.update(dictionary)
            else:
                for key, value in dictionary.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = merge_dicts(result[key], value, deep=True)
                    else:
                        result[key] = value
        
        return result
        
    except Exception as e:
        logger.error(f"Error merging dictionaries: {e}")
        return {}

# ================================================================
# LIST MANIPULATION
# ================================================================

def chunk_list(lst, chunk_size):
    """
    Split list into chunks of specified size
    
    Args:
        lst (list): List to chunk
        chunk_size (int): Size of each chunk
        
    Returns:
        list: List of chunks
    """
    try:
        if not isinstance(lst, list) or chunk_size <= 0:
            return []
        
        chunks = []
        for i in range(0, len(lst), chunk_size):
            chunks.append(lst[i:i + chunk_size])
        
        return chunks
        
    except Exception as e:
        logger.error(f"Error chunking list: {e}")
        return []

def remove_duplicates(lst, key=None):
    """
    Remove duplicates from list with optional key function
    
    Args:
        lst (list): List to deduplicate
        key (callable, optional): Key function for comparison
        
    Returns:
        list: List with duplicates removed
    """
    try:
        if not isinstance(lst, list):
            return []
        
        if key is None:
            return list(dict.fromkeys(lst))
        else:
            seen = set()
            result = []
            for item in lst:
                k = key(item)
                if k not in seen:
                    seen.add(k)
                    result.append(item)
            return result
            
    except Exception as e:
        logger.error(f"Error removing duplicates: {e}")
        return lst if isinstance(lst, list) else []

# ================================================================
# MATHEMATICAL UTILITIES
# ================================================================

def calculate_percentage(part, total):
    """
    Calculate percentage safely
    
    Args:
        part (number): Part value
        total (number): Total value
        
    Returns:
        float: Percentage value
    """
    try:
        if total == 0:
            return 0.0
        return (part / total) * 100
    except (TypeError, ValueError):
        return 0.0

def format_bytes(bytes_value):
    """
    Format bytes to human-readable format
    
    Args:
        bytes_value (int/float): Number of bytes
        
    Returns:
        str: Formatted string (e.g., "1.5 MB")
    """
    try:
        if not isinstance(bytes_value, (int, float)) or bytes_value < 0:
            return "0B"
        
        if bytes_value == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(bytes_value, 1024)))
        i = min(i, len(size_names) - 1)
        
        p = math.pow(1024, i)
        s = round(bytes_value / p, 2)
        
        return f"{s} {size_names[i]}"
        
    except Exception as e:
        logger.error(f"Error formatting bytes: {e}")
        return str(bytes_value) if bytes_value is not None else "0B"

def format_duration(seconds):
    """
    Format duration in seconds to human-readable format
    
    Args:
        seconds (int/float): Duration in seconds
        
    Returns:
        str: Formatted duration (e.g., "2h 30m")
    """
    try:
        if not isinstance(seconds, (int, float)) or seconds < 0:
            return "0s"
        
        seconds = int(seconds)
        
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h"
            
    except Exception as e:
        logger.error(f"Error formatting duration: {e}")
        return str(seconds) if seconds is not None else "0s"

# ================================================================
# STRING UTILITIES
# ================================================================

def generate_random_string(length=8, charset=None):
    """
    Generate random string with specified length and character set
    
    Args:
        length (int): Length of string to generate
        charset (str, optional): Character set to use
        
    Returns:
        str: Random string
    """
    try:
        if charset is None:
            charset = string.ascii_letters + string.digits
        
        if length <= 0:
            return ''
        
        return ''.join(random.choice(charset) for _ in range(length))
        
    except Exception as e:
        logger.error(f"Error generating random string: {e}")
        return ''

def safe_int(value, default=0):
    """
    Safely convert value to integer with fallback
    
    Args:
        value: Value to convert
        default (int): Default value if conversion fails
        
    Returns:
        int: Converted integer or default
    """
    try:
        if value is None:
            return default
        
        if isinstance(value, bool):
            return int(value)
        
        if isinstance(value, (int, float)):
            return int(value)
        
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
            
            # Remove common formatting
            value = value.replace(',', '')
            return int(float(value))
        
        return default
        
    except (ValueError, TypeError, OverflowError):
        return default

def safe_float(value, default=0.0):
    """
    Safely convert value to float with fallback
    
    Args:
        value: Value to convert
        default (float): Default value if conversion fails
        
    Returns:
        float: Converted float or default
    """
    try:
        if value is None:
            return default
        
        if isinstance(value, bool):
            return float(value)
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
            
            # Remove common formatting
            value = value.replace(',', '')
            return float(value)
        
        return default
        
    except (ValueError, TypeError, OverflowError):
        return default

def escape_html(text):
    """
    Escape HTML characters in text
    
    Args:
        text (str): Text to escape
        
    Returns:
        str: HTML-escaped text
    """
    if not text or not isinstance(text, str):
        return str(text) if text is not None else ''
    
    escape_map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;'
    }
    
    escaped = text
    for char, escaped_char in escape_map.items():
        escaped = escaped.replace(char, escaped_char)
    
    return escaped

def truncate_string(text, max_length=100, suffix='...'):
    """
    Truncate string to specified length with suffix
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        suffix (str): Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if not text or not isinstance(text, str):
        return str(text) if text is not None else ''
    
    if len(text) <= max_length:
        return text
    
    if len(suffix) >= max_length:
        return text[:max_length]
    
    truncate_at = max_length - len(suffix)
    return text[:truncate_at] + suffix

def sanitize_filename(filename):
    """
    Sanitize filename for safe filesystem usage
    
    Args:
        filename (str): Filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    if not filename or not isinstance(filename, str):
        return 'untitled'
    
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, '_', filename)
    sanitized = sanitized.strip(' .')
    
    # Limit length (filesystem limitation)
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        max_name_len = 255 - len(ext)
        sanitized = name[:max_name_len] + ext
    
    if not sanitized:
        sanitized = 'untitled'
    
    return sanitized

# ================================================================
# TIME AND DATE UTILITIES
# ================================================================

def format_timestamp(timestamp=None, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Format timestamp with optional custom format
    
    Args:
        timestamp: Timestamp to format (datetime, int, float, or str)
        format_str (str): Format string
        
    Returns:
        str: Formatted timestamp
    """
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
# VALIDATION UTILITIES
# ================================================================

def validate_server_id(server_id):
    """
    Validate server ID format
    
    Args:
        server_id: Server ID to validate
        
    Returns:
        tuple: (is_valid, validated_id)
    """
    try:
        if server_id is None:
            return False, "Server ID cannot be None"
        
        server_id_str = str(server_id).strip()
        
        if not server_id_str:
            return False, "Server ID cannot be empty"
        
        # Handle test server IDs
        if '_test' in server_id_str:
            server_id_str = server_id_str.split('_')[0]
        
        if server_id_str.isdigit():
            server_id_int = int(server_id_str)
            if server_id_int <= 0:
                return False, "Numeric server ID must be positive"
            return True, server_id_int
        
        # Allow alphanumeric IDs
        if re.match(r'^[a-zA-Z0-9_-]+$', server_id_str):
            return True, server_id_str
        
        return False, "Invalid server ID format"
        
    except Exception as e:
        logger.error(f"Error validating server ID: {e}")
        return False, f"Validation error: {e}"

def validate_region(region):
    """
    Validate server region
    
    Args:
        region (str): Region to validate
        
    Returns:
        tuple: (is_valid, validated_region)
    """
    try:
        if not region or not isinstance(region, str):
            return False, "Region must be a non-empty string"
        
        region_upper = region.strip().upper()
        valid_regions = {'US', 'EU', 'AS', 'OCE', 'SA', 'AU'}
        
        if region_upper in valid_regions:
            return True, region_upper
        
        return False, f"Invalid region. Must be one of: {', '.join(sorted(valid_regions))}"
        
    except Exception as e:
        logger.error(f"Error validating region: {e}")
        return False, f"Validation error: {e}"

def is_valid_steam_id(steam_id):
    """
    Validate Steam ID format
    
    Args:
        steam_id: Steam ID to validate
        
    Returns:
        bool: True if valid Steam ID format
    """
    try:
        if not steam_id:
            return False
        steam_id_str = str(steam_id).strip()
        # Steam ID should be 17 digits starting with 7656119
        return re.match(r'^7656119[0-9]{10}$', steam_id_str) is not None
    except Exception:
        return False

def validate_email(email):
    """
    Basic email validation
    
    Args:
        email (str): Email to validate
        
    Returns:
        bool: True if valid email format
    """
    try:
        if not email or not isinstance(email, str):
            return False
        email = email.strip().lower()
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None
    except Exception:
        return False

def validate_url(url):
    """
    Basic URL validation
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid URL format
    """
    try:
        if not url or not isinstance(url, str):
            return False
        url = url.strip()
        return re.match(r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$', url) is not None
    except Exception:
        return False

# ================================================================
# SERVER AND GAME UTILITIES
# ================================================================

def get_server_region(server_data):
    """
    Extract region from server data
    
    Args:
        server_data (dict): Server data dictionary
        
    Returns:
        str: Server region
    """
    try:
        if not isinstance(server_data, dict):
            return 'US'
        
        region = server_data.get('region', 'US')
        region_valid, validated_region = validate_region(region)
        
        if region_valid:
            return validated_region
        else:
            logger.warning(f"Invalid region '{region}' in server data, using US")
            return 'US'
            
    except Exception as e:
        logger.error(f"Error getting server region: {e}")
        return 'US'

def create_server_data(server_info):
    """
    Create standardized server data structure
    
    Args:
        server_info (dict): Raw server information
        
    Returns:
        dict: Standardized server data
    """
    try:
        # Validate required fields
        required_fields = ['serverId', 'serverName', 'serverRegion']
        for field in required_fields:
            if field not in server_info:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate server ID
        id_valid, validated_id = validate_server_id(server_info['serverId'])
        if not id_valid:
            raise ValueError(f"Invalid server ID: {validated_id}")
        
        # Validate region
        region_valid, validated_region = validate_region(server_info['serverRegion'])
        if not region_valid:
            raise ValueError(f"Invalid region: {validated_region}")
        
        # Validate server name
        server_name = str(server_info['serverName']).strip()
        if not server_name:
            raise ValueError("Server name cannot be empty")
        if len(server_name) > 100:
            raise ValueError("Server name too long (max 100 characters)")
        
        # Create standardized structure
        server_data = {
            'serverId': validated_id,
            'serverName': server_name,
            'serverRegion': validated_region,
            'serverType': server_info.get('serverType', 'Standard'),
            'description': server_info.get('description', ''),
            'guildId': server_info.get('guildId', ''),
            'channelId': server_info.get('channelId', ''),
            'status': 'unknown',
            'lastPing': None,
            'playerCount': 0,
            'maxPlayers': server_info.get('maxPlayers', 100),
            'isActive': server_info.get('isActive', True),
            'isFavorite': server_info.get('isFavorite', False),
            'added_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        # Add any additional fields
        for key, value in server_info.items():
            if key not in server_data:
                server_data[key] = value
        
        return server_data
        
    except Exception as e:
        logger.error(f"Error creating server data: {e}")
        raise

# ================================================================
# UI AND STATUS UTILITIES
# ================================================================

def get_countdown_announcements():
    """
    Get countdown announcements for events
    
    Returns:
        list: List of countdown announcement dictionaries
    """
    return [
        {'minutes': 60, 'message': '1 hour remaining!'},
        {'minutes': 30, 'message': '30 minutes remaining!'},
        {'minutes': 15, 'message': '15 minutes remaining!'},
        {'minutes': 10, 'message': '10 minutes remaining!'},
        {'minutes': 5, 'message': '5 minutes remaining!'},
        {'minutes': 3, 'message': '3 minutes remaining!'},
        {'minutes': 1, 'message': '1 minute remaining!'},
        {'minutes': 0, 'message': 'Event starting now!'}
    ]

def get_status_class(status):
    """
    Get CSS class for status
    
    Args:
        status (str): Status string
        
    Returns:
        str: CSS class name
    """
    status_classes = {
        'online': 'status-online',
        'offline': 'status-offline',
        'starting': 'status-starting',
        'stopping': 'status-stopping',
        'maintenance': 'status-maintenance',
        'error': 'status-error',
        'unknown': 'status-unknown'
    }
    
    return status_classes.get(str(status).lower(), 'status-unknown')

def get_status_text(status):
    """
    Get human-readable status text
    
    Args:
        status (str): Status string
        
    Returns:
        str: Human-readable status
    """
    status_texts = {
        'online': 'Online',
        'offline': 'Offline',
        'starting': 'Starting',
        'stopping': 'Stopping',
        'maintenance': 'Maintenance',
        'error': 'Error',
        'unknown': 'Unknown'
    }
    
    return status_texts.get(str(status).lower(), 'Unknown')

# ================================================================
# MODULE EXPORTS
# ================================================================

__all__ = [
    # Dictionary manipulation
    'deep_get', 'flatten_dict', 'merge_dicts',
    
    # List manipulation
    'chunk_list', 'remove_duplicates',
    
    # Mathematical utilities
    'calculate_percentage', 'format_bytes', 'format_duration',
    
    # String utilities
    'generate_random_string', 'safe_int', 'safe_float', 'escape_html',
    'truncate_string', 'sanitize_filename',
    
    # Time and date utilities
    'format_timestamp',
    
    # Validation utilities
    'validate_server_id', 'validate_region', 'is_valid_steam_id',
    'validate_email', 'validate_url',
    
    # Server and game utilities
    'get_server_region', 'create_server_data',
    
    # UI and status utilities
    'get_countdown_announcements', 'get_status_class', 'get_status_text'
]

logger.info("✅ Modular data helpers loaded successfully")