"""
"""
"""
GUST Bot Enhanced - Helper Functions
===================================
Common utility functions used across the application
"""

# Standard library imports
from datetime import datetime
import json
import logging
import time

# Local imports
from config import Config



logger = logging.getLogger(__name__)

def load_token():
    """
    Load and refresh G-Portal token if needed
    
    Returns:
        str: Valid access token or empty string if unavailable
    """
    try:
        with open(Config.TOKEN_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            current_time = time.time()
            token_exp = data.get('access_token_exp', 0)
            
            if token_exp - current_time > 30:
                return data.get('access_token', '')
            else:
                # Token expired, try to refresh
                if refresh_token():
                    with open(Config.TOKEN_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return data.get('access_token', '')
                return ''
    except FileNotFoundError:
        return ''
    except Exception as e:
        logger.error(f"Error loading token: {e}")
        return ''

def refresh_token():
    """
    Refresh G-Portal access token using refresh token
    
    Returns:
        bool: True if refresh successful, False otherwise
    """
    import requests
    
    try:
        with open(Config.TOKEN_FILE, 'r', encoding='utf-8') as f:
            tokens = json.load(f)
    except:
        return False
    
    if 'refresh_token' not in tokens:
        return False
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': tokens['refresh_token'],
        'client_id': 'website'
    }
    
    try:
        response = requests.post(
            Config.GPORTAL_AUTH_URL,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        if response.status_code == 200:
            new_tokens = response.json()
            current_time = time.time()
            
            tokens.update({
                'access_token': new_tokens['access_token'],
                'refresh_token': new_tokens.get('refresh_token', tokens['refresh_token']),
                'access_token_exp': int(current_time + new_tokens.get('expires_in', 300)),
                'timestamp': datetime.now().isoformat()
            })
            
            with open(Config.TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(tokens, f, indent=2)
            
            return True
        return False
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        return False

def save_token(tokens, username):
    """
    Save G-Portal authentication tokens
    
    Args:
        tokens (dict): Token data from G-Portal
        username (str): Username for tracking
        
    Returns:
        bool: True if save successful
    """
    try:
        current_time = time.time()
        
        session_data = {
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'access_token_exp': int(current_time + tokens.get('expires_in', 300)),
            'refresh_token_exp': int(current_time + tokens.get('refresh_expires_in', 86400)),
            'timestamp': datetime.now().isoformat(),
            'username': username
        }
        
        with open(Config.TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Error saving token: {e}")
        return False

def classify_message(message):
    """
    Classify console message type based on content
    
    Args:
        message (str): Console message text
        
    Returns:
        str: Message type classification
    """
    if not message:
        return "system"
        
    message_lower = message.lower()
    
    if any(pattern in message_lower for pattern in ["[save]", "saving", "saved", "save to", "beginning save"]):
        return "save"
    elif any(pattern in message_lower for pattern in ["[chat]", "global.say", "player chat", "say "]):
        return "chat"
    elif any(pattern in message_lower for pattern in ["vip", "admin", "moderator", "owner", "auth"]):
        return "auth"
    elif any(pattern in message_lower for pattern in ["[kill]", "killed", "died", "death", "suicide"]):
        return "kill"
    elif any(pattern in message_lower for pattern in ["error", "exception", "failed", "fail", "crash"]):
        return "error"
    elif any(pattern in message_lower for pattern in ["warning", "warn", "alert"]):
        return "warning"
    elif any(pattern in message_lower for pattern in ["executing console", "command", "executed"]):
        return "command"
    elif any(pattern in message_lower for pattern in ["player", "connected", "disconnected", "joined", "left"]):
        return "player"
    elif any(pattern in message_lower for pattern in ["server", "startup", "shutdown", "restart"]):
        return "server"
    else:
        return "system"

def get_type_icon(message_type):
    """
    Get emoji icon for message type
    
    Args:
        message_type (str): Message type
        
    Returns:
        str: Emoji icon
    """
    icons = {
        'chat': 'ðŸ’¬',
        'auth': 'ðŸ”',
        'save': 'ðŸ’¾',
        'kill': 'âš”ï¸',
        'error': 'âŒ',
        'warning': 'âš ï¸',
        'command': 'ðŸ”§',
        'player': 'ðŸ‘¥',
        'system': 'ðŸ–¥ï¸',
        'event': 'ðŸŽ¯',
        'ban': 'ðŸš«'
    }
    return icons.get(message_type, 'ðŸ“‹')

def format_console_message(message_data):
    """
    Format console message for display
    
    Args:
        message_data (dict): Message data
        
    Returns:
        dict: Formatted message
    """
    return {
        "timestamp": message_data.get("timestamp", datetime.now().isoformat()),
        "server_id": message_data.get("server_id", ""),
        "message": message_data.get("message", ""),
        "type": classify_message(message_data.get("message", "")),
        "source": message_data.get("source", "unknown"),
        "formatted_time": datetime.fromisoformat(
            message_data.get("timestamp", datetime.now().isoformat()).replace('Z', '+00:00')
        ).strftime("%H:%M:%S") if message_data.get("timestamp") else datetime.now().strftime("%H:%M:%S")
    }

def validate_server_id(server_id):
    """
    Validate server ID format
    
    Args:
        server_id: Server ID to validate
        
    Returns:
        tuple: (is_valid, clean_server_id)
    """
    try:
        # Handle test server IDs that might have suffixes
        if isinstance(server_id, str) and '_test' in server_id:
            clean_id = int(server_id.split('_')[0])
        else:
            clean_id = int(server_id)
        return True, clean_id
    except (ValueError, TypeError):
        return False, None

def validate_region(region):
    """
    Validate server region
    
    Args:
        region (str): Region code
        
    Returns:
        bool: True if valid region
    """
    valid_regions = ['US', 'EU', 'AS']
    return region.upper() in valid_regions

def format_command(command):
    """
    Format console command properly
    
    Args:
        command (str): Raw command
        
    Returns:
        str: Formatted command
    """
    command = command.strip()
    
    if command.startswith('say '):
        return f'global.say "{command[4:]}"'
    elif command.startswith('global.'):
        return command
    else:
        return command

def create_server_data(server_info):
    """
    Create standardized server data structure
    
    Args:
        server_info (dict): Raw server information
        
    Returns:
        dict: Standardized server data
    """
    return {
        'serverId': server_info['serverId'],
        'serverName': server_info['serverName'],
        'serverRegion': server_info['serverRegion'],
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

def get_countdown_announcements():
    """
    Get countdown announcement schedule for KOTH events
    
    Returns:
        list: List of (delay_seconds, message) tuples
    """
    return [
        (240, "4 minutes"),
        (180, "3 minutes"), 
        (120, "2 minutes"),
        (60, "1 minute"),
        (30, "30 seconds"),
        (10, "10 seconds"),
        (5, "5 seconds"),
        (3, "3 seconds"),
        (2, "2 seconds"),
        (1, "1 second")
    ]

def escape_html(text):
    """
    Escape HTML characters in text
    
    Args:
        text (str): Text to escape
        
    Returns:
        str: HTML-escaped text
    """
    if not text:
        return ""
    
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;"))

def safe_int(value, default=0):
    """
    Safely convert value to integer
    
    Args:
        value: Value to convert
        default (int): Default value if conversion fails
        
    Returns:
        int: Converted integer or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """
    Safely convert value to float
    
    Args:
        value: Value to convert
        default (float): Default value if conversion fails
        
    Returns:
        float: Converted float or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def get_status_class(status):
    """
    Get CSS class for server status
    
    Args:
        status (str): Server status
        
    Returns:
        str: CSS class name
    """
    status_classes = {
        'online': 'bg-green-800 text-green-200',
        'offline': 'bg-red-800 text-red-200',
        'unknown': 'bg-gray-700 text-gray-300'
    }
    return status_classes.get(status, 'bg-gray-700 text-gray-300')

def get_status_text(status):
    """
    Get display text for server status
    
    Args:
        status (str): Server status
        
    Returns:
        str: Display text with emoji
    """
    status_texts = {
        'online': 'ðŸŸ¢ Online',
        'offline': 'ðŸ”´ Offline',
        'unknown': 'âšª Unknown'
    }
    return status_texts.get(status, 'âšª Unknown')
