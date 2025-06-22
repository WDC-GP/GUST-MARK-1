"""
GUST Bot Enhanced - Authentication Routes (COMPLETE WORKING VERSION WITH FIXED URLS)
====================================================================================
✅ FIXED: Correct G-Portal authentication URL (ngpapi/oauth/token)
✅ FIXED: Changed /token/status to /api/token/status to match frontend
✅ COMPLETE: OAuth and session cookie authentication support
✅ COMPLETE: Auto-auth with empty credentials support
✅ COMPLETE: Enhanced error handling and logging
✅ COMPLETE: System health monitoring
✅ WORKING: All authentication flows tested and functional
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
from config import Config, WEBSOCKETS_AVAILABLE, CRYPTOGRAPHY_AVAILABLE

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# ================================================================
# AUTHENTICATION DECORATORS
# ================================================================

def require_auth(f):
    """Authentication decorator for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            logger.warning(f"❌ Unauthenticated access attempt to {f.__name__}")
            
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
    """API-specific authentication decorator"""
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
    """Decorator to require live mode (not demo mode)"""
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
# MAIN LOGIN ROUTE (FIXED URL)
# ================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login with OAuth, session cookies, and auto-auth support
    ✅ FIXED: Correct G-Portal authentication URL (ngpapi/oauth/token)
    """
    if request.method == 'GET':
        return render_template('login.html')
    
    # Handle POST login
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    enable_auto_auth = data.get('enable_auto_auth', False)
    
    # Track if this is an auto-auth attempt
    is_auto_auth_attempt = enable_auto_auth and (not username or not password)
    
    # Handle auto-auth credential loading FIRST
    if not username or not password:
        if enable_auto_auth:
            logger.info("🔐 Auto-auth enabled with empty credentials - attempting stored credential loading")
            
            try:
                from utils.credential_manager import credential_manager
                
                if not credential_manager:
                    logger.error("❌ Auto-auth: Credential manager not available")
                    return jsonify({
                        'success': False,
                        'error': 'Auto-authentication failed: Credential manager not available. Please check your installation.'
                    })
                
                if not credential_manager.credentials_exist():
                    logger.warning("⚠️ Auto-auth: No stored credentials found")
                    return jsonify({
                        'success': False,
                        'error': 'Auto-authentication failed: No stored credentials found. Please log in manually first to enable auto-authentication.'
                    })
                
                stored_creds = credential_manager.load_credentials()
                if not stored_creds or not stored_creds.get('username') or not stored_creds.get('password'):
                    logger.warning("⚠️ Auto-auth: Stored credentials are incomplete")
                    return jsonify({
                        'success': False,
                        'error': 'Auto-authentication failed: Stored credentials are incomplete. Please log in manually to update stored credentials.'
                    })
                
                # Successfully loaded stored credentials
                username = stored_creds.get('username', '')
                password = stored_creds.get('password', '')
                logger.info(f"✅ Auto-auth: Successfully loaded stored credentials for {username}")
                
            except ImportError:
                logger.error("❌ Auto-auth: Credential manager module not available")
                return jsonify({
                    'success': False,
                    'error': 'Auto-authentication failed: Required modules not installed. Please install cryptography package.'
                })
            except Exception as e:
                logger.error(f"❌ Auto-auth credential loading failed: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Auto-authentication failed: {str(e)}. Please log in manually.'
                })
        
        # Final validation after auto-auth attempt
        if not username or not password:
            error_message = "Please enter both username and password"
            if enable_auto_auth:
                error_message = "Auto-authentication failed and no manual credentials provided"
            
            log_auth_attempt('login', success=False, details=error_message)
            return jsonify({
                'success': False,
                'error': error_message
            })
    
    # Check for demo mode
    demo_usernames = ['demo', 'test', 'admin', 'guest']
    is_demo = username.lower() in demo_usernames and len(password) < 10
    
    if is_demo:
        # Demo authentication
        session['logged_in'] = True
        session['username'] = username
        session['demo_mode'] = True
        session['user_level'] = 'admin' if username.lower() == 'admin' else 'user'
        session['login_time'] = time.time()
        session['login_method'] = 'demo'
        
        # Store credentials for auto-auth if requested (demo mode)
        if enable_auto_auth:
            try:
                from utils.credential_manager import credential_manager
                credential_manager.store_credentials(username, password)
                logger.info("🔐 Demo credentials stored for auto-authentication")
            except ImportError:
                logger.warning("⚠️ Auto-auth requested but credential manager not available")
        
        auth_type = "auto-auth demo" if is_auto_auth_attempt else "manual demo"
        log_auth_attempt('login', success=True, details=f"{auth_type}: {username}")
        logger.info(f"🎭 Demo mode login successful ({auth_type}): {username}")
        
        return jsonify({
            'success': True,
            'demo_mode': True,
            'username': username,
            'user_level': session['user_level'],
            'login_time': session['login_time'],
            'auto_auth_enabled': enable_auto_auth,
            'auto_auth_used': is_auto_auth_attempt,
            'redirect_url': '/'
        })
    
    else:
        # G-Portal authentication
        if is_auto_auth_attempt:
            logger.info(f"🔐 Auto-authentication attempt for stored user: {username}")
        else:
            logger.info(f"🔐 Manual G-Portal authentication for {username}")
        
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
            
            # ✅ FIXED: Use correct G-Portal authentication URL with /ngpapi/
            auth_url = getattr(Config, 'GPORTAL_AUTH_URL', 'https://www.g-portal.com/ngpapi/oauth/token')
            
            # Make authentication request
            logger.info(f"📡 Sending G-Portal authentication request to {auth_url} for {username}")
            response = requests.post(
                auth_url,
                data=auth_data,
                headers=headers,
                timeout=15
            )
            
            logger.info(f"📡 G-Portal response: {response.status_code}")
            
            if response.status_code == 200:
                # SUCCESS: Detect response type (JSON OAuth vs HTML cookies)
                content_type = response.headers.get('content-type', '').lower()
                oauth_success = False
                
                # Try OAuth JSON first
                try:
                    if 'application/json' in content_type:
                        tokens = response.json()
                        
                        if 'access_token' in tokens and 'refresh_token' in tokens:
                            logger.info("🔑 Received OAuth tokens from G-Portal")
                            
                            # Save OAuth tokens
                            if save_token(tokens, username):
                                oauth_success = True
                                
                                # Store credentials for auto-auth if requested
                                if enable_auto_auth:
                                    try:
                                        from utils.credential_manager import credential_manager
                                        credential_manager.store_credentials(username, password)
                                        logger.info("🔐 Credentials stored for auto-authentication")
                                        
                                        # Auto-start the auth service
                                        try:
                                            from services.auth_service import auth_service
                                            if auth_service.start():
                                                logger.info("🚀 Auto-authentication service started successfully")
                                        except Exception as service_error:
                                            logger.error(f"❌ Error starting auto-auth service: {service_error}")
                                            
                                    except ImportError:
                                        logger.warning("⚠️ Auto-auth requested but credential manager not available")
                                
                                # Set session data
                                session['logged_in'] = True
                                session['username'] = username
                                session['demo_mode'] = False
                                session['user_level'] = 'admin'
                                session['login_time'] = time.time()
                                session['login_method'] = 'gportal_oauth'
                                
                                # Enhanced logging
                                auth_type = "auto-auth OAuth" if is_auto_auth_attempt else "manual OAuth"
                                log_auth_attempt('login', success=True, details=f"{auth_type}: {username}")
                                logger.info(f"✅ {auth_type} authentication successful for {username}")
                                
                                return jsonify({
                                    'success': True,
                                    'demo_mode': False,
                                    'username': username,
                                    'user_level': 'admin',
                                    'auth_type': 'oauth',
                                    'auto_auth_enabled': enable_auto_auth,
                                    'auto_auth_used': is_auto_auth_attempt,
                                    'token_expires': tokens.get('expires_in', 300),
                                    'login_time': session['login_time'],
                                    'redirect_url': '/'
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
                    logger.info("🔄 Response is not JSON, checking for HTML with cookies")
                
                # Check for HTML response with session cookies
                if not oauth_success and ('text/html' in content_type or response.text.strip().startswith('<!')):
                    logger.info("🔄 Received HTML response - analyzing for successful login")
                    
                    # Extract cookies
                    session_cookies = {}
                    for cookie in response.cookies:
                        session_cookies[cookie.name] = cookie.value
                    
                    logger.info(f"🍪 Found session cookies: {list(session_cookies.keys())}")
                    
                    # Check for success indicators
                    html_content = response.text.lower()
                    success_indicators = ['dashboard', 'server', 'logout', 'account', 'welcome']
                    
                    login_successful = any(indicator in html_content for indicator in success_indicators)
                    has_cookies = len(session_cookies) > 0
                    
                    if login_successful and has_cookies:
                        logger.info("✅ HTML response indicates successful login")
                        
                        # Save session cookies
                        cookie_data = {
                            'type': 'cookie_auth',
                            'session_cookies': session_cookies,
                            'html_indicators': success_indicators[:3]
                        }
                        
                        if save_token(cookie_data, username):
                            # Store credentials for auto-auth if requested
                            if enable_auto_auth:
                                try:
                                    from utils.credential_manager import credential_manager
                                    credential_manager.store_credentials(username, password)
                                    logger.info("🔐 Credentials stored for auto-authentication")
                                    
                                    # Auto-start the auth service
                                    try:
                                        from services.auth_service import auth_service
                                        if auth_service.start():
                                            logger.info("🚀 Auto-authentication service started successfully")
                                    except Exception as service_error:
                                        logger.error(f"❌ Error starting auto-auth service: {service_error}")
                                        
                                except ImportError:
                                    logger.warning("⚠️ Auto-auth requested but credential manager not available")
                            
                            # Set session data
                            session['logged_in'] = True
                            session['username'] = username
                            session['demo_mode'] = False
                            session['user_level'] = 'admin'
                            session['login_time'] = time.time()
                            session['login_method'] = 'gportal_cookie'
                            
                            # Enhanced logging
                            auth_type = "auto-auth Cookie" if is_auto_auth_attempt else "manual Cookie"
                            log_auth_attempt('login', success=True, details=f"{auth_type}: {username}")
                            logger.info(f"✅ {auth_type} authentication successful for {username}")
                            
                            return jsonify({
                                'success': True,
                                'demo_mode': False,
                                'username': username,
                                'user_level': 'admin',
                                'auth_type': 'cookie',
                                'auto_auth_enabled': enable_auto_auth,
                                'auto_auth_used': is_auto_auth_attempt,
                                'session_expires': 240,
                                'login_time': session['login_time'],
                                'redirect_url': '/'
                            })
                        else:
                            logger.error(f"❌ Failed to save session cookies for {username}")
                            return jsonify({
                                'success': False,
                                'error': 'Failed to save session cookies'
                            })
                    else:
                        logger.warning(f"❌ HTML response does not indicate successful login for {username}")
                        return jsonify({
                            'success': False,
                            'error': 'Login failed - invalid credentials or account issue'
                        })
                
                # Unknown response format
                else:
                    logger.error(f"❌ Unknown response format for {username}: {content_type}")
                    return jsonify({
                        'success': False,
                        'error': 'Unexpected response format from G-Portal'
                    })
            
            elif response.status_code == 401:
                logger.warning(f"❌ Invalid credentials for {username}")
                
                if is_auto_auth_attempt:
                    return jsonify({
                        'success': False,
                        'error': 'Auto-authentication failed: Stored credentials are no longer valid. Please log in manually to update your stored credentials.'
                    })
                else:
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
                
                error_message = f'Authentication service error: {response.status_code}'
                if is_auto_auth_attempt:
                    error_message = f'Auto-authentication failed: G-Portal returned HTTP {response.status_code}. Your stored credentials may be invalid.'
                
                return jsonify({
                    'success': False,
                    'error': error_message
                })
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ G-Portal auth timeout for {username}")
            
            error_message = 'Authentication service timeout. Please try again.'
            if is_auto_auth_attempt:
                error_message = 'Auto-authentication failed: Connection timeout. Please try again or log in manually.'
            
            return jsonify({
                'success': False,
                'error': error_message
            })
        except Exception as e:
            logger.error(f"❌ Authentication exception for {username}: {e}")
            
            error_message = 'Authentication error occurred. Please try again.'
            if is_auto_auth_attempt:
                error_message = f'Auto-authentication failed: {str(e)}. Please try logging in manually.'
            
            return jsonify({
                'success': False,
                'error': error_message
            })

# ================================================================
# LOGOUT AND SESSION MANAGEMENT
# ================================================================

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Handle user logout and stop auto-auth service"""
    username = session.get('username', 'unknown')
    
    # Stop auto-auth service if running
    try:
        from services.auth_service import auth_service
        if auth_service.running:
            auth_service.stop()
            logger.info("🛑 Auto-authentication service stopped on logout")
    except Exception as e:
        logger.warning(f"⚠️ Error stopping auto-auth service on logout: {e}")
    
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

# ================================================================
# SESSION AND STATUS ENDPOINTS
# ================================================================

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

@auth_bp.route('/api/token/status')
@require_auth
def token_status():
    """✅ FIXED: Get detailed token status with /api/ prefix"""
    try:
        # Get demo mode status
        demo_mode = session.get('demo_mode', False)
        
        if demo_mode:
            # Demo mode response
            return jsonify({
                'success': True,
                'valid': True,
                'demo_mode': True,
                'message': 'Demo mode active',
                'time_left': 86400,  # 24 hours
                'expires_at': 'N/A',
                'status': 'healthy',
                'health': {
                    'status': 'healthy',
                    'message': 'Demo mode - no real token'
                }
            })
        
        # Live mode - check actual token
        validation = validate_token_file()
        health = monitor_token_health()
        
        return jsonify({
            'success': True,
            'valid': validation['valid'],
            'demo_mode': False,
            'validation': validation,
            'health': health,
            'timestamp': time.time(),
            'time_left': int(validation.get('time_left', 0)),
            'expires_at': validation.get('expires_at', 'Unknown'),
            'status': health.get('status', 'unknown'),
            'message': health.get('message', 'Token status retrieved')
        })
        
    except Exception as e:
        logger.error(f"❌ Error in token status endpoint: {e}")
        return jsonify({
            'success': False,
            'valid': False,
            'error': str(e),
            'message': 'Failed to get token status'
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
            'enabled': getattr(Config, 'AUTO_AUTH_ENABLED', False),
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
        data = request.get_json() or {}
        enable = data.get('enable', False)
        
        try:
            from services.auth_service import auth_service
            
            if enable:
                if auth_service.start():
                    message = "Auto-authentication enabled"
                    logger.info("🚀 Auto-authentication service started via toggle")
                else:
                    message = "Auto-authentication failed to start"
                    logger.warning("⚠️ Auto-authentication service failed to start via toggle")
            else:
                auth_service.stop()
                message = "Auto-authentication disabled"
                logger.info("🛑 Auto-authentication service stopped via toggle")
            
            return jsonify({
                'success': True,
                'message': message,
                'enabled': enable and auth_service.running
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
                try:
                    validation = validate_token_file()
                    health_data['token'] = validation
                except:
                    health_data['token'] = {'valid': False, 'error': 'Token validation failed'}
        
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
    """Complete system health check with auto-auth component structure"""
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
            try:
                validation = validate_token_file()
                auth_info['token_valid'] = validation['valid']
                auth_info['token_time_left'] = validation['time_left']
            except:
                auth_info['token_valid'] = False
                auth_info['token_time_left'] = 0
        
        health_data['authentication'] = auth_info
        
        # Add auto-auth status in the correct components structure
        try:
            from services.auth_service import auth_service
            service_status = auth_service.get_status()
            
            # Check for missing dependencies
            if not CRYPTOGRAPHY_AVAILABLE:
                health_data['components'] = {
                    'auto_auth': {
                        'status': 'unavailable',
                        'enabled': False,
                        'reason': 'Cryptography package not installed. Run: pip install cryptography'
                    }
                }
            elif not getattr(Config, 'AUTO_AUTH_ENABLED', False):
                health_data['components'] = {
                    'auto_auth': {
                        'status': 'unavailable', 
                        'enabled': False,
                        'reason': 'Disabled in configuration'
                    }
                }
            else:
                # All requirements met - auto-auth available
                health_data['components'] = {
                    'auto_auth': {
                        'status': 'available',
                        'enabled': True,
                        'service_status': service_status
                    }
                }
                
        except ImportError as e:
            health_data['components'] = {
                'auto_auth': {
                    'status': 'unavailable',
                    'enabled': False,
                    'reason': f'Auto-auth service not available: {str(e)}'
                }
            }
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"❌ Error in system health check: {e}")
        return jsonify({
            'timestamp': time.time(),
            'status': 'error',
            'components': {
                'auto_auth': {
                    'status': 'error',
                    'enabled': False,
                    'reason': f'System health check failed: {str(e)}'
                }
            },
            'error': str(e)
        }), 500

# ================================================================
# UTILITY FUNCTIONS
# ================================================================

def get_auth_status():
    """Get current authentication status"""
    return {
        'logged_in': session.get('logged_in', False),
        'username': session.get('username', 'unknown'),
        'demo_mode': session.get('demo_mode', False),
        'user_level': session.get('user_level', 'user'),
        'login_time': session.get('login_time', 0),
        'login_method': session.get('login_method', 'unknown')
    }

def log_auth_attempt(action, success=False, details=None):
    """Log authentication attempts for monitoring"""
    try:
        if success:
            logger.info(f"✅ Auth success: {action} - {details or 'No details'}")
        else:
            logger.warning(f"❌ Auth failure: {action} - {details or 'No details'}")
            
    except Exception as e:
        logger.error(f"❌ Error logging auth attempt: {e}")

# ================================================================
# MODULE EXPORTS
# ================================================================

__all__ = [
    'auth_bp', 'require_auth', 'api_auth_required', 'require_live_mode',
    'get_auth_status', 'log_auth_attempt'
]

logger.info("✅ Complete authentication routes loaded with correct G-Portal URL and /api/token/status")