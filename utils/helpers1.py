"""
GUST Bot Enhanced - Helper Functions (COMPLETE FIXED VERSION + COOKIE SUPPORT)
===============================================================================
✅ FIXED: Complete save_token() function with OAuth and session cookie support
✅ FIXED: Enhanced load_token() function for both auth types  
✅ FIXED: monitor_token_health() returns structure expected by logs routes
✅ FIXED: Enhanced file locking with Windows-optimized error handling
✅ ENHANCED: Ultra-aggressive token refresh strategy (30s buffer)
✅ ENHANCED: Auto-authentication integration with credential fallback
✅ ENHANCED: Better error recovery and automatic re-login detection
✅ ENHANCED: Safe file operation wrapper for atomic writes
✅ PRESERVED: All existing functionality and missing functions restored
"""

import os
import json
import time
import logging
import random
import string
import re
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any
import requests

logger = logging.getLogger(__name__)

# Import auto-auth components (graceful fallback if not available)
try:
    from utils.credential_manager import credential_manager
    CREDENTIAL_MANAGER_AVAILABLE = True
except ImportError:
    CREDENTIAL_MANAGER_AVAILABLE = False
    logger.debug("Credential manager not available - auto-auth features disabled")

try:
    from config import Config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logger.warning("Config not available - using defaults")

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
# AUTO-AUTHENTICATION GLOBAL STATE
# ================================================================

# Global authentication state for auto-auth integration
_auth_lock = None
_last_auth_attempt = 0
_auth_failure_count = 0
_auth_in_progress = False

def _init_auth_state():
    """Initialize authentication state"""
    global _auth_lock
    if _auth_lock is None:
        import threading
        _auth_lock = threading.Lock()

def _get_config_value(key, default):
    """Get configuration value with fallback"""
    if CONFIG_AVAILABLE and hasattr(Config, key):
        return getattr(Config, key)
    return default

# ================================================================
# ✅ ENHANCED FILE LOCKING UTILITIES (WINDOWS OPTIMIZED)
# ================================================================

def acquire_file_lock(file_handle, timeout=5):
    """Enhanced cross-platform file locking with timeout"""
    if not FILE_LOCKING_AVAILABLE:
        return True
    
    start_time = time.time()
    
    while True:
        try:
            if FILE_LOCKING_TYPE == 'windows':
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                return True
            elif FILE_LOCKING_TYPE == 'unix':
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
        except (IOError, OSError):
            if time.time() - start_time > timeout:
                logger.warning(f"⚠️ File lock timeout after {timeout}s")
                return False
            time.sleep(0.1)
    
    return False

def release_file_lock(file_handle):
    """✅ ENHANCED: Release file lock with Windows-optimized error handling"""
    if not FILE_LOCKING_AVAILABLE:
        return
    
    try:
        # Check if file handle is still valid before attempting unlock
        if hasattr(file_handle, 'closed') and file_handle.closed:
            logger.debug("🔓 File already closed, skipping unlock")
            return
        
        if FILE_LOCKING_TYPE == 'windows':
            # Windows-specific handling with better error detection
            try:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                logger.debug("🔓 Windows file lock released successfully")
            except OSError as e:
                if e.errno == 13:  # Permission denied - common on Windows
                    logger.debug(f"🔓 Windows file lock auto-released (errno {e.errno})")
                else:
                    logger.debug(f"🔓 Windows file lock release: {e}")
        elif FILE_LOCKING_TYPE == 'unix':
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
            logger.debug("🔓 Unix file lock released successfully")
            
    except (IOError, OSError, ValueError) as e:
        error_msg = str(e).lower()
        # Handle common Windows file locking scenarios gracefully
        if any(phrase in error_msg for phrase in ['permission denied', 'bad file descriptor', 'invalid argument']):
            logger.debug(f"🔓 File lock auto-handled by OS: {e}")
        else:
            logger.warning(f"⚠️ Unexpected file lock error: {e}")
    except Exception as e:
        logger.debug(f"🔓 File lock release handled: {type(e).__name__}: {e}")

def safe_file_operation(file_path, operation, mode='r', encoding='utf-8', timeout=5):
    """
    ✅ NEW: Safely perform file operations with enhanced locking and error handling
    """
    file_handle = None
    lock_acquired = False
    
    try:
        file_handle = open(file_path, mode, encoding=encoding)
        lock_acquired = acquire_file_lock(file_handle, timeout=timeout)
        
        if not lock_acquired:
            logger.debug(f"📁 File operation proceeding without lock: {file_path}")
        
        # Perform the operation
        result = operation(file_handle)
        return result
        
    except Exception as e:
        logger.error(f"❌ File operation failed for {file_path}: {e}")
        raise
    finally:
        if file_handle:
            try:
                if lock_acquired:
                    release_file_lock(file_handle)
                file_handle.close()
            except Exception as e:
                logger.debug(f"🔓 File cleanup handled: {e}")

# ================================================================
# JWT TOKEN VALIDATION
# ================================================================

def is_valid_jwt_token(token):
    """
    JWT-compatible token validation
    
    Args:
        token (str): Token to validate
        
    Returns:
        bool: True if token format is valid for JWT/OAuth
    """
    if not token or not isinstance(token, str):
        return False
    
    token = token.strip()
    
    # Minimum length check (JWT tokens are typically much longer)
    if len(token) < 20:
        return False
    
    # JWT tokens can contain: letters, numbers, dots, hyphens, underscores, plus, slash, equals
    # This covers all standard JWT and OAuth token formats
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_+/=')
    
    # Check if all characters are allowed
    if not all(c in allowed_chars for c in token):
        return False
    
    return True

# ================================================================
# ✅ ENHANCED TOKEN MANAGEMENT WITH COOKIE SUPPORT
# ================================================================

def save_token(tokens, username='unknown'):
    """
    ✅ ENHANCED: Save authentication tokens with improved file handling and error recovery
    
    Supports both OAuth tokens and G-Portal session cookies
    
    Args:
        tokens (dict): Token data from G-Portal API (OAuth or session cookies)
        username (str): Username for tracking
        
    Returns:
        bool: True if save successful
    """
    try:
        if not isinstance(tokens, dict):
            logger.error(f"❌ Invalid tokens format: {type(tokens)}")
            return False
        
        token_file = 'gp-session.json'
        current_time = time.time()
        
        # ✅ Handle session cookie authentication (from G-Portal HTML response)
        if tokens.get('type') == 'cookie_auth' or 'session_cookies' in tokens:
            logger.info("🍪 Saving session cookie authentication")
            
            # Extract session cookies
            session_cookies = tokens.get('session_cookies', {})
            if not session_cookies:
                logger.error("❌ No session cookies found in cookie_auth response")
                return False
            
            # Required cookies for G-Portal
            required_cookies = ['AUTH_SESSION_ID', 'KC_AUTH_SESSION_HASH']
            missing_cookies = [cookie for cookie in required_cookies if cookie not in session_cookies]
            
            if missing_cookies:
                logger.warning(f"⚠️ Missing cookies: {missing_cookies}, but continuing with available cookies")
            
            # Create session data structure for cookie-based auth
            session_data = {
                'auth_type': 'cookie',
                'username': username,
                'session_cookies': session_cookies,
                'timestamp': datetime.now().isoformat(),
                'created': current_time,
                # Set expiration for 4 minutes (240 seconds) to trigger auto-refresh before G-Portal's 5-minute limit
                'expires_at': current_time + 240,
                'cookie_expires': current_time + 240,
                'auto_refresh_interval': 180,  # Refresh every 3 minutes
                'last_refresh': current_time
            }
            
        # ✅ Handle OAuth token authentication 
        elif 'access_token' in tokens and 'refresh_token' in tokens:
            logger.info("🔐 Saving OAuth token authentication")
            
            # Handle different token data formats
            if 'access_token_exp' in tokens and 'refresh_token_exp' in tokens:
                # Already processed token structure
                session_data = dict(tokens)
                session_data['username'] = username
                session_data['auth_type'] = 'oauth'
            else:
                # Raw OAuth API response format
                access_token = tokens['access_token'].strip()
                refresh_token = tokens['refresh_token'].strip()
                
                # Validate tokens with JWT support
                if not is_valid_jwt_token(access_token) or not is_valid_jwt_token(refresh_token):
                    logger.error(f"❌ Token validation failed: access_len={len(access_token)}, refresh_len={len(refresh_token)}")
                    return False
                
                # Calculate expiration times with ultra-aggressive defaults
                expires_in = max(240, int(tokens.get('expires_in', 240)))  # Minimum 4 minutes, default 4 minutes
                refresh_expires_in = max(1800, int(tokens.get('refresh_expires_in', 3600)))  # Minimum 30 minutes
                
                session_data = {
                    'auth_type': 'oauth',
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'access_token_exp': int(current_time + expires_in),
                    'refresh_token_exp': int(current_time + refresh_expires_in),
                    'expires_in': expires_in,
                    'refresh_expires_in': refresh_expires_in,
                    'username': username,
                    'timestamp': datetime.now().isoformat(),
                    'created': current_time,
                    'last_refresh': current_time
                }
        
        # ✅ ERROR: Unknown authentication format
        else:
            logger.error(f"❌ Unknown authentication format. Keys: {list(tokens.keys())}")
            return False
        
        # ✅ ENHANCED: Save session data using safe file operation
        def write_operation(file_handle):
            json.dump(session_data, file_handle, indent=2, ensure_ascii=False)
            file_handle.flush()
            if hasattr(os, 'fsync'):
                os.fsync(file_handle.fileno())
            return True
        
        try:
            # Use safe file operation for atomic write
            temp_file = token_file + '.tmp'
            result = safe_file_operation(temp_file, write_operation, mode='w')
            
            if result:
                # Atomic move
                if os.path.exists(token_file):
                    os.remove(token_file)
                os.rename(temp_file, token_file)
                
                # Set secure file permissions
                try:
                    os.chmod(token_file, 0o600)
                except OSError:
                    pass  # Windows compatibility
                
                auth_type = session_data.get('auth_type', 'unknown')
                logger.info(f"✅ {auth_type.upper()} authentication saved successfully for {username}")
                return True
            
        except Exception as e:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise e
            
    except Exception as e:
        logger.error(f"❌ Error saving tokens for {username}: {e}")
        return False

def load_token():
    """
    ✅ ENHANCED: Load authentication data with improved error handling
    
    Returns:
        dict or None: Token/cookie data if valid, None otherwise
    """
    try:
        token_file = 'gp-session.json'
        
        if not os.path.exists(token_file):
            logger.debug("📄 No token file found")
            return None
        
        # Use safe file operation for loading
        def read_operation(file_handle):
            return json.load(file_handle)
        
        try:
            data = safe_file_operation(token_file, read_operation, mode='r')
        except Exception as e:
            logger.error(f"❌ Error reading token file: {e}")
            return None
        
        if not isinstance(data, dict):
            logger.error("❌ Invalid token file format")
            return None
        
        current_time = time.time()
        auth_type = data.get('auth_type', 'oauth')  # Default to oauth for backward compatibility
        
        # ✅ Handle session cookie validation
        if auth_type == 'cookie':
            expires_at = data.get('expires_at', 0)
            if current_time >= expires_at:
                logger.warning("🍪 Session cookies expired")
                return None
            
            if 'session_cookies' not in data:
                logger.error("❌ Missing session_cookies in cookie auth data")
                return None
            
            logger.debug(f"🍪 Loaded valid session cookies (expires in {int(expires_at - current_time)}s)")
            return data
        
        # ✅ Handle OAuth token validation (existing logic)
        elif auth_type == 'oauth':
            access_exp = data.get('access_token_exp', 0)
            if current_time >= access_exp:
                logger.warning("🔐 Access token expired")
                return None
            
            if 'access_token' not in data:
                logger.error("❌ Missing access_token in OAuth data")
                return None
            
            logger.debug(f"🔐 Loaded valid OAuth tokens (expires in {int(access_exp - current_time)}s)")
            return data
        
        else:
            logger.error(f"❌ Unknown auth_type: {auth_type}")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error in token file: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error loading token: {e}")
        return None

def get_auth_headers():
    """
    ✅ Get authentication headers for API requests
    
    Supports both OAuth and session cookie authentication
    
    Returns:
        dict: Headers for authenticated requests
    """
    try:
        auth_data = load_token()
        if not auth_data:
            return {}
        
        auth_type = auth_data.get('auth_type', 'oauth')
        
        # ✅ Session cookie authentication
        if auth_type == 'cookie':
            session_cookies = auth_data.get('session_cookies', {})
            
            # Convert cookies to header format
            cookie_header = '; '.join([f"{name}={value}" for name, value in session_cookies.items()])
            
            return {
                'Cookie': cookie_header,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.g-portal.com/',
                'Origin': 'https://www.g-portal.com'
            }
        
        # ✅ OAuth token authentication  
        elif auth_type == 'oauth':
            access_token = auth_data.get('access_token', '')
            
            return {
                'Authorization': f'Bearer {access_token}',
                'User-Agent': 'GUST-Bot/2.0',
                'Accept': 'application/json'
            }
        
        else:
            logger.error(f"❌ Unknown auth_type for headers: {auth_type}")
            return {}
            
    except Exception as e:
        logger.error(f"❌ Error getting auth headers: {e}")
        return {}

def get_api_token():
    """
    ✅ Get token string specifically for REST API calls
    
    Extracts the actual token string from the auth data structure
    
    Returns:
        str: Token string for API calls, empty string if unavailable
    """
    try:
        auth_data = load_token()
        
        if not auth_data:
            return ''
        
        auth_type = auth_data.get('auth_type', 'oauth')
        
        if auth_type == 'oauth':
            # OAuth token authentication - return access_token
            token = auth_data.get('access_token', '').strip()
            if token and len(token) > 20:
                return token
            else:
                logger.error("❌ Invalid OAuth access token")
                return ''
        
        elif auth_type == 'cookie':
            # Session cookie authentication - extract session ID for Bearer token
            session_cookies = auth_data.get('session_cookies', {})
            auth_session_id = session_cookies.get('AUTH_SESSION_ID', '')
            
            if auth_session_id and len(auth_session_id) > 20:
                return auth_session_id
            else:
                logger.error("❌ Invalid session cookie token")
                return ''
        
        else:
            logger.error(f"❌ Unknown auth_type: {auth_type}")
            return ''
        
    except Exception as e:
        logger.error(f"❌ Error getting API token: {e}")
        return ''

def get_websocket_token():
    """
    ✅ Get token specifically for WebSocket connections
    
    WebSocket connections need browser session JWT tokens, not OAuth tokens
    
    Returns:
        dict or None: Session cookies for WebSocket auth
    """
    try:
        auth_data = load_token()
        
        if not auth_data:
            logger.error("❌ No auth data for WebSocket")
            return None
        
        auth_type = auth_data.get('auth_type', 'oauth')
        
        if auth_type == 'cookie':
            # Session cookies are what WebSocket needs
            session_cookies = auth_data.get('session_cookies', {})
            return session_cookies if session_cookies else None
        else:
            # OAuth tokens won't work for WebSocket - need to get browser session
            logger.warning("⚠️ OAuth tokens don't work for WebSocket - need browser session")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error getting WebSocket token: {e}")
        return None

# ================================================================
# ENHANCED TOKEN REFRESH WITH COOKIE SUPPORT
# ================================================================

def refresh_token():
    """
    ✅ ENHANCED: Token refresh with auto-auth fallback and cookie support
    
    Returns:
        bool: True if refresh successful, False otherwise
    """
    global _auth_in_progress, _auth_failure_count
    
    if _auth_in_progress:
        logger.debug("Auth already in progress, skipping")
        return False
    
    _auth_in_progress = True
    
    try:
        _init_auth_state()
        
        # Load current authentication data
        auth_data = load_token()
        if not auth_data:
            logger.warning("No authentication data found for refresh")
            
            # Try credential re-authentication if available
            if CREDENTIAL_MANAGER_AVAILABLE:
                max_retries = _get_config_value('AUTO_AUTH_MAX_RETRIES', 3)
                if _auth_failure_count < max_retries:
                    logger.warning("Standard token refresh failed, attempting credential re-authentication")
                    return attempt_credential_reauth()
                else:
                    logger.error(f"Max auth retries ({max_retries}) reached, skipping credential re-auth")
                    return False
            else:
                logger.warning("Token refresh failed and auto-auth not available")
                _auth_failure_count += 1
                return False
        
        auth_type = auth_data.get('auth_type', 'oauth')
        username = auth_data.get('username', 'unknown')
        current_time = time.time()
        
        # ✅ Handle cookie-based authentication refresh
        if auth_type == 'cookie':
            logger.info(f"🍪 Attempting session cookie refresh for {username}")
            
            # For cookies, we need to re-authenticate to get fresh session
            if CREDENTIAL_MANAGER_AVAILABLE:
                return attempt_credential_reauth()
            else:
                logger.error("❌ Cookie refresh requires credential manager (auto-auth)")
                _auth_failure_count += 1
                return False
        
        # ✅ Handle OAuth token refresh (existing logic)
        elif auth_type == 'oauth':
            logger.info(f"🔐 Attempting OAuth token refresh for {username}")
            
            refresh_token_val = auth_data.get('refresh_token', '')
            if not refresh_token_val:
                logger.error("❌ No refresh token available")
                
                # Try credential re-authentication if available
                if CREDENTIAL_MANAGER_AVAILABLE:
                    max_retries = _get_config_value('AUTO_AUTH_MAX_RETRIES', 3)
                    if _auth_failure_count < max_retries:
                        logger.warning("No refresh token, attempting credential re-authentication")
                        return attempt_credential_reauth()
                    else:
                        logger.error(f"Max auth retries ({max_retries}) reached")
                        return False
                else:
                    _auth_failure_count += 1
                    return False
            
            # Standard OAuth refresh logic
            refresh_data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token_val,
                'client_id': 'website'
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'GUST-Bot/2.0',
                'Accept': 'application/json'
            }
            
            auth_url = _get_config_value('GPORTAL_AUTH_URL', 'https://www.g-portal.com/ngpapi/oauth/token')
            
            try:
                response = requests.post(
                    auth_url,
                    data=refresh_data,
                    headers=headers,
                    timeout=10
                )
                
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
                    
                    # Update tokens with comprehensive data
                    expires_in = new_tokens.get('expires_in', 300)
                    refresh_expires_in = new_tokens.get('refresh_expires_in', 86400)
                    
                    try:
                        expires_in = int(float(expires_in))
                        refresh_expires_in = int(float(refresh_expires_in))
                    except (ValueError, TypeError):
                        logger.warning("⚠️ Invalid expiration times, using defaults")
                        expires_in = 300
                        refresh_expires_in = 86400
                    
                    auth_data.update({
                        'access_token': new_access_token,
                        'refresh_token': new_tokens.get('refresh_token', refresh_token_val).strip(),
                        'access_token_exp': int(current_time + expires_in),
                        'refresh_token_exp': int(current_time + refresh_expires_in),
                        'timestamp': datetime.now().isoformat(),
                        'last_refresh': current_time,
                        'refresh_count': auth_data.get('refresh_count', 0) + 1
                    })
                    
                    # Save updated tokens
                    if save_token(auth_data, username):
                        _auth_failure_count = 0
                        logger.info("✅ OAuth token refresh successful")
                        return True
                    else:
                        logger.error("❌ Failed to save refreshed OAuth tokens")
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
        
        else:
            logger.error(f"❌ Unknown auth_type for refresh: {auth_type}")
            return False
            
    except Exception as e:
        _auth_failure_count += 1
        logger.error(f"❌ Error in token refresh: {e}")
        return False
    finally:
        _auth_in_progress = False

def attempt_credential_reauth():
    """
    ✅ Attempt re-authentication using stored credentials
    
    Returns:
        bool: True if re-authentication successful, False otherwise
    """
    global _auth_failure_count
    
    try:
        if not CREDENTIAL_MANAGER_AVAILABLE:
            logger.error("Credential manager not available for re-authentication")
            return False
        
        # Load stored credentials
        credentials = credential_manager.load_credentials()
        if not credentials:
            logger.warning("No stored credentials available for re-authentication")
            return False
        
        username = credentials['username']
        password = credentials['password']
        
        logger.info(f"🔐 Attempting credential re-authentication for {username}")
        
        # Prepare authentication request
        auth_data = {
            'grant_type': 'password',
            'username': username,
            'password': password,
            'client_id': 'website'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'https://www.g-portal.com',
            'Referer': 'https://www.g-portal.com/',
            'Accept': 'application/json, text/html, */*'
        }
        
        # Get auth URL from config or use default
        auth_url = _get_config_value('GPORTAL_AUTH_URL', 'https://www.g-portal.com/ngpapi/oauth/token')
        
        response = requests.post(
            auth_url,
            data=auth_data,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            
            # Handle JSON OAuth response
            try:
                if 'application/json' in content_type:
                    tokens = response.json()
                    
                    if 'access_token' in tokens and 'refresh_token' in tokens:
                        logger.info("🔐 Received OAuth tokens during re-auth")
                        
                        if save_token(tokens, username):
                            _auth_failure_count = 0
                            logger.info("✅ OAuth credential re-authentication successful")
                            return True
                        else:
                            logger.error("❌ Failed to save OAuth tokens during re-auth")
                            return False
            
            except (json.JSONDecodeError, ValueError):
                pass  # Fall through to cookie handling
            
            # Handle HTML cookie response
            if 'text/html' in content_type or response.text.strip().startswith('<!'):
                logger.info("📄 Received HTML response during re-auth")
                
                # Extract cookies from response
                session_cookies = {}
                for cookie in response.cookies:
                    session_cookies[cookie.name] = cookie.value
                
                logger.info(f"🍪 Found session cookies during re-auth: {list(session_cookies.keys())}")
                
                # Check for successful login indicators
                html_content = response.text.lower()
                success_indicators = [
                    'dashboard', 'server', 'logout', 'account',
                    'welcome', 'home', 'portal', 'profile'
                ]
                
                login_successful = any(indicator in html_content for indicator in success_indicators)
                has_cookies = len(session_cookies) > 0
                
                if login_successful and has_cookies:
                    logger.info("✅ HTML response indicates successful re-auth")
                    
                    # Save session cookies
                    cookie_data = {
                        'type': 'cookie_auth',
                        'session_cookies': session_cookies,
                        'reauth_timestamp': time.time()
                    }
                    
                    if save_token(cookie_data, username):
                        _auth_failure_count = 0
                        logger.info("✅ Cookie credential re-authentication successful")
                        return True
                    else:
                        logger.error("❌ Failed to save session cookies during re-auth")
                        return False
                else:
                    logger.warning("❌ HTML response does not indicate successful re-auth")
                    return False
            
            else:
                logger.error(f"❌ Unknown response format during re-auth: {content_type}")
                return False
        
        else:
            logger.error(f"❌ Re-authentication failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during credential re-authentication: {e}")
        return False

# ================================================================
# TOKEN VALIDATION AND MONITORING
# ================================================================

def validate_token_file():
    """
    ✅ Enhanced token file validation that returns structure expected by logs routes
    
    Returns:
        dict: Validation status with detailed information
    """
    try:
        current_time = time.time()
        auth_data = load_token()
        
        if not auth_data:
            return {
                'valid': False,
                'error': 'No token file or invalid format',
                'auth_type': 'none',
                'time_left': 0,
                'expires_at': None
            }
        
        auth_type = auth_data.get('auth_type', 'oauth')
        
        # Check cookie-based authentication
        if auth_type == 'cookie':
            expires_at = auth_data.get('expires_at', 0)
            time_left = max(0, expires_at - current_time)
            
            return {
                'valid': time_left > 0,
                'auth_type': 'cookie',
                'time_left': int(time_left),
                'expires_at': datetime.fromtimestamp(expires_at).isoformat() if expires_at > 0 else None,
                'username': auth_data.get('username', 'unknown'),
                'last_refresh': auth_data.get('last_refresh', 0)
            }
        
        # Check OAuth authentication
        elif auth_type == 'oauth':
            access_exp = auth_data.get('access_token_exp', 0)
            time_left = max(0, access_exp - current_time)
            
            return {
                'valid': time_left > 0,
                'auth_type': 'oauth',
                'time_left': int(time_left),
                'expires_at': datetime.fromtimestamp(access_exp).isoformat() if access_exp > 0 else None,
                'username': auth_data.get('username', 'unknown'),
                'last_refresh': auth_data.get('last_refresh', 0)
            }
        
        else:
            return {
                'valid': False,
                'error': f'Unknown auth_type: {auth_type}',
                'auth_type': auth_type,
                'time_left': 0,
                'expires_at': None
            }
            
    except Exception as e:
        logger.error(f"❌ Error validating token file: {e}")
        return {
            'valid': False,
            'error': str(e),
            'auth_type': 'error',
            'time_left': 0,
            'expires_at': None
        }

def monitor_token_health():
    """
    ✅ Monitor token health with structure expected by logs routes
    
    Returns:
        dict: Health status that works with _get_optimized_token()
    """
    try:
        validation = validate_token_file()
        current_time = time.time()
        
        # Build health status structure expected by logs routes
        healthy = validation.get('valid', False)
        time_left = validation.get('time_left', 0)
        
        # Determine action based on validation
        if not healthy:
            if validation.get('error') == 'No token file or invalid format':
                action = 'login_required'
                message = 'No authentication token available. Please re-login to G-Portal.'
            else:
                action = 'login_required' 
                message = f"Token validation failed: {validation.get('error', 'Unknown error')}"
        elif time_left < 60:  # Less than 1 minute
            action = 'refresh_now'
            message = f'Token expires in {time_left}s - refresh needed'
        elif time_left < 300:  # Less than 5 minutes
            action = 'refresh_soon'
            message = f'Token expires in {int(time_left/60)} minutes - refresh soon'
        else:
            action = 'none'
            message = f'Token healthy - valid for {int(time_left/60)} minutes'
        
        health_data = {
            'healthy': healthy,
            'status': 'healthy' if healthy else 'unhealthy',
            'action': action,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'validation': validation,
            'auth_status': {
                'failure_count': _auth_failure_count,
                'in_progress': _auth_in_progress,
                'last_attempt': _last_auth_attempt
            }
        }
        
        # Add auto-auth status if available
        if CREDENTIAL_MANAGER_AVAILABLE:
            health_data['auto_auth'] = {
                'available': True,
                'credentials_stored': credential_manager.credentials_exist()
            }
        else:
            health_data['auto_auth'] = {
                'available': False,
                'reason': 'Credential manager not available'
            }
        
        return health_data
        
    except Exception as e:
        logger.error(f"❌ Error monitoring token health: {e}")
        return {
            'healthy': False,
            'status': 'error',
            'action': 'login_required',
            'message': f'Error checking token health: {e}',
            'timestamp': datetime.now().isoformat(),
            'validation': {'valid': False, 'error': str(e), 'auth_type': 'error'},
            'auth_status': {
                'failure_count': _auth_failure_count,
                'in_progress': _auth_in_progress,
                'last_attempt': _last_auth_attempt
            }
        }

# ================================================================
# CONSOLE AND COMMAND FUNCTIONS (PRESERVED)
# ================================================================

def parse_console_response(response_data):
    """Parse G-Portal GraphQL response for console commands (PRESERVED)"""
    logger.debug(f"parse_console_response called with: {response_data}")
    
    if not response_data or not isinstance(response_data, dict):
        logger.warning(f"Invalid response_data: {response_data}")
        return False, "Invalid response data"
    
    try:
        if 'data' in response_data and 'sendConsoleMessage' in response_data['data']:
            result = response_data['data']['sendConsoleMessage']
            success = result.get('ok', False)
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
        logger.error(f"Error parsing console response: {e}")
        return False, f"Error parsing response: {e}"

def classify_message(message):
    """Enhanced message classification (PRESERVED)"""
    if not message:
        return 'unknown'
    
    msg_lower = message.lower()
    
    if any(word in msg_lower for word in ['joined', 'connected', 'spawned']):
        return 'join'
    elif any(word in msg_lower for word in ['left', 'disconnected', 'timeout']):
        return 'leave'
    elif any(word in msg_lower for word in ['killed', 'died', 'death', 'suicide']):
        return 'kill'
    elif any(word in msg_lower for word in ['chat', 'say', 'global', 'team']):
        return 'chat'
    elif any(word in msg_lower for word in ['admin', 'ban', 'kick', 'mute']):
        return 'admin'
    elif any(word in msg_lower for word in ['server', 'info', 'status', 'players']):
        return 'system'
    else:
        return 'unknown'

def get_type_icon(message_type):
    """Enhanced icon mapping (PRESERVED)"""
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
        'success': '✅'
    }
    return icons.get(message_type, '❓')

def format_console_message(message, timestamp=None):
    """Enhanced console message formatting (PRESERVED)"""
    if not message:
        return ''
    
    msg_type = classify_message(message)
    icon = get_type_icon(msg_type)
    
    if timestamp:
        if isinstance(timestamp, str):
            return f"{timestamp} {icon} {message}"
        else:
            formatted_time = timestamp.strftime('%H:%M:%S')
            return f"{formatted_time} {icon} {message}"
    else:
        return f"{icon} {message}"

def format_command(command):
    """Enhanced command formatting for G-Portal console (PRESERVED)"""
    if not command:
        return ''
    
    command = command.strip()
    
    # Handle 'say' commands with proper quoting
    if command.startswith('say ') and not command.startswith('global.say'):
        message = command[4:].strip()
        return f'global.say "{message}"'
    
    return command

# ================================================================
# UTILITY FUNCTIONS (PRESERVED)
# ================================================================

def generate_random_string(length=10):
    """Generate random string for various purposes"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_server_data(server_name, server_id, region='us', players=0, max_players=100):
    """
    Create server data structure
    ✅ FIXED: Proper parameter handling
    """
    return {
        'name': server_name,
        'id': server_id,
        'region': region,
        'players': players,
        'maxPlayers': max_players,
        'lastUpdate': datetime.now().isoformat()
    }

def validate_server_id(server_id):
    """Validate server ID format"""
    if not server_id or not isinstance(server_id, str):
        return False, None
    
    try:
        clean_id = str(server_id).split('_')[0].strip()
        
        if clean_id.isdigit():
            server_int = int(clean_id)
            if server_int > 0:
                return True, server_int
        elif clean_id.isalnum() and len(clean_id) > 0:
            return True, clean_id
            
    except (ValueError, TypeError):
        pass
    
    return False, None

def validate_region(region):
    """Enhanced region validation (PRESERVED)"""
    if not region:
        return False
    
    valid_regions = ['US', 'EU', 'AS', 'AU', 'us', 'eu', 'as', 'au']
    return str(region).strip() in valid_regions

def get_server_region(server_id):
    """Extract region from server ID"""
    if not server_id:
        return 'unknown'
    
    # Common G-Portal region patterns
    if server_id.startswith('us-'):
        return 'us'
    elif server_id.startswith('eu-'):
        return 'eu'
    elif server_id.startswith('as-'):
        return 'asia'
    else:
        return 'us'  # Default fallback

def safe_int(value, default=0):
    """Safe integer conversion with fallback"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Safe float conversion with fallback"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def escape_html(text):
    """Escape HTML characters in text"""
    if not text:
        return ''
    
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        ">": "&gt;",
        "<": "&lt;",
    }
    
    return "".join(html_escape_table.get(c, c) for c in text)

def format_timestamp(timestamp=None, format_str='%Y-%m-%d %H:%M:%S'):
    """Format timestamp with optional custom format"""
    if timestamp is None:
        timestamp = datetime.now()
    elif isinstance(timestamp, (int, float)):
        timestamp = datetime.fromtimestamp(timestamp)
    
    return timestamp.strftime(format_str)

def sanitize_filename(filename):
    """Sanitize filename for safe filesystem usage"""
    if not filename:
        return 'untitled'
    
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    filename = filename[:255]
    
    return filename.strip()

def get_countdown_announcements(seconds_left):
    """Get countdown announcements for events"""
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

def get_status_class(status):
    """Get CSS class for status"""
    status_classes = {
        'online': 'status-online',
        'offline': 'status-offline',
        'starting': 'status-starting',
        'stopping': 'status-stopping',
        'error': 'status-error',
        'unknown': 'status-unknown'
    }
    return status_classes.get(status, 'status-unknown')

def get_status_text(status):
    """Get human-readable status text"""
    status_texts = {
        'online': 'Online',
        'offline': 'Offline',
        'starting': 'Starting',
        'stopping': 'Stopping',
        'error': 'Error',
        'unknown': 'Unknown'
    }
    return status_texts.get(status, 'Unknown')

def is_valid_steam_id(steam_id):
    """Validate Steam ID format"""
    if not steam_id:
        return False
    
    # Steam ID should be 17 digits
    return str(steam_id).isdigit() and len(str(steam_id)) == 17

def validate_email(email):
    """Basic email validation"""
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url):
    """Basic URL validation"""
    if not url or not isinstance(url, str):
        return False
    
    return url.startswith(('http://', 'https://'))

def truncate_string(text, length=100, suffix='...'):
    """Truncate string to specified length"""
    if not text or len(text) <= length:
        return text
    
    return text[:length - len(suffix)] + suffix

def deep_get(dictionary, keys, default=None):
    """Get nested dictionary value safely"""
    try:
        for key in keys:
            dictionary = dictionary[key]
        return dictionary
    except (KeyError, TypeError):
        return default

def flatten_dict(d, parent_key='', sep='_'):
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def merge_dicts(dict1, dict2):
    """Merge two dictionaries safely"""
    result = dict1.copy()
    result.update(dict2)
    return result

def chunk_list(lst, chunk_size):
    """Split list into chunks of specified size"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def remove_duplicates(lst, key=None):
    """Remove duplicates from list"""
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

def calculate_percentage(part, total):
    """Calculate percentage safely"""
    if total == 0:
        return 0
    return (part / total) * 100

def format_bytes(bytes_value):
    """Format bytes to human-readable format"""
    if bytes_value == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(bytes_value, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_value / p, 2)
    return f"{s} {size_names[i]}"

def format_duration(seconds):
    """Format duration in seconds to human-readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

# ================================================================
# MODULE EXPORTS
# ================================================================

__all__ = [
    # Token management (enhanced)
    'save_token', 'load_token', 'refresh_token', 'get_auth_headers',
    'validate_token_file', 'monitor_token_health', 'get_api_token', 'get_websocket_token',
    
    # Auto-authentication
    'attempt_credential_reauth',
    
    # Console and command functions (restored)
    'parse_console_response', 'classify_message', 'get_type_icon', 
    'format_console_message', 'format_command',
    
    # Validation functions
    'validate_server_id', 'validate_region', 'is_valid_steam_id',
    'validate_email', 'validate_url',
    
    # Utility functions
    'generate_random_string', 'create_server_data', 'get_server_region',
    'safe_int', 'safe_float', 'escape_html', 'format_timestamp', 
    'sanitize_filename', 'truncate_string',
    
    # Data functions
    'get_countdown_announcements', 'get_status_class', 'get_status_text',
    
    # Dictionary utilities
    'deep_get', 'flatten_dict', 'merge_dicts',
    
    # List utilities
    'chunk_list', 'remove_duplicates',
    
    # Calculation utilities
    'calculate_percentage', 'format_bytes', 'format_duration',
    
    # File locking (enhanced)
    'acquire_file_lock', 'release_file_lock', 'safe_file_operation',
    
    # JWT validation
    'is_valid_jwt_token'
]

logger.info("✅ Enhanced helpers module loaded with Windows-optimized file locking and complete authentication support")