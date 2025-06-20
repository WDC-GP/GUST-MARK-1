"""
GUST Bot Enhanced - Authentication Routes (FIXED VERSION)
=========================================================
✅ FIXED: Consistent session handling and token management
✅ FIXED: Proper token status checking with validation
✅ FIXED: Better error handling and logging
✅ FIXED: Integrated with centralized auth system
✅ FIXED: Token refresh endpoint improvements
✅ FIXED: System status endpoint enhancements
"""

# Standard library imports
import logging
import os
import json
import time

# Third-party imports
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
import requests

# Utility imports
from utils.helpers import save_token, load_token, refresh_token, validate_token_file
from utils.auth_decorators import get_auth_status, log_auth_attempt

# Local imports
from config import Config, WEBSOCKETS_AVAILABLE

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# ================================================================
# LOGIN AND LOGOUT ROUTES
# ================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login
    ✅ FIXED: Consistent session management
    """
    if request.method == 'POST':
        data = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            log_auth_attempt('login', success=False, details="Missing credentials")
            return jsonify({
                'success': False, 
                'error': 'Please enter username and password'
            })
        
        # Check if this looks like demo credentials
        demo_usernames = ['demo', 'test', 'admin', 'guest']
        is_demo = username.lower() in demo_usernames and len(password) < 10
        
        if is_demo:
            # ✅ FIXED: Consistent session setting
            session['logged_in'] = True  # Always use 'logged_in'
            session['username'] = username
            session['demo_mode'] = True
            session['user_level'] = 'admin' if username.lower() == 'admin' else 'user'
            
            log_auth_attempt('login', success=True, details=f"Demo mode: {username}")
            logger.info(f"🎭 Demo mode login successful: {username}")
            
            return jsonify({
                'success': True, 
                'demo_mode': True,
                'username': username,
                'user_level': session['user_level']
            })
        else:
            # Real G-Portal authentication
            logger.info(f"🔐 Attempting G-Portal authentication for: {username}")
            
            try:
                auth_success = authenticate_gportal(username, password)
                
                if auth_success:
                    # ✅ FIXED: Consistent session setting
                    session['logged_in'] = True  # Always use 'logged_in'
                    session['username'] = username
                    session['demo_mode'] = False
                    session['user_level'] = 'user'  # Could be enhanced with G-Portal role detection
                    
                    log_auth_attempt('login', success=True, details=f"G-Portal auth: {username}")
                    logger.info(f"✅ G-Portal authentication successful: {username}")
                    
                    return jsonify({
                        'success': True, 
                        'demo_mode': False,
                        'username': username,
                        'user_level': session['user_level']
                    })
                else:
                    log_auth_attempt('login', success=False, details=f"G-Portal auth failed: {username}")
                    logger.warning(f"❌ G-Portal authentication failed: {username}")
                    
                    return jsonify({
                        'success': False, 
                        'error': 'G-Portal authentication failed. Check credentials or try your email address as username.'
                    })
                    
            except Exception as e:
                log_auth_attempt('login', success=False, details=f"Auth exception: {str(e)}")
                logger.error(f"❌ Authentication exception for {username}: {e}")
                
                return jsonify({
                    'success': False,
                    'error': 'Authentication error occurred. Please try again.'
                })
    
    # GET request - show login form
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """
    Handle user logout
    ✅ FIXED: Better session cleanup and logging
    """
    auth = get_auth_status()
    username = auth['username']
    demo_mode = auth['demo_mode']
    
    # Clean up session completely
    session.clear()
    
    log_auth_attempt('logout', success=True, details=f"User: {username}, Mode: {'demo' if demo_mode else 'live'}")
    logger.info(f"👋 User logged out: {username} ({'demo' if demo_mode else 'live'} mode)")
    
    return redirect(url_for('auth.login'))

# ================================================================
# TOKEN MANAGEMENT ROUTES
# ================================================================

@auth_bp.route('/api/token/status')
def token_status():
    """
    Check G-Portal token status
    ✅ FIXED: Better token validation and consistent response format
    """
    try:
        auth = get_auth_status()
        
        # Always return auth status
        base_response = {
            'demo_mode': auth['demo_mode'],
            'logged_in': auth['logged_in'],
            'username': auth['username'],
            'websockets_available': WEBSOCKETS_AVAILABLE
        }
        
        # If in demo mode, return basic status
        if auth['demo_mode']:
            return jsonify({
                **base_response,
                'has_token': False,
                'token_valid': False,
                'time_left': 0,
                'message': 'Demo mode - no G-Portal token required'
            })
        
        # If not logged in, return auth required
        if not auth['logged_in']:
            return jsonify({
                **base_response,
                'has_token': False,
                'token_valid': False,
                'time_left': 0,
                'error': 'Authentication required'
            })
        
        # ✅ FIXED: Use the new validation function
        token_validation = validate_token_file()
        
        if token_validation['exists'] and token_validation['valid']:
            return jsonify({
                **base_response,
                'has_token': True,
                'token_valid': token_validation['access_token_valid'],
                'time_left': int(token_validation['time_left']),
                'refresh_valid': token_validation['refresh_token_valid'],
                'refresh_time_left': int(token_validation['refresh_time_left']),
                'expires_at': token_validation['expires_at'],
                'refresh_expires_at': token_validation['refresh_expires_at']
            })
        else:
            return jsonify({
                **base_response,
                'has_token': token_validation['exists'],
                'token_valid': False,
                'time_left': 0,
                'issues': token_validation['issues'],
                'error': 'Invalid or missing G-Portal token'
            })
            
    except Exception as e:
        logger.error(f"❌ Error checking token status: {e}")
        return jsonify({
            'has_token': False,
            'token_valid': False,
            'error': f'Token status check failed: {str(e)}',
            'demo_mode': session.get('demo_mode', True),
            'logged_in': session.get('logged_in', False),
            'websockets_available': WEBSOCKETS_AVAILABLE
        }), 500

@auth_bp.route('/api/token/refresh', methods=['POST'])
def refresh_token_endpoint():
    """
    Manually refresh G-Portal token
    ✅ FIXED: Better error handling and validation
    """
    try:
        auth = get_auth_status()
        
        # Check authentication
        if not auth['logged_in']:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        if auth['demo_mode']:
            return jsonify({
                'success': False,
                'error': 'Token refresh not available in demo mode'
            }), 403
        
        # Attempt refresh
        logger.info(f"🔄 Manual token refresh requested by {auth['username']}")
        
        success = refresh_token()
        
        if success:
            logger.info(f"✅ Manual token refresh successful for {auth['username']}")
            
            # Get updated token status
            token_validation = validate_token_file()
            
            return jsonify({
                'success': True,
                'message': 'Token refreshed successfully',
                'token_status': {
                    'valid': token_validation['valid'],
                    'time_left': int(token_validation['time_left']),
                    'expires_at': token_validation['expires_at']
                }
            })
        else:
            logger.warning(f"❌ Manual token refresh failed for {auth['username']}")
            return jsonify({
                'success': False,
                'error': 'Token refresh failed. You may need to re-login.'
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error in token refresh endpoint: {e}")
        return jsonify({
            'success': False,
            'error': f'Token refresh error: {str(e)}'
        }), 500

@auth_bp.route('/api/token/validate', methods=['POST'])
def validate_token_endpoint():
    """
    Validate current token without refreshing
    ✅ NEW: Token validation endpoint
    """
    try:
        auth = get_auth_status()
        
        if not auth['logged_in']:
            return jsonify({
                'valid': False,
                'error': 'Authentication required'
            }), 401
        
        if auth['demo_mode']:
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
            'issues': token_validation['issues'],
            'expires_at': token_validation['expires_at'],
            'refresh_expires_at': token_validation['refresh_expires_at']
        })
        
    except Exception as e:
        logger.error(f"❌ Error validating token: {e}")
        return jsonify({
            'valid': False,
            'error': f'Token validation error: {str(e)}'
        }), 500

# ================================================================
# SYSTEM STATUS AND INFO ROUTES
# ================================================================

@auth_bp.route('/api/system/status')
def system_status():
    """
    Get comprehensive system status including WebSocket availability
    ✅ FIXED: Better status reporting and error handling
    """
    try:
        auth = get_auth_status()
        
        # Get token status
        token_info = {
            'has_token': False,
            'token_valid': False,
            'time_left': 0,
            'issues': []
        }
        
        if not auth['demo_mode'] and auth['logged_in']:
            try:
                token_validation = validate_token_file()
                token_info = {
                    'has_token': token_validation['exists'],
                    'token_valid': token_validation['valid'],
                    'time_left': int(token_validation['time_left']),
                    'refresh_time_left': int(token_validation['refresh_time_left']),
                    'issues': token_validation['issues']
                }
            except Exception as e:
                logger.error(f"Error getting token info for system status: {e}")
                token_info['issues'].append(f'Token check failed: {str(e)}')
        
        # System capabilities
        system_info = {
            'websockets_available': WEBSOCKETS_AVAILABLE,
            'live_console_ready': WEBSOCKETS_AVAILABLE and auth['live_mode'],
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            'flask_available': True  # If we're running, Flask is available
        }
        
        # Database status
        database_info = {'available': False, 'type': 'in-memory'}
        try:
            from pymongo import MongoClient
            database_info = {'available': True, 'type': 'mongodb'}
        except ImportError:
            pass
        
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'auth_status': auth,
            'token_info': token_info,
            'system_info': system_info,
            'database_info': database_info
        })
        
    except Exception as e:
        logger.error(f"❌ System status error: {e}")
        return jsonify({
            'status': 'error',
            'timestamp': time.time(),
            'error': str(e),
            'auth_status': get_auth_status()
        }), 500

@auth_bp.route('/api/auth/info')
def auth_info():
    """
    Get detailed authentication information
    ✅ NEW: Detailed auth info endpoint
    """
    try:
        auth = get_auth_status()
        
        # Get user info safely
        user_info = {
            'username': auth['username'],
            'logged_in': auth['logged_in'],
            'demo_mode': auth['demo_mode'],
            'live_mode': auth['live_mode'],
            'user_level': session.get('user_level', 'user') if auth['logged_in'] else None
        }
        
        # Get capabilities
        capabilities = {
            'can_use_live_console': WEBSOCKETS_AVAILABLE and auth['live_mode'],
            'can_manage_servers': auth['logged_in'],
            'can_use_api': auth['logged_in'],
            'requires_live_mode': ['console_commands', 'server_logs', 'live_monitoring']
        }
        
        # Get requirements
        requirements = {
            'websockets_package': WEBSOCKETS_AVAILABLE,
            'live_mode_for_console': not auth['demo_mode'],
            'authentication_required': auth['logged_in']
        }
        
        return jsonify({
            'user_info': user_info,
            'capabilities': capabilities,
            'requirements': requirements,
            'websockets_available': WEBSOCKETS_AVAILABLE
        })
        
    except Exception as e:
        logger.error(f"❌ Auth info error: {e}")
        return jsonify({
            'error': f'Auth info error: {str(e)}',
            'user_info': get_auth_status()
        }), 500

# ================================================================
# AUTHENTICATION HELPER FUNCTIONS
# ================================================================

def authenticate_gportal(username, password):
    """
    Authenticate with G-Portal API
    ✅ FIXED: Better error handling and logging
    
    Args:
        username (str): G-Portal username/email
        password (str): G-Portal password
        
    Returns:
        bool: True if authentication successful
    """
    if not username or not password:
        logger.error("❌ Missing username or password for G-Portal auth")
        return False
    
    try:
        # Prepare authentication request
        auth_data = {
            'grant_type': 'password',
            'username': username.strip(),
            'password': password.strip(),
            'client_id': 'website'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'GUST-Bot/2.0',
            'Accept': 'application/json'
        }
        
        # Use Config URL if available, otherwise hardcoded
        try:
            auth_url = Config.GPORTAL_AUTH_URL
        except:
            auth_url = 'https://www.g-portal.com/ngpapi/oauth/token'
        
        logger.debug(f"🔐 Authenticating with G-Portal: {auth_url}")
        
        # Make authentication request
        response = requests.post(
            auth_url,
            data=auth_data,
            headers=headers,
            timeout=15,
            allow_redirects=False
        )
        
        logger.debug(f"📡 G-Portal auth response: {response.status_code}")
        
        if response.status_code == 200:
            try:
                tokens = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in auth response: {e}")
                return False
            
            # Validate token structure
            if not isinstance(tokens, dict) or 'access_token' not in tokens:
                logger.error(f"❌ Invalid token structure in auth response")
                return False
            
            # Save tokens using helper function
            if save_token(tokens, username):
                logger.info(f"✅ G-Portal authentication and token save successful: {username}")
                return True
            else:
                logger.error(f"❌ G-Portal auth succeeded but token save failed: {username}")
                return False
                
        elif response.status_code == 400:
            # Bad request - likely invalid credentials
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Bad request')
                error_desc = error_data.get('error_description', '')
                logger.warning(f"❌ G-Portal auth bad request: {error_msg} - {error_desc}")
            except:
                logger.warning(f"❌ G-Portal auth bad request: {response.text[:200]}")
            return False
            
        elif response.status_code == 401:
            logger.warning(f"❌ G-Portal authentication failed: Invalid credentials for {username}")
            return False
            
        else:
            logger.warning(f"❌ G-Portal auth failed with status {response.status_code}")
            try:
                error_data = response.json()
                logger.warning(f"❌ G-Portal auth error details: {error_data}")
            except:
                logger.warning(f"❌ G-Portal auth error response: {response.text[:200]}")
            return False
                
    except requests.exceptions.Timeout:
        logger.error("❌ G-Portal authentication timeout - servers may be slow")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ G-Portal connection error - check internet connection")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected G-Portal authentication error: {e}")
        return False

# ================================================================
# LEGACY COMPATIBILITY DECORATORS
# ================================================================

def require_auth(f):
    """
    Legacy compatibility decorator
    ✅ FIXED: Now uses the centralized auth system
    """
    # Import the fixed decorator from auth_decorators
    from utils.auth_decorators import require_auth as new_require_auth
    return new_require_auth(f)

def require_live_mode(f):
    """
    Legacy compatibility decorator
    ✅ FIXED: Now uses the centralized auth system
    """
    from utils.auth_decorators import require_live_mode as new_require_live_mode
    return new_require_live_mode(f)

def get_user_info():
    """
    Legacy compatibility function
    ✅ FIXED: Now uses the centralized auth system
    """
    from utils.auth_decorators import get_user_info as new_get_user_info
    return new_get_user_info()

def check_websocket_requirements():
    """
    Legacy compatibility function
    ✅ FIXED: Now uses the centralized auth system
    """
    from utils.auth_decorators import check_websocket_requirements as new_check_websocket_requirements
    return new_check_websocket_requirements()