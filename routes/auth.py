"""
GUST Bot Enhanced - Authentication Routes (COMPLETE FIXED VERSION)
==================================================================
✅ ENHANCED: Token health monitoring endpoints
✅ ENHANCED: Comprehensive token status checking with validation
✅ ENHANCED: Better error handling and detailed logging
✅ ENHANCED: Integration with centralized auth system
✅ ENHANCED: Advanced token refresh with comprehensive status
✅ ENHANCED: System status monitoring with health metrics
✅ FIXED: Added missing require_auth decorator function
"""

# Standard library imports
import logging
import os
import json
import time
from functools import wraps

# Third-party imports
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
import requests

# Utility imports
from utils.helpers import save_token, load_token, refresh_token, validate_token_file, monitor_token_health
from config import Config, WEBSOCKETS_AVAILABLE

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# ================================================================
# ✅ FIXED: MISSING AUTHENTICATION DECORATOR
# ================================================================

def require_auth(f):
    """
    Authentication decorator for routes
    ✅ FIXED: Uses consistent session checking (logged_in not authenticated)
    ✅ FIXED: Proper error handling for both API and web requests
    
    Redirects to login page if not authenticated
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'logged_in' not in session:
            logger.warning(f"❌ Unauthenticated access attempt to {f.__name__} from {request.remote_addr}")
            
            # Return JSON error for API requests
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Authentication required',
                    'code': 401,
                    'path': request.path
                }), 401
            else:
                # Redirect to login for web requests
                return redirect(url_for('auth.login'))
        
        # User is authenticated, proceed
        logger.debug(f"✅ Authenticated access to {f.__name__} by {session.get('username', 'unknown')}")
        return f(*args, **kwargs)
    
    return decorated_function

# ================================================================
# ENHANCED LOGIN AND LOGOUT ROUTES
# ================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login with enhanced session management
    ✅ ENHANCED: Consistent session handling and improved validation
    """
    if request.method == 'POST':
        data = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            logger.warning(f"❌ Login attempt with missing credentials from {request.remote_addr}")
            return jsonify({
                'success': False, 
                'error': 'Please enter username and password'
            })
        
        # Check if this looks like demo credentials
        demo_usernames = ['demo', 'test', 'admin', 'guest']
        is_demo = username.lower() in demo_usernames and len(password) < 10
        
        if is_demo:
            # ✅ ENHANCED: Consistent session setting with additional tracking
            session['logged_in'] = True
            session['username'] = username
            session['demo_mode'] = True
            session['user_level'] = 'admin' if username.lower() == 'admin' else 'user'
            session['login_time'] = time.time()
            session['login_method'] = 'demo'
            
            logger.info(f"🎭 Demo mode login successful: {username} from {request.remote_addr}")
            
            return jsonify({
                'success': True, 
                'demo_mode': True,
                'username': username,
                'user_level': session['user_level'],
                'login_time': session['login_time']
            })
        else:
            # Real G-Portal authentication with enhanced error handling
            logger.info(f"🔐 Attempting G-Portal authentication for {username}")
            
            try:
                # Enhanced G-Portal authentication
                auth_data = {
                    'grant_type': 'password',
                    'username': username,
                    'password': password,
                    'client_id': 'website'
                }
                
                # ✅ ENHANCED: Better headers for G-Portal compatibility
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Origin': 'https://www.g-portal.com',
                    'Referer': 'https://www.g-portal.com/'
                }
                
                response = requests.post(
                    Config.GPORTAL_AUTH_URL,
                    data=auth_data,
                    headers=headers,
                    timeout=15
                )
                
                logger.debug(f"🔍 G-Portal auth response: {response.status_code}")
                
                if response.status_code == 200:
                    tokens = response.json()
                    
                    if 'access_token' in tokens and 'refresh_token' in tokens:
                        # Save tokens
                        if save_token(tokens, username):
                            # ✅ ENHANCED: Complete session setup
                            session['logged_in'] = True
                            session['username'] = username
                            session['demo_mode'] = False
                            session['user_level'] = 'admin'  # G-Portal users get admin access
                            session['login_time'] = time.time()
                            session['login_method'] = 'gportal'
                            
                            logger.info(f"✅ G-Portal authentication successful for {username}")
                            
                            return jsonify({
                                'success': True,
                                'demo_mode': False,
                                'username': username,
                                'user_level': 'admin',
                                'token_expires': tokens.get('expires_in', 300),
                                'login_time': session['login_time']
                            })
                        else:
                            logger.error(f"❌ Failed to save tokens for {username}")
                            return jsonify({
                                'success': False,
                                'error': 'Failed to save authentication tokens'
                            })
                    else:
                        logger.error(f"❌ Invalid token response for {username}")
                        return jsonify({
                            'success': False,
                            'error': 'Invalid response from G-Portal'
                        })
                elif response.status_code == 401:
                    logger.warning(f"❌ Invalid credentials for {username}")
                    return jsonify({
                        'success': False,
                        'error': 'Invalid username or password'
                    })
                elif response.status_code == 429:
                    logger.warning(f"❌ Rate limited authentication attempt for {username}")
                    return jsonify({
                        'success': False,
                        'error': 'Too many login attempts. Please try again later.'
                    })
                else:
                    logger.error(f"❌ G-Portal auth failed for {username}: {response.status_code}")
                    return jsonify({
                        'success': False,
                        'error': f'Authentication service error: {response.status_code}'
                    })
                    
            except requests.exceptions.Timeout:
                logger.error(f"❌ G-Portal auth timeout for {username}")
                return jsonify({
                    'success': False,
                    'error': 'Authentication service timeout. Please try again.'
                })
            except requests.exceptions.ConnectionError:
                logger.error(f"❌ G-Portal auth connection error for {username}")
                return jsonify({
                    'success': False,
                    'error': 'Cannot connect to authentication service'
                })
            except Exception as e:
                logger.error(f"❌ G-Portal auth exception for {username}: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Authentication error occurred'
                })
    
    # GET request - show login page
    return render_template('login.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Handle user logout with enhanced cleanup
    ✅ ENHANCED: Complete session cleanup and logging
    """
    username = session.get('username', 'unknown')
    demo_mode = session.get('demo_mode', False)
    
    # Clear all session data
    session.clear()
    
    logger.info(f"👋 User logged out: {username} ({'demo' if demo_mode else 'gportal'})")
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })

# ================================================================
# ✅ ENHANCED TOKEN HEALTH MONITORING ENDPOINTS
# ================================================================

@auth_bp.route('/api/auth/token/health')
def token_health():
    """
    ✅ NEW: Get comprehensive token health information
    """
    if 'logged_in' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Check if demo mode
        if session.get('demo_mode', False):
            return jsonify({
                'success': True,
                'demo_mode': True,
                'health': {
                    'status': 'demo',
                    'healthy': True,
                    'action': 'none',
                    'message': 'Demo mode - no token validation needed'
                },
                'timestamp': time.time()
            })
        
        # Get comprehensive token health
        health_status = monitor_token_health()
        
        return jsonify({
            'success': True,
            'demo_mode': False,
            'health': health_status,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"❌ Error in token health endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@auth_bp.route('/api/token/status')
def token_status():
    """
    ✅ ENHANCED: Get authentication token status with detailed information
    """
    try:
        # Check authentication
        if 'logged_in' not in session:
            return jsonify({
                'has_token': False,
                'token_valid': False,
                'demo_mode': False,
                'websockets_available': WEBSOCKETS_AVAILABLE,
                'time_left': 0,
                'error': 'Not authenticated'
            })
        
        demo_mode = session.get('demo_mode', True)
        
        if demo_mode:
            return jsonify({
                'has_token': False,
                'token_valid': False,
                'demo_mode': True,
                'websockets_available': WEBSOCKETS_AVAILABLE,
                'time_left': 0,
                'username': session.get('username', 'demo'),
                'login_time': session.get('login_time', time.time())
            })
        
        # Real mode - check actual token
        try:
            token_validation = validate_token_file()
            
            return jsonify({
                'has_token': token_validation['exists'],
                'token_valid': token_validation['access_token_valid'],
                'demo_mode': False,
                'websockets_available': WEBSOCKETS_AVAILABLE,
                'time_left': int(token_validation['time_left']),
                'refresh_time_left': int(token_validation['refresh_time_left']),
                'expires_at': token_validation['expires_at'],
                'refresh_expires_at': token_validation['refresh_expires_at'],
                'username': session.get('username', 'unknown'),
                'login_time': session.get('login_time', time.time()),
                'issues': token_validation['issues']
            })
            
        except Exception as validation_error:
            logger.error(f"❌ Token validation error: {validation_error}")
            return jsonify({
                'has_token': False,
                'token_valid': False,
                'demo_mode': False,
                'websockets_available': WEBSOCKETS_AVAILABLE,
                'time_left': 0,
                'error': 'Token validation failed'
            })
            
    except Exception as e:
        logger.error(f"❌ Error checking token status: {e}")
        return jsonify({
            'has_token': False,
            'token_valid': False,
            'demo_mode': True,
            'websockets_available': WEBSOCKETS_AVAILABLE,
            'time_left': 0,
            'error': str(e)
        })

@auth_bp.route('/api/token/refresh', methods=['POST'])
def refresh_token_endpoint():
    """
    ✅ ENHANCED: Manually refresh G-Portal token with comprehensive status reporting
    """
    try:
        # Check authentication
        if 'logged_in' not in session:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        if session.get('demo_mode', False):
            return jsonify({
                'success': False,
                'error': 'Token refresh not available in demo mode'
            }), 403
        
        username = session.get('username', 'unknown')
        
        # Check current token status before refresh
        pre_refresh_status = validate_token_file()
        
        logger.info(f"🔄 Manual token refresh requested by {username}")
        logger.debug(f"🔍 Pre-refresh token status: {pre_refresh_status['valid']}")
        
        # Attempt refresh
        success = refresh_token()
        
        if success:
            # Get updated token status
            post_refresh_status = validate_token_file()
            
            logger.info(f"✅ Manual token refresh successful for {username}")
            
            return jsonify({
                'success': True,
                'message': 'Token refreshed successfully',
                'pre_refresh': {
                    'valid': pre_refresh_status['valid'],
                    'time_left': int(pre_refresh_status['time_left'])
                },
                'post_refresh': {
                    'valid': post_refresh_status['valid'],
                    'time_left': int(post_refresh_status['time_left']),
                    'expires_at': post_refresh_status['expires_at'],
                    'refresh_expires_at': post_refresh_status['refresh_expires_at']
                },
                'timestamp': time.time()
            })
        else:
            logger.warning(f"❌ Manual token refresh failed for {username}")
            
            # Get token health to understand why it failed
            health_status = monitor_token_health()
            
            return jsonify({
                'success': False,
                'error': 'Token refresh failed',
                'health_status': health_status,
                'recommended_action': health_status.get('action', 'check_system'),
                'timestamp': time.time()
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error in token refresh endpoint: {e}")
        return jsonify({
            'success': False,
            'error': f'Token refresh error: {str(e)}',
            'timestamp': time.time()
        }), 500

@auth_bp.route('/api/token/validate', methods=['POST'])
def validate_token_endpoint():
    """
    ✅ NEW: Validate current token without refreshing
    """
    try:
        if 'logged_in' not in session:
            return jsonify({
                'valid': False,
                'error': 'Authentication required'
            }), 401
        
        if session.get('demo_mode', False):
            return jsonify({
                'valid': True,
                'demo_mode': True,
                'message': 'Demo mode - no token validation needed'
            })
        
        # Validate token
        token_validation = validate_token_file()
        
        return jsonify({
            'valid': token_validation['valid'],
            'exists': token_validation['exists'],
            'access_token_valid': token_validation['access_token_valid'],
            'refresh_token_valid': token_validation['refresh_token_valid'],
            'time_left': int(token_validation['time_left']),
            'refresh_time_left': int(token_validation['refresh_time_left']),
            'expires_at': token_validation['expires_at'],
            'refresh_expires_at': token_validation['refresh_expires_at'],
            'issues': token_validation['issues'],
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"❌ Error in token validation endpoint: {e}")
        return jsonify({
            'valid': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

# ================================================================
# ✅ ENHANCED SYSTEM STATUS AND MONITORING ENDPOINTS
# ================================================================

@auth_bp.route('/api/auth/system/status')
def system_status():
    """
    ✅ NEW: Get comprehensive system status including authentication health
    """
    try:
        # Basic system info
        system_info = {
            'websockets_available': WEBSOCKETS_AVAILABLE,
            'timestamp': time.time(),
            'server_time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }
        
        # Authentication status
        if 'logged_in' in session:
            auth_info = {
                'authenticated': True,
                'username': session.get('username', 'unknown'),
                'demo_mode': session.get('demo_mode', False),
                'user_level': session.get('user_level', 'user'),
                'login_time': session.get('login_time', 0),
                'login_method': session.get('login_method', 'unknown')
            }
            
            # Add token health for non-demo users
            if not session.get('demo_mode', False):
                try:
                    auth_info['token_health'] = monitor_token_health()
                    auth_info['token_validation'] = validate_token_file()
                except Exception as token_error:
                    auth_info['token_error'] = str(token_error)
        else:
            auth_info = {
                'authenticated': False
            }
        
        return jsonify({
            'success': True,
            'system': system_info,
            'authentication': auth_info
        })
        
    except Exception as e:
        logger.error(f"❌ Error in system status endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@auth_bp.route('/api/auth/session/info')
def session_info():
    """
    ✅ NEW: Get current session information
    """
    try:
        if 'logged_in' not in session:
            return jsonify({
                'authenticated': False,
                'session_exists': False
            })
        
        # Calculate session duration
        login_time = session.get('login_time', time.time())
        session_duration = time.time() - login_time
        
        session_data = {
            'authenticated': True,
            'session_exists': True,
            'username': session.get('username', 'unknown'),
            'demo_mode': session.get('demo_mode', False),
            'user_level': session.get('user_level', 'user'),
            'login_time': login_time,
            'session_duration': int(session_duration),
            'login_method': session.get('login_method', 'unknown')
        }
        
        # Add token info for non-demo sessions
        if not session.get('demo_mode', False):
            try:
                token_validation = validate_token_file()
                session_data['token_status'] = {
                    'valid': token_validation['valid'],
                    'time_left': int(token_validation['time_left']),
                    'expires_at': token_validation['expires_at']
                }
            except Exception as token_error:
                session_data['token_error'] = str(token_error)
        
        return jsonify(session_data)
        
    except Exception as e:
        logger.error(f"❌ Error in session info endpoint: {e}")
        return jsonify({
            'authenticated': False,
            'session_exists': False,
            'error': str(e)
        }), 500

# ================================================================
# UTILITY FUNCTIONS
# ================================================================

def get_auth_status():
    """
    ✅ NEW: Get current authentication status (utility function)
    
    Returns:
        dict: Authentication status information
    """
    return {
        'logged_in': session.get('logged_in', False),
        'username': session.get('username', 'unknown'),
        'demo_mode': session.get('demo_mode', False),
        'user_level': session.get('user_level', 'user'),
        'login_time': session.get('login_time', 0),
        'login_method': session.get('login_method', 'unknown')
    }

def log_auth_attempt(action, success=False, details=None):
    """
    ✅ NEW: Log authentication attempts for monitoring
    
    Args:
        action (str): Action attempted (login, logout, refresh, etc.)
        success (bool): Whether the action was successful
        details (str): Additional details about the attempt
    """
    try:
        log_entry = {
            'action': action,
            'success': success,
            'timestamp': time.time(),
            'user_ip': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', 'unknown') if request else 'unknown',
            'details': details or ''
        }
        
        if success:
            logger.info(f"✅ Auth success: {action} - {details or 'No details'}")
        else:
            logger.warning(f"❌ Auth failure: {action} - {details or 'No details'}")
            
    except Exception as e:
        logger.error(f"❌ Error logging auth attempt: {e}")

# ================================================================
# ✅ ADDITIONAL COMPATIBILITY DECORATORS
# ================================================================

def api_auth_required(f):
    """
    API-specific authentication decorator (for API-only routes)
    ✅ FIXED: Always returns JSON errors
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            logger.warning(f"❌ API authentication required for {f.__name__}")
            return jsonify({
                'error': 'Authentication required',
                'code': 401
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_live_mode(f):
    """
    Decorator to require live mode (not demo mode)
    ✅ NEW: For endpoints that require G-Portal authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return jsonify({
                'error': 'Authentication required',
                'code': 401
            }), 401
        
        if session.get('demo_mode', True):
            return jsonify({
                'error': 'This feature requires G-Portal authentication (live mode)',
                'demo_mode': True,
                'code': 403
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

# Make all functions available for import
__all__ = [
    'auth_bp', 'require_auth', 'api_auth_required', 'require_live_mode',
    'get_auth_status', 'log_auth_attempt'
]
