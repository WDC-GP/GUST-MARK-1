"""
GUST Bot Enhanced - Authentication Routes (COMPLETE COOKIE SUPPORT VERSION)
============================================================================
✅ ENHANCED: Complete OAuth and session cookie authentication support
✅ ENHANCED: Detects G-Portal response type (JSON vs HTML) automatically
✅ ENHANCED: Comprehensive token status checking with validation
✅ ENHANCED: Better error handling and detailed logging
✅ ENHANCED: Integration with auto-authentication system
✅ ENHANCED: System status monitoring with health metrics
✅ FIXED: All authentication decorators and utility functions
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
# AUTHENTICATION DECORATORS
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
            
            # Redirect to login for web requests
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

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

# ================================================================
# ✅ ENHANCED LOGIN ROUTE WITH COOKIE DETECTION
# ================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    ✅ ENHANCED: Handle user login with OAuth and session cookie support
    
    Automatically detects G-Portal response type and handles both:
    - JSON responses with OAuth tokens
    - HTML responses with session cookies
    """
    if request.method == 'GET':
        return render_template('login.html')
    
    # Handle POST login
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    enable_auto_auth = data.get('enable_auto_auth', False)
    
    if not username or not password:
        log_auth_attempt('login', success=False, details="Missing credentials")
        return jsonify({
            'success': False, 
            'error': 'Please enter username and password'
        })
    
    # Check for demo mode
    demo_usernames = ['demo', 'test', 'admin', 'guest']
    is_demo = username.lower() in demo_usernames and len(password) < 10
    
    if is_demo:
        # ✅ Demo authentication (preserved existing logic)
        session['logged_in'] = True
        session['username'] = username
        session['demo_mode'] = True
        session['user_level'] = 'admin' if username.lower() == 'admin' else 'user'
        session['login_time'] = time.time()
        session['login_method'] = 'demo'
        
        log_auth_attempt('login', success=True, details=f"Demo mode: {username}")
        logger.info(f"🎭 Demo mode login successful: {username}")
        
        return jsonify({
            'success': True, 
            'demo_mode': True,
            'username': username,
            'user_level': session['user_level'],
            'login_time': session['login_time']
        })
    
    else:
        # ✅ ENHANCED: G-Portal authentication with automatic response type detection
        logger.info(f"🔐 Attempting G-Portal authentication for {username}")
        
        try:
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
            
            response = requests.post(
                Config.GPORTAL_AUTH_URL,
                data=auth_data,
                headers=headers,
                timeout=15
            )
            
            logger.info(f"📡 G-Portal response: {response.status_code}")
            
            if response.status_code == 200:
                # ✅ NEW: Detect response type (JSON OAuth vs HTML cookies)
                content_type = response.headers.get('content-type', '').lower()
                
                # Try to parse as JSON first (OAuth tokens)
                oauth_success = False
                try:
                    if 'application/json' in content_type:
                        tokens = response.json()
                        
                        if 'access_token' in tokens and 'refresh_token' in tokens:
                            logger.info("🔐 Received OAuth tokens from G-Portal")
                            
                            # Save OAuth tokens using existing logic
                            if save_token(tokens, username):
                                oauth_success = True
                                
                                # Store credentials for auto-auth if requested
                                if enable_auto_auth:
                                    try:
                                        from utils.credential_manager import credential_manager
                                        credential_manager.store_credentials(username, password)
                                        logger.info("🔐 Credentials stored for auto-authentication")
                                    except ImportError:
                                        logger.warning("⚠️ Auto-auth requested but credential manager not available")
                                
                                session['logged_in'] = True
                                session['username'] = username
                                session['demo_mode'] = False
                                session['user_level'] = 'admin'
                                session['login_time'] = time.time()
                                session['login_method'] = 'gportal_oauth'
                                
                                log_auth_attempt('login', success=True, details=f"OAuth auth: {username}")
                                logger.info(f"✅ OAuth authentication successful for {username}")
                                
                                return jsonify({
                                    'success': True,
                                    'demo_mode': False,
                                    'username': username,
                                    'user_level': 'admin',
                                    'auth_type': 'oauth',
                                    'auto_auth_enabled': enable_auto_auth,
                                    'token_expires': tokens.get('expires_in', 300),
                                    'login_time': session['login_time']
                                })
                            else:
                                logger.error(f"❌ Failed to save OAuth tokens for {username}")
                                return jsonify({
                                    'success': False,
                                    'error': 'Failed to save authentication tokens'
                                })
                        else:
                            logger.warning(f"⚠️ JSON response missing tokens for {username}")
                            # Fall through to cookie detection
                
                except (json.JSONDecodeError, ValueError):
                    logger.info("📄 Response is not JSON, checking for HTML with cookies")
                
                # ✅ NEW: Check for HTML response with session cookies (if OAuth didn't work)
                if not oauth_success and ('text/html' in content_type or response.text.strip().startswith('<!')):
                    logger.info("📄 Received HTML response - analyzing for successful login")
                    
                    # Extract cookies from response
                    session_cookies = {}
                    for cookie in response.cookies:
                        session_cookies[cookie.name] = cookie.value
                    
                    logger.info(f"🍪 Found session cookies: {list(session_cookies.keys())}")
                    
                    # Check for successful login indicators in HTML
                    html_content = response.text.lower()
                    success_indicators = [
                        'dashboard', 'server', 'logout', 'account',
                        'welcome', 'home', 'portal', 'profile'
                    ]
                    
                    login_successful = any(indicator in html_content for indicator in success_indicators)
                    has_cookies = len(session_cookies) > 0
                    
                    if login_successful and has_cookies:
                        logger.info("✅ HTML response indicates successful login")
                        
                        # ✅ NEW: Save session cookies using enhanced save_token
                        cookie_data = {
                            'type': 'cookie_auth',
                            'session_cookies': session_cookies,
                            'html_indicators': success_indicators[:3]  # Store some indicators for debugging
                        }
                        
                        if save_token(cookie_data, username):
                            # Store credentials for auto-auth if requested
                            if enable_auto_auth:
                                try:
                                    from utils.credential_manager import credential_manager
                                    credential_manager.store_credentials(username, password)
                                    logger.info("🔐 Credentials stored for auto-authentication")
                                except ImportError:
                                    logger.warning("⚠️ Auto-auth requested but credential manager not available")
                            
                            session['logged_in'] = True
                            session['username'] = username
                            session['demo_mode'] = False
                            session['user_level'] = 'admin'
                            session['login_time'] = time.time()
                            session['login_method'] = 'gportal_cookie'
                            
                            log_auth_attempt('login', success=True, details=f"Cookie auth: {username}")
                            logger.info(f"✅ Cookie authentication successful for {username}")
                            
                            return jsonify({
                                'success': True,
                                'demo_mode': False,
                                'username': username,
                                'user_level': 'admin',
                                'auth_type': 'cookie',
                                'auto_auth_enabled': enable_auto_auth,
                                'session_expires': 240,  # 4 minutes until auto-refresh
                                'login_time': session['login_time']
                            })
                        else:
                            log_auth_attempt('login', success=False, details=f"Failed to save cookies: {username}")
                            logger.error(f"❌ Failed to save session cookies for {username}")
                            return jsonify({
                                'success': False,
                                'error': 'Failed to save session cookies'
                            })
                    else:
                        log_auth_attempt('login', success=False, details=f"HTML login failed: {username}")
                        logger.warning(f"❌ HTML response does not indicate successful login for {username}")
                        return jsonify({
                            'success': False,
                            'error': 'Login failed - invalid credentials or account issue'
                        })
                
                # ✅ FALLBACK: Unknown response format
                else:
                    log_auth_attempt('login', success=False, details=f"Unknown response format: {content_type}")
                    logger.error(f"❌ Unknown response format for {username}: {content_type}")
                    return jsonify({
                        'success': False,
                        'error': 'Unexpected response format from G-Portal'
                    })
            
            elif response.status_code == 401:
                log_auth_attempt('login', success=False, details=f"Invalid credentials: {username}")
                logger.warning(f"❌ Invalid credentials for {username}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid username or password'
                })
            elif response.status_code == 429:
                log_auth_attempt('login', success=False, details=f"Rate limited: {username}")
                logger.warning(f"❌ Rate limited authentication attempt for {username}")
                return jsonify({
                    'success': False,
                    'error': 'Too many login attempts. Please try again later.'
                })
            else:
                log_auth_attempt('login', success=False, details=f"HTTP {response.status_code}: {username}")
                logger.error(f"❌ G-Portal auth failed for {username}: {response.status_code}")
                return jsonify({
                    'success': False,
                    'error': f'Authentication service error: {response.status_code}'
                })
                
        except requests.exceptions.Timeout:
            log_auth_attempt('login', success=False, details=f"Timeout: {username}")
            logger.error(f"❌ G-Portal auth timeout for {username}")
            return jsonify({
                'success': False,
                'error': 'Authentication service timeout. Please try again.'
            })
        except Exception as e:
            log_auth_attempt('login', success=False, details=f"Exception: {str(e)}")
            logger.error(f"❌ Authentication exception for {username}: {e}")
            return jsonify({
                'success': False,
                'error': 'Authentication error occurred. Please try again.'
            })

# ================================================================
# LOGOUT AND SESSION MANAGEMENT
# ================================================================

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Handle user logout"""
    username = session.get('username', 'unknown')
    
    # Clear session
    session.clear()
    
    # Remove token file
    try:
        token_file = 'gp-session.json'
        if os.path.exists(token_file):
            os.remove(token_file)
            logger.info(f"🗑️ Token file removed for {username}")
    except Exception as e:
        logger.warning(f"⚠️ Error removing token file: {e}")
    
    log_auth_attempt('logout', success=True, details=f"User logged out: {username}")
    logger.info(f"👋 User logged out: {username}")
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    else:
        return redirect(url_for('auth.login'))

@auth_bp.route('/session/info')
@require_auth
def session_info():
    """Get current session information"""
    try:
        if 'logged_in' not in session:
            return jsonify({
                'authenticated': False,
                'session_exists': False,
                'error': 'No active session'
            }), 401
        
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
# TOKEN AND AUTHENTICATION STATUS ENDPOINTS
# ================================================================

@auth_bp.route('/token/status')
@require_auth
def token_status():
    """Get detailed token status"""
    try:
        validation = validate_token_file()
        health = monitor_token_health()
        
        return jsonify({
            'success': True,
            'validation': validation,
            'health': health,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"❌ Error in token status endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/token/refresh', methods=['POST'])
@require_auth
def manual_token_refresh():
    """Manually refresh authentication token"""
    try:
        success = refresh_token()
        
        if success:
            validation = validate_token_file()
            return jsonify({
                'success': True,
                'message': 'Token refreshed successfully',
                'validation': validation
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Token refresh failed'
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error in manual token refresh: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================================================================
# AUTO-AUTHENTICATION ENDPOINTS
# ================================================================

@auth_bp.route('/auto-auth/status')
def auto_auth_status():
    """Get auto-authentication service status"""
    try:
        # Try to get auto-auth service status
        try:
            from services.auth_service import auth_service
            service_status = auth_service.get_status()
            auto_auth_available = True
        except ImportError:
            service_status = {
                'running': False,
                'error': 'Auto-auth service not available'
            }
            auto_auth_available = False
        
        # Get credential storage status
        try:
            from utils.credential_manager import credential_manager
            credentials_stored = credential_manager.credentials_exist()
        except ImportError:
            credentials_stored = False
        
        return jsonify({
            'success': True,
            'available': auto_auth_available,
            'enabled': Config.AUTO_AUTH_ENABLED if hasattr(Config, 'AUTO_AUTH_ENABLED') else False,
            'service_status': service_status,
            'credentials_stored': credentials_stored,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"❌ Error in auto-auth status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/auto-auth/toggle', methods=['POST'])
@require_auth
def toggle_auto_auth():
    """Toggle auto-authentication service"""
    try:
        data = request.json or {}
        enable = data.get('enable', False)
        
        try:
            from services.auth_service import auth_service
            
            if enable:
                auth_service.start()
                message = "Auto-authentication enabled"
            else:
                auth_service.stop()
                message = "Auto-authentication disabled"
            
            return jsonify({
                'success': True,
                'message': message,
                'enabled': enable
            })
            
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Auto-authentication service not available'
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error toggling auto-auth: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================================================================
# SYSTEM HEALTH ENDPOINTS
# ================================================================

@auth_bp.route('/health/auth')
def auth_health():
    """Authentication system health check"""
    try:
        health_data = {
            'timestamp': time.time(),
            'auth_system': 'operational',
            'session_active': 'logged_in' in session,
            'websockets_available': WEBSOCKETS_AVAILABLE
        }
        
        if 'logged_in' in session:
            health_data['user'] = {
                'username': session.get('username', 'unknown'),
                'demo_mode': session.get('demo_mode', False),
                'user_level': session.get('user_level', 'user'),
                'login_method': session.get('login_method', 'unknown')
            }
            
            # Add token health for non-demo sessions
            if not session.get('demo_mode', False):
                validation = validate_token_file()
                health_data['token'] = validation
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"❌ Error in auth health check: {e}")
        return jsonify({
            'timestamp': time.time(),
            'auth_system': 'error',
            'error': str(e)
        }), 500

@auth_bp.route('/health/system')
def system_health():
    """Complete system health check"""
    try:
        health_data = {
            'timestamp': time.time(),
            'status': 'operational',
            'auth_available': True,
            'websocket_manager': 'available' if WEBSOCKETS_AVAILABLE else 'unavailable'
        }
        
        # Add authentication info
        auth_info = {
            'session_active': 'logged_in' in session,
            'demo_mode': session.get('demo_mode', True)
        }
        
        if 'logged_in' in session and not session.get('demo_mode', False):
            validation = validate_token_file()
            auth_info['token_valid'] = validation['valid']
            auth_info['token_time_left'] = validation['time_left']
        
        health_data['authentication'] = auth_info
        
        # Add auto-auth status
        try:
            from services.auth_service import auth_service
            health_data['auto_auth'] = auth_service.get_status()
        except ImportError:
            health_data['auto_auth'] = {'available': False}
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"❌ Error in system health check: {e}")
        return jsonify({
            'timestamp': time.time(),
            'status': 'error',
            'error': str(e)
        }), 500

# ================================================================
# UTILITY FUNCTIONS
# ================================================================

def get_auth_status():
    """
    Get current authentication status (utility function)
    
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
    Log authentication attempts for monitoring
    
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
# MODULE EXPORTS
# ================================================================

# Make all functions available for import
__all__ = [
    'auth_bp', 'require_auth', 'api_auth_required', 'require_live_mode',
    'get_auth_status', 'log_auth_attempt'
]

logger.info("✅ Enhanced authentication routes loaded with OAuth and cookie support")