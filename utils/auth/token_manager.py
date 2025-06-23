"""
Basic Token Manager
Provides basic token operations
"""

import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class TokenManager:
    """Basic token management operations"""
    
    def __init__(self):
        self.token_cache = {}
    
    def get_token_expiry_info(self, token_data):
        """Get basic token expiry information"""
        try:
            if not token_data or not isinstance(token_data, dict):
                return None
            
            auth_type = token_data.get('auth_type', 'oauth')
            current_time = time.time()
            
            if auth_type == 'oauth':
                expires_at = token_data.get('access_token_exp', 0)
            else:
                expires_at = token_data.get('expires_at', 0)
            
            return {
                'expires_at': expires_at,
                'expires_in': max(0, expires_at - current_time),
                'is_expired': current_time >= expires_at,
                'expires_soon': (expires_at - current_time) < 300,
                'auth_type': auth_type
            }
        except Exception as e:
            logger.error(f"Error getting token expiry info: {e}")
            return None

# Global instance
token_manager = TokenManager()
