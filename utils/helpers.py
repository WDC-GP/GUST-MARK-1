"""
GUST Bot Enhanced - Helper Functions (ENHANCED TOKEN MANAGEMENT VERSION)
========================================================================
✅ ENHANCED: Reduced buffer time from 120s to 60s for earlier refresh detection
✅ ENHANCED: Comprehensive token validation before returning (length > 10 chars)
✅ ENHANCED: Proper refresh token expiration checking
✅ ENHANCED: Enhanced error handling with detailed logging
✅ ENHANCED: Better file handling and JSON validation
✅ NEW: monitor_token_health() function for comprehensive token status
✅ NEW: Enhanced validate_token_file() with detailed validation
✅ ENHANCED: Improved G-Portal API request formatting with proper headers
✅ ENHANCED: Better error handling for different HTTP status codes
✅ ENHANCED: Single attempt with comprehensive error logging
✅ FIXED: create_server_data() function signature corrected
✅ FIXED: save_token() function parameter handling corrected
"""

import os
import json
import time
import logging
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any
import requests

logger = logging.getLogger(__name__)

# Cross-platform file locking
try:
    import msvcrt
    FILE_LOCKING_TYPE = 'windows'
    FILE_LOCKING_AVAILABLE = True
except ImportError:
    try:
        import fcntl
        FILE_LOCKING_TYPE = 'unix'
        FILE_LOCKING_AVAILABLE = True
    except ImportError:
        FILE_LOCKING_AVAILABLE = False
        FILE_LOCKING_TYPE = 'none'

# ================================================================
# FILE LOCKING UTILITIES
# ================================================================

def acquire_file_lock(file_handle):
    """Cross-platform file locking"""
    if not FILE_LOCKING_AVAILABLE:
        return False
    
    try:
        if FILE_LOCKING_TYPE == 'windows':
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
            logger.debug("🔒 Windows file lock acquired")
            return True
        elif FILE_LOCKING_TYPE == 'unix':
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.debug("🔒 Unix file lock acquired")
            return True
    except Exception as e:
        logger.debug(f"⚠️ Could not acquire file lock: {e}")
        return False

def release_file_lock(file_handle):
    """Cross-platform file lock release"""
    if not FILE_LOCKING_AVAILABLE:
        return
    
    try:
        if FILE_LOCKING_TYPE == 'windows':
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            logger.debug("🔓 Windows file lock released")
        elif FILE_LOCKING_TYPE == 'unix':
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
            logger.debug("🔓 Unix file lock released")
    except Exception as e:
        logger.debug(f"⚠️ Error releasing file lock: {e}")

# ================================================================
# ✅ ENHANCED TOKEN MANAGEMENT FUNCTIONS
# ================================================================

def load_token():
    """
    ✅ ENHANCED: Load and refresh G-Portal token with reduced buffer time
    
    CHANGES:
    - Buffer time reduced from 120s to 60s for earlier refresh detection
    - Comprehensive token validation before returning (length > 10 chars)
    - Proper refresh token expiration checking
    - Enhanced error handling with detailed logging
    - Better file handling and JSON validation
    
    Returns:
        str: Valid access token or empty string if unavailable
    """
    try:
        token_file = 'gp-session.json'
        
        # Check if file exists
        if not os.path.exists(token_file):
            logger.debug("📁 Token file not found")
            return ''
            
        with open(token_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # ✅ ENHANCED: Validate data structure
        if not isinstance(data, dict):
            logger.error("❌ Invalid token file format - not a dictionary")
            return ''
            
        current_time = time.time()
        token_exp = data.get('access_token_exp', 0)
        
        # ✅ ENHANCED: Convert to proper numeric type with validation
        try:
            token_exp = float(token_exp) if token_exp else 0
        except (ValueError, TypeError):
            logger.error(f"❌ Invalid token expiration format: {token_exp}")
            return ''
            
        # ✅ CRITICAL FIX: Reduced buffer time from 120s to 60s for earlier refresh detection
        buffer_time = 60  # CRITICAL: Must be 60 seconds, not 120!
        time_until_expiry = token_exp - current_time
        
        logger.debug(f"⏰ Token expires in {time_until_expiry:.1f} seconds (buffer: {buffer_time}s)")
        
        if time_until_expiry > buffer_time:
            # Token is still valid
            access_token = data.get('access_token', '')
            
            # ✅ ENHANCED: Comprehensive token validation (length > 10 chars)
            if access_token and access_token.strip() and len(access_token.strip()) > 10:
                logger.debug("✅ Returning valid access token")
                return access_token.strip()
            else:
                logger.error("❌ Access token invalid or too short")
                return ''
        else:
            # Token expired or expiring soon, try to refresh
            logger.info(f"🔄 Token expires in {time_until_expiry:.1f}s, attempting refresh...")
            
            if refresh_token():
                # Refresh successful, reload token
                try:
                    with open(token_file, 'r', encoding='utf-8') as f:
                        refreshed_data = json.load(f)
                    new_token = refreshed_data.get('access_token', '')
                    
                    # ✅ ENHANCED: Validate refreshed token
                    if new_token and new_token.strip() and len(new_token.strip()) > 10:
                        logger.info("✅ Token refresh successful, returning new token")
                        return new_token.strip()
                    else:
                        logger.error("❌ Refreshed token invalid or too short")
                except Exception as e:
                    logger.error(f"❌ Error reading refreshed token: {e}")
            
            logger.warning("❌ Token refresh failed or no token available")
            return ''
            
    except FileNotFoundError:
        logger.debug("📁 Token file not found")
        return ''
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in token file: {e}")
        return ''
    except Exception as e:
        logger.error(f"❌ Unexpected error loading token: {e}")
        return ''

def refresh_token():
    """
    ✅ ENHANCED: Refresh G-Portal access token with improved error handling
    
    CHANGES:
    - Improved G-Portal API request formatting with proper headers
    - Better error handling for different HTTP status codes
    - Proper token expiration calculation and storage  
    - Single attempt with comprehensive error logging
    - Remove retry loops that may trigger rate limiting
    
    Returns:
        bool: True if refresh successful, False otherwise
    """
    token_file = 'gp-session.json'
    
    # Check if file exists before attempting to open
    if not os.path.exists(token_file):
        logger.error("❌ Token file not found for refresh")
        return False
    
    try:
        # Load existing tokens with file locking
        with open(token_file, 'r+', encoding='utf-8') as f:
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
            
            # ✅ ENHANCED: Check if refresh token is expired
            current_time = time.time()
            refresh_exp = tokens.get('refresh_token_exp', 0)
            if refresh_exp and current_time > refresh_exp:
                logger.error(f"❌ Refresh token expired at {datetime.fromtimestamp(refresh_exp)}")
                return False
            
            # ✅ ENHANCED: Prepare refresh request with improved formatting
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token_value.strip(),
                'client_id': 'website'
            }
            
            # ✅ ENHANCED: Improved headers for better G-Portal compatibility
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Origin': 'https://www.g-portal.com',
                'Referer': 'https://www.g-portal.com/',
                'Accept': 'application/json'
            }
            
            gportal_auth_url = 'https://www.g-portal.com/ngpapi/oauth/token'
            
            logger.info("🔄 Attempting enhanced token refresh...")
            
            # ✅ ENHANCED: Single attempt with comprehensive error logging
            try:
                response = requests.post(
                    gportal_auth_url,
                    data=data,
                    headers=headers,
                    timeout=15,
                    allow_redirects=False
                )
                
                logger.debug(f"📡 Enhanced refresh response: {response.status_code}")
                
                # ✅ ENHANCED: Better error handling for different HTTP status codes
                if response.status_code == 200:
                    try:
                        new_tokens = response.json()
                    except json.JSONDecodeError:
                        logger.error("❌ Invalid JSON in refresh response")
                        return False
                    
                    # Validate response structure
                    if not isinstance(new_tokens, dict) or 'access_token' not in new_tokens:
                        logger.error(f"❌ Invalid token response format: {new_tokens}")
                        return False
                    
                    # Validate token content
                    new_access_token = new_tokens.get('access_token', '').strip()
                    if not new_access_token or len(new_access_token) < 10:
                        logger.error("❌ Invalid access token in refresh response")
                        return False
                    
                    # ✅ ENHANCED: Proper token expiration calculation and storage
                    expires_in = new_tokens.get('expires_in', 300)
                    refresh_expires_in = new_tokens.get('refresh_expires_in', 86400)
                    
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
                        'refresh_count': tokens.get('refresh_count', 0) + 1
                    })
                    
                    # ✅ FIXED: Save updated tokens with correct username
                    username = tokens.get('username', 'unknown')
                    if save_token(tokens, username):
                        logger.info("✅ Enhanced token refresh successful")
                        return True
                    else:
                        logger.error("❌ Failed to save refreshed tokens")
                        return False
                        
                elif response.status_code == 400:
                    logger.error("❌ Bad request - refresh token invalid/expired")
                    return False
                elif response.status_code == 401:
                    logger.error("❌ Unauthorized - refresh token expired")
                    return False
                elif response.status_code == 429:
                    logger.error("❌ Rate limited - too many requests")
                    return False
                else:
                    logger.error(f"❌ HTTP error {response.status_code}: {response.text}")
                    return False
                    
            except requests.exceptions.Timeout:
                logger.error("❌ Request timeout during token refresh")
                return False
            except requests.exceptions.ConnectionError:
                logger.error("❌ Connection error during token refresh")
                return False
            except Exception as request_error:
                logger.error(f"❌ Request error during token refresh: {request_error}")
                return False
            
    except Exception as e:
        logger.error(f"❌ Error in token refresh: {e}")
        return False

def save_token(tokens, username='unknown'):
    """
    ✅ FIXED: Save tokens to file with enhanced validation and corrected parameter handling
    
    Args:
        tokens (dict): Token data (can be dict with 'access_token' etc. OR full token response)
        username (str): Username for tracking (optional)
        
    Returns:
        bool: True if save successful
    """
    try:
        token_file = 'gp-session.json'
        current_time = time.time()
        
        # ✅ FIXED: Handle different input formats
        if not isinstance(tokens, dict):
            logger.error("❌ Tokens must be a dictionary")
            return False
        
        # Check if this is already a properly formatted token structure
        if 'access_token_exp' in tokens and 'refresh_token_exp' in tokens:
            # This is already a complete token structure, just save it
            temp_file = token_file + '.tmp'
            
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    lock_acquired = acquire_file_lock(f)
                    try:
                        json.dump(tokens, f, indent=2, ensure_ascii=False)
                        f.flush()
                        if hasattr(os, 'fsync'):
                            os.fsync(f.fileno())
                    finally:
                        if lock_acquired:
                            release_file_lock(f)
                
                # Atomic move
                if os.path.exists(token_file):
                    os.remove(token_file)
                os.rename(temp_file, token_file)
                
                logger.info(f"✅ Updated token saved successfully for {username}")
                return True
                
            except Exception as e:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                raise e
        
        # Handle new token format from G-Portal API response
        if 'access_token' not in tokens or 'refresh_token' not in tokens:
            logger.error("❌ Missing required tokens in save_token")
            return False
        
        # Calculate expiration times
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
        
        # Atomic file write
        temp_file = token_file + '.tmp'
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                lock_acquired = acquire_file_lock(f)
                try:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    if hasattr(os, 'fsync'):
                        os.fsync(f.fileno())
                finally:
                    if lock_acquired:
                        release_file_lock(f)
            
            # Atomic move
            if os.path.exists(token_file):
                os.remove(token_file)
            os.rename(temp_file, token_file)
            
            logger.info(f"✅ Token saved successfully for {username}")
            return True
            
        except Exception as e:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise e
        
    except Exception as e:
        logger.error(f"❌ Error saving token: {e}")
        return False

# ================================================================
# ✅ NEW: ENHANCED TOKEN HEALTH MONITORING
# ================================================================

def monitor_token_health():
    """
    ✅ NEW: Comprehensive token status reporting
    
    Returns:
        dict: Complete token health assessment with recommendations
    """
    try:
        token_file = 'gp-session.json'
        current_time = time.time()
        
        health_status = {
            'healthy': False,
            'status': 'unknown',
            'action': 'check_system',
            'message': 'Token status unknown',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        if not os.path.exists(token_file):
            health_status.update({
                'status': 'missing',
                'action': 'login_required',
                'message': 'No token file found - login required',
                'details': {'file_exists': False}
            })
            return health_status
        
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            health_status.update({
                'status': 'corrupted',
                'action': 'login_required',
                'message': f'Token file corrupted: {e}',
                'details': {'file_exists': True, 'valid_json': False}
            })
            return health_status
        
        if not isinstance(data, dict):
            health_status.update({
                'status': 'invalid',
                'action': 'login_required',
                'message': 'Token file is not a valid dictionary',
                'details': {'file_exists': True, 'valid_json': True, 'valid_structure': False}
            })
            return health_status
        
        # Get token info
        access_token = data.get('access_token', '')
        refresh_token = data.get('refresh_token', '')
        access_exp = data.get('access_token_exp', 0)
        refresh_exp = data.get('refresh_token_exp', 0)
        
        # Calculate time remaining
        access_time_left = access_exp - current_time if access_exp else 0
        refresh_time_left = refresh_exp - current_time if refresh_exp else 0
        
        details = {
            'file_exists': True,
            'valid_json': True,
            'valid_structure': True,
            'has_access_token': bool(access_token and len(access_token.strip()) > 10),
            'has_refresh_token': bool(refresh_token and len(refresh_token.strip()) > 10),
            'access_time_left_seconds': max(0, access_time_left),
            'refresh_time_left_seconds': max(0, refresh_time_left),
            'access_expires_at': datetime.fromtimestamp(access_exp).isoformat() if access_exp else None,
            'refresh_expires_at': datetime.fromtimestamp(refresh_exp).isoformat() if refresh_exp else None
        }
        
        # Determine health status
        if not details['has_access_token']:
            health_status.update({
                'status': 'no_access_token',
                'action': 'login_required',
                'message': 'No valid access token found',
                'details': details
            })
        elif not details['has_refresh_token']:
            health_status.update({
                'status': 'no_refresh_token',
                'action': 'login_required',
                'message': 'No valid refresh token found',
                'details': details
            })
        elif refresh_time_left <= 0:
            health_status.update({
                'status': 'refresh_expired',
                'action': 'login_required',
                'message': 'Refresh token has expired - re-login required',
                'details': details
            })
        elif access_time_left <= 0:
            if refresh_time_left > 300:  # 5 minutes buffer
                health_status.update({
                    'healthy': False,
                    'status': 'expired_refreshable',
                    'action': 'refresh_now',
                    'message': 'Access token expired but refresh token valid - refresh recommended',
                    'details': details
                })
            else:
                health_status.update({
                    'status': 'refresh_expiring_soon',
                    'action': 'login_required',
                    'message': 'Both tokens expiring soon - re-login recommended',
                    'details': details
                })
        elif access_time_left < 300:  # 5 minutes
            health_status.update({
                'healthy': False,
                'status': 'expiring_soon',
                'action': 'refresh_soon',
                'message': f'Access token expires in {int(access_time_left/60)} minutes - refresh soon',
                'details': details
            })
        else:
            health_status.update({
                'healthy': True,
                'status': 'healthy',
                'action': 'none',
                'message': f'Tokens healthy - access token valid for {int(access_time_left/60)} minutes',
                'details': details
            })
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Error monitoring token health: {e}")
        return {
            'healthy': False,
            'status': 'error',
            'action': 'check_system',
            'message': f'Error checking token health: {e}',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }

def validate_token_file():
    """
    ✅ ENHANCED: Comprehensive token file validation
    
    Returns:
        dict: Detailed validation results with status and time information
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
        if access_token and access_token.strip() and len(access_token.strip()) > 10:
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
            result['issues'].append('No valid access token in file')
            
        # Check refresh token
        refresh_token = data.get('refresh_token')
        if refresh_token and refresh_token.strip() and len(refresh_token.strip()) > 10:
            result['has_refresh_token'] = True
            
            # Check refresh token expiration
            refresh_exp = data.get('refresh_token_exp', 0)
            if refresh_exp:
                try:
                    refresh_exp = float(refresh_exp)
                    refresh_time_left = refresh_exp - current_time
                    result['refresh_time_left'] = max(0, refresh_time_left)
                    result['refresh_expires_at'] = datetime.fromtimestamp(refresh_exp).isoformat()
                    result['refresh_token_valid'] = refresh_time_left > 300  # 5 minute buffer
                except (ValueError, TypeError):
                    result['issues'].append('Invalid refresh token expiration format')
            else:
                result['issues'].append('No refresh token expiration time')
        else:
            result['issues'].append('No valid refresh token in file')
            
        # Overall validity
        result['valid'] = (
            result['has_access_token'] and 
            result['has_refresh_token'] and
            result['access_token_valid'] and 
            result['refresh_token_valid']
        )
        
        return result
        
    except json.JSONDecodeError as e:
        result['issues'].append(f'Invalid JSON: {e}')
        return result
    except Exception as e:
        result['issues'].append(f'Validation error: {e}')
        return result

# ================================================================
# EXISTING HELPER FUNCTIONS (PRESERVED)
# ================================================================

def parse_console_response(text):
    """Parse console response and extract relevant information"""
    if not text:
        return {}
    
    parsed = {
        'text': text,
        'type': 'response',
        'timestamp': datetime.now().isoformat()
    }
    
    # Extract player information
    if 'Players:' in text:
        try:
            player_line = [line for line in text.split('\n') if 'Players:' in line][0]
            player_count = player_line.split('Players:')[1].strip().split()[0]
            parsed['player_count'] = int(player_count)
        except:
            pass
    
    return parsed

def classify_message(message):
    """Classify console message type"""
    if not message:
        return 'unknown'
    
    msg_lower = message.lower()
    
    if any(word in msg_lower for word in ['joined', 'connected']):
        return 'join'
    elif any(word in msg_lower for word in ['left', 'disconnected']):
        return 'leave'
    elif any(word in msg_lower for word in ['killed', 'died']):
        return 'kill'
    elif any(word in msg_lower for word in ['chat', 'say']):
        return 'chat'
    elif any(word in msg_lower for word in ['admin', 'ban', 'kick']):
        return 'admin'
    else:
        return 'system'

def get_type_icon(message_type):
    """Get icon for message type"""
    icons = {
        'join': '🟢',
        'leave': '🔴',
        'kill': '💀',
        'chat': '💬',
        'admin': '🛡️',
        'system': 'ℹ️',
        'unknown': '❓'
    }
    return icons.get(message_type, '❓')

def format_console_message(message, timestamp=None):
    """Format console message for display"""
    if not message:
        return ''
    
    msg_type = classify_message(message)
    icon = get_type_icon(msg_type)
    
    if timestamp:
        return f"{timestamp} {icon} {message}"
    else:
        return f"{icon} {message}"

def validate_server_id(server_id):
    """Validate server ID format"""
    if not server_id:
        return False, None
    
    try:
        # Remove any test suffix
        clean_id = str(server_id).split('_')[0]
        server_int = int(clean_id)
        if server_int > 0:
            return True, server_int
    except (ValueError, TypeError):
        pass
    
    return False, None

def validate_region(region):
    """Validate region format"""
    if not region:
        return False
    
    valid_regions = ['US', 'EU', 'AS', 'AU']
    return str(region).upper() in valid_regions

def format_command(command):
    """Format command for sending"""
    if not command:
        return ''
    
    command = command.strip()
    if not command.startswith('/'):
        command = f"/{command}"
    
    return command

def create_server_data(server_id, name, region='US', server_type='Standard'):
    """
    ✅ FIXED: Create server data structure with correct signature
    
    Args:
        server_id: Server ID
        name (str): Server name  
        region (str): Server region (default: 'US')
        server_type (str): Server type (default: 'Standard')
        
    Returns:
        dict: Standardized server data structure
    """
    return {
        'serverId': str(server_id),
        'serverName': name,
        'serverRegion': region,
        'serverType': server_type,
        'status': 'unknown',
        'isActive': True,
        'isFavorite': False,
        'addedAt': datetime.now().isoformat()
    }

def get_countdown_announcements(minutes_left):
    """Get countdown announcements for events"""
    announcements = []
    
    if minutes_left in [30, 15, 10, 5, 3, 2, 1]:
        announcements.append(f"Event starts in {minutes_left} minute{'s' if minutes_left != 1 else ''}!")
    
    return announcements

def escape_html(text):
    """Escape HTML characters"""
    if not text:
        return ''
    
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;'))

def safe_int(value, default=0):
    """Safely convert to integer"""
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def get_status_class(status):
    """Get CSS class for status"""
    status_classes = {
        'online': 'bg-green-800 text-green-200',
        'offline': 'bg-red-800 text-red-200',
        'unknown': 'bg-gray-700 text-gray-300'
    }
    return status_classes.get(status, 'bg-gray-700 text-gray-300')

def get_status_text(status):
    """Get display text for status"""
    status_text = {
        'online': '🟢 Online',
        'offline': '🔴 Offline',
        'unknown': '⚪ Unknown'
    }
    return status_text.get(status, '⚪ Unknown')

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if not timestamp:
        return ''
    
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        return dt.strftime('%H:%M:%S')
    except:
        return str(timestamp)

def is_valid_steam_id(steam_id):
    """Validate Steam ID format"""
    if not steam_id:
        return False
    
    # Steam ID should be 17 digits
    return str(steam_id).isdigit() and len(str(steam_id)) == 17

def sanitize_filename(filename):
    """Sanitize filename for safe filesystem use"""
    if not filename:
        return 'unknown'
    
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    return filename.strip()
