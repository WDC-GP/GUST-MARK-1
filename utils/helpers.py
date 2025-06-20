"""
GUST Bot Enhanced - Helper Functions (ULTRA-AGGRESSIVE TOKEN FIX + COMPLETE FUNCTIONS)
=======================================================================================
✅ CRITICAL: Buffer time reduced to 30 seconds for maximum G-Portal compatibility  
✅ ENHANCED: Ultra-aggressive token refresh strategy
✅ ENHANCED: Priority token operations bypass rate limiting
✅ ENHANCED: Better error recovery and automatic re-login detection
✅ ENHANCED: Coordination with optimization systems
✅ FIXED: All existing functionality preserved
✅ FIXED: All missing functions restored for complete compatibility
"""

import os
import json
import time
import logging
import random
import string
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any
import requests

logger = logging.getLogger(__name__)

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
# ENHANCED FILE LOCKING UTILITIES
# ================================================================

def acquire_file_lock(file_handle, timeout=5):
    """Enhanced cross-platform file locking with timeout"""
    if not FILE_LOCKING_AVAILABLE:
        return False
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            if FILE_LOCKING_TYPE == 'windows':
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                logger.debug("🔒 Windows file lock acquired")
                return True
            elif FILE_LOCKING_TYPE == 'unix':
                import fcntl
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.debug("🔒 Unix file lock acquired")
                return True
        except Exception as e:
            logger.debug(f"⚠️ Lock attempt failed: {e}")
            time.sleep(0.1)
    
    logger.warning(f"⚠️ Could not acquire file lock within {timeout}s")
    return False

def release_file_lock(file_handle):
    """Enhanced cross-platform file lock release"""
    if not FILE_LOCKING_AVAILABLE:
        return
    
    try:
        if FILE_LOCKING_TYPE == 'windows':
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            logger.debug("🔓 Windows file lock released")
        elif FILE_LOCKING_TYPE == 'unix':
            import fcntl
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
            logger.debug("🔓 Unix file lock released")
    except Exception as e:
        logger.debug(f"⚠️ Error releasing file lock: {e}")

# ================================================================
# ULTRA-AGGRESSIVE TOKEN MANAGEMENT FUNCTIONS
# ================================================================

def load_token():
    """
    ✅ ULTRA-AGGRESSIVE FIX: Load and return ONLY the access token as string
    
    CRITICAL CHANGES:
    - Buffer time reduced to 30 seconds (was 60) for maximum G-Portal compatibility
    - Enhanced priority handling for token operations
    - Better coordination with rate limiting systems
    - Ultra-aggressive refresh strategy
    
    Returns:
        str: Valid access token string or empty string if unavailable
    """
    try:
        token_file = 'gp-session.json'
        
        # Check if file exists
        if not os.path.exists(token_file):
            logger.debug("📁 Token file not found")
            return ''
            
        with open(token_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Enhanced data structure validation
        if not isinstance(data, dict):
            logger.error("❌ Invalid token file format - not a dictionary")
            return ''
            
        current_time = time.time()
        token_exp = data.get('access_token_exp', 0)
        
        # Enhanced expiration time validation
        try:
            token_exp = float(token_exp) if token_exp else 0
        except (ValueError, TypeError):
            logger.error(f"❌ Invalid token expiration format: {token_exp}")
            return ''
            
        # ✅ ULTRA-AGGRESSIVE FIX: 30-second buffer time for maximum G-Portal compatibility
        # This is the most aggressive timing that still allows for refresh operations
        buffer_time = 30  # CRITICAL: Changed from 60 to 30 seconds
        time_until_expiry = token_exp - current_time
        
        logger.debug(f"⏰ Token expires in {time_until_expiry:.1f} seconds (ultra-aggressive buffer: {buffer_time}s)")
        
        if time_until_expiry > buffer_time:
            # Token is still valid with buffer
            access_token = data.get('access_token', '')
            
            # Enhanced JWT-compatible token validation
            if is_valid_jwt_token(access_token):
                logger.debug(f"✅ Returning valid access token (length: {len(access_token.strip())})")
                return access_token.strip()
            else:
                logger.error(f"❌ Access token validation failed: length={len(access_token.strip()) if access_token else 0}")
                return ''
        else:
            # Token expired or expiring soon, attempt ultra-aggressive refresh
            logger.info(f"🚀 Ultra-aggressive refresh: Token expires in {time_until_expiry:.1f}s, attempting immediate refresh...")
            
            # Set priority flag for rate limiter bypass
            _set_token_operation_priority(True)
            
            try:
                if refresh_token():
                    # Refresh successful, reload and return new token
                    try:
                        with open(token_file, 'r', encoding='utf-8') as f:
                            refreshed_data = json.load(f)
                        
                        new_token = refreshed_data.get('access_token', '')
                        
                        # Validate refreshed token
                        if is_valid_jwt_token(new_token):
                            logger.info("✅ Ultra-aggressive token refresh successful, returning new token")
                            return new_token.strip()
                        else:
                            logger.error(f"❌ Refreshed token failed validation: length={len(new_token)}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error reading refreshed token: {e}")
                
                logger.warning("❌ Ultra-aggressive token refresh failed or no valid token available")
                return ''
            finally:
                # Always clear priority flag
                _set_token_operation_priority(False)
            
    except FileNotFoundError:
        logger.debug("📁 Token file not found")
        return ''
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in token file: {e}")
        return ''
    except Exception as e:
        logger.error(f"❌ Unexpected error loading token: {e}")
        return ''

def refresh_token():
    """
    ✅ ULTRA-AGGRESSIVE FIX: Enhanced token refresh with bypass capabilities
    
    Returns:
        bool: True if refresh successful, False otherwise
    """
    token_file = 'gp-session.json'
    
    # Set priority for rate limiter bypass
    _set_token_operation_priority(True)
    
    try:
        # Verify file exists
        if not os.path.exists(token_file):
            logger.error("❌ Token file not found for refresh")
            return False
        
        try:
            # Enhanced file locking with timeout
            with open(token_file, 'r+', encoding='utf-8') as f:
                lock_acquired = acquire_file_lock(f, timeout=10)
                
                try:
                    f.seek(0)
                    tokens = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON in token file: {e}")
                    return False
                finally:
                    if lock_acquired:
                        release_file_lock(f)
                
                # Validate token file structure
                if not isinstance(tokens, dict):
                    logger.error("❌ Token file is not a valid dictionary")
                    return False
                
                refresh_token_value = tokens.get('refresh_token', '').strip()
                
                # Enhanced JWT token validation for refresh token
                if not is_valid_jwt_token(refresh_token_value):
                    logger.error(f"❌ Invalid refresh token: length={len(refresh_token_value)}")
                    return False
                
                # Check refresh token expiration with ultra-aggressive timing
                current_time = time.time()
                refresh_exp = tokens.get('refresh_token_exp', 0)
                if refresh_exp and current_time >= (refresh_exp - 10):  # 10 second grace period
                    logger.error(f"❌ Refresh token expired or expiring very soon at {datetime.fromtimestamp(refresh_exp)}")
                    return False
                
                # Prepare enhanced refresh request with priority headers
                data = {
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token_value,
                    'client_id': 'website'
                }
                
                # Ultra-enhanced headers for maximum G-Portal compatibility
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Origin': 'https://www.g-portal.com',
                    'Referer': 'https://www.g-portal.com/',
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'X-Priority': 'high',  # Custom priority header
                    'X-Token-Operation': 'refresh'  # Custom operation header
                }
                
                gportal_auth_url = 'https://www.g-portal.com/ngpapi/oauth/token'
                
                logger.info("🚀 Attempting ultra-aggressive token refresh...")
                
                try:
                    # Ultra-aggressive timing: reduced timeout for faster failure detection
                    response = requests.post(
                        gportal_auth_url,
                        data=data,
                        headers=headers,
                        timeout=20,  # Reduced from 30 to 20 seconds
                        allow_redirects=False
                    )
                    
                    logger.debug(f"📡 Ultra-aggressive refresh response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            new_tokens = response.json()
                        except json.JSONDecodeError:
                            logger.error("❌ Invalid JSON in refresh response")
                            return False
                        
                        # Enhanced response validation
                        if (not isinstance(new_tokens, dict) or 
                            'access_token' not in new_tokens or
                            not new_tokens['access_token'].strip()):
                            logger.error("❌ Invalid token response format")
                            return False
                        
                        new_access_token = new_tokens['access_token'].strip()
                        
                        # Validate new token with JWT support
                        if not is_valid_jwt_token(new_access_token):
                            logger.error(f"❌ New access token failed validation: length={len(new_access_token)}")
                            return False
                        
                        # Calculate expiration times with conservative defaults for ultra-aggressive mode
                        expires_in = new_tokens.get('expires_in', 240)  # Reduced default from 300 to 240
                        refresh_expires_in = new_tokens.get('refresh_expires_in', 3600)  # Keep refresh at 1 hour
                        
                        try:
                            expires_in = max(240, int(float(expires_in)))  # Minimum 4 minutes
                            refresh_expires_in = max(1800, int(float(refresh_expires_in)))  # Minimum 30 minutes
                        except (ValueError, TypeError):
                            logger.warning("⚠️ Invalid expiration times, using ultra-aggressive defaults")
                            expires_in = 240
                            refresh_expires_in = 1800
                        
                        # Update tokens with comprehensive data
                        tokens.update({
                            'access_token': new_access_token,
                            'refresh_token': new_tokens.get('refresh_token', refresh_token_value).strip(),
                            'access_token_exp': int(current_time + expires_in),
                            'refresh_token_exp': int(current_time + refresh_expires_in),
                            'timestamp': datetime.now().isoformat(),
                            'last_refresh': datetime.now().isoformat(),
                            'refresh_count': tokens.get('refresh_count', 0) + 1,
                            'expires_in': expires_in,
                            'refresh_expires_in': refresh_expires_in,
                            'ultra_aggressive_mode': True,  # Flag for monitoring
                            'buffer_time_used': 30  # Track buffer time used
                        })
                        
                        # Atomic file write with rollback capability
                        temp_file = token_file + '.tmp'
                        backup_file = token_file + '.backup'
                        
                        try:
                            # Create backup
                            if os.path.exists(token_file):
                                import shutil
                                shutil.copy2(token_file, backup_file)
                            
                            # Write new tokens to temp file
                            with open(temp_file, 'w', encoding='utf-8') as write_f:
                                write_lock_acquired = acquire_file_lock(write_f, timeout=5)
                                try:
                                    json.dump(tokens, write_f, indent=2, ensure_ascii=False)
                                    write_f.flush()
                                    if hasattr(os, 'fsync'):
                                        os.fsync(write_f.fileno())
                                finally:
                                    if write_lock_acquired:
                                        release_file_lock(write_f)
                            
                            # Atomic move
                            if os.path.exists(token_file):
                                os.remove(token_file)
                            os.rename(temp_file, token_file)
                            
                            # Clean up backup
                            if os.path.exists(backup_file):
                                os.remove(backup_file)
                            
                            logger.info("✅ Ultra-aggressive token refresh successful")
                            return True
                            
                        except Exception as write_error:
                            logger.error(f"❌ Failed to save refreshed tokens: {write_error}")
                            
                            # Rollback on error
                            try:
                                if os.path.exists(temp_file):
                                    os.remove(temp_file)
                                if os.path.exists(backup_file):
                                    if os.path.exists(token_file):
                                        os.remove(token_file)
                                    os.rename(backup_file, token_file)
                                    logger.info("🔄 Rolled back to previous token file")
                            except Exception as rollback_error:
                                logger.error(f"❌ Rollback failed: {rollback_error}")
                            
                            return False
                            
                    elif response.status_code == 400:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('error', 'Bad request')
                            error_desc = error_data.get('error_description', '')
                            logger.error(f"❌ Bad request - refresh token invalid/expired: {error_msg} - {error_desc}")
                        except:
                            logger.error("❌ Bad request - refresh token invalid/expired")
                        return False
                        
                    elif response.status_code == 401:
                        logger.error("❌ Unauthorized - refresh token expired or invalid")
                        return False
                    elif response.status_code == 429:
                        logger.error("❌ Rate limited - too many refresh requests")
                        return False
                    elif response.status_code == 503:
                        logger.error("❌ Service unavailable - G-Portal servers may be down")
                        return False
                    else:
                        logger.error(f"❌ HTTP error {response.status_code}: {response.text[:200]}")
                        return False
                        
                except requests.exceptions.Timeout:
                    logger.error("❌ Request timeout during ultra-aggressive token refresh")
                    return False
                except requests.exceptions.ConnectionError:
                    logger.error("❌ Connection error during ultra-aggressive token refresh")
                    return False
                except requests.exceptions.RequestException as e:
                    logger.error(f"❌ Request error during ultra-aggressive token refresh: {e}")
                    return False
                except Exception as e:
                    logger.error(f"❌ Unexpected error during ultra-aggressive token refresh: {e}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Error in ultra-aggressive token refresh process: {e}")
            return False
    finally:
        # Always clear priority flag
        _set_token_operation_priority(False)

def _set_token_operation_priority(enabled):
    """
    Set priority flag for token operations to bypass rate limiting
    
    Args:
        enabled (bool): Whether to enable priority mode
    """
    try:
        # Create/update priority flag file for rate limiter coordination
        priority_file = '.token_priority'
        if enabled:
            with open(priority_file, 'w') as f:
                f.write(str(time.time()))
            logger.debug("🚀 Token operation priority enabled")
        else:
            if os.path.exists(priority_file):
                os.remove(priority_file)
            logger.debug("🔄 Token operation priority disabled")
    except Exception as e:
        logger.debug(f"⚠️ Error setting token priority: {e}")

def is_token_operation_priority():
    """
    Check if token operations should get priority
    
    Returns:
        bool: True if token operations should bypass rate limiting
    """
    try:
        priority_file = '.token_priority'
        if os.path.exists(priority_file):
            with open(priority_file, 'r') as f:
                timestamp = float(f.read().strip())
            # Priority expires after 60 seconds
            if time.time() - timestamp < 60:
                return True
            else:
                os.remove(priority_file)
        return False
    except:
        return False

def is_valid_jwt_token(token):
    """
    ✅ ENHANCED: JWT-compatible token validation
    
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
    
    # JWT tokens typically have dots (.) separating header, payload, signature
    # OAuth bearer tokens may not have dots but should still be valid
    # Both patterns are acceptable
    
    return True

def save_token(tokens, username='unknown'):
    """
    ✅ ENHANCED: Save tokens with comprehensive validation
    
    Args:
        tokens (dict): Token data from G-Portal API
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
        
        # Handle different token data formats
        if 'access_token_exp' in tokens and 'refresh_token_exp' in tokens:
            # Already processed token structure
            session_data = dict(tokens)
            session_data['username'] = username
        else:
            # Raw API response format
            if 'access_token' not in tokens or 'refresh_token' not in tokens:
                logger.error("❌ Missing required tokens")
                return False
            
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
                'access_token': access_token,
                'refresh_token': refresh_token,
                'access_token_exp': int(current_time + expires_in),
                'refresh_token_exp': int(current_time + refresh_expires_in),
                'timestamp': datetime.now().isoformat(),
                'username': username.strip() if username else 'unknown',
                'expires_in': expires_in,
                'refresh_expires_in': refresh_expires_in,
                'saved_at': datetime.now().isoformat(),
                'token_version': '2.2',
                'ultra_aggressive_mode': True,  # Flag for monitoring
                'buffer_time_used': 30  # Track buffer time used
            }
        
        # Atomic file write with backup
        temp_file = token_file + '.tmp'
        backup_file = token_file + '.backup'
        
        try:
            # Create backup if file exists
            if os.path.exists(token_file):
                import shutil
                shutil.copy2(token_file, backup_file)
            
            # Write to temp file
            with open(temp_file, 'w', encoding='utf-8') as f:
                lock_acquired = acquire_file_lock(f, timeout=5)
                try:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    if hasattr(os, 'fsync'):
                        os.fsync(f.fileno())
                finally:
                    if lock_acquired:
                        release_file_lock(f)
            
            # Atomic move
            if os.path.exists(token_file):
                os.remove(token_file)
            os.rename(temp_file, token_file)
            
            # Clean up backup
            if os.path.exists(backup_file):
                os.remove(backup_file)
            
            logger.info(f"✅ Token saved successfully for {username} (ultra-aggressive mode)")
            return True
            
        except Exception as e:
            # Rollback on error
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                if os.path.exists(backup_file) and not os.path.exists(token_file):
                    os.rename(backup_file, token_file)
            except:
                pass
            raise e
        
    except Exception as e:
        logger.error(f"❌ Error saving token: {e}")
        return False

# ================================================================
# TOKEN HEALTH MONITORING (ENHANCED)
# ================================================================

def monitor_token_health():
    """Ultra-aggressive token health monitoring"""
    try:
        token_file = 'gp-session.json'
        current_time = time.time()
        
        health_status = {
            'healthy': False,
            'status': 'unknown',
            'action': 'check_system',
            'message': 'Token status unknown',
            'details': {},
            'recommendations': [],
            'timestamp': datetime.now().isoformat(),
            'ultra_aggressive_mode': True
        }
        
        if not os.path.exists(token_file):
            health_status.update({
                'status': 'missing',
                'action': 'login_required',
                'message': 'No token file found - login required',
                'details': {'file_exists': False},
                'recommendations': ['Login with G-Portal credentials']
            })
            return health_status
        
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            health_status.update({
                'status': 'corrupted',
                'action': 'login_required',
                'message': f'Token file corrupted: {e}',
                'details': {'file_exists': True, 'valid_json': False},
                'recommendations': ['Delete corrupted token file', 'Login again']
            })
            return health_status
        
        if not isinstance(data, dict):
            health_status.update({
                'status': 'invalid_format',
                'action': 'login_required',
                'message': 'Token file has invalid format',
                'details': {'file_exists': True, 'valid_json': True, 'valid_structure': False},
                'recommendations': ['Delete invalid token file', 'Login again']
            })
            return health_status
        
        # Get token information
        access_token = data.get('access_token', '').strip()
        refresh_token = data.get('refresh_token', '').strip()
        access_exp = data.get('access_token_exp', 0)
        refresh_exp = data.get('refresh_token_exp', 0)
        
        # Calculate time remaining
        access_time_left = max(0, access_exp - current_time) if access_exp else 0
        refresh_time_left = max(0, refresh_exp - current_time) if refresh_exp else 0
        
        # Enhanced validation with JWT token support
        access_valid = is_valid_jwt_token(access_token)
        refresh_valid = is_valid_jwt_token(refresh_token)
        
        details = {
            'file_exists': True,
            'valid_json': True,
            'valid_structure': True,
            'has_access_token': bool(access_token),
            'has_refresh_token': bool(refresh_token),
            'access_token_valid_format': access_valid,
            'refresh_token_valid_format': refresh_valid,
            'access_time_left_seconds': access_time_left,
            'refresh_time_left_seconds': refresh_time_left,
            'access_expires_at': datetime.fromtimestamp(access_exp).isoformat() if access_exp else None,
            'refresh_expires_at': datetime.fromtimestamp(refresh_exp).isoformat() if refresh_exp else None,
            'ultra_aggressive_buffer': 30,
            'ultra_aggressive_mode': data.get('ultra_aggressive_mode', False)
        }
        
        # Determine health status with ultra-aggressive thresholds
        recommendations = []
        
        if not access_valid:
            health_status.update({
                'status': 'invalid_access_token',
                'action': 'login_required',
                'message': 'Access token is invalid or malformed',
                'details': details
            })
            recommendations.extend(['Login again', 'Check token file integrity'])
            
        elif not refresh_valid:
            health_status.update({
                'status': 'invalid_refresh_token',
                'action': 'login_required',
                'message': 'Refresh token is invalid or malformed',
                'details': details
            })
            recommendations.extend(['Login again', 'Check token file integrity'])
            
        elif refresh_time_left <= 0:
            health_status.update({
                'status': 'refresh_expired',
                'action': 'login_required',
                'message': 'Refresh token has expired - re-login required',
                'details': details
            })
            recommendations.extend(['Login with G-Portal credentials'])
            
        elif access_time_left <= 0:
            if refresh_time_left > 300:  # 5 minutes
                health_status.update({
                    'healthy': False,
                    'status': 'expired_refreshable',
                    'action': 'refresh_now',
                    'message': 'Access token expired but refresh possible',
                    'details': details
                })
                recommendations.extend(['Refresh access token immediately'])
            else:
                health_status.update({
                    'status': 'refresh_expiring_soon',
                    'action': 'login_required',
                    'message': 'Both tokens expiring soon - re-login recommended',
                    'details': details
                })
                recommendations.extend(['Login again before tokens expire'])
                
        elif access_time_left < 120:  # Ultra-aggressive: warn at 2 minutes instead of 10
            health_status.update({
                'healthy': False,
                'status': 'expiring_very_soon',
                'action': 'refresh_immediately',
                'message': f'ULTRA-AGGRESSIVE: Access token expires in {int(access_time_left)} seconds',
                'details': details
            })
            recommendations.extend(['Refresh token immediately'])
            
        else:
            health_status.update({
                'healthy': True,
                'status': 'healthy',
                'action': 'none',
                'message': f'Tokens healthy - {int(access_time_left)} seconds remaining (ultra-aggressive monitoring)',
                'details': details
            })
        
        health_status['recommendations'] = recommendations
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Error monitoring token health: {e}")
        return {
            'healthy': False,
            'status': 'error',
            'action': 'check_system',
            'message': f'Error checking token health: {e}',
            'details': {},
            'recommendations': ['Check logs for errors'],
            'timestamp': datetime.now().isoformat(),
            'ultra_aggressive_mode': True
        }

def validate_token_file():
    """Ultra-aggressive token file validation"""
    token_file = 'gp-session.json'
    
    result = {
        'valid': False,
        'exists': False,
        'has_access_token': False,
        'has_refresh_token': False,
        'access_token_valid': False,
        'refresh_token_valid': False,
        'access_token_format_valid': False,
        'refresh_token_format_valid': False,
        'time_left': 0,
        'refresh_time_left': 0,
        'issues': [],
        'expires_at': None,
        'refresh_expires_at': None,
        'ultra_aggressive_buffer': 30
    }
    
    try:
        if not os.path.exists(token_file):
            result['issues'].append('Token file does not exist')
            return result
            
        result['exists'] = True
        
        with open(token_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, dict):
            result['issues'].append('Token file is not a valid JSON object')
            return result
            
        current_time = time.time()
        
        # Check access token
        access_token = data.get('access_token', '').strip()
        if access_token:
            result['has_access_token'] = True
            
            if is_valid_jwt_token(access_token):
                result['access_token_format_valid'] = True
            else:
                result['issues'].append('Access token format invalid')
            
            # Check expiration with ultra-aggressive buffer
            token_exp = data.get('access_token_exp', 0)
            if token_exp:
                try:
                    token_exp = float(token_exp)
                    time_left = token_exp - current_time
                    result['time_left'] = max(0, time_left)
                    result['expires_at'] = datetime.fromtimestamp(token_exp).isoformat()
                    result['access_token_valid'] = time_left > 30  # Ultra-aggressive: 30 second buffer
                except (ValueError, TypeError):
                    result['issues'].append('Invalid access token expiration format')
            else:
                result['issues'].append('No access token expiration time')
        else:
            result['issues'].append('No access token in file')
            
        # Check refresh token
        refresh_token = data.get('refresh_token', '').strip()
        if refresh_token:
            result['has_refresh_token'] = True
            
            if is_valid_jwt_token(refresh_token):
                result['refresh_token_format_valid'] = True
            else:
                result['issues'].append('Refresh token format invalid')
            
            # Check refresh token expiration
            refresh_exp = data.get('refresh_token_exp', 0)
            if refresh_exp:
                try:
                    refresh_exp = float(refresh_exp)
                    refresh_time_left = refresh_exp - current_time
                    result['refresh_time_left'] = max(0, refresh_time_left)
                    result['refresh_expires_at'] = datetime.fromtimestamp(refresh_exp).isoformat()
                    result['refresh_token_valid'] = refresh_time_left > 60  # 1 minute buffer for refresh token
                except (ValueError, TypeError):
                    result['issues'].append('Invalid refresh token expiration format')
            else:
                result['issues'].append('No refresh token expiration time')
        else:
            result['issues'].append('No refresh token in file')
            
        # Overall validity with ultra-aggressive criteria
        result['valid'] = (
            result['has_access_token'] and 
            result['has_refresh_token'] and
            result['access_token_format_valid'] and
            result['refresh_token_format_valid'] and
            (result['access_token_valid'] or result['refresh_token_valid'])
        )
        
        return result
        
    except json.JSONDecodeError as e:
        result['issues'].append(f'Invalid JSON: {e}')
        return result
    except Exception as e:
        result['issues'].append(f'Validation error: {e}')
        return result

# ================================================================
# CONSOLE AND COMMAND PARSING FUNCTIONS
# ================================================================

def parse_console_response(response_data):
    """Parse G-Portal GraphQL response for console commands"""
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
    """Enhanced message classification"""
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
    """Enhanced icon mapping"""
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
    """Enhanced console message formatting"""
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
    """Enhanced command formatting for G-Portal console"""
    if not command:
        return ''
    
    command = command.strip()
    
    # Handle 'say' commands with proper quoting
    if command.startswith('say ') and not command.startswith('global.say'):
        message = command[4:].strip()
        return f'global.say "{message}"'
    
    return command

# ================================================================
# VALIDATION FUNCTIONS
# ================================================================

def validate_server_id(server_id):
    """Enhanced server ID validation"""
    if not server_id:
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
    """Enhanced region validation"""
    if not region:
        return False
    
    valid_regions = ['US', 'EU', 'AS', 'AU', 'us', 'eu', 'as', 'au']
    return str(region).strip() in valid_regions

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
    return bool(re.match(pattern, email.strip()))

def validate_url(url):
    """Basic URL validation"""
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    return url.startswith(('http://', 'https://')) and len(url) > 10

# ================================================================
# DATA CREATION AND UTILITY FUNCTIONS
# ================================================================

def create_server_data(server_id, name, region='US', server_type='Standard'):
    """Enhanced server data structure creation"""
    return {
        'serverId': str(server_id),
        'serverName': str(name),
        'serverRegion': str(region).upper(),
        'serverType': str(server_type),
        'status': 'unknown',
        'isActive': True,
        'isFavorite': False,
        'addedAt': datetime.now().isoformat(),
        'lastChecked': None,
        'playerCount': None,
        'maxPlayers': None
    }

def get_countdown_announcements(minutes_left):
    """Enhanced countdown announcements"""
    announcements = []
    
    if minutes_left == 30:
        announcements.append("🎯 Event starts in 30 minutes! Get ready!")
    elif minutes_left == 15:
        announcements.append("⏰ Event starts in 15 minutes! Final preparations!")
    elif minutes_left == 10:
        announcements.append("🚨 Event starts in 10 minutes!")
    elif minutes_left == 5:
        announcements.append("🔥 Event starts in 5 minutes! Last chance to prepare!")
    elif minutes_left == 3:
        announcements.append("⚡ Event starts in 3 minutes!")
    elif minutes_left == 2:
        announcements.append("⚡ Event starts in 2 minutes!")
    elif minutes_left == 1:
        announcements.append("🚀 Event starts in 1 minute! Get ready!")
    
    return announcements

# ================================================================
# STRING AND FORMAT UTILITY FUNCTIONS
# ================================================================

def escape_html(text):
    """Enhanced HTML escaping"""
    if not text:
        return ''
    
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;')
            .replace('/', '&#x2F;'))

def safe_int(value, default=0):
    """Enhanced safe integer conversion"""
    try:
        if isinstance(value, (int, float)):
            return int(value)
        elif isinstance(value, str):
            if not value.strip():
                return default
            cleaned = value.strip().replace(',', '').replace(' ', '')
            return int(float(cleaned))
        else:
            return default
    except (ValueError, TypeError, AttributeError):
        return default

def safe_float(value, default=0.0):
    """Enhanced safe float conversion"""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            if not value.strip():
                return default
            cleaned = value.strip().replace(',', '').replace(' ', '')
            return float(cleaned)
        else:
            return default
    except (ValueError, TypeError, AttributeError):
        return default

def format_timestamp(timestamp):
    """Enhanced timestamp formatting"""
    if not timestamp:
        return ''
    
    try:
        if isinstance(timestamp, str):
            # Handle different timestamp formats
            if 'T' in timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        else:
            dt = timestamp
        
        return dt.strftime('%H:%M:%S')
    except:
        return str(timestamp)

def sanitize_filename(filename):
    """Sanitize filename for safe filesystem use"""
    if not filename:
        return 'unknown'
    
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    return filename.strip()

def generate_random_string(length=8):
    """Generate random string"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def truncate_string(text, max_length=100, suffix='...'):
    """Truncate string to maximum length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

# ================================================================
# STATUS AND DISPLAY FUNCTIONS
# ================================================================

def get_status_class(status):
    """Enhanced status CSS classes"""
    status_classes = {
        'online': 'bg-green-800 text-green-200 border-green-600',
        'offline': 'bg-red-800 text-red-200 border-red-600',
        'unknown': 'bg-gray-700 text-gray-300 border-gray-600',
        'connecting': 'bg-yellow-800 text-yellow-200 border-yellow-600',
        'error': 'bg-red-900 text-red-100 border-red-700'
    }
    return status_classes.get(status, 'bg-gray-700 text-gray-300 border-gray-600')

def get_status_text(status):
    """Enhanced status text"""
    status_text = {
        'online': '🟢 Online',
        'offline': '🔴 Offline',
        'unknown': '⚪ Unknown',
        'connecting': '🟡 Connecting',
        'error': '❌ Error'
    }
    return status_text.get(status, '⚪ Unknown')

# ================================================================
# COLLECTION AND DATA UTILITY FUNCTIONS
# ================================================================

def deep_get(dictionary, keys, default=None):
    """Get nested dictionary value safely"""
    for key in keys:
        if isinstance(dictionary, dict) and key in dictionary:
            dictionary = dictionary[key]
        else:
            return default
    return dictionary

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

def merge_dicts(*dicts):
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result

def chunk_list(lst, chunk_size):
    """Split list into chunks"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def remove_duplicates(lst, key=None):
    """Remove duplicates from list"""
    if key:
        seen = set()
        result = []
        for item in lst:
            k = key(item)
            if k not in seen:
                seen.add(k)
                result.append(item)
        return result
    else:
        return list(dict.fromkeys(lst))

# ================================================================
# CALCULATION AND FORMATTING UTILITIES
# ================================================================

def calculate_percentage(part, whole, decimal_places=1):
    """Calculate percentage safely"""
    try:
        if whole == 0:
            return 0.0
        return round((part / whole) * 100, decimal_places)
    except (TypeError, ZeroDivisionError):
        return 0.0

def format_bytes(bytes_val):
    """Format bytes to human readable format"""
    try:
        bytes_val = float(bytes_val)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"
    except (TypeError, ValueError):
        return "0 B"

def format_duration(seconds):
    """Format seconds to human readable duration"""
    try:
        seconds = int(seconds)
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs}s"
    except (TypeError, ValueError):
        return "0s"
