"""
GUST Bot Enhanced - Authentication Routes (AUTO-AUTHENTICATION INTEGRATED)
==========================================================================
✅ ENHANCED: Auto-authentication integration with credential storage
✅ ENHANCED: Background auth service management
✅ ENHANCED: Auto-auth status and control endpoints
✅ NEW: Seamless credential fallback and token renewal
✅ PRESERVED: All existing functionality
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

# Auto-authentication imports (graceful fallback)
try:
    from utils.credential_manager import credential_manager
    from services.auth_service import auth_service
    AUTO_AUTH_AVAILABLE = True
except ImportError:
    AUTO_AUTH_AVAILABLE = False

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# ================================================================
# AUTHENTICATION DECORATOR (PRESERVED)
# ================================================================

def require_auth(f):
    """
    Authentication decorator for routes
    ✅ PRESERVED: Uses consistent session checking (logged_in not authenticated)
    ✅ PRESERVED: Proper error handling for both API and web requests
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

def require_live_mode(f):
    """Decorator to require live (non-demo) mode"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('demo_mode', False):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Feature not available in demo mode',
                    'code': 403
                }), 403
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# ================================================================
# ENHANCED LOGIN ROUTE WITH AUTO-AUTHENTICATION
# ================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def enhanced_login():
    """
    Enhanced login with auto-authentication support
    ✅ NEW: Auto-auth credential storage
    ✅ NEW: Background service startup
    ✅ PRESERVED: All existing login functionality
    """
    if request.method == 'POST':
        data = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        enable_auto_auth = data.get('enableAutoAuth', False)
        
        if not username or not password:
            return jsonify({
                'success': False, 
                'error': 'Please enter username and password'
            })
        
        # Check if this looks like demo credentials
        demo_usernames = ['demo', 'test', 'admin', 'guest']
        is_demo = username.lower() in demo_usernames and len(password) < 10
        
        if is_demo:
            # Demo mode login (auto-auth disabled in demo)
            session['logged_in'] = True
            session['username'] = username
            session['demo_mode'] = True
            session['user_level'] = 'admin' if username.lower() == 'admin' else 'user'
            
            logger.info(f"🎭 Demo mode login successful: {username}")
            
            return jsonify({
                'success': True, 
                'demo_mode': True,
                'username': username,
                'user_level': session['user_level'],
                'auto_auth_enabled': False,
                'auto_auth_available': False
            })
        else:
            # Real G-Portal authentication
            logger.info(f"🔐 Attempting G-Portal authentication for {username}")
            
            try:
                # Authenticate with G-Portal
                login_url = 'https://www.g-portal.com/auth/login'
                login_data = {
                    'email': username,
                    'password': password
                }
                
                response = requests.post(login_url, json=login_data, timeout=10)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if response_data.get('success') and response_data.get('token'):
                        token = response_data['token']
                        
                        # Save token using existing system
                        if save_token(token):
                            # Set session
                            session['logged_in'] = True
                            session['username'] = username
                            session['demo_mode'] = False
                            session['user_level'] = 'admin'
                            
                            # Handle auto-authentication if enabled and available
                            auto_auth_status = {'enabled': False, 'service_started': False}
                            
                            if enable_auto_auth and AUTO_AUTH_AVAILABLE and Config.AUTO_AUTH_ENABLED:
                                try:
                                    # Store credentials securely
                                    if credential_manager.store_credentials(username, password, session.get('user_id')):
                                        # Start background auth service
                                        auth_service.start()
                                        auto_auth_status = {
                                            'enabled': True,
                                            'service_started': True,
                                            'credentials_stored': True
                                        }
                                        logger.info(f"🔐 Auto-authentication enabled for {username}")
                                    else:
                                        logger.warning(f"⚠️ Failed to store credentials for {username}")
                                        auto_auth_status['error'] = 'Failed to store credentials'
                                except Exception as e:
                                    logger.error(f"❌ Auto-auth setup error: {e}")
                                    auto_auth_status['error'] = str(e)
                            
                            logger.info(f"✅ G-Portal login successful: {username}")
                            
                            return jsonify({
                                'success': True,
                                'demo_mode': False,
                                'username': username,
                                'user_level': session['user_level'],
                                'auto_auth_available': AUTO_AUTH_AVAILABLE and Config.AUTO_AUTH_ENABLED,
                                'auto_auth_status': auto_auth_status
                            })
                        else:
                            logger.error(f"❌ Failed to save token for {username}")
                            return jsonify({
                                'success': False,
                                'error': 'Failed to save authentication token'
                            })
                    else:
                        logger.warning(f"⚠️ G-Portal authentication failed for {username}")
                        return jsonify({
                            'success': False,
                            'error': 'Invalid username or password'
                        })
                else:
                    logger.error(f"❌ G-Portal API error for {username}: {response.status_code}")
                    return jsonify({
                        'success': False,
                        'error': f'Authentication service error: {response.status_code}'
                    })
                    
            except Exception as e:
                logger.error(f"❌ Authentication exception for {username}: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Authentication error occurred. Please try again.'
                })
    
    # GET request - show login form
    return render_template('login.html')

# ================================================================
# AUTO-AUTHENTICATION STATUS AND CONTROL ROUTES
# ================================================================

@auth_bp.route('/auth/auto-auth/status')
@require_auth
def auto_auth_status():
    """
    Get comprehensive auto-authentication status
    ✅ NEW: Complete auto-auth status for frontend
    """
    try:
        if not AUTO_AUTH_AVAILABLE:
            return jsonify({
                'available': False,
                'error': 'Auto-authentication not available'
            })
        
        service_status = auth_service.get_status()
        
        status = {
            'available': True,
            'enabled': Config.AUTO_AUTH_ENABLED,
            'credentials_stored': credential_manager.credentials_exist(),
            'service_status': service_status,
            'config': {
                'renewal_interval': Config.AUTO_AUTH_RENEWAL_INTERVAL,
                'max_retries': Config.AUTO_AUTH_MAX_RETRIES,
                'failure_cooldown': Config.AUTO_AUTH_FAILURE_COOLDOWN
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ Error getting auto-auth status: {e}")
        return jsonify({
            'available': False,
            'error': str(e)
        }), 500

@auth_bp.route('/auth/auto-auth/toggle', methods=['POST'])
@require_auth
@require_live_mode
def toggle_auto_auth():
    """
    Enable/disable auto-authentication
    ✅ NEW: Runtime auto-auth control
    """
    try:
        if not AUTO_AUTH_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Auto-authentication not available'
            }), 400
        
        data = request.json or {}
        enable = data.get('enable', False)
        
        if enable:
            # Enable auto-auth - need credentials
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({
                    'success': False,
                    'error': 'Username and password required to enable auto-auth'
                }), 400
            
            # Store credentials and start service
            if credential_manager.store_credentials(username, password, session.get('user_id')):
                auth_service.start()
                logger.info(f"🔐 Auto-authentication enabled for {session.get('username')}")
                
                return jsonify({
                    'success': True,
                    'enabled': True,
                    'service_started': True
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to store credentials'
                }), 500
        else:
            # Disable auto-auth
            auth_service.stop()
            credential_manager.clear_credentials()
            logger.info(f"🔐 Auto-authentication disabled for {session.get('username')}")
            
            return jsonify({
                'success': True,
                'enabled': False,
                'service_started': False
            })
            
    except Exception as e:
        logger.error(f"❌ Error toggling auto-auth: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================================================================
# ENHANCED LOGOUT WITH AUTO-AUTH CLEANUP
# ================================================================

@auth_bp.route('/logout', methods=['POST'])
def enhanced_logout():
    """
    Enhanced logout with optional auto-auth cleanup
    ✅ NEW: Optional credential cleanup
    ✅ PRESERVED: Normal logout functionality
    """
    try:
        data = request.json or {}
        clear_credentials = data.get('clearCredentials', False)
        
        username = session.get('username', 'Unknown')
        demo_mode = session.get('demo_mode', False)
        
        # Clean up session
        session.clear()
        
        # Optional auto-auth cleanup
        if clear_credentials and AUTO_AUTH_AVAILABLE and not demo_mode:
            try:
                auth_service.stop()
                credential_manager.clear_credentials()
                logger.info(f"🔐 Auto-auth credentials cleared for {username}")
            except Exception as e:
                logger.error(f"❌ Error clearing auto-auth: {e}")
        
        logger.info(f"👋 User logged out: {username} ({'demo' if demo_mode else 'live'} mode)")
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Logout error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================================================================
# TOKEN MANAGEMENT ROUTES (PRESERVED WITH ENHANCEMENTS)
# ================================================================

@auth_bp.route('/api/token/status')
def token_status():
    """
    Check G-Portal token status with auto-auth integration
    ✅ ENHANCED: Auto-auth status included
    ✅ PRESERVED: Existing token checking
    """
    try:
        # Basic session status
        demo_mode = session.get('demo_mode', False)
        logged_in = session.get('logged_in', False)
        username = session.get('username', '')
        
        base_response = {
            'demo_mode': demo_mode,
            'logged_in': logged_in,
            'username': username,
            'websockets_available': WEBSOCKETS_AVAILABLE
        }
        
        # Demo mode response
        if demo_mode:
            return jsonify({
                **base_response,
                'has_token': False,
                'token_valid': False,
                'time_left': 0,
                'message': 'Demo mode - no G-Portal token required',
                'auto_auth_status': {'available': False, 'reason': 'demo_mode'}
            })
        
        # Not logged in response
        if not logged_in:
            return jsonify({
                **base_response,
                'has_token': False,
                'token_valid': False,
                'time_left': 0,
                'message': 'Not authenticated',
                'auto_auth_status': {'available': False, 'reason': 'not_logged_in'}
            })
        
        # Check token status
        token = load_token()
        token_valid = bool(token and validate_token_file())
        
        # Auto-auth status
        auto_auth_status = {'available': False}
        if AUTO_AUTH_AVAILABLE:
            try:
                auto_auth_status = {
                    'available': True,
                    'enabled': Config.AUTO_AUTH_ENABLED,
                    'credentials_stored': credential_manager.credentials_exist(),
                    'service_running': auth_service.running if hasattr(auth_service, 'running') else False
                }
            except Exception as e:
                auto_auth_status = {'available': False, 'error': str(e)}
        
        return jsonify({
            **base_response,
            'has_token': bool(token),
            'token_valid': token_valid,
            'time_left': 240 if token_valid else 0,  # Approximate
            'message': 'Token valid' if token_valid else 'Token invalid or expired',
            'auto_auth_status': auto_auth_status
        })
        
    except Exception as e:
        logger.error(f"❌ Token status error: {e}")
        return jsonify({
            'error': str(e),
            'has_token': False,
            'token_valid': False
        }), 500

@auth_bp.route('/api/token/refresh', methods=['POST'])
@require_auth
@require_live_mode
def refresh_token_endpoint():
    """
    Manual token refresh endpoint
    ✅ ENHANCED: Integrates with auto-auth system
    ✅ PRESERVED: Manual refresh functionality
    """
    try:
        logger.info("🔄 Manual token refresh requested")
        
        # Try normal token refresh first
        new_token = refresh_token()
        
        if new_token:
            logger.info("✅ Manual token refresh successful")
            return jsonify({
                'success': True,
                'message': 'Token refreshed successfully',
                'method': 'normal_refresh'
            })
        
        # If normal refresh fails and auto-auth is available, try credential fallback
        if AUTO_AUTH_AVAILABLE and credential_manager.credentials_exist():
            try:
                from utils.helpers import enhanced_refresh_token
                fallback_token = enhanced_refresh_token()
                
                if fallback_token:
                    logger.info("✅ Token refresh via credential fallback successful")
                    return jsonify({
                        'success': True,
                        'message': 'Token refreshed via credential fallback',
                        'method': 'credential_fallback'
                    })
            except Exception as e:
                logger.error(f"❌ Credential fallback error: {e}")
        
        logger.warning("❌ All token refresh methods failed")
        return jsonify({
            'success': False,
            'error': 'Token refresh failed'
        }), 400
        
    except Exception as e:
        logger.error(f"❌ Token refresh error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================================================================
# SYSTEM STATUS WITH AUTO-AUTH MONITORING
# ================================================================

@auth_bp.route('/api/system/status')
def system_status():
    """
    System status with auto-auth monitoring
    ✅ ENHANCED: Auto-auth service monitoring
    ✅ PRESERVED: System health checks
    """
    try:
        # Basic system status
        status = {
            'server_running': True,
            'websockets_available': WEBSOCKETS_AVAILABLE,
            'mongodb_available': getattr(__import__('config'), 'MONGODB_AVAILABLE', False),
            'session_active': session.get('logged_in', False),
            'demo_mode': session.get('demo_mode', False)
        }
        
        # Token health
        token = load_token()
        status['token_status'] = {
            'has_token': bool(token),
            'token_valid': bool(token and validate_token_file()),
            'token_health': monitor_token_health() if token else None
        }
        
        # Auto-auth status
        if AUTO_AUTH_AVAILABLE:
            try:
                auth_service_status = auth_service.get_status()
                status['auto_auth'] = {
                    'available': True,
                    'enabled': Config.AUTO_AUTH_ENABLED,
                    'service_status': auth_service_status,
                    'credentials_stored': credential_manager.credentials_exist()
                }
            except Exception as e:
                status['auto_auth'] = {
                    'available': False,
                    'error': str(e)
                }
        else:
            status['auto_auth'] = {'available': False}
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ System status error: {e}")
        return jsonify({
            'error': str(e),
            'server_running': False
        }), 500