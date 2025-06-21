"""
Background Authentication Service for GUST Bot Enhanced (COMPLETE COOKIE SUPPORT)
==================================================================================
✅ ENHANCED: Complete OAuth and session cookie authentication renewal support
✅ ENHANCED: Automatic detection of authentication type and appropriate renewal
✅ ENHANCED: Comprehensive error handling and retry logic
✅ ENHANCED: Integration with credential manager for seamless re-authentication
✅ ENHANCED: Advanced monitoring and status reporting
✅ ENHANCED: Configurable intervals and safety mechanisms
"""

import time
import threading
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Third-party imports
import requests
import schedule

# Local imports
from utils.helpers import load_token, save_token, validate_token_file, _get_config_value
from config import Config

logger = logging.getLogger(__name__)

# Try to import credential manager (graceful fallback if not available)
try:
    from utils.credential_manager import credential_manager
    CREDENTIAL_MANAGER_AVAILABLE = True
except ImportError:
    CREDENTIAL_MANAGER_AVAILABLE = False
    credential_manager = None
    logger.warning("⚠️ Credential manager not available - auto-auth features limited")

class BackgroundAuthService:
    """
    Enhanced background authentication service with OAuth and cookie support
    
    Features:
    - Automatic token/session renewal every 3 minutes
    - Support for both OAuth tokens and session cookies
    - Intelligent renewal strategy based on authentication type
    - Comprehensive error handling and retry logic
    - Real-time status monitoring and reporting
    """
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_renewal = None
        self.renewal_count = 0
        self.failure_count = 0
        self.last_error = None
        self.renewal_interval = getattr(Config, 'AUTO_AUTH_RENEWAL_INTERVAL', 180)  # 3 minutes default
        self.max_retries = getattr(Config, 'AUTO_AUTH_MAX_RETRIES', 3)
        self.failure_cooldown = getattr(Config, 'AUTO_AUTH_FAILURE_COOLDOWN', 600)  # 10 minutes
        
        # Service state
        self._stop_event = threading.Event()
        self._service_lock = threading.Lock()
        
        logger.info(f"🔐 Background auth service initialized (interval: {self.renewal_interval}s)")
    
    def start(self):
        """Start the background authentication service"""
        with self._service_lock:
            if self.running:
                logger.warning("⚠️ Auth service already running")
                return False
            
            # Check if auto-auth is enabled in config
            if not getattr(Config, 'AUTO_AUTH_ENABLED', True):
                logger.info("ℹ️ Auto-authentication disabled in config")
                return False
            
            # Check if credentials are available
            if not CREDENTIAL_MANAGER_AVAILABLE:
                logger.warning("⚠️ Credential manager not available - service cannot start")
                return False
            
            if not credential_manager.credentials_exist():
                logger.info("ℹ️ No stored credentials - service not started")
                return False
            
            # Start the service
            self.running = True
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._run_service, daemon=True)
            self.thread.start()
            
            logger.info(f"✅ Background auth service started (renewal every {self.renewal_interval}s)")
            return True
    
    def stop(self):
        """Stop the background authentication service"""
        with self._service_lock:
            if not self.running:
                logger.debug("Auth service not running")
                return
            
            self.running = False
            self._stop_event.set()
            
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
                if self.thread.is_alive():
                    logger.warning("⚠️ Auth service thread did not stop gracefully")
            
            logger.info("🛑 Background auth service stopped")
    
    def _run_service(self):
        """Main service loop with enhanced error handling"""
        logger.info("🚀 Auth service main loop started")
        
        # Schedule the renewal task
        schedule.every(self.renewal_interval).seconds.do(self._perform_renewal)
        
        # Initial renewal attempt (optional - can be disabled if not needed)
        self._schedule_initial_check()
        
        while self.running and not self._stop_event.is_set():
            try:
                # Run pending scheduled tasks
                schedule.run_pending()
                
                # Sleep for a short interval
                self._stop_event.wait(timeout=10)
                
            except Exception as e:
                logger.error(f"❌ Error in auth service main loop: {e}")
                self.last_error = str(e)
                
                # Sleep longer on error to avoid rapid failures
                self._stop_event.wait(timeout=30)
        
        logger.info("🏁 Auth service main loop finished")
    
    def _schedule_initial_check(self):
        """Schedule an initial authentication check"""
        def initial_check():
            try:
                validation = validate_token_file()
                if not validation['valid']:
                    logger.info("🔄 Initial auth check: performing renewal")
                    self._perform_renewal()
                else:
                    time_left = validation['time_left']
                    logger.info(f"🔄 Initial auth check: token valid for {time_left}s")
            except Exception as e:
                logger.error(f"❌ Error in initial auth check: {e}")
        
        # Schedule initial check for 10 seconds after start
        schedule.every(10).seconds.do(initial_check).tag('initial_check')
    
    def _perform_renewal(self):
        """Perform authentication renewal with comprehensive error handling"""
        try:
            logger.debug("🔄 Checking if renewal is needed")
            
            # Check if renewal is actually needed
            if not self._should_renew():
                logger.debug("✅ Renewal not needed yet")
                return
            
            logger.info("🔐 Starting authentication renewal process")
            start_time = time.time()
            
            # Perform the actual renewal
            success = self._renew_authentication()
            
            duration = time.time() - start_time
            
            if success:
                self.last_renewal = datetime.now()
                self.renewal_count += 1
                self.failure_count = 0
                self.last_error = None
                
                logger.info(f"✅ Authentication renewal successful (#{self.renewal_count}) - took {duration:.1f}s")
                
                # Remove initial check task if it exists
                schedule.clear('initial_check')
                
            else:
                self.failure_count += 1
                self.last_error = f"Renewal failed (attempt #{self.failure_count})"
                
                logger.warning(f"❌ Authentication renewal failed (#{self.failure_count}) - took {duration:.1f}s")
                
                # Handle failure escalation
                if self.failure_count >= self.max_retries:
                    logger.error(f"🚨 Maximum failures reached ({self.max_retries}), pausing for {self.failure_cooldown}s")
                    time.sleep(self.failure_cooldown)
                    self.failure_count = 0  # Reset failure count after cooldown
                
        except Exception as e:
            self.failure_count += 1
            self.last_error = str(e)
            logger.error(f"❌ Error during renewal process: {e}")
    
    def _should_renew(self) -> bool:
        """Determine if authentication renewal is needed"""
        try:
            # Check token file validity
            validation = validate_token_file()
            
            if not validation['valid']:
                logger.debug("🔄 Token invalid, renewal needed")
                return True
            
            time_left = validation['time_left']
            
            # Renew if less than 60 seconds left (aggressive renewal)
            if time_left <= 60:
                logger.debug(f"🔄 Token expires in {time_left}s, renewal needed")
                return True
            
            # Check if renewal is overdue (backup check)
            if self.last_renewal:
                time_since_renewal = datetime.now() - self.last_renewal
                max_interval = timedelta(seconds=self.renewal_interval * 2)
                
                if time_since_renewal > max_interval:
                    logger.debug(f"🔄 Renewal overdue ({time_since_renewal} > {max_interval})")
                    return True
            
            logger.debug(f"✅ Token valid for {time_left}s, no renewal needed")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking renewal need: {e}")
            return True  # Err on the side of caution
    
    def _renew_authentication(self) -> bool:
        """
        ✅ ENHANCED: Renew authentication with OAuth and cookie support
        
        Returns:
            bool: True if renewal successful, False otherwise
        """
        try:
            # Load current authentication data
            auth_data = load_token()
            if not auth_data:
                logger.warning("⚠️ No authentication data found, attempting credential re-auth")
                return self._attempt_credential_reauth()
            
            auth_type = auth_data.get('auth_type', 'oauth')
            username = auth_data.get('username', 'unknown')
            
            logger.info(f"🔄 Renewing {auth_type} authentication for {username}")
            
            # ✅ Handle cookie-based authentication renewal
            if auth_type == 'cookie':
                logger.info("🍪 Cookie-based auth detected, performing credential re-authentication")
                return self._attempt_credential_reauth()
            
            # ✅ Handle OAuth token renewal
            elif auth_type == 'oauth':
                logger.info("🔐 OAuth auth detected, attempting token refresh")
                return self._refresh_oauth_token(auth_data, username)
            
            else:
                logger.error(f"❌ Unknown auth_type: {auth_type}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in authentication renewal: {e}")
            return False
    
    def _refresh_oauth_token(self, auth_data: dict, username: str) -> bool:
        """
        Refresh OAuth tokens using refresh token
        
        Args:
            auth_data (dict): Current authentication data
            username (str): Username for logging
            
        Returns:
            bool: True if refresh successful
        """
        try:
            refresh_token_val = auth_data.get('refresh_token', '')
            if not refresh_token_val:
                logger.warning("⚠️ No refresh token available, attempting credential re-auth")
                return self._attempt_credential_reauth()
            
            # Prepare refresh request
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
            
            logger.debug(f"🔐 Making OAuth refresh request to {auth_url}")
            
            response = requests.post(
                auth_url,
                data=refresh_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    new_tokens = response.json()
                except json.JSONDecodeError:
                    logger.error("❌ Invalid JSON in OAuth refresh response")
                    return self._attempt_credential_reauth()
                
                if 'access_token' not in new_tokens:
                    logger.error("❌ No access_token in OAuth refresh response")
                    return self._attempt_credential_reauth()
                
                # Calculate expiration times
                current_time = time.time()
                expires_in = new_tokens.get('expires_in', 300)
                refresh_expires_in = new_tokens.get('refresh_expires_in', 86400)
                
                # Update auth data
                auth_data.update({
                    'access_token': new_tokens['access_token'],
                    'refresh_token': new_tokens.get('refresh_token', refresh_token_val),
                    'access_token_exp': int(current_time + expires_in),
                    'refresh_token_exp': int(current_time + refresh_expires_in),
                    'timestamp': datetime.now().isoformat(),
                    'last_refresh': current_time,
                    'refresh_count': auth_data.get('refresh_count', 0) + 1
                })
                
                # Save updated tokens
                if save_token(auth_data, username):
                    logger.info(f"✅ OAuth token refresh successful for {username}")
                    return True
                else:
                    logger.error(f"❌ Failed to save refreshed OAuth tokens for {username}")
                    return False
            
            elif response.status_code in [400, 401]:
                logger.warning(f"⚠️ OAuth refresh failed ({response.status_code}), attempting credential re-auth")
                return self._attempt_credential_reauth()
            
            else:
                logger.error(f"❌ OAuth refresh failed with status {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ OAuth refresh request timeout")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ OAuth refresh connection error")
            return False
        except Exception as e:
            logger.error(f"❌ Error in OAuth token refresh: {e}")
            return False
    
    def _attempt_credential_reauth(self) -> bool:
        """
        ✅ ENHANCED: Attempt re-authentication using stored credentials with cookie support
        
        Returns:
            bool: True if re-authentication successful, False otherwise
        """
        try:
            if not CREDENTIAL_MANAGER_AVAILABLE or not credential_manager:
                logger.error("❌ Credential manager not available for re-authentication")
                return False
            
            # Load stored credentials
            credentials = credential_manager.load_credentials()
            if not credentials:
                logger.warning("⚠️ No stored credentials available for re-authentication")
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
            
            auth_url = _get_config_value('GPORTAL_AUTH_URL', 'https://www.g-portal.com/ngpapi/oauth/token')
            
            logger.debug(f"🔐 Making credential re-auth request to {auth_url}")
            
            response = requests.post(
                auth_url,
                data=auth_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                # ✅ Handle JSON OAuth response
                try:
                    if 'application/json' in content_type:
                        tokens = response.json()
                        
                        if 'access_token' in tokens and 'refresh_token' in tokens:
                            logger.info("🔐 Received OAuth tokens during credential re-auth")
                            
                            if save_token(tokens, username):
                                logger.info("✅ OAuth credential re-authentication successful")
                                return True
                            else:
                                logger.error("❌ Failed to save OAuth tokens during re-auth")
                                return False
                
                except (json.JSONDecodeError, ValueError):
                    pass  # Fall through to cookie handling
                
                # ✅ Handle HTML cookie response
                if 'text/html' in content_type or response.text.strip().startswith('<!'):
                    logger.info("📄 Received HTML response during credential re-auth")
                    
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
                        logger.info("✅ HTML response indicates successful credential re-auth")
                        
                        # Save session cookies
                        cookie_data = {
                            'type': 'cookie_auth',
                            'session_cookies': session_cookies,
                            'reauth_timestamp': time.time()
                        }
                        
                        if save_token(cookie_data, username):
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
                logger.error(f"❌ Credential re-authentication failed with status: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ Credential re-auth request timeout")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ Credential re-auth connection error")
            return False
        except Exception as e:
            logger.error(f"❌ Error during credential re-authentication: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive service status
        
        Returns:
            dict: Service status information
        """
        try:
            status = {
                'running': self.running,
                'enabled': getattr(Config, 'AUTO_AUTH_ENABLED', True),
                'last_renewal': self.last_renewal.isoformat() if self.last_renewal else None,
                'renewal_count': self.renewal_count,
                'failure_count': self.failure_count,
                'last_error': self.last_error,
                'renewal_interval': self.renewal_interval,
                'max_retries': self.max_retries,
                'credentials_stored': False,
                'thread_alive': self.thread.is_alive() if self.thread else False
            }
            
            # Add credential manager status
            if CREDENTIAL_MANAGER_AVAILABLE and credential_manager:
                status['credentials_stored'] = credential_manager.credentials_exist()
            
            # Add current token status
            try:
                validation = validate_token_file()
                status['current_token'] = {
                    'valid': validation['valid'],
                    'time_left': validation['time_left'],
                    'auth_type': validation.get('auth_type', 'unknown')
                }
            except Exception as e:
                status['current_token'] = {
                    'valid': False,
                    'error': str(e)
                }
            
            # Calculate next renewal time
            if self.last_renewal and self.running:
                next_renewal = self.last_renewal + timedelta(seconds=self.renewal_interval)
                status['next_renewal'] = next_renewal.isoformat()
                status['seconds_until_renewal'] = max(0, (next_renewal - datetime.now()).total_seconds())
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Error getting service status: {e}")
            return {
                'running': self.running,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def force_renewal(self) -> bool:
        """
        Force an immediate authentication renewal
        
        Returns:
            bool: True if renewal successful
        """
        try:
            logger.info("🔄 Force renewal requested")
            return self._renew_authentication()
        except Exception as e:
            logger.error(f"❌ Error in force renewal: {e}")
            return False

# ================================================================
# GLOBAL SERVICE INSTANCE
# ================================================================

# Create global service instance
auth_service = BackgroundAuthService()

# ================================================================
# CONVENIENCE FUNCTIONS
# ================================================================

def start_auto_auth():
    """Start the auto-authentication service"""
    return auth_service.start()

def stop_auto_auth():
    """Stop the auto-authentication service"""
    auth_service.stop()

def get_auto_auth_status():
    """Get auto-authentication service status"""
    return auth_service.get_status()

def force_auth_renewal():
    """Force an immediate authentication renewal"""
    return auth_service.force_renewal()

# ================================================================
# MODULE EXPORTS
# ================================================================

__all__ = [
    'BackgroundAuthService',
    'auth_service',
    'start_auto_auth',
    'stop_auto_auth', 
    'get_auto_auth_status',
    'force_auth_renewal'
]

logger.info("✅ Enhanced background auth service loaded with OAuth and cookie support")