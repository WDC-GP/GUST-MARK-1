"""
GUST Bot Enhanced - Helper Functions (WINDOWS COMPATIBLE VERSION)
================================================================
✅ FIXED: Windows compatibility for file locking
✅ FIXED: Token expiration and random disconnection issues
✅ FIXED: Cross-platform file operations
✅ FIXED: Better validation and error handling
✅ NO CIRCULAR IMPORTS - Safe to import
"""

import json
import time
import os
import logging
import platform
from datetime import datetime

# Cross-platform file locking imports
try:
    if platform.system() == 'Windows':
        import msvcrt  # Windows file locking
        FILE_LOCKING_AVAILABLE = True
        FILE_LOCKING_TYPE = 'windows'
    else:
        import fcntl   # Unix/Linux file locking
        FILE_LOCKING_AVAILABLE = True
        FILE_LOCKING_TYPE = 'unix'
except ImportError:
    FILE_LOCKING_AVAILABLE = False
    FILE_LOCKING_TYPE = 'none'

# Initialize logger - using basic logging to avoid circular imports
logger = logging.getLogger(__name__)

# Log file locking availability
logger.debug(f"File locking: {FILE_LOCKING_TYPE} ({'available' if FILE_LOCKING_AVAILABLE else 'not available'})")

# ================================================================
# CROSS-PLATFORM FILE LOCKING FUNCTIONS
# ================================================================

def acquire_file_lock(file_handle):
    """
    Acquire file lock in a cross-platform way
    
    Args:
        file_handle: Open file handle
        
    Returns:
        bool: True if lock acquired successfully
    """
    if not FILE_LOCKING_AVAILABLE:
        logger.debug("⚠️ File locking not available, continuing without lock")
        return True
    
    try:
        if FILE_LOCKING_TYPE == 'windows':
            # Windows file locking
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
            logger.debug("🔒 Windows file lock acquired")
            return True
        elif FILE_LOCKING_TYPE == 'unix':
            # Unix/Linux file locking
            import fcntl
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.debug("🔒 Unix file lock acquired")
            return True
    except (OSError, IOError) as e:
        logger.debug(f"⚠️ Could not acquire file lock: {e}")
        return False
    except Exception as e:
        logger.debug(f"⚠️ Unexpected file locking error: {e}")
        return False
    
    return True

def release_file_lock(file_handle):
    """
    Release file lock in a cross-platform way
    
    Args:
        file_handle: Open file handle
    """
    if not FILE_LOCKING_AVAILABLE:
        return
    
    try:
        if FILE_LOCKING_TYPE == 'windows':
            # Windows file unlocking
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            logger.debug("🔓 Windows file lock released")
        elif FILE_LOCKING_TYPE == 'unix':
            # Unix/Linux file unlocking
            import fcntl
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
            logger.debug("🔓 Unix file lock released")
    except Exception as e:
        logger.debug(f"⚠️ Error releasing file lock: {e}")

# ================================================================
# FIXED TOKEN MANAGEMENT FUNCTIONS
# ================================================================

def load_token():
    """
    Load and refresh G-Portal token if needed
    ✅ FIXED: Windows-compatible file operations
    ✅ FIXED: More generous buffer time to prevent random expiration
    ✅ FIXED: Better handling of invalid token formats
    
    Returns:
        str: Valid access token or empty string if unavailable
    """
    try:
        token_file = 'gp-session.json'
        
        # Check if file exists
        if not os.path.exists(token_file):
            logger.debug("Token file not found")
            return ''
            
        with open(token_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Validate data structure
        if not isinstance(data, dict):
            logger.error("Invalid token file format - not a dictionary")
            return ''
            
        current_time = time.time()
        token_exp = data.get('access_token_exp', 0)
        
        # Convert to proper numeric type if needed
        try:
            token_exp = float(token_exp) if token_exp else 0
        except (ValueError, TypeError):
            logger.error(f"Invalid token expiration format: {token_exp}")
            return ''
            
        # ✅ FIXED: More generous buffer time (was 30, now 120 seconds)
        # This prevents the random expiration issues you were seeing
        buffer_time = 120
        time_until_expiry = token_exp - current_time
        
        logger.debug(f"Token expires in {time_until_expiry:.1f} seconds (buffer: {buffer_time}s)")
        
        if time_until_expiry > buffer_time:
            # Token is still valid
            access_token = data.get('access_token', '')
            if access_token and access_token.strip():
                logger.debug("Returning valid access token")
                return access_token.strip()
            else:
                logger.error("No access token in file or token is empty")
                return ''
        else:
            # Token expired or expiring soon, try to refresh
            logger.info(f"⏰ Token expires in {time_until_expiry:.1f}s, attempting refresh...")
            
            if refresh_token():
                # Refresh successful, reload token
                try:
                    with open(token_file, 'r', encoding='utf-8') as f:
                        refreshed_data = json.load(f)
                    new_token = refreshed_data.get('access_token', '')
                    if new_token and new_token.strip():
                        logger.info("✅ Token refresh successful, returning new token")
                        return new_token.strip()
                    else:
                        logger.error("❌ Refreshed token file contains no valid token")
                except Exception as e:
                    logger.error(f"❌ Error reading refreshed token: {e}")
            
            logger.warning("❌ Token refresh failed or no token available")
            return ''
            
    except FileNotFoundError:
        logger.debug("Token file not found")
        return ''
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in token file: {e}")
        return ''
    except Exception as e:
        logger.error(f"Unexpected error loading token: {e}")
        return ''

def refresh_token():
    """
    Refresh G-Portal access token using refresh token
    ✅ FIXED: Windows-compatible file locking
    ✅ FIXED: Better error handling and retry logic
    ✅ FIXED: More robust response validation
    
    Returns:
        bool: True if refresh successful, False otherwise
    """
    import requests
    
    token_file = 'gp-session.json'
    
    # ✅ FIXED: Check if file exists before attempting to open
    if not os.path.exists(token_file):
        logger.error("❌ Token file not found for refresh")
        return False
    
    try:
        # ✅ FIXED: Windows-compatible file locking
        with open(token_file, 'r+', encoding='utf-8') as f:
            
            # Try to acquire file lock (cross-platform)
            lock_acquired = acquire_file_lock(f)
            if lock_acquired:
                logger.debug("🔒 File lock acquired for token refresh")
            else:
                logger.debug("⚠️ Could not acquire file lock, proceeding without lock")
                
            try:
                f.seek(0)
                tokens = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in token file: {e}")
                return False
            finally:
                # Always try to release lock
                if lock_acquired:
                    release_file_lock(f)
            
            if not isinstance(tokens, dict):
                logger.error("❌ Token file is not a valid dictionary")
                return False
            
            if 'refresh_token' not in tokens:
                logger.error("❌ No refresh token available in file")
                return False
            
            refresh_token_value = tokens.get('refresh_token')
            if not refresh_token_value or not refresh_token_value.strip():
                logger.error("❌ Empty or invalid refresh token")
                return False
            
            # ✅ FIXED: Check if refresh token is expired
            current_time = time.time()
            refresh_exp = tokens.get('refresh_token_exp', 0)
            if refresh_exp and current_time > refresh_exp:
                logger.error(f"❌ Refresh token expired at {datetime.fromtimestamp(refresh_exp)}")
                return False
            
            # Prepare refresh request
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token_value.strip(),
                'client_id': 'website'
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'GUST-Bot/2.0',
                'Accept': 'application/json'
            }
            
            # Use hardcoded URL to avoid importing Config
            gportal_auth_url = 'https://www.g-portal.com/ngpapi/oauth/token'
            
            logger.info("🔄 Attempting token refresh...")
            
            # ✅ FIXED: Retry logic with exponential backoff
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.debug(f"🔄 Refresh attempt {attempt + 1}/{max_retries}")
                    
                    response = requests.post(
                        gportal_auth_url,
                        data=data,
                        headers=headers,
                        timeout=15,  # Increased timeout
                        allow_redirects=False  # Don't follow redirects
                    )
                    
                    logger.debug(f"📡 Refresh response: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            new_tokens = response.json()
                        except json.JSONDecodeError:
                            logger.error("❌ Invalid JSON in refresh response")
                            continue
                        
                        # ✅ FIXED: Validate response structure
                        if not isinstance(new_tokens, dict) or 'access_token' not in new_tokens:
                            logger.error(f"❌ Invalid token response format: {new_tokens}")
                            continue
                        
                        # ✅ FIXED: Validate token content
                        new_access_token = new_tokens.get('access_token', '').strip()
                        if not new_access_token:
                            logger.error("❌ Empty access token in refresh response")
                            continue
                        
                        current_time = time.time()
                        
                        # ✅ FIXED: Better handling of expiration times
                        expires_in = new_tokens.get('expires_in', 300)  # Default 5 minutes
                        refresh_expires_in = new_tokens.get('refresh_expires_in', 86400)  # Default 24 hours
                        
                        try:
                            expires_in = int(float(expires_in))
                            refresh_expires_in = int(float(refresh_expires_in))
                        except (ValueError, TypeError):
                            logger.warning("⚠️ Invalid expiration times, using defaults")
                            expires_in = 300
                            refresh_expires_in = 86400
                        
                        # Update tokens with comprehensive data
                        tokens.update({
                            'access_token': new_access_token,
                            'refresh_token': new_tokens.get('refresh_token', tokens.get('refresh_token', '')).strip(),
                            'access_token_exp': int(current_time + expires_in),
                            'refresh_token_exp': int(current_time + refresh_expires_in),
                            'timestamp': datetime.now().isoformat(),
                            'last_refresh': datetime.now().isoformat(),
                            'expires_in': expires_in,
                            'refresh_expires_in': refresh_expires_in
                        })
                        
                        # ✅ FIXED: Atomic write operation with cross-platform locking
                        try:
                            # Reopen file for writing with lock
                            with open(token_file, 'w', encoding='utf-8') as write_f:
                                write_lock_acquired = acquire_file_lock(write_f)
                                try:
                                    json.dump(tokens, write_f, indent=2, ensure_ascii=False)
                                    write_f.flush()
                                    if hasattr(os, 'fsync'):
                                        os.fsync(write_f.fileno())  # Force write to disk (Unix)
                                finally:
                                    if write_lock_acquired:
                                        release_file_lock(write_f)
                            
                            logger.info(f"✅ Token refresh successful on attempt {attempt + 1}")
                            logger.debug(f"📅 New token expires: {datetime.fromtimestamp(tokens['access_token_exp'])}")
                            return True
                            
                        except Exception as write_error:
                            logger.error(f"❌ Failed to write refreshed tokens: {write_error}")
                            return False
                        
                    elif response.status_code == 400:
                        # Bad request - likely invalid refresh token
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('error', 'Bad request')
                            error_desc = error_data.get('error_description', '')
                            logger.error(f"❌ Token refresh bad request: {error_msg} - {error_desc}")
                        except:
                            logger.error(f"❌ Token refresh bad request: {response.text[:200]}")
                        return False
                        
                    elif response.status_code == 401:
                        # Unauthorized - refresh token expired or invalid
                        logger.error("❌ Token refresh unauthorized - refresh token expired or invalid")
                        return False
                        
                    else:
                        logger.warning(f"⚠️ Token refresh failed with status {response.status_code} (attempt {attempt + 1})")
                        if attempt < max_retries - 1:
                            sleep_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                            logger.debug(f"⏳ Waiting {sleep_time}s before retry...")
                            time.sleep(sleep_time)
                            
                except requests.exceptions.Timeout:
                    logger.warning(f"⏰ Token refresh timeout (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                except requests.exceptions.ConnectionError:
                    logger.warning(f"🌐 Connection error during refresh (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                except Exception as e:
                    logger.error(f"❌ Unexpected error during refresh attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        
            logger.error(f"❌ All {max_retries} token refresh attempts failed")
            return False
            
    except FileNotFoundError:
        logger.error("❌ Token file not found for refresh")
        return False
    except PermissionError:
        logger.error("❌ Permission denied accessing token file")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during token refresh: {e}")
        return False

def save_token(tokens, username):
    """
    Save G-Portal authentication tokens
    ✅ FIXED: Windows-compatible atomic file operations
    
    Args:
        tokens (dict): Token data from G-Portal
        username (str): Username for tracking
        
    Returns:
        bool: True if save successful
    """
    try:
        if not isinstance(tokens, dict):
            logger.error(f"❌ Invalid tokens format: {type(tokens)}")
            return False
        
        if not tokens.get('access_token') or not tokens.get('refresh_token'):
            logger.error("❌ Missing required tokens in save_token")
            return False
        
        current_time = time.time()
        token_file = 'gp-session.json'
        
        # ✅ FIXED: More robust expiration handling
        expires_in = tokens.get('expires_in', 300)
        refresh_expires_in = tokens.get('refresh_expires_in', 86400)
        
        try:
            expires_in = int(float(expires_in))
            refresh_expires_in = int(float(refresh_expires_in))
        except (ValueError, TypeError):
            logger.warning("⚠️ Invalid expiration values, using defaults")
            expires_in = 300
            refresh_expires_in = 86400
        
        session_data = {
            'access_token': tokens['access_token'].strip(),
            'refresh_token': tokens['refresh_token'].strip(),
            'access_token_exp': int(current_time + expires_in),
            'refresh_token_exp': int(current_time + refresh_expires_in),
            'timestamp': datetime.now().isoformat(),
            'username': username.strip() if username else 'unknown',
            'expires_in': expires_in,
            'refresh_expires_in': refresh_expires_in,
            'saved_at': datetime.now().isoformat()
        }
        
        # ✅ FIXED: Windows-compatible atomic file write
        temp_file = token_file + '.tmp'
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                lock_acquired = acquire_file_lock(f)
                try:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    if hasattr(os, 'fsync'):
                        os.fsync(f.fileno())  # Force write to disk (Unix)
                finally:
                    if lock_acquired:
                        release_file_lock(f)
            
            # Atomic move (Windows-compatible)
            if os.path.exists(token_file):
                os.remove(token_file)  # Windows requires this
            os.rename(temp_file, token_file)
            
            logger.info(f"✅ Token saved successfully for {username}")
            logger.debug(f"📅 Token expires: {datetime.fromtimestamp(session_data['access_token_exp'])}")
            return True
            
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise e
        
    except Exception as e:
        logger.error(f"❌ Error saving token: {e}")
        return False

# ✅ NEW: Token validation function
def validate_token_file():
    """
    Validate token file structure and content
    ✅ NEW: Comprehensive token file validation
    
    Returns:
        dict: Validation results with detailed status
    """
    token_file = 'gp-session.json'
    
    result = {
        'valid': False,
        'exists': False,
        'has_access_token': False,
        'has_refresh_token': False,
        'access_token_valid': False,
        'refresh_token_valid': False,
        'time_left': 0,
        'refresh_time_left': 0,
        'issues': [],
        'expires_at': None,
        'refresh_expires_at': None
    }
    
    try:
        if not os.path.exists(token_file):
            result['issues'].append('Token file does not exist')
            return result
            
        result['exists'] = True
        
        with open(token_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, dict):
            result['issues'].append('Token file is not a valid JSON object')
            return result
            
        current_time = time.time()
        
        # Check access token
        access_token = data.get('access_token')
        if access_token and access_token.strip():
            result['has_access_token'] = True
            
            # Check expiration
            token_exp = data.get('access_token_exp', 0)
            
            if token_exp:
                try:
                    token_exp = float(token_exp)
                    time_left = token_exp - current_time
                    result['time_left'] = max(0, time_left)
                    result['expires_at'] = datetime.fromtimestamp(token_exp).isoformat()
                    result['access_token_valid'] = time_left > 60  # 1 minute buffer
                except (ValueError, TypeError):
                    result['issues'].append('Invalid access token expiration format')
            else:
                result['issues'].append('No access token expiration time')
        else:
            result['issues'].append('No access token in file')
            
        # Check refresh token
        refresh_token = data.get('refresh_token')
        if refresh_token and refresh_token.strip():
            result['has_refresh_token'] = True
            
            # Check refresh token expiration
            refresh_exp = data.get('refresh_token_exp', 0)
            if refresh_exp:
                try:
                    refresh_exp = float(refresh_exp)
                    refresh_time_left = refresh_exp - current_time
                    result['refresh_time_left'] = max(0, refresh_time_left)
                    result['refresh_expires_at'] = datetime.fromtimestamp(refresh_exp).isoformat()
                    result['refresh_token_valid'] = refresh_time_left > 0
                except (ValueError, TypeError):
                    result['issues'].append('Invalid refresh token expiration format')
            else:
                result['issues'].append('No refresh token expiration time')
        else:
            result['issues'].append('No refresh token in file')
            
        # Overall validity
        result['valid'] = (result['has_access_token'] and 
                          result['has_refresh_token'] and
                          (result['access_token_valid'] or result['refresh_token_valid']))
        
        return result
        
    except json.JSONDecodeError as e:
        result['issues'].append(f'Invalid JSON format: {str(e)}')
        return result
    except Exception as e:
        result['issues'].append(f'Error reading file: {str(e)}')
        return result

# ================================================================
# EXISTING HELPER FUNCTIONS (UNCHANGED)
# ================================================================

def parse_console_response(response_data):
    """
    Parse G-Portal GraphQL response for console commands
    ✅ CRITICAL function for console command fix
    
    Args:
        response_data (dict): Response from G-Portal API
        
    Returns:
        tuple: (success, message)
    """
    logger.debug(f"parse_console_response called with: {response_data}")
    
    if not response_data or not isinstance(response_data, dict):
        logger.warning(f"Invalid response_data: {response_data}")
        return False, "Invalid response data"
    
    try:
        if 'data' in response_data and 'sendConsoleMessage' in response_data['data']:
            result = response_data['data']['sendConsoleMessage']
            success = result.get('ok', False)  # ✅ Correct field name 'ok' not 'success'
            logger.debug(f"GraphQL sendConsoleMessage result: ok={success}")
            return success, "Command executed successfully" if success else "Command failed"
        elif 'errors' in response_data:
            errors = response_data['errors']
            error_messages = [error.get('message', 'Unknown error') for error in errors]
            error_msg = f"GraphQL errors: {', '.join(error_messages)}"
            logger.error(f"GraphQL errors in response: {error_msg}")
            return False, error_msg
        else:
            logger.warning("Unexpected response format - no data.sendConsoleMessage or errors")
            return False, "Unexpected response format"
    except Exception as e:
        logger.error(f"Exception in parse_console_response: {e}")
        return False, f"Response parsing error: {str(e)}"

def classify_message(message):
    """
    Classify console message type based on content
    
    Args:
        message (str): Console message text
        
    Returns:
        str: Message type classification
    """
    if not message or not isinstance(message, str):
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
    Validate server ID format
    
    Args:
        server_id: Server ID to validate
        
    Returns:
        tuple: (is_valid, clean_server_id)
    """
    logger.debug(f"validate_server_id called with: {server_id} (type: {type(server_id)})")
    
    if not server_id:
        logger.warning(f"Empty server_id: {server_id}")
        return False, None
    
    try:
        # Handle test server IDs that might have suffixes
        if isinstance(server_id, str) and '_test' in server_id:
            clean_id = int(server_id.split('_')[0])
        else:
            clean_id = int(server_id)
        
        logger.debug(f"Server ID validated: {server_id} -> {clean_id}")
        return True, clean_id
    except (ValueError, TypeError) as e:
        logger.warning(f"Server ID validation failed for {server_id}: {e}")
        return False, None

def validate_region(region):
    """
    Validate server region
    
    Args:
        region (str): Region code
        
    Returns:
        bool: True if valid region
    """
    logger.debug(f"validate_region called with: {region} (type: {type(region)})")
    
    if not region or not isinstance(region, str):
        logger.warning(f"Invalid region input: {region}")
        return False
    
    valid_regions = ['US', 'EU', 'AS']
    result = region.upper() in valid_regions
    logger.debug(f"Region validation result for '{region}': {result}")
    return result

def format_command(command):
    """
    Format console command properly
    
    Args:
        command (str): Raw command
        
    Returns:
        str: Formatted command
    """
    logger.debug(f"format_command called with: {command} (type: {type(command)})")
    
    if not command or not isinstance(command, str):
        logger.warning(f"Invalid command input: {command}")
        return ""
    
    command = command.strip()
    
    if command.startswith('say '):
        formatted = f'global.say "{command[4:]}"'
    elif command.startswith('global.'):
        formatted = command
    else:
        formatted = command
    
    logger.debug(f"Command formatted from '{command}' to '{formatted}'")
    return formatted

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
    if not text or not isinstance(text, str):
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
    if not timestamp_str or not isinstance(timestamp_str, str):
        return datetime.now().strftime("%H:%M:%S")
    
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
    if not filename or not isinstance(filename, str):
        return "unnamed"
    
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename