"""
GUST Bot Enhanced - Console Helper Functions (MODULAR VERSION)
========================================================================
✅ EXTRACTED: Console & command processing functions from helpers.py
✅ ENHANCED: Better message parsing and classification
✅ MODULAR: Clean separation of console-specific functionality
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple, Any

logger = logging.getLogger(__name__)

# ================================================================
# MESSAGE PATTERNS AND TYPES
# ================================================================

MESSAGE_PATTERNS = {
    'player_connect': re.compile(r'Player\s+connected.*SteamID\[(\d+)\]'),
    'player_disconnect': re.compile(r'Player\s+disconnected.*SteamID\[(\d+)\]'),
    'player_death': re.compile(r'(\w+)\s+was\s+killed\s+by\s+(\w+)'),
    'player_chat': re.compile(r'\[CHAT\]\s*(\w+):\s*(.+)'),
    'admin_command': re.compile(r'\[ADMIN\]\s*(.+)'),
    'server_info': re.compile(r'hostname:\s*(.+)|players:\s*(\d+)/(\d+)'),
    'server_start': re.compile(r'Server\s+startup'),
    'server_shutdown': re.compile(r'Server\s+shutdown'),
    'error': re.compile(r'\[ERROR\]|\[EXCEPTION\]|ERROR:|Exception:'),
    'warning': re.compile(r'\[WARNING\]|\[WARN\]|WARNING:'),
    'info': re.compile(r'\[INFO\]|INFO:'),
    'debug': re.compile(r'\[DEBUG\]|DEBUG:')
}

MESSAGE_TYPE_ICONS = {
    'player_connect': '🟢',
    'player_disconnect': '🔴',
    'player_death': '💀',
    'player_chat': '💬',
    'admin_command': '🛡️',
    'server_info': 'ℹ️',
    'server_start': '🚀',
    'server_shutdown': '🛑',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'debug': '🔍',
    'join': '🟢',
    'leave': '🔴',
    'kill': '💀',
    'chat': '💬',
    'admin': '🛡️',
    'system': 'ℹ️',
    'unknown': '❓',
    'success': '✅'
}

COMMAND_TEMPLATES = {
    'serverinfo': 'serverinfo',
    'kick': 'kick {player_id} "{reason}"',
    'ban': 'ban {player_id} "{reason}"',
    'unban': 'unban {player_id}',
    'say': 'say "{message}"',
    'give': 'inventory.give {player_id} {item} {amount}',
    'teleport': 'teleportany {player_id} {target_id}',
    'weather': 'weather {type}',
    'time': 'env.time {time}',
    'save': 'server.writecfg',
    'players': 'players',
    'status': 'status'
}

# ================================================================
# CONSOLE MESSAGE PARSING
# ================================================================

def parse_console_response(response_text):
    """
    Parse console response from G-Portal GraphQL API
    
    Args:
        response_text (str or dict): Raw response text or GraphQL response
        
    Returns:
        dict: Parsed response with messages and metadata
    """
    try:
        # Handle GraphQL response format
        if isinstance(response_text, dict):
            if 'data' in response_text and 'sendConsoleMessage' in response_text['data']:
                result = response_text['data']['sendConsoleMessage']
                success = result.get('ok', False)
                logger.debug(f"GraphQL sendConsoleMessage result: ok={success}")
                return {
                    'success': success,
                    'message': "Command executed successfully" if success else "Command failed",
                    'type': 'graphql_command',
                    'parsed_at': datetime.now().isoformat()
                }
            elif 'errors' in response_text:
                errors = response_text['errors']
                error_messages = [error.get('message', 'Unknown error') for error in errors]
                error_msg = f"GraphQL errors: {', '.join(error_messages)}"
                logger.error(f"GraphQL errors in response: {error_msg}")
                return {
                    'success': False,
                    'message': error_msg,
                    'type': 'graphql_error',
                    'parsed_at': datetime.now().isoformat()
                }
        
        # Handle text response format
        if not response_text or not isinstance(response_text, str):
            return {
                'messages': [],
                'total_lines': 0,
                'parsed_at': datetime.now().isoformat(),
                'success': True
            }
        
        lines = response_text.strip().split('\n')
        messages = []
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            message_data = parse_console_line(line.strip(), line_num)
            if message_data:
                messages.append(message_data)
        
        return {
            'messages': messages,
            'total_lines': len(lines),
            'parsed_lines': len(messages),
            'parsed_at': datetime.now().isoformat(),
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error parsing console response: {e}")
        return {
            'messages': [],
            'total_lines': 0,
            'error': str(e),
            'parsed_at': datetime.now().isoformat(),
            'success': False
        }

def parse_console_line(line, line_number=None):
    """
    Parse a single console line into structured data
    
    Args:
        line (str): Console line to parse
        line_number (int, optional): Line number for reference
        
    Returns:
        dict or None: Parsed line data or None if invalid
    """
    try:
        if not line or not isinstance(line, str):
            return None
        
        line = line.strip()
        if not line:
            return None
        
        # Extract timestamp if present
        timestamp_match = re.match(r'\[(\d{2}:\d{2}:\d{2})\]', line)
        timestamp = None
        message_text = line
        
        if timestamp_match:
            timestamp = timestamp_match.group(1)
            message_text = line[timestamp_match.end():].strip()
        
        # Classify and extract data from message
        message_type = classify_message(message_text)
        extracted_data = extract_message_data(message_text, message_type)
        
        return {
            'line_number': line_number,
            'timestamp': timestamp,
            'raw_text': line,
            'message': message_text,
            'type': message_type,
            'icon': get_type_icon(message_type),
            'data': extracted_data,
            'parsed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error parsing console line: {e}")
        return {
            'line_number': line_number,
            'raw_text': line,
            'message': line,
            'type': 'unknown',
            'icon': get_type_icon('unknown'),
            'error': str(e)
        }

def extract_message_data(message_text, message_type):
    """
    Extract structured data from message based on type
    
    Args:
        message_text (str): The message text to parse
        message_type (str): The classified message type
        
    Returns:
        dict: Extracted data from the message
    """
    data = {}
    
    try:
        if message_type == 'player_connect':
            match = MESSAGE_PATTERNS['player_connect'].search(message_text)
            if match:
                data['steam_id'] = match.group(1)
        
        elif message_type == 'player_disconnect':
            match = MESSAGE_PATTERNS['player_disconnect'].search(message_text)
            if match:
                data['steam_id'] = match.group(1)
        
        elif message_type == 'player_death':
            match = MESSAGE_PATTERNS['player_death'].search(message_text)
            if match:
                data['victim'] = match.group(1)
                data['killer'] = match.group(2)
        
        elif message_type == 'player_chat':
            match = MESSAGE_PATTERNS['player_chat'].search(message_text)
            if match:
                data['player'] = match.group(1)
                data['message'] = match.group(2)
        
        elif message_type == 'admin_command':
            match = MESSAGE_PATTERNS['admin_command'].search(message_text)
            if match:
                data['command'] = match.group(1)
        
        elif message_type == 'server_info':
            hostname_match = re.search(r'hostname:\s*(.+)', message_text)
            if hostname_match:
                data['hostname'] = hostname_match.group(1).strip()
            
            players_match = re.search(r'players:\s*(\d+)/(\d+)', message_text)
            if players_match:
                data['current_players'] = int(players_match.group(1))
                data['max_players'] = int(players_match.group(2))
        
    except Exception as e:
        logger.error(f"Error extracting message data: {e}")
        data['extraction_error'] = str(e)
    
    return data

def classify_message(message):
    """
    Classify message type based on content patterns
    
    Args:
        message (str): Message text to classify
        
    Returns:
        str: Message type classification
    """
    try:
        if not message or not isinstance(message, str):
            return 'unknown'
        
        message_lower = message.lower()
        
        # Check specific patterns first
        for message_type, pattern in MESSAGE_PATTERNS.items():
            if pattern.search(message):
                return message_type
        
        # Check for general keywords
        if any(keyword in message_lower for keyword in ['joined', 'connected', 'spawned']):
            return 'join'
        elif any(keyword in message_lower for keyword in ['left', 'disconnected', 'timeout']):
            return 'leave'
        elif any(keyword in message_lower for keyword in ['killed', 'died', 'death', 'suicide']):
            return 'kill'
        elif any(keyword in message_lower for keyword in ['chat', 'say', 'global', 'team']):
            return 'chat'
        elif any(keyword in message_lower for keyword in ['admin', 'ban', 'kick', 'mute']):
            return 'admin'
        elif any(keyword in message_lower for keyword in ['server', 'info', 'status', 'players']):
            return 'system'
        elif any(keyword in message_lower for keyword in ['error', 'exception', 'failed']):
            return 'error'
        elif any(keyword in message_lower for keyword in ['warning', 'warn']):
            return 'warning'
        elif any(keyword in message_lower for keyword in ['info', 'information']):
            return 'info'
        elif any(keyword in message_lower for keyword in ['debug', 'trace']):
            return 'debug'
        
        return 'unknown'
        
    except Exception as e:
        logger.error(f"Error classifying message: {e}")
        return 'unknown'

def get_type_icon(message_type):
    """
    Get icon for message type
    
    Args:
        message_type (str): Message type
        
    Returns:
        str: Unicode icon for the message type
    """
    return MESSAGE_TYPE_ICONS.get(message_type, MESSAGE_TYPE_ICONS['unknown'])

# ================================================================
# MESSAGE FORMATTING
# ================================================================

def format_console_message(message_data, include_timestamp=True, include_icon=True):
    """
    Format console message for display
    
    Args:
        message_data: Message data dict or raw message string
        include_timestamp (bool): Include timestamp in output
        include_icon (bool): Include type icon in output
        
    Returns:
        str: Formatted message string
    """
    try:
        # Handle different input types
        if isinstance(message_data, str):
            # Simple string message
            message_type = classify_message(message_data)
            icon = get_type_icon(message_type) if include_icon else ''
            return f"{icon} {message_data}".strip()
        
        if not isinstance(message_data, dict):
            return str(message_data)
        
        parts = []
        
        # Add timestamp if present and requested
        if include_timestamp and message_data.get('timestamp'):
            parts.append(f"[{message_data['timestamp']}]")
        
        # Add icon if present and requested
        if include_icon and message_data.get('icon'):
            parts.append(message_data['icon'])
        
        # Add message text
        message_text = message_data.get('message', message_data.get('raw_text', ''))
        parts.append(message_text)
        
        return ' '.join(parts)
        
    except Exception as e:
        logger.error(f"Error formatting console message: {e}")
        return str(message_data)

# ================================================================
# COMMAND FORMATTING
# ================================================================

def format_command(command_type, **kwargs):
    """
    Format console command with proper syntax
    
    Args:
        command_type (str): Type of command to format
        **kwargs: Parameters for the command template
        
    Returns:
        str: Formatted command string
    """
    try:
        # Handle simple command formatting
        if isinstance(command_type, str) and not kwargs:
            command = command_type.strip()
            
            # Handle 'say' commands with proper quoting
            if command.startswith('say ') and not command.startswith('global.say'):
                message = command[4:].strip()
                return f'global.say "{message}"'
            
            return command
        
        # Handle template-based formatting
        if command_type not in COMMAND_TEMPLATES:
            logger.warning(f"Unknown command type: {command_type}")
            return command_type
        
        template = COMMAND_TEMPLATES[command_type]
        formatted_command = template.format(**kwargs)
        
        logger.debug(f"Formatted command: {formatted_command}")
        return formatted_command
        
    except KeyError as e:
        logger.error(f"Missing required parameter for {command_type}: {e}")
        return command_type
    except Exception as e:
        logger.error(f"Error formatting command {command_type}: {e}")
        return command_type

# ================================================================
# ENHANCED PARSING FUNCTIONS
# ================================================================

def parse_player_list(response_text):
    """
    Parse player list from console response
    
    Args:
        response_text (str): Raw console response
        
    Returns:
        list: List of player data dictionaries
    """
    players = []
    
    try:
        if not response_text:
            return players
        
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for player entries (various formats)
            player_match = re.search(r'(\d+)\s+"([^"]+)"\s+(\d+)\s+(\d+)\s+([\d.]+)', line)
            if player_match:
                players.append({
                    'id': int(player_match.group(1)),
                    'name': player_match.group(2),
                    'steam_id': player_match.group(3),
                    'ping': int(player_match.group(4)),
                    'time_connected': player_match.group(5)
                })
    
    except Exception as e:
        logger.error(f"Error parsing player list: {e}")
    
    return players

def parse_server_info(response_text):
    """
    Parse server information from console response
    
    Args:
        response_text (str): Raw console response
        
    Returns:
        dict: Server information
    """
    info = {}
    
    try:
        if not response_text:
            return info
        
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse various server info patterns
            if 'hostname:' in line:
                match = re.search(r'hostname:\s*(.+)', line)
                if match:
                    info['hostname'] = match.group(1).strip()
            
            elif 'players:' in line:
                match = re.search(r'players:\s*(\d+)/(\d+)', line)
                if match:
                    info['current_players'] = int(match.group(1))
                    info['max_players'] = int(match.group(2))
            
            elif 'map:' in line:
                match = re.search(r'map:\s*(.+)', line)
                if match:
                    info['map'] = match.group(1).strip()
            
            elif 'version:' in line:
                match = re.search(r'version:\s*(.+)', line)
                if match:
                    info['version'] = match.group(1).strip()
    
    except Exception as e:
        logger.error(f"Error parsing server info: {e}")
    
    return info

# ================================================================
# MODULE EXPORTS
# ================================================================

__all__ = [
    # Core parsing functions
    'parse_console_response', 'parse_console_line', 'extract_message_data',
    
    # Message classification and formatting
    'classify_message', 'get_type_icon', 'format_console_message',
    
    # Command handling
    'format_command',
    
    # Enhanced parsing
    'parse_player_list', 'parse_server_info'
]

logger.info("✅ Modular console helpers loaded successfully")