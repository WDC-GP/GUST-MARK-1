"""
GUST Bot Enhanced - Helper Functions
===================================
Common utility functions used across the application
✅ All helper functions for console command fix included
✅ Proper GraphQL response parsing
✅ Enhanced command formatting and validation
"""

# Standard library imports
from datetime import datetime
import json
import logging
import time
import os

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
        'chat': '💬',
        'auth': '🔐',
        'save': '💾',
        'kill': '⚔️',
        'error': '❌',
        'warning': '⚠️',
        'command': '🔧',
        'player': '👥',
        'system': '🖥️',
        'event': '🎯',
        'ban': '🚫'
    }
    return icons.get(message_type, '📋')

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
    Validate server ID format and convert to proper type for G-Portal API
    ✅ CRITICAL for console command fix
    
    Args:
        server_id: Server ID to validate
        
    Returns:
        tuple: (is_valid, clean_server_id)
    """
    try:
        # Handle test server IDs that might have suffixes like "_test"
        if isinstance(server_id, str) and '_test' in server_id:
            clean_id = int(server_id.split('_')[0])
        else:
            clean_id = int(server_id)
        
        # Additional validation - server IDs should be positive integers
        if clean_id <= 0:
            return False, None
            
        return True, clean_id
    except (ValueError, TypeError):
        return False, None

def validate_region(region):
    """
    Validate server region against G-Portal supported regions
    ✅ CRITICAL for console command fix
    
    Args:
        region (str): Region code
        
    Returns:
        bool: True if valid region
    """
    if not region or not isinstance(region, str):
        return False
        
    valid_regions = ['US', 'EU', 'AS']  # G-Portal supported regions
    return region.upper() in valid_regions

def format_command(command):
    """
    Format console command properly for G-Portal API
    ✅ ENHANCED for console command fix
    
    Args:
        command (str): Raw command
        
    Returns:
        str: Formatted command
    """
    if not command:
        return ""
        
    command = command.strip()
    
    # Handle special command formats
    if command.startswith('say '):
        # Convert "say message" to proper global say format
        message = command[4:].strip()
        return f'global.say "{message}"'
    elif command.startswith('global.'):
        # Already properly formatted global command
        return command
    elif command.startswith('give '):
        # Ensure give commands are properly quoted
        parts = command.split(' ')
        if len(parts) >= 4:
            # give player item amount
            player = parts[1]
            item = parts[2]
            amount = parts[3]
            return f'give "{player}" "{item}" {amount}'
        return command
    elif command.startswith('kick '):
        # Ensure kick commands are properly quoted
        parts = command.split(' ', 2)
        if len(parts) >= 3:
            # kick player reason
            player = parts[1]
            reason = parts[2]
            return f'kick "{player}" "{reason}"'
        elif len(parts) == 2:
            # kick player (no reason)
            player = parts[1]
            return f'kick "{player}" "Kicked by admin"'
        return command
    elif command.startswith('ban '):
        # Ensure ban commands are properly quoted
        parts = command.split(' ', 2)
        if len(parts) >= 3:
            # ban player reason
            player = parts[1]
            reason = parts[2]
            return f'ban "{player}" "{reason}"'
        elif len(parts) == 2:
            # ban player (no reason)
            player = parts[1]
            return f'ban "{player}" "Banned by admin"'
        return command
    else:
        # Return command as-is for other commands
        return command

def log_console_command(command, server_id, result, error=None):
    """
    Log console command execution for debugging
    ✅ NEW function for console command fix
    
    Args:
        command (str): Command that was executed
        server_id (str): Server ID
        result (bool): Whether command succeeded
        error (str, optional): Error message if failed
    """
    status = "SUCCESS" if result else "FAILED"
    message = f"Console Command [{status}] Server: {server_id}, Command: {command}"
    
    if error:
        message += f", Error: {error}"
    
    if result:
        logger.info(message)
    else:
        logger.error(message)

def parse_console_response(response_data):
    """
    Parse G-Portal GraphQL response for console commands
    ✅ CRITICAL function for console command fix
    
    Args:
        response_data (dict): Response from G-Portal API
        
    Returns:
        tuple: (success, message)
    """
    try:
        if 'data' in response_data and 'sendConsoleMessage' in response_data['data']:
            result = response_data['data']['sendConsoleMessage']
            success = result.get('ok', False)  # ✅ Correct field name 'ok' not 'success'
            return success, "Command executed successfully" if success else "Command failed"
        elif 'errors' in response_data:
            errors = response_data['errors']
            error_messages = [error.get('message', 'Unknown error') for error in errors]
            return False, f"GraphQL errors: {', '.join(error_messages)}"
        else:
            return False, "Unexpected response format"
    except Exception as e:
        return False, f"Response parsing error: {str(e)}"

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
        'online': '🟢 Online',
        'offline': '🔴 Offline',
        'unknown': '⚪ Unknown'
    }
    return status_texts.get(status, '⚪ Unknown')

def format_timestamp(timestamp_str):
    """
    Format timestamp for display
    
    Args:
        timestamp_str (str): ISO timestamp string
        
    Returns:
        str: Formatted timestamp
    """
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%H:%M:%S")
    except:
        return datetime.now().strftime("%H:%M:%S")

def is_valid_steam_id(steam_id):
    """
    Validate Steam ID format
    
    Args:
        steam_id (str): Steam ID to validate
        
    Returns:
        bool: True if valid Steam ID format
    """
    if not steam_id or not isinstance(steam_id, str):
        return False
    
    # Steam ID patterns
    # Steam64: 17 digits starting with 7656119
    # Steam32: STEAM_0:X:XXXXXXX or STEAM_1:X:XXXXXXX
    
    steam_id = steam_id.strip()
    
    # Check Steam64 format
    if steam_id.isdigit() and len(steam_id) == 17 and steam_id.startswith('7656119'):
        return True
    
    # Check Steam32 format
    if steam_id.startswith('STEAM_'):
        parts = steam_id.split(':')
        if len(parts) == 3:
            try:
                int(parts[1])  # Y value
                int(parts[2])  # Z value
                return True
            except ValueError:
                pass
    
    return False

def sanitize_filename(filename):
    """
    Sanitize filename for safe file operations
    
    Args:
        filename (str): Filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Ensure not empty
    if not filename:
        filename = "unnamed"
    
    return filename

def calculate_time_remaining(start_time, duration_minutes):
    """
    Calculate time remaining for an event
    
    Args:
        start_time (str): ISO timestamp of start time
        duration_minutes (int): Event duration in minutes
        
    Returns:
        dict: Time remaining info
    """
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        current_dt = datetime.now()
        
        elapsed = (current_dt - start_dt).total_seconds()
        total_duration = duration_minutes * 60
        remaining = max(0, total_duration - elapsed)
        
        if remaining <= 0:
            return {
                'is_active': False,
                'time_remaining': 0,
                'minutes_remaining': 0,
                'seconds_remaining': 0,
                'formatted': 'Expired'
            }
        
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        
        return {
            'is_active': True,
            'time_remaining': remaining,
            'minutes_remaining': minutes,
            'seconds_remaining': seconds,
            'formatted': f"{minutes}m {seconds}s"
        }
        
    except Exception as e:
        logger.error(f"Error calculating time remaining: {e}")
        return {
            'is_active': False,
            'time_remaining': 0,
            'minutes_remaining': 0,
            'seconds_remaining': 0,
            'formatted': 'Unknown'
        }

def build_console_command_log_entry(command, server_id, region, status, response=None, error=None):
    """
    Build a console command log entry
    ✅ NEW function for console command fix
    
    Args:
        command (str): The command that was executed
        server_id (str): Server ID
        region (str): Server region
        status (str): Command status ('sent', 'failed', 'success')
        response (str, optional): Response message
        error (str, optional): Error message
        
    Returns:
        dict: Log entry
    """
    entry = {
        'timestamp': datetime.now().isoformat(),
        'command': command,
        'server_id': str(server_id),
        'region': region,
        'status': status,
        'source': 'gportal_graphql_fixed',
        'type': 'command'
    }
    
    if response:
        entry['response'] = response
    if error:
        entry['error'] = error
    
    return entry

# Console command validation helpers
def is_dangerous_command(command):
    """
    Check if a command is potentially dangerous
    
    Args:
        command (str): Command to check
        
    Returns:
        bool: True if command could be dangerous
    """
    dangerous_patterns = [
        'oxide.unload',
        'oxide.reload',
        'quit',
        'shutdown',
        'restart',
        'server.stop',
        'server.quit'
    ]
    
    command_lower = command.lower().strip()
    return any(pattern in command_lower for pattern in dangerous_patterns)

def get_command_category(command):
    """
    Categorize a console command
    
    Args:
        command (str): Console command
        
    Returns:
        str: Command category
    """
    command_lower = command.lower().strip()
    
    if command_lower.startswith(('say ', 'global.say')):
        return 'communication'
    elif command_lower.startswith(('give ', 'inventory.give')):
        return 'items'
    elif command_lower.startswith(('kick ', 'ban ', 'unban ')):
        return 'moderation'
    elif command_lower.startswith(('teleport', 'tp', 'goto')):
        return 'teleportation'
    elif command_lower in ['save', 'serverinfo', 'status', 'fps', 'players']:
        return 'information'
    elif command_lower.startswith(('weather.', 'time.')):
        return 'environment'
    else:
        return 'general'
