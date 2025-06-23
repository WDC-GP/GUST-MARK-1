"""
GUST Bot Enhanced - Authentication Helper Functions (MODULAR VERSION - FIXED)
=============================================================================
✅ FIXED: load_token() returns string for backwards compatibility
✅ FIXED: Proper file operations with Windows compatibility
✅ ENHANCED: Complete OAuth and session cookie support
✅ MODULAR: Cleanly separated from main helpers.py
"""

import os
import json
import time
import logging
import threading
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

# Enhanced config loading with multiple fallback paths
CONFIG_AVAILABLE = False
Config = None

try:
    from config import Config
    CONFIG_AVAILABLE = True
    logger.debug("Config imported successfully")
except ImportError:
    try:
        # Try relative import
        from .config import Config
        CONFIG_AVAILABLE = True
        logger.debug("Config imported via relative import")
    except ImportError:
        try:
            # Try absolute import
            import config as Config
            CONFIG_AVAILABLE = True
            logger.debug("Config imported as module")
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
# AUTHENTICATION GLOBAL STATE
# ================================================================

_auth_lock = None
_last_auth_attempt = 0
_auth_failure_count = 0
_auth_in_progress = False

def _init_auth_state():
    """Initialize authentication state"""
    global _auth_lock
    if _auth_lock is None:
        _auth_lock = threading.Lock()

def _get_config_value(key, default):
    """Get configuration value with enhanced fallback"""
    try:
        if CONFIG_AVAILABLE and hasattr(Config, key):
            value = getattr(Config, key)
            if value is not None:
                return value
    except (ImportError, AttributeError):
        pass
    
    # Try environment variables as fallback
    try:
        import os
        env_value = os.environ.get(key)
        if env_value is not None:
            return env_value
    except:
        pass
    
    return default

# ================================================================
# SIMPLE FILE OPERATIONS (NO COMPLEX LOCKING)
# ================================================================

def _safe_json_write(file_path, data):
    """Simple atomic JSON write operation"""
    temp_file = file_path + '.tmp'
    try:
        # Write to temp file first
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        if os.path.exists(file_path):
            os.replace(temp_file, file_path)
        else:
            os.rename(temp_file, file_path)
        
        return True
    except Exception as e:
        logger.error(f"Error writing {file_path}: {e}")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        return False

def _safe_json_read(file_path):
    """Simple JSON read operation"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

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
# CORE TOKEN MANAGEMENT (BACKWARDS COMPATIBLE)
# ================================================================

def load_token_data():
    """
    Load full authentication data structure
    
    Returns:
        dict or None: Complete token/cookie data if valid, None otherwise
    """
    try:
        token_file = 'gp-session.json'
        
        if not os.path.exists(token_file):
            logger.debug("📄 No token file found")
            return None
        
        data = _safe_json_read(token_file)
        if not data or not isinstance(data, dict):
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
            # Handle both old and new token formats
            if 'access_token_exp' in data:
                access_exp = data.get('access_token_exp', 0)
            else:
                # Old format - calculate from created_at and expires_in
                created_at = data.get('created_at', 0)
                expires_in = data.get('expires_in', 3600)
                access_exp = created_at + expires_in
            
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
            
    except Exception as e:
        logger.error(f"❌ Error loading token data: {e}")
        return None

def load_token():
    """
    ✅ BACKWARDS COMPATIBLE: Returns token string like original
    
    This maintains backwards compatibility with existing code that expects
    load_token() to return the actual token string, not a dictionary.
    
    Returns:
        str: Token string for API calls, empty string if unavailable
    """
    try:
        auth_data = load_token_data()
        
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
        logger.error(f"❌ Error loading token: {e}")
        return ''

def save_token(tokens, username='unknown'):
    """
    Save authentication tokens with support for both OAuth and session cookies
    
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
            
            # Create session data structure for cookie-based auth
            session_data = {
                'auth_type': 'cookie',
                'username': username,
                'session_cookies': session_cookies,
                'timestamp': datetime.now().isoformat(),
                'created_at': current_time,
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
                
                # Calculate expiration times with conservative defaults
                expires_in = max(300, int(tokens.get('expires_in', 300)))  # Minimum 5 minutes
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
                    'created_at': current_time,
                    'last_refresh': current_time
                }
        
        # Handle old format tokens (backwards compatibility)
        elif 'access_token' in tokens:
            logger.info("🔐 Saving OAuth token authentication (old format)")
            
            access_token = tokens['access_token'].strip()
            refresh_token = tokens.get('refresh_token', '').strip()
            
            expires_in = int(tokens.get('expires_in', 3600))
            refresh_expires_in = int(tokens.get('refresh_expires_in', 86400))
            
            session_data = {
                'auth_type': 'oauth',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'created_at': current_time,
                'expires_in': expires_in,
                'refresh_expires_in': refresh_expires_in,
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'last_refresh': current_time
            }
        
        # ✅ ERROR: Unknown authentication format
        else:
            logger.error(f"❌ Unknown authentication format. Keys: {list(tokens.keys())}")
            return False
        
        # Save the token data
        if _safe_json_write(token_file, session_data):
            auth_type = session_data.get('auth_type', 'unknown')
            logger.info(f"✅ {auth_type.upper()} authentication saved successfully for {username}")
            return True
        else:
            logger.error(f"❌ Failed to write token file")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error saving tokens for {username}: {e}")
        return False

def get_auth_headers():
    """
    Get authentication headers for API requests
    
    Returns:
        dict: Headers for authenticated requests
    """
    try:
        # ✅ Use backwards compatible load_token() that returns string
        token = load_token()
        if token:
            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        else:
            logger.warning("No valid token available for auth headers")
            return {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"❌ Error getting auth headers: {e}")
        return {'Content-Type': 'application/json'}

def get_api_token():
    """
    Get token string specifically for REST API calls
    
    Returns:
        str: Token string for API calls, empty string if unavailable
    """
    return load_token()

def get_websocket_token():
    """
    Get token specifically for WebSocket connections
    
    Returns:
        dict or None: Session cookies for WebSocket auth
    """
    try:
        auth_data = load_token_data()
        
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
# TOKEN REFRESH
# ================================================================

def refresh_token():
    """
    Enhanced token refresh with auto-auth fallback and cookie support
    
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
        auth_data = load_token_data()
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
        
        # ✅ Handle OAuth token refresh
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
                'client_id': _get_config_value('GPORTAL_CLIENT_ID', 'website')
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'GUST-Bot/2.0',
                'Accept': 'application/json'
            }
            
            auth_url = _get_config_value('GPORTAL_AUTH_URL', 'https://auth.g-portal.com/auth/realms/master/protocol/openid-connect/token')
            
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
                    
                    # Save updated tokens
                    if save_token(new_tokens, username):
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
    Attempt re-authentication using stored credentials
    
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
            'client_id': _get_config_value('GPORTAL_CLIENT_ID', 'website')
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'https://www.g-portal.com',
            'Referer': 'https://www.g-portal.com/',
            'Accept': 'application/json, text/html, */*'
        }
        
        # Get auth URL from config
        auth_url = _get_config_value('GPORTAL_AUTH_URL', 'https://auth.g-portal.com/auth/realms/master/protocol/openid-connect/token')
        
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
    Enhanced token file validation that returns structure expected by logs routes
    
    Returns:
        dict: Validation status with detailed information
    """
    try:
        current_time = time.time()
        auth_data = load_token_data()
        
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
            # Handle both old and new formats
            if 'access_token_exp' in auth_data:
                access_exp = auth_data.get('access_token_exp', 0)
            else:
                # Old format
                created_at = auth_data.get('created_at', 0)
                expires_in = auth_data.get('expires_in', 3600)
                access_exp = created_at + expires_in
            
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
    Monitor token health with structure expected by logs routes
    
    Returns:
        dict: Health status that works with optimization routines
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
# MODULE EXPORTS
# ================================================================

__all__ = [
    # Core token functions (backwards compatible)
    'load_token', 'load_token_data', 'save_token', 'refresh_token',
    
    # Auth headers and token access
    'get_auth_headers', 'get_api_token', 'get_websocket_token',
    
    # Token validation and monitoring
    'validate_token_file', 'monitor_token_health',
    
    # Auto-authentication
    'attempt_credential_reauth',
    
    # JWT validation
    'is_valid_jwt_token'
]

logger.info("✅ Modular authentication helpers loaded successfully with backwards compatibility")