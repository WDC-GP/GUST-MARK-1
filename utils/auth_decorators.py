"""
Authentication decorators for GUST Bot Enhanced (FIXED VERSION)
===============================================================
✅ FIXED: Consistent session checking (logged_in vs authenticated)
✅ FIXED: Standardized demo_mode handling with consistent defaults
✅ FIXED: Better error responses with detailed information
✅ FIXED: Proper integration with token validation
✅ FIXED: Centralized authentication logic to prevent inconsistencies

This module provides standardized authentication decorators to replace
the scattered authentication checks throughout the application.
"""

# Standard library imports
from functools import wraps
import logging

# Handle Flask imports gracefully
try:
    from flask import session, jsonify, request, redirect, url_for
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    session = jsonify = request = redirect = url_for = None

logger = logging.getLogger(__name__)

# ================================================================
# CENTRALIZED AUTHENTICATION LOGIC
# ================================================================

def get_auth_status():
    """
    Get standardized authentication status
    ✅ FIXES: Inconsistent session checking across modules
    ✅ FIXES: Different demo_mode defaults causing random auth failures
    
    Returns:
        dict: Standardized auth status
    """
    if not FLASK_AVAILABLE:
        return {
            'logged_in': False,
            'demo_mode': True,
            'live_mode': False,
            'username': 'No Flask'
        }
    
    # ✅ FIXED: Always check 'logged_in' (not 'authenticated')
    # This matches what routes/auth.py sets during login
    logged_in = session.get('logged_in', False)
    
    # ✅ FIXED: Always default demo_mode to True for safety
    # This prevents accidentally hitting live APIs without proper auth
    demo_mode = session.get('demo_mode', True)
    
    # Get username safely
    username = session.get('username', 'Anonymous')
    
    return {
        'logged_in': logged_in,
        'demo_mode': demo_mode,
        'live_mode': logged_in and not demo_mode,
        'username': username
    }

def is_live_mode():
    """
    Check if user is in live mode with valid authentication
    ✅ FIXES: Multiple different live mode checks throughout codebase
    
    Returns:
        bool: True if live mode and authenticated
    """
    auth = get_auth_status()
    return auth['live_mode']

def is_demo_mode():
    """
    Check if user is in demo mode
    
    Returns:
        bool: True if demo mode
    """
    auth = get_auth_status()
    return auth['demo_mode']

def require_live_mode_for_api():
    """
    Check if live mode is required for API calls
    ✅ FIXES: Inconsistent API authentication checking
    
    Returns:
        tuple: (is_allowed, error_response)
    """
    auth = get_auth_status()
    
    if not auth['logged_in']:
        return False, {
            'success': False,
            'error': 'Authentication required',
            'code': 401,
            'auth_status': auth
        }
    
    if auth['demo_mode']:
        return False, {
            'success': False,
            'error': 'This feature requires G-Portal authentication (live mode)',
            'demo_mode': True,
            'code': 403,
            'auth_status': auth
        }
    
    return True, None

def log_auth_attempt(endpoint, success=True, details=None):
    """
    Log authentication attempts for debugging
    ✅ NEW: Better logging to help diagnose auth issues
    
    Args:
        endpoint (str): Endpoint being accessed
        success (bool): Whether auth was successful
        details (str): Additional details
    """
    auth = get_auth_status()
    
    status = "SUCCESS" if success else "FAILED"
    mode = "DEMO" if auth['demo_mode'] else "LIVE"
    
    log_msg = f"AUTH {status}: {endpoint} - User: {auth['username']} - Mode: {mode}"
    if details:
        log_msg += f" - {details}"
    
    if success:
        logger.info(log_msg)
    else:
        logger.warning(log_msg)

# ================================================================
# FIXED AUTHENTICATION DECORATORS
# ================================================================

def require_auth(f):
    """
    Standard authentication decorator for web routes
    ✅ FIXED: Uses consistent session checking (logged_in not authenticated)
    ✅ FIXED: Better error handling and logging
    
    Redirects to login page if not authenticated
    """
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for authentication decorators")
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = get_auth_status()
        
        if not auth['logged_in']:
            log_auth_attempt(f.__name__, success=False, details="Not logged in")
            
            if request.is_json:
                return jsonify({
                    'error': 'Authentication required',
                    'code': 401,
                    'auth_status': auth
                }), 401
            else:
                return redirect(url_for('auth.login'))
        
        log_auth_attempt(f.__name__, success=True)
        return f(*args, **kwargs)
    
    return decorated_function

def api_auth_required(f):
    """
    API endpoint authentication decorator
    ✅ FIXED: Consistent with main auth system
    ✅ FIXED: Better error responses
    
    Returns JSON error if not authenticated
    """
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for authentication decorators")
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = get_auth_status()
        
        if not auth['logged_in']:
            # Check for API key in headers as fallback
            api_key = request.headers.get('X-API-Key')
            if not api_key or not validate_api_key(api_key):
                log_auth_attempt(f.__name__, success=False, details="No valid auth or API key")
                return jsonify({
                    'error': 'Authentication required',
                    'code': 401,
                    'auth_status': auth
                }), 401
        
        log_auth_attempt(f.__name__, success=True)
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """
    Admin-level authentication decorator
    ✅ FIXED: Uses consistent session checking
    
    Requires authenticated user with admin privileges
    """
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for authentication decorators")
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = get_auth_status()
        
        if not auth['logged_in']:
            log_auth_attempt(f.__name__, success=False, details="Not logged in for admin")
            return jsonify({
                'error': 'Authentication required',
                'code': 401,
                'auth_status': auth
            }), 401
        
        # Check admin level (adjust based on your user model)
        user_level = session.get('user_level', 'user')
        if user_level != 'admin':
            log_auth_attempt(f.__name__, success=False, details=f"Non-admin access attempt by {auth['username']}")
            return jsonify({
                'error': 'Administrator privileges required',
                'code': 403,
                'auth_status': auth
            }), 403
        
        log_auth_attempt(f.__name__, success=True, details="Admin access granted")
        return f(*args, **kwargs)
    
    return decorated_function

def demo_mode_auth(f):
    """
    Demo mode compatible authentication decorator
    ✅ FIXED: Uses centralized auth logic
    
    Allows access in demo mode or with proper authentication
    """
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for authentication decorators")
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = get_auth_status()
        
        # Allow if demo mode is enabled OR if properly authenticated
        if auth['demo_mode'] or auth['logged_in']:
            log_auth_attempt(f.__name__, success=True, details=f"Demo mode access ({auth['demo_mode']})")
            return f(*args, **kwargs)
        
        # Not authenticated and not in demo mode
        log_auth_attempt(f.__name__, success=False, details="No demo mode or auth")
        return jsonify({
            'error': 'Authentication required',
            'code': 401,
            'auth_status': auth
        }), 401
    
    return decorated_function

def require_live_mode(f):
    """
    Decorator to require live mode (not demo) for routes
    ✅ NEW: Centralized live mode requirement
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for authentication decorators")
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_allowed, error_response = require_live_mode_for_api()
        
        if not is_allowed:
            log_auth_attempt(f.__name__, success=False, details="Live mode required")
            return jsonify(error_response), error_response['code']
        
        log_auth_attempt(f.__name__, success=True, details="Live mode access granted")
        return f(*args, **kwargs)
    
    return decorated_function

# ================================================================
# UTILITY FUNCTIONS
# ================================================================

def validate_api_key(key):
    """
    Validate API key for API authentication
    ✅ FIXED: Better validation logic
    
    Replace this with your actual API key validation logic
    """
    if not key:
        return False
    
    # Basic validation - ensure it's a string and has minimum length
    if not isinstance(key, str):
        return False
    
    # Remove whitespace
    key = key.strip()
    
    if len(key) < 32:  # Minimum 32 characters
        return False
    
    # Additional validation could go here:
    # - Check against database
    # - Validate format/checksum
    # - Check expiration
    
    return True

def get_current_user():
    """
    Get current authenticated user information
    ✅ FIXED: Uses centralized auth logic
    
    Returns user data or None if not authenticated
    """
    if not FLASK_AVAILABLE:
        return None
    
    auth = get_auth_status()
    
    if auth['logged_in']:
        return {
            'username': auth['username'],
            'user_level': session.get('user_level', 'user'),
            'authenticated': True,
            'demo_mode': auth['demo_mode'],
            'live_mode': auth['live_mode']
        }
    
    return None

def is_authenticated():
    """
    Simple check if current session is authenticated
    ✅ FIXED: Uses centralized auth logic
    """
    if not FLASK_AVAILABLE:
        return False
    
    auth = get_auth_status()
    return auth['logged_in']

def is_admin():
    """
    Check if current user has admin privileges
    ✅ FIXED: Uses centralized auth logic
    """
    if not is_authenticated():
        return False
    
    user_level = session.get('user_level', 'user')
    return user_level == 'admin'

def get_user_info():
    """
    Get current user information including WebSocket status
    ✅ NEW: Comprehensive user info for frontend
    
    Returns:
        dict: User information including authentication status
    """
    try:
        # Try to import config for WebSocket availability
        from config import WEBSOCKETS_AVAILABLE
    except ImportError:
        WEBSOCKETS_AVAILABLE = False
    
    auth = get_auth_status()
    
    return {
        'username': auth['username'],
        'logged_in': auth['logged_in'],
        'demo_mode': auth['demo_mode'],
        'live_mode': auth['live_mode'],
        'websockets_available': WEBSOCKETS_AVAILABLE,
        'can_use_live_console': WEBSOCKETS_AVAILABLE and auth['live_mode'],
        'user_level': session.get('user_level', 'user') if FLASK_AVAILABLE else 'user'
    }

def check_websocket_requirements():
    """
    Check if all WebSocket requirements are met
    ✅ NEW: WebSocket requirement checking
    
    Returns:
        dict: WebSocket requirements status
    """
    try:
        from config import WEBSOCKETS_AVAILABLE
    except ImportError:
        WEBSOCKETS_AVAILABLE = False
    
    auth = get_auth_status()
    
    return {
        'websockets_package': WEBSOCKETS_AVAILABLE,
        'live_mode_required': auth['live_mode'],
        'ready_for_live_console': WEBSOCKETS_AVAILABLE and auth['live_mode'],
        'auth_status': auth,
        'install_instructions': {
            'package': 'pip install websockets==11.0.3' if not WEBSOCKETS_AVAILABLE else None,
            'authentication': 'Login with G-Portal credentials (not demo mode)' if auth['demo_mode'] else None
        }
    }

# ================================================================
# VALIDATION DECORATORS
# ================================================================

def validate_token_for_endpoint(f):
    """
    Decorator to validate token before API calls that need G-Portal access
    ✅ NEW: Token validation decorator
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = get_auth_status()
        
        # Skip validation for demo mode
        if auth['demo_mode']:
            return f(*args, **kwargs)
        
        # Check if we have a valid token
        try:
            from utils.helpers import validate_token_file
            token_status = validate_token_file()
            
            if not token_status['valid']:
                log_auth_attempt(f.__name__, success=False, details="Invalid token")
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired G-Portal token. Please re-login.',
                    'token_status': token_status,
                    'auth_status': auth
                }), 401
        except ImportError:
            # If we can't import validation, just continue
            pass
        except Exception as e:
            logger.error(f"Error validating token for {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': 'Token validation error. Please re-login.',
                'auth_status': auth
            }), 500
        
        return f(*args, **kwargs)
    
    return decorated_function

# Export decorators for easy importing
__all__ = [
    # Main decorators
    'require_auth', 'api_auth_required', 'require_admin', 'demo_mode_auth', 'require_live_mode',
    
    # Utility functions
    'validate_api_key', 'get_current_user', 'is_authenticated', 'is_admin',
    'get_user_info', 'check_websocket_requirements',
    
    # Authentication status functions
    'get_auth_status', 'is_live_mode', 'is_demo_mode', 'require_live_mode_for_api',
    'log_auth_attempt',
    
    # Validation decorators
    'validate_token_for_endpoint'
]