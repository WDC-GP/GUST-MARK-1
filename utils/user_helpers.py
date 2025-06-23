"""
GUST Bot Utils - User Helpers Compatibility Shim
===============================================
This file provides backwards compatibility by importing all functions
from the new organized database/user_helpers.py location.
"""

# Import everything from the new database location
try:
    from .database.user_helpers import *
    print("✅ User helpers loaded from database/user_helpers.py")
except ImportError as e:
    print(f"❌ Failed to import from database/user_helpers: {e}")
    
    # Minimal fallback functions
    def get_user_profile(user_id):
        """Fallback user profile function"""
        return {"user_id": user_id, "status": "fallback"}
    
    def create_user_profile(user_data):
        """Fallback user creation function"""
        return {"status": "fallback", "data": user_data}
    
    print("⚠️ Using minimal user helpers fallback functions")

# Ensure backwards compatibility
__all__ = [
    'get_user_profile', 'create_user_profile', 'update_user_profile',
    'delete_user_profile', 'validate_user_data'
]
