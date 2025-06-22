"""
GUST Bot Enhanced - Console Helpers Module (COMPLETE FIXED VERSION)
===================================================================
✅ RESTORED: All missing console functions from original helpers.py
✅ FIXED: format_command function that handles console command formatting
✅ PRESERVED: All existing functionality with enhanced error handling
✅ ADDED: Enhanced GraphQL response parsing

This module contains all console-related functions that were in the original helpers.py
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

logger = logging.getLogger(__name__)

# ================================================================
# ✅ RESTORED: CONSOLE RESPONSE PARSING
# ================================================================

def parse_console_response(response_data):
    """
    ✅ RESTORED: Parse G-Portal GraphQL response for console commands
    
    This function was in the original helpers.py and is critical for console functionality.
    
    Args:
        response_data: Response from G-Portal API
        
    Returns:
        tuple: (success, message)
    """
    logger.debug(f"parse_console_response called with: {response_data}")
    
    if not response_data or not isinstance(response_data, dict):
        logger.warning(f"Invalid response_data: {response_data}")
        return False, "Invalid response data"
    
    try:
        # Handle GraphQL responses
        if 'data' in response_data and 'sendConsoleMessage' in response_data['data']:
            result = response_data['data']['sendConsoleMessage']
            success = result.get('ok', False)
            logger.debug(f"GraphQL sendConsoleMessage result: ok={success}")
            return success, "Command executed successfully" if success else "Command failed"
        
        # Handle error responses
        elif 'errors' in response_data:
            errors = response_data['errors']
            error_messages = [error.get('message', 'Unknown error') for error in errors]
            error_msg = f"GraphQL errors: {', '.join(error_messages)}"
            logger.error(f"GraphQL errors in response: {error_msg}")
            return False, error_msg
        
        # Handle plain text responses (for demo mode or other cases)
        elif isinstance(response_data, str):
            # Simple text response - assume success if no error indicators
            if any(word in response_data.lower() for word in ['error', 'failed', 'invalid']):
                return False, response_data
            else:
                return True, response_data
        
        else:
            logger.warning("Unexpected response format - no data.sendConsoleMessage or errors")
            return False, "Unexpected response format"
            
    except Exception as e:
        logger.error(f"Error parsing console response: {e}")
        return False, f"Error parsing response: {e}"

# ================================================================
# ✅ RESTORED: MESSAGE CLASSIFICATION AND FORMATTING
# ================================================================

def classify_message(message):
    """
    ✅ RESTORED: Enhanced message classification
    
    This function was in the original helpers.py and is used throughout the system.
    
    Args:
        message (str): Message to classify
        
    Returns:
        str: Message type classification
    """
    if not message:
        return 'unknown'
    
    # Handle non-string input
    if not isinstance(message, str):
        message = str(message)
    
    msg_lower = message.lower()
    
    # Player connection events
    if any(word in msg_lower for word in ['joined', 'connected', 'spawned', 'entered']):
        return 'join'
    elif any(word in msg_lower for word in ['left', 'disconnected', 'timeout', 'quit']):
        return 'leave'
    
    # Combat and death events
    elif any(word in msg_lower for word in ['killed', 'died', 'death', 'suicide', 'eliminated']):
        return 'kill'
    
    # Chat messages
    elif any(word in msg_lower for word in ['chat', 'say', 'global', 'team', 'whisper']):
        return 'chat'
    
    # Administrative actions
    elif any(word in msg_lower for word in ['admin', 'ban', 'kick', 'mute', 'warn']):
        return 'admin'
    
    # Server information and status
    elif any(word in msg_lower for word in ['server', 'info', 'status', 'players', 'fps', 'performance']):
        return 'system'
    
    # Error and warning messages
    elif any(word in msg_lower for word in ['error', 'failed', 'warning', 'exception']):
        return 'error'
    
    # Success messages
    elif any(word in msg_lower for word in ['success', 'completed', 'ok', 'done']):
        return 'success'
    
    else:
        return 'unknown'

def get_type_icon(message_type):
    """
    ✅ RESTORED: Enhanced icon mapping for message types
    
    Args:
        message_type (str): Type of message
        
    Returns:
        str: Emoji icon for the message type
    """
    icons = {
        'join': '🟢',
        'leave': '🔴', 
        'kill': '💀',
        'chat': '💬',
        'admin': '🛡️',
        'system': 'ℹ️',
        'unknown': '❓',
        'error': '❌',
        'warning': '⚠️',
        'success': '✅',
        'info': 'ℹ️',
        'debug': '🔧',
        'auto_command': '🤖'
    }
    return icons.get(message_type, '❓')

def format_console_message(message, timestamp=None):
    """
    ✅ RESTORED: Enhanced console message formatting
    
    Args:
        message (str): Message to format
        timestamp: Optional timestamp (datetime, str, or None)
        
    Returns:
        str: Formatted message with icon and timestamp
    """
    if not message:
        return ''
    
    # Handle non-string input
    if not isinstance(message, str):
        message = str(message)
    
    msg_type = classify_message(message)
    icon = get_type_icon(msg_type)
    
    # Format timestamp
    if timestamp:
        if isinstance(timestamp, str):
            formatted_time = timestamp
        elif hasattr(timestamp, 'strftime'):
            formatted_time = timestamp.strftime('%H:%M:%S')
        else:
            formatted_time = str(timestamp)
        return f"{formatted_time} {icon} {message}"
    else:
        return f"{icon} {message}"

# ================================================================
# ✅ CRITICAL RESTORATION: COMMAND FORMATTING
# ================================================================

def format_command(command):
    """
    ✅ CRITICAL RESTORATION: Enhanced command formatting for G-Portal console
    
    This function was missing from the modular helpers and is ESSENTIAL for console commands.
    It formats commands properly for the G-Portal console system.
    
    Args:
        command (str): Raw command to format
        
    Returns:
        str: Formatted command ready for G-Portal console
    """
    if not command:
        return ''
    
    # Handle non-string input
    if not isinstance(command, str):
        command = str(command)
    
    command = command.strip()
    
    # Handle 'say' commands with proper quoting
    if command.startswith('say ') and not command.startswith('global.say'):
        message = command[4:].strip()
        # Escape quotes in the message
        message = message.replace('"', '\\"')
        return f'global.say "{message}"'
    
    # Handle other common command formats
    elif command.startswith('broadcast '):
        message = command[10:].strip()
        message = message.replace('"', '\\"')
        return f'global.say "{message}"'
    
    # Handle kick commands with reason
    elif command.startswith('kick ') and '"' not in command:
        parts = command.split(' ', 2)
        if len(parts) >= 3:
            # kick player reason -> kick "player" "reason"
            player = parts[1]
            reason = ' '.join(parts[2:])
            return f'kick "{player}" "{reason}"'
    
    # Handle ban commands with reason
    elif command.startswith('ban ') and '"' not in command:
        parts = command.split(' ', 2)
        if len(parts) >= 3:
            # ban player reason -> banid "player" "reason"
            player = parts[1]
            reason = ' '.join(parts[2:])
            return f'banid "{player}" "{reason}"'
    
    # Return command as-is if no special formatting needed
    return command

# ================================================================
# ✅ ENHANCED: CONSOLE LINE PARSING
# ================================================================

def parse_console_line(line):
    """
    ✅ ENHANCED: Parse individual console log line
    
    Args:
        line (str): Console log line
        
    Returns:
        dict: Parsed line data
    """
    if not line:
        return {}
    
    # Handle non-string input
    if not isinstance(line, str):
        line = str(line)
    
    line = line.strip()
    
    # Basic parsing structure
    parsed = {
        'raw': line,
        'timestamp': None,
        'level': None,
        'message': line,
        'type': 'unknown',
        'player': None,
        'server_id': None
    }
    
    try:
        # Try to extract timestamp (common formats)
        timestamp_patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',  # 2023-12-01 15:30:45
            r'(\d{2}:\d{2}:\d{2})',                     # 15:30:45
            r'\[(\d{2}:\d{2}:\d{2})\]',                 # [15:30:45]
        ]
        
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                parsed['timestamp'] = match.group(1)
                # Remove timestamp from message
                parsed['message'] = re.sub(pattern, '', line).strip()
                break
        
        # Try to extract log level
        level_pattern = r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL)\b'
        level_match = re.search(level_pattern, parsed['message'], re.IGNORECASE)
        if level_match:
            parsed['level'] = level_match.group(1).upper()
            parsed['message'] = re.sub(level_pattern, '', parsed['message'], flags=re.IGNORECASE).strip()
        
        # Try to extract player name
        player_patterns = [
            r'Player[:\s]+([^\s]+)',
            r'User[:\s]+([^\s]+)',
            r'([^\s]+)\s+joined',
            r'([^\s]+)\s+left',
            r'([^\s]+)\s+connected',
            r'([^\s]+)\s+disconnected'
        ]
        
        for pattern in player_patterns:
            match = re.search(pattern, parsed['message'], re.IGNORECASE)
            if match:
                parsed['player'] = match.group(1)
                break
        
        # Classify the message
        parsed['type'] = classify_message(parsed['message'])
        
    except Exception as e:
        logger.debug(f"Error parsing console line: {e}")
        # Return basic parsed structure even if detailed parsing fails
    
    return parsed

# ================================================================
# ✅ ENHANCED: PLAYER LIST PARSING
# ================================================================

def parse_player_list(response):
    """
    ✅ ENHANCED: Parse player list from console response
    
    Args:
        response: Console response containing player information
        
    Returns:
        list: List of player dictionaries
    """
    players = []
    
    if not response:
        return players
    
    try:
        # Handle different response formats
        if isinstance(response, dict):
            # GraphQL response format
            if 'data' in response:
                # Extract from GraphQL structure
                response_text = str(response.get('data', ''))
            else:
                response_text = str(response)
        else:
            response_text = str(response)
        
        # Common player list patterns
        player_patterns = [
            r'Player:\s*([^\s]+)',
            r'ID:\s*(\d+)\s+Name:\s*([^\s]+)',
            r'(\d+)\.\s*([^\s]+)',
            r'([^\s]+)\s+\((\d+)\)',
        ]
        
        for pattern in player_patterns:
            matches = re.findall(pattern, response_text, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) == 2:
                        # ID and name or name and ID
                        if match[0].isdigit():
                            player_id, name = match
                        else:
                            name, player_id = match
                    else:
                        name = match[0]
                        player_id = None
                else:
                    name = match
                    player_id = None
                
                player_data = {
                    'name': name,
                    'id': player_id,
                    'status': 'online'
                }
                
                if player_data not in players:
                    players.append(player_data)
    
    except Exception as e:
        logger.error(f"Error parsing player list: {e}")
    
    return players

# ================================================================
# ✅ ENHANCED: SERVER INFO PARSING
# ================================================================

def parse_server_info(response):
    """
    ✅ ENHANCED: Parse server info from console response
    
    Args:
        response: Console response containing server information
        
    Returns:
        dict: Server information dictionary
    """
    server_info = {
        'players': 0,
        'max_players': 0,
        'fps': 0,
        'map': None,
        'gamemode': None,
        'version': None
    }
    
    if not response:
        return server_info
    
    try:
        # Handle different response formats
        if isinstance(response, dict):
            response_text = str(response.get('data', response))
        else:
            response_text = str(response)
        
        # Extract player count
        player_patterns = [
            r'Players:\s*(\d+)/(\d+)',
            r'(\d+)\s*players\s*online\s*of\s*(\d+)',
            r'Player\s*Count:\s*(\d+)\s*/\s*(\d+)'
        ]
        
        for pattern in player_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                server_info['players'] = int(match.group(1))
                server_info['max_players'] = int(match.group(2))
                break
        
        # Extract FPS
        fps_patterns = [
            r'FPS:\s*(\d+)',
            r'Framerate:\s*(\d+)',
            r'(\d+)\s*fps'
        ]
        
        for pattern in fps_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                server_info['fps'] = int(match.group(1))
                break
        
        # Extract map name
        map_patterns = [
            r'Map:\s*([^\s\n]+)',
            r'Level:\s*([^\s\n]+)',
            r'Current\s*Map:\s*([^\s\n]+)'
        ]
        
        for pattern in map_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                server_info['map'] = match.group(1)
                break
        
        # Extract game mode
        mode_patterns = [
            r'Mode:\s*([^\s\n]+)',
            r'Gamemode:\s*([^\s\n]+)',
            r'Game\s*Mode:\s*([^\s\n]+)'
        ]
        
        for pattern in mode_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                server_info['gamemode'] = match.group(1)
                break
    
    except Exception as e:
        logger.error(f"Error parsing server info: {e}")
    
    return server_info

# ================================================================
# ✅ ENHANCED: MESSAGE DATA EXTRACTION
# ================================================================

def extract_message_data(message, message_type):
    """
    ✅ ENHANCED: Extract structured data from console messages
    
    Args:
        message (str): Console message
        message_type (str): Type of message
        
    Returns:
        dict: Extracted message data
    """
    data = {
        'type': message_type,
        'message': message,
        'player': None,
        'action': None,
        'target': None,
        'reason': None,
        'value': None
    }
    
    if not message:
        return data
    
    try:
        # Handle non-string input
        if not isinstance(message, str):
            message = str(message)
        
        message_lower = message.lower()
        
        # Extract player information based on message type
        if message_type == 'join':
            # Player joined patterns
            patterns = [
                r'([^\s]+)\s+joined',
                r'([^\s]+)\s+connected',
                r'Player\s+([^\s]+)\s+spawned'
            ]
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    data['player'] = match.group(1)
                    data['action'] = 'join'
                    break
        
        elif message_type == 'leave':
            # Player left patterns
            patterns = [
                r'([^\s]+)\s+left',
                r'([^\s]+)\s+disconnected',
                r'([^\s]+)\s+timed\s+out'
            ]
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    data['player'] = match.group(1)
                    data['action'] = 'leave'
                    break
        
        elif message_type == 'kill':
            # Kill event patterns
            patterns = [
                r'([^\s]+)\s+killed\s+([^\s]+)',
                r'([^\s]+)\s+was\s+killed\s+by\s+([^\s]+)',
                r'([^\s]+)\s+died'
            ]
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    if 'killed by' in message_lower:
                        data['player'] = match.group(1)  # victim
                        data['target'] = match.group(2)  # killer
                    elif 'killed' in message_lower:
                        data['player'] = match.group(1)  # killer
                        data['target'] = match.group(2)  # victim
                    else:
                        data['player'] = match.group(1)  # died
                    data['action'] = 'kill'
                    break
        
        elif message_type == 'admin':
            # Admin action patterns
            patterns = [
                r'([^\s]+)\s+banned\s+([^\s]+)\s*(?:for\s+(.+))?',
                r'([^\s]+)\s+kicked\s+([^\s]+)\s*(?:for\s+(.+))?',
                r'([^\s]+)\s+muted\s+([^\s]+)\s*(?:for\s+(.+))?'
            ]
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    data['player'] = match.group(1)  # admin
                    data['target'] = match.group(2)  # target player
                    if len(match.groups()) > 2 and match.group(3):
                        data['reason'] = match.group(3).strip()
                    
                    if 'banned' in message_lower:
                        data['action'] = 'ban'
                    elif 'kicked' in message_lower:
                        data['action'] = 'kick'
                    elif 'muted' in message_lower:
                        data['action'] = 'mute'
                    break
    
    except Exception as e:
        logger.debug(f"Error extracting message data: {e}")
    
    return data

# ================================================================
# MODULE EXPORTS
# ================================================================

__all__ = [
    # Core parsing functions
    'parse_console_response',
    'parse_console_line',
    'extract_message_data',
    
    # Message processing
    'classify_message',
    'get_type_icon',
    'format_console_message',
    
    # Command handling (CRITICAL)
    'format_command',
    
    # Enhanced parsing
    'parse_player_list',
    'parse_server_info'
]

logger.info("✅ COMPLETE console_helpers module loaded with ALL MISSING FUNCTIONS restored")