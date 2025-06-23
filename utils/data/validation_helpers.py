"""
Validation helper functions for GUST Bot Enhanced (ENHANCED VERSION)
====================================================================
✅ ENHANCED: Added session validation and authentication integration
✅ ENHANCED: Token validation support
✅ ENHANCED: Better error messages and logging
✅ EXISTING: All original validation functions maintained
✅ NEW: Session authentication validation functions

This module provides standardized validation functions for common
input types and patterns used throughout the application.
"""

# Standard library imports
import logging
import re

# Third-party imports
from typing import Dict, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)

class ValidationHelper:
    """Centralized validation functions with consistent error handling"""
    
    # Common regex patterns
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
    SERVER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,50}$')
    NICKNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\s]{2,50}$')
    
    # ✅ NEW: Additional patterns for enhanced validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    TOKEN_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{32,}$')
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate G-Portal username format
        
        Args:
            username: Username string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username is required"
        
        if not isinstance(username, str):
            return False, "Username must be a string"
        
        username = username.strip()
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(username) > 30:
            return False, "Username must be no more than 30 characters"
        
        if not ValidationHelper.USERNAME_PATTERN.match(username):
            return False, "Username can only contain letters, numbers, underscores, and hyphens"
        
        return True, ""
    
    @staticmethod
    def validate_server_id(server_id: str) -> Tuple[bool, str]:
        """
        Validate server ID format
        
        Args:
            server_id: Server ID string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not server_id:
            return False, "Server ID is required"
        
        if not isinstance(server_id, str):
            return False, "Server ID must be a string"
        
        server_id = server_id.strip()
        
        if len(server_id) < 1:
            return False, "Server ID cannot be empty"
        
        if len(server_id) > 50:
            return False, "Server ID must be no more than 50 characters"
        
        if not ValidationHelper.SERVER_ID_PATTERN.match(server_id):
            return False, "Server ID can only contain letters, numbers, underscores, and hyphens"
        
        return True, ""
    
    @staticmethod
    def validate_nickname(nickname: str) -> Tuple[bool, str]:
        """
        Validate user nickname format
        
        Args:
            nickname: Nickname string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not nickname:
            return False, "Nickname is required"
        
        if not isinstance(nickname, str):
            return False, "Nickname must be a string"
        
        nickname = nickname.strip()
        
        if len(nickname) < 2:
            return False, "Nickname must be at least 2 characters"
        
        if len(nickname) > 50:
            return False, "Nickname must be no more than 50 characters"
        
        if not ValidationHelper.NICKNAME_PATTERN.match(nickname):
            return False, "Nickname can only contain letters, numbers, spaces, underscores, and hyphens"
        
        return True, ""
    
    @staticmethod
    def validate_balance(balance: Union[int, float, str]) -> Tuple[bool, str, float]:
        """
        Validate and normalize balance value
        
        Args:
            balance: Balance value to validate
            
        Returns:
            Tuple of (is_valid, error_message, normalized_value)
        """
        try:
            if isinstance(balance, str):
                balance = balance.strip()
                if not balance:
                    return False, "Balance cannot be empty", 0.0
                balance = float(balance)
            elif isinstance(balance, int):
                balance = float(balance)
            elif not isinstance(balance, float):
                return False, "Balance must be a number", 0.0
            
            if balance < 0:
                return False, "Balance cannot be negative", 0.0
            
            if balance > 999999999:  # 1 billion limit
                return False, "Balance too large (max: 999,999,999)", 0.0
            
            # Round to 2 decimal places
            balance = round(balance, 2)
            
            return True, "", balance
            
        except (ValueError, TypeError) as e:
            return False, f"Invalid balance format: {str(e)}", 0.0
    
    @staticmethod
    def validate_internal_id(internal_id: Union[int, str]) -> Tuple[bool, str, int]:
        """
        Validate user internal ID (1-9 digits)
        
        Args:
            internal_id: Internal ID to validate
            
        Returns:
            Tuple of (is_valid, error_message, normalized_value)
        """
        try:
            if isinstance(internal_id, str):
                internal_id = internal_id.strip()
                if not internal_id.isdigit():
                    return False, "Internal ID must contain only digits", 0
                internal_id = int(internal_id)
            elif not isinstance(internal_id, int):
                return False, "Internal ID must be a number", 0
            
            if internal_id < 1:
                return False, "Internal ID must be at least 1", 0
            
            if internal_id > 999999999:  # 9 digits max
                return False, "Internal ID must be no more than 9 digits", 0
            
            return True, "", internal_id
            
        except (ValueError, TypeError) as e:
            return False, f"Invalid internal ID format: {str(e)}", 0
    
    @staticmethod
    def validate_clan_tag(clan_tag: Optional[str]) -> Tuple[bool, str, str]:
        """
        Validate clan tag format (optional field)
        
        Args:
            clan_tag: Clan tag to validate (can be None/empty)
            
        Returns:
            Tuple of (is_valid, error_message, normalized_value)
        """
        if not clan_tag:
            return True, "", ""  # Clan tag is optional
        
        if not isinstance(clan_tag, str):
            return False, "Clan tag must be a string", ""
        
        clan_tag = clan_tag.strip().upper()
        
        if len(clan_tag) < 2:
            return False, "Clan tag must be at least 2 characters", ""
        
        if len(clan_tag) > 10:
            return False, "Clan tag must be no more than 10 characters", ""
        
        if not re.match(r'^[A-Z0-9]+$', clan_tag):
            return False, "Clan tag can only contain uppercase letters and numbers", ""
        
        return True, "", clan_tag
    
    @staticmethod
    def validate_request_data(data: Dict, required_fields: List[str]) -> Tuple[bool, str, Dict]:
        """
        Validate request data has required fields
        
        Args:
            data: Request data dictionary
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, error_message, cleaned_data)
        """
        if not isinstance(data, dict):
            return False, "Request data must be a dictionary", {}
        
        cleaned_data = {}
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            else:
                # Basic cleaning - strip strings
                value = data[field]
                if isinstance(value, str):
                    value = value.strip()
                cleaned_data[field] = value
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}", {}
        
        return True, "", cleaned_data
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """
        Sanitize string input for safe storage and display
        
        Args:
            value: String value to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return str(value)
        
        # Strip whitespace
        value = value.strip()
        
        # Remove potentially dangerous characters
        value = re.sub(r'[<>"\']', '', value)
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    # ================================================================
    # ✅ NEW: SESSION AND AUTHENTICATION VALIDATION
    # ================================================================
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate email format
        ✅ NEW: Email validation for G-Portal accounts
        
        Args:
            email: Email string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        if not isinstance(email, str):
            return False, "Email must be a string"
        
        email = email.strip().lower()
        
        if len(email) > 254:  # RFC 5321 limit
            return False, "Email too long (max: 254 characters)"
        
        if not ValidationHelper.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_password(password: str, min_length: int = 6) -> Tuple[bool, str]:
        """
        Validate password strength
        ✅ NEW: Password validation
        
        Args:
            password: Password to validate
            min_length: Minimum password length
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        if not isinstance(password, str):
            return False, "Password must be a string"
        
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters"
        
        if len(password) > 128:
            return False, "Password too long (max: 128 characters)"
        
        # Could add more strength requirements here
        return True, ""
    
    @staticmethod
    def validate_session_data(session_data: Dict) -> Tuple[bool, str, Dict]:
        """
        Validate Flask session data structure
        ✅ NEW: Session validation
        
        Args:
            session_data: Session dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message, validated_data)
        """
        if not isinstance(session_data, dict):
            return False, "Session data must be a dictionary", {}
        
        validated = {}
        issues = []
        
        # Validate username if present
        if 'username' in session_data:
            username = session_data['username']
            if username and isinstance(username, str):
                validated['username'] = username.strip()
            else:
                issues.append("Invalid username in session")
        
        # Validate boolean flags
        for flag in ['logged_in', 'demo_mode']:
            if flag in session_data:
                value = session_data[flag]
                if isinstance(value, bool):
                    validated[flag] = value
                else:
                    # Try to convert
                    try:
                        validated[flag] = bool(value)
                    except:
                        issues.append(f"Invalid {flag} flag in session")
        
        # Validate user level
        if 'user_level' in session_data:
            user_level = session_data['user_level']
            if user_level in ['admin', 'user', 'moderator']:
                validated['user_level'] = user_level
            else:
                issues.append("Invalid user_level in session")
        
        if issues:
            return False, "; ".join(issues), {}
        
        return True, "", validated
    
    @staticmethod
    def validate_auth_status(auth_data: Dict) -> Tuple[bool, str]:
        """
        Validate authentication status data
        ✅ NEW: Auth status validation
        
        Args:
            auth_data: Authentication status dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ['logged_in', 'demo_mode', 'username']
        
        for field in required_fields:
            if field not in auth_data:
                return False, f"Missing required auth field: {field}"
        
        # Validate boolean fields
        for bool_field in ['logged_in', 'demo_mode']:
            if not isinstance(auth_data[bool_field], bool):
                return False, f"Auth field {bool_field} must be boolean"
        
        # Validate username
        username = auth_data['username']
        if not isinstance(username, str) or not username.strip():
            return False, "Username must be a non-empty string"
        
        # Check for logical consistency
        if auth_data['logged_in'] and not auth_data['username'].strip():
            return False, "Cannot be logged in without username"
        
        return True, ""

# ================================================================
# ✅ NEW: SESSION MANAGEMENT FUNCTIONS
# ================================================================

def validate_user_session():
    """
    Validate current Flask session
    ✅ NEW: Current session validation
    
    Returns:
        Tuple of (is_valid, auth_status, issues)
    """
    try:
        from flask import session
        
        # Get current session data
        session_dict = dict(session)
        
        # Validate session structure
        is_valid, error, validated = ValidationHelper.validate_session_data(session_dict)
        
        if not is_valid:
            return False, {}, [error]
        
        # Build auth status
        auth_status = {
            'logged_in': validated.get('logged_in', False),
            'demo_mode': validated.get('demo_mode', True),
            'username': validated.get('username', 'Anonymous'),
            'user_level': validated.get('user_level', 'user')
        }
        
        # Additional validation
        auth_valid, auth_error = ValidationHelper.validate_auth_status(auth_status)
        
        if not auth_valid:
            return False, auth_status, [auth_error]
        
        return True, auth_status, []
        
    except ImportError:
        return False, {}, ["Flask not available"]
    except Exception as e:
        return False, {}, [f"Session validation error: {str(e)}"]

def validate_token_request_data(data: Dict) -> Tuple[bool, str, Dict]:
    """
    Validate token-related request data
    ✅ NEW: Token request validation
    
    Args:
        data: Request data for token operations
        
    Returns:
        Tuple of (is_valid, error_message, cleaned_data)
    """
    if not isinstance(data, dict):
        return False, "Request data must be a dictionary", {}
    
    cleaned = {}
    
    # Validate refresh_token if present
    if 'refresh_token' in data:
        refresh_token = data['refresh_token']
        if not isinstance(refresh_token, str) or not refresh_token.strip():
            return False, "Refresh token must be a non-empty string", {}
        
        if not ValidationHelper.TOKEN_PATTERN.match(refresh_token.strip()):
            return False, "Invalid refresh token format", {}
        
        cleaned['refresh_token'] = refresh_token.strip()
    
    # Validate access_token if present
    if 'access_token' in data:
        access_token = data['access_token']
        if not isinstance(access_token, str) or not access_token.strip():
            return False, "Access token must be a non-empty string", {}
        
        if not ValidationHelper.TOKEN_PATTERN.match(access_token.strip()):
            return False, "Invalid access token format", {}
        
        cleaned['access_token'] = access_token.strip()
    
    # Validate expiration times
    for exp_field in ['expires_in', 'refresh_expires_in', 'access_token_exp', 'refresh_token_exp']:
        if exp_field in data:
            try:
                exp_value = int(data[exp_field])
                if exp_value < 0:
                    return False, f"{exp_field} cannot be negative", {}
                cleaned[exp_field] = exp_value
            except (ValueError, TypeError):
                return False, f"Invalid {exp_field} format", {}
    
    return True, "", cleaned

# ================================================================
# EXISTING UTILITY FUNCTIONS (ENHANCED)
# ================================================================

def validate_user_registration_data(data: Dict) -> Tuple[bool, str, Dict]:
    """
    Validate user registration request data
    ✅ ENHANCED: Better validation and error messages
    """
    required_fields = ['userId', 'nickname', 'internalId']
    
    is_valid, error, cleaned_data = ValidationHelper.validate_request_data(data, required_fields)
    if not is_valid:
        return False, error, {}
    
    # Validate individual fields with better error context
    username_valid, username_error = ValidationHelper.validate_username(cleaned_data['userId'])
    if not username_valid:
        return False, f"Invalid username: {username_error}", {}
    
    nickname_valid, nickname_error = ValidationHelper.validate_nickname(cleaned_data['nickname'])
    if not nickname_valid:
        return False, f"Invalid nickname: {nickname_error}", {}
    
    id_valid, id_error, normalized_id = ValidationHelper.validate_internal_id(cleaned_data['internalId'])
    if not id_valid:
        return False, f"Invalid internal ID: {id_error}", {}
    
    cleaned_data['internalId'] = normalized_id
    
    # ✅ NEW: Additional optional field validation
    if 'email' in data:
        email_valid, email_error = ValidationHelper.validate_email(data['email'])
        if not email_valid:
            return False, f"Invalid email: {email_error}", {}
        cleaned_data['email'] = data['email'].strip().lower()
    
    return True, "", cleaned_data

def validate_server_data(data: Dict) -> Tuple[bool, str, Dict]:
    """
    Validate server-related request data
    ✅ ENHANCED: More comprehensive server validation
    """
    cleaned_data = {}
    
    # Validate server ID if present
    if 'serverId' in data:
        server_valid, server_error = ValidationHelper.validate_server_id(data['serverId'])
        if not server_valid:
            return False, f"Invalid server ID: {server_error}", {}
        cleaned_data['serverId'] = data['serverId'].strip()
    
    # ✅ NEW: Validate server name
    if 'serverName' in data:
        server_name = data['serverName']
        if isinstance(server_name, str) and server_name.strip():
            if len(server_name.strip()) > 100:
                return False, "Server name too long (max: 100 characters)", {}
            cleaned_data['serverName'] = server_name.strip()
        else:
            return False, "Server name must be a non-empty string", {}
    
    # ✅ NEW: Validate server region
    if 'serverRegion' in data:
        region = data['serverRegion']
        if isinstance(region, str) and region.strip().upper() in ['US', 'EU', 'AS']:
            cleaned_data['serverRegion'] = region.strip().upper()
        else:
            return False, "Server region must be one of: US, EU, AS", {}
    
    return True, "", cleaned_data

def validate_auth_request_data(data: Dict) -> Tuple[bool, str, Dict]:
    """
    Validate authentication request data
    ✅ NEW: Authentication request validation
    
    Args:
        data: Authentication request data
        
    Returns:
        Tuple of (is_valid, error_message, cleaned_data)
    """
    required_fields = ['username', 'password']
    
    is_valid, error, cleaned_data = ValidationHelper.validate_request_data(data, required_fields)
    if not is_valid:
        return False, error, {}
    
    # Validate username (could be email or username)
    username = cleaned_data['username']
    
    # Try email validation first
    email_valid, _ = ValidationHelper.validate_email(username)
    if email_valid:
        cleaned_data['username'] = username.lower()
    else:
        # Try username validation
        username_valid, username_error = ValidationHelper.validate_username(username)
        if not username_valid:
            return False, f"Invalid username/email: {username_error}", {}
    
    # Validate password
    password_valid, password_error = ValidationHelper.validate_password(cleaned_data['password'])
    if not password_valid:
        return False, f"Invalid password: {password_error}", {}
    
    return True, "", cleaned_data

# Export validation classes and functions
__all__ = [
    # Main validation class
    'ValidationHelper',
    
    # Existing functions (enhanced)
    'validate_user_registration_data', 
    'validate_server_data',
    
    # New session and auth functions
    'validate_user_session',
    'validate_token_request_data',
    'validate_auth_request_data'
]