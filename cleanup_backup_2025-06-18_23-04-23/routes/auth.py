"""
GUST Bot Enhanced - Authentication Routes
========================================
Routes for user authentication and session management
"""

# Standard library imports
import logging

# Third-party imports
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
import requests

# Utility imports
from utils.helpers import save_token

# Local imports
from config import Config




logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        data = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Please enter username and password'})
        
        # Check if this looks like demo credentials
        demo_usernames = ['demo', 'test', 'admin', 'guest']
        is_demo = username.lower() in demo_usernames and len(password) < 10
        
        if is_demo:
            # Demo mode - accept demo credentials
            session['logged_in'] = True
            session['username'] = username
            session['demo_mode'] = True
            logger.info(f"ðŸŽ­ Demo mode login: {username}")
            return jsonify({'success': True, 'demo_mode': True})
        else:
            # Real G-Portal authentication
            logger.info(f"ðŸ” Attempting G-Portal authentication for: {username}")
            auth_success = authenticate_gportal(username, password)
            
            if auth_success:
                session['logged_in'] = True
                session['username'] = username
                session['demo_mode'] = False
                logger.info(f"âœ… G-Portal authentication successful for: {username}")
                return jsonify({'success': True, 'demo_mode': False})
            else:
                logger.warning(f"âŒ G-Portal authentication failed for: {username}")
                return jsonify({
                    'success': False, 
                    'error': 'G-Portal authentication failed. Check credentials or try your email address as username.'
                })
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    username = session.get('username', 'Unknown')
    demo_mode = session.get('demo_mode', True)
    
    # Clean up session
    session.clear()
    
    logger.info(f"ðŸ‘‹ User logged out: {username} ({'demo' if demo_mode else 'live'} mode)")
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/token/status')
def token_status():
    """Check G-Portal token status"""
    import os
    import json
    import time
    
    try:
        if os.path.exists(Config.TOKEN_FILE):
            with open(Config.TOKEN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            current_time = time.time()
            token_exp = data.get('access_token_exp', 0)
            refresh_exp = data.get('refresh_token_exp', 0)
            
            time_left = max(0, token_exp - current_time)
            refresh_time_left = max(0, refresh_exp - current_time)
            
            return jsonify({
                'has_token': True,
                'token_valid': time_left > 30,
                'time_left': int(time_left),
                'refresh_valid': refresh_time_left > 0,
                'refresh_time_left': int(refresh_time_left),
                'demo_mode': session.get('demo_mode', True),
                'websockets_available': True  # Will be updated by main app
            })
        else:
            return jsonify({
                'has_token': False,
                'token_valid': False,
                'demo_mode': session.get('demo_mode', True),
                'websockets_available': True  # Will be updated by main app
            })
    except Exception as e:
        logger.error(f"âŒ Error checking token status: {e}")
        return jsonify({
            'has_token': False,
            'token_valid': False,
            'error': str(e),
            'demo_mode': session.get('demo_mode', True),
            'websockets_available': True  # Will be updated by main app
        })

@auth_bp.route('/api/token/refresh', methods=['POST'])
def refresh_token_endpoint():
    """Manually refresh G-Portal token"""
    from utils.helpers import refresh_token
    
    try:
        success = refresh_token()
        if success:
            logger.info("âœ… Token refreshed successfully")
        else:
            logger.warning("âŒ Token refresh failed")
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"âŒ Error refreshing token: {e}")
        return jsonify({'success': False, 'error': str(e)})

def authenticate_gportal(username, password):
    """
    Authenticate with G-Portal and store token
    
    Args:
        username (str): G-Portal username/email
        password (str): G-Portal password
        
    Returns:
        bool: True if authentication successful
    """
    data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_id': 'website',
        'scope': 'openid email profile gportal'
    }
    
    try:
        logger.info(f"ðŸ”„ Making authentication request to G-Portal...")
        response = requests.post(
            Config.GPORTAL_AUTH_URL,
            data=data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'GUST-Bot/1.0'
            },
            timeout=15
        )
        
        logger.info(f"ðŸ“¡ G-Portal auth response: {response.status_code}")
        
        if response.status_code == 200:
            tokens = response.json()
            
            # Save tokens using helper function
            if save_token(tokens, username):
                logger.info(f"âœ… Token saved successfully for {username}")
                return True
            else:
                logger.error(f"âŒ Failed to save token for {username}")
                return False
        else:
            logger.warning(f"âŒ Authentication failed with status {response.status_code}")
            try:
                error_data = response.json()
                logger.warning(f"âŒ Error details: {error_data}")
            except:
                pass
            return False
                
    except requests.exceptions.Timeout:
        logger.error("âŒ Authentication timeout - G-Portal servers may be slow")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("âŒ Connection error - check internet connection")
        return False
    except Exception as e:
        logger.error(f"âŒ Authentication error: {e}")
        return False

def require_auth(f):
    """
    Decorator to require authentication for routes
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def require_live_mode(f):
    """
    Decorator to require live mode (not demo) for routes
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('demo_mode', True):
            if request.is_json:
                return jsonify({
                    'error': 'This feature requires G-Portal authentication',
                    'demo_mode': True
                }), 403
            return jsonify({
                'error': 'Live mode required',
                'demo_mode': True
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def get_user_info():
    """
    Get current user information
    
    Returns:
        dict: User information
    """
    return {
        'username': session.get('username', 'Anonymous'),
        'logged_in': session.get('logged_in', False),
        'demo_mode': session.get('demo_mode', True)
    }
