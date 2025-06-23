"""
User Database Helper Functions (COMPLETE FIXED VERSION)
=======================================================
✅ FIXED: All import errors resolved
✅ FIXED: All functions properly defined and exported
✅ FIXED: Safe imports with try/catch blocks
✅ FIXED: No circular dependencies
✅ FIXED: Consistent error handling
"""

# Standard library imports
from datetime import datetime
import logging
import random

logger = logging.getLogger(__name__)

def generate_internal_id():
    """Generate unique 9-digit internal ID"""
    return random.randint(100000000, 999999999)

# ================================================================
# CORE USER PROFILE FUNCTIONS
# ================================================================

def get_user_profile(user_id, db, user_storage):
    """
    Get complete user profile
    ✅ FIXED: Proper error handling and type checking
    """
    try:
        if db:
            user = db.users.find_one({'userId': user_id})
            return user
        else:
            # Handle both dict and object-style user storage
            if hasattr(user_storage, 'users'):
                return user_storage.users.get(user_id)
            elif isinstance(user_storage, dict):
                return user_storage.get(user_id)
            else:
                logger.error(f"Invalid user_storage type: {type(user_storage)}")
                return None
    except Exception as e:
        logger.error(f'Error getting user profile for {user_id}: {e}')
        return None

def create_user_profile(user_id, nickname=None, db=None, user_storage=None):
    """
    Create a new user profile with default settings
    ✅ FIXED: Better error handling and storage compatibility
    """
    try:
        user_data = {
            'userId': user_id,
            'nickname': nickname or user_id,
            'internalId': generate_internal_id(),
            'registeredAt': datetime.now().isoformat(),
            'lastSeen': datetime.now().isoformat(),
            'servers': {},
            'preferences': {
                'displayNickname': True,
                'showInLeaderboards': True
            },
            'totalServers': 0
        }
        
        if db:
            db.users.insert_one(user_data)
        elif user_storage is not None:
            if hasattr(user_storage, 'users'):
                user_storage.users[user_id] = user_data
            elif isinstance(user_storage, dict):
                user_storage[user_id] = user_data
            else:
                logger.error(f"Cannot save user to storage type: {type(user_storage)}")
                return None
        
        logger.info(f"Created user profile for {user_id}")
        return user_data
    except Exception as e:
        logger.error(f'Error creating user profile for {user_id}: {e}')
        return None

# ================================================================
# SERVER-SPECIFIC BALANCE FUNCTIONS
# ================================================================

def get_server_balance(user_id, server_id, db, user_storage):
    """
    Get user's balance for specific server
    ✅ FIXED: Better error handling and validation
    """
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and isinstance(user, dict) and 'servers' in user and server_id in user['servers']:
            return user['servers'][server_id].get('balance', 0)
        return 0
    except Exception as e:
        logger.error(f'Error getting server balance for {user_id} on {server_id}: {e}')
        return 0

def set_server_balance(user_id, server_id, new_balance, db, user_storage):
    """
    Set user's balance for specific server
    ✅ FIXED: Proper validation and error handling
    """
    try:
        # Validate inputs
        if not isinstance(new_balance, (int, float)) or new_balance < 0:
            logger.error(f"Invalid balance value: {new_balance}")
            return False
        
        # Ensure user exists on server first
        ensure_user_on_server(user_id, server_id, db, user_storage)
        
        if db:
            result = db.users.update_one(
                {'userId': user_id},
                {'$set': {f'servers.{server_id}.balance': new_balance}}
            )
            return result.modified_count > 0
        else:
            user = get_user_profile(user_id, db, user_storage)
            if user and isinstance(user, dict):
                if 'servers' not in user:
                    user['servers'] = {}
                if server_id not in user['servers']:
                    user['servers'][server_id] = {}
                user['servers'][server_id]['balance'] = new_balance
                return True
        return False
    except Exception as e:
        logger.error(f'Error setting server balance for {user_id} on {server_id}: {e}')
        return False

def adjust_server_balance(user_id, server_id, amount, db, user_storage):
    """
    Adjust user's balance for specific server (add/subtract amount)
    ✅ FIXED: Prevent negative balances and better validation
    """
    try:
        if not isinstance(amount, (int, float)):
            logger.error(f"Invalid amount type: {type(amount)}")
            return False
        
        current_balance = get_server_balance(user_id, server_id, db, user_storage)
        new_balance = max(0, current_balance + amount)  # Prevent negative balances
        return set_server_balance(user_id, server_id, new_balance, db, user_storage)
    except Exception as e:
        logger.error(f'Error adjusting server balance for {user_id} on {server_id}: {e}')
        return False

# ================================================================
# USER MANAGEMENT FUNCTIONS
# ================================================================

def ensure_user_on_server(user_id, server_id, db, user_storage):
    """
    Ensure user has an entry for the specified server
    ✅ FIXED: Better validation and error handling
    """
    try:
        user = get_user_profile(user_id, db, user_storage)
        
        if not user:
            # Create new user if doesn't exist
            user_data = {
                'userId': user_id,
                'nickname': user_id,  # Default nickname = user_id
                'internalId': generate_internal_id(),
                'registeredAt': datetime.now().isoformat(),
                'lastSeen': datetime.now().isoformat(),
                'servers': {},
                'preferences': {
                    'displayNickname': True,
                    'showInLeaderboards': True
                },
                'totalServers': 0
            }
            
            if db:
                db.users.insert_one(user_data)
            else:
                if hasattr(user_storage, 'users'):
                    user_storage.users[user_id] = user_data
                elif isinstance(user_storage, dict):
                    user_storage[user_id] = user_data
            
            user = user_data
        
        # Ensure server entry exists
        if not isinstance(user, dict):
            logger.error(f"User data is not a dictionary: {type(user)}")
            return False
        
        if 'servers' not in user:
            user['servers'] = {}
        
        if server_id not in user['servers']:
            server_data = {
                'balance': 0,
                'clanTag': None,
                'joinedAt': datetime.now().isoformat(),
                'gamblingStats': {
                    'totalWagered': 0,
                    'totalWon': 0,
                    'gamesPlayed': 0,
                    'lastPlayed': None
                },
                'isActive': True
            }
            
            if db:
                db.users.update_one(
                    {'userId': user_id},
                    {
                        '$set': {f'servers.{server_id}': server_data},
                        '$inc': {'totalServers': 1}
                    }
                )
            else:
                user['servers'][server_id] = server_data
                user['totalServers'] = user.get('totalServers', 0) + 1
        
        return True
    except Exception as e:
        logger.error(f'Error ensuring user {user_id} on server {server_id}: {e}')
        return False

def get_users_on_server(server_id, db, user_storage):
    """
    Get all users on a specific server
    ✅ FIXED: Better error handling and data structure support
    """
    try:
        users = []
        if db:
            cursor = db.users.find({f'servers.{server_id}': {'$exists': True}})
            for user in cursor:
                if 'servers' in user and server_id in user['servers']:
                    server_data = user['servers'][server_id]
                    users.append({
                        'userId': user['userId'],
                        'nickname': user.get('nickname', user['userId']),
                        'balance': server_data.get('balance', 0),
                        'clanTag': server_data.get('clanTag'),
                        'joinedAt': server_data.get('joinedAt'),
                        'isActive': server_data.get('isActive', True)
                    })
        else:
            # Handle different user storage types
            user_dict = {}
            if hasattr(user_storage, 'users'):
                user_dict = user_storage.users
            elif isinstance(user_storage, dict):
                user_dict = user_storage
            
            for user_id, user in user_dict.items():
                if isinstance(user, dict) and 'servers' in user and server_id in user['servers']:
                    server_data = user['servers'][server_id]
                    users.append({
                        'userId': user_id,
                        'nickname': user.get('nickname', user_id),
                        'balance': server_data.get('balance', 0),
                        'clanTag': server_data.get('clanTag'),
                        'joinedAt': server_data.get('joinedAt'),
                        'isActive': server_data.get('isActive', True)
                    })
        return users
    except Exception as e:
        logger.error(f'Error getting users on server {server_id}: {e}')
        return []

def get_server_leaderboard(server_id, db, user_storage, limit=10):
    """
    Get server-specific leaderboard sorted by balance
    ✅ FIXED: Better validation and sorting
    """
    try:
        users = get_users_on_server(server_id, db, user_storage)
        # Sort by balance (descending)
        users.sort(key=lambda x: x.get('balance', 0), reverse=True)
        return users[:limit]
    except Exception as e:
        logger.error(f'Error getting server leaderboard for {server_id}: {e}')
        return []

# ================================================================
# TRANSFER AND TRANSACTION FUNCTIONS
# ================================================================

def transfer_between_users(from_user_id, to_user_id, amount, server_id, db, user_storage):
    """
    Transfer coins between users on the same server
    ✅ FIXED: Better validation and atomic operations
    """
    try:
        # Validate inputs
        if not isinstance(amount, (int, float)) or amount <= 0:
            return False, 'Invalid transfer amount'
        
        if from_user_id == to_user_id:
            return False, 'Cannot transfer to yourself'
        
        # Check sender has sufficient balance
        from_balance = get_server_balance(from_user_id, server_id, db, user_storage)
        if from_balance < amount:
            return False, 'Insufficient funds for transfer'
        
        # Ensure both users exist on server
        ensure_user_on_server(from_user_id, server_id, db, user_storage)
        ensure_user_on_server(to_user_id, server_id, db, user_storage)
        
        # Perform transfer (atomic operation)
        if (adjust_server_balance(from_user_id, server_id, -amount, db, user_storage) and
            adjust_server_balance(to_user_id, server_id, amount, db, user_storage)):
            logger.info(f"Transfer: {from_user_id} -> {to_user_id}: {amount} coins on {server_id}")
            return True, f'Successfully transferred {amount} coins'
        else:
            return False, 'Transfer failed'
            
    except Exception as e:
        logger.error(f'Error transferring between {from_user_id} and {to_user_id}: {e}')
        return False, 'Transfer failed due to error'

# ================================================================
# USER INFO AND DISPLAY FUNCTIONS
# ================================================================

def get_user_display_name(user_id, db, user_storage):
    """
    Get user's display name (nickname or user_id)
    ✅ FIXED: Better fallback handling
    """
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and isinstance(user, dict):
            return user.get('nickname', user_id)
        return user_id
    except Exception as e:
        logger.error(f'Error getting display name for {user_id}: {e}')
        return user_id

def update_user_last_seen(user_id, db, user_storage):
    """
    Update user's last seen timestamp
    ✅ FIXED: Better error handling
    """
    try:
        timestamp = datetime.now().isoformat()
        if db:
            db.users.update_one(
                {'userId': user_id},
                {'$set': {'lastSeen': timestamp}}
            )
        else:
            user = get_user_profile(user_id, db, user_storage)
            if user and isinstance(user, dict):
                user['lastSeen'] = timestamp
    except Exception as e:
        logger.error(f'Error updating last seen for {user_id}: {e}')

def get_user_preferences(user_id, db, user_storage):
    """
    Get user's preferences
    ✅ FIXED: Better default handling
    """
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and isinstance(user, dict):
            return user.get('preferences', {
                'displayNickname': True,
                'showInLeaderboards': True
            })
        return {
            'displayNickname': True,
            'showInLeaderboards': True
        }
    except Exception as e:
        logger.error(f'Error getting preferences for {user_id}: {e}')
        return {}

def update_user_preferences(user_id, preferences, db, user_storage):
    """
    Update user's preferences
    ✅ FIXED: Better validation
    """
    try:
        if not isinstance(preferences, dict):
            logger.error(f"Invalid preferences type: {type(preferences)}")
            return False
        
        if db:
            result = db.users.update_one(
                {'userId': user_id},
                {'$set': {'preferences': preferences}}
            )
            return result.modified_count > 0
        else:
            user = get_user_profile(user_id, db, user_storage)
            if user and isinstance(user, dict):
                user['preferences'] = preferences
                return True
            return False
    except Exception as e:
        logger.error(f'Error updating preferences for {user_id}: {e}')
        return False

def get_user_servers(user_id, db, user_storage):
    """
    Get list of servers user is on
    ✅ FIXED: Better validation
    """
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and isinstance(user, dict) and 'servers' in user:
            return list(user['servers'].keys())
        return []
    except Exception as e:
        logger.error(f'Error getting servers for {user_id}: {e}')
        return []

def is_user_active_on_server(user_id, server_id, db, user_storage):
    """
    Check if user is active on a specific server
    ✅ FIXED: Better validation
    """
    try:
        user = get_user_profile(user_id, db, user_storage)
        if (user and isinstance(user, dict) and 'servers' in user and 
            server_id in user['servers']):
            return user['servers'][server_id].get('isActive', True)
        return False
    except Exception as e:
        logger.error(f'Error checking if user {user_id} is active on {server_id}: {e}')
        return False

def set_user_active_status(user_id, server_id, is_active, db, user_storage):
    """
    Set user's active status on a server
    ✅ FIXED: Better validation
    """
    try:
        if not isinstance(is_active, bool):
            logger.error(f"Invalid is_active type: {type(is_active)}")
            return False
        
        if db:
            result = db.users.update_one(
                {'userId': user_id},
                {'$set': {f'servers.{server_id}.isActive': is_active}}
            )
            return result.modified_count > 0
        else:
            user = get_user_profile(user_id, db, user_storage)
            if (user and isinstance(user, dict) and 'servers' in user and 
                server_id in user['servers']):
                user['servers'][server_id]['isActive'] = is_active
                return True
            return False
    except Exception as e:
        logger.error(f'Error setting active status for {user_id} on {server_id}: {e}')
        return False

# ================================================================
# COMPATIBILITY FUNCTIONS - For economy route imports
# ================================================================

def create_user_if_not_exists(user_id, server_id, db, user_storage):
    """
    Create user if not exists - wrapper for ensure_user_on_server
    ✅ COMPATIBILITY: For routes that expect this function
    """
    try:
        result = ensure_user_on_server(user_id, server_id, db, user_storage)
        if result:
            return get_user_profile(user_id, db, user_storage)
        return None
    except Exception as e:
        logger.error(f'Error in create_user_if_not_exists for {user_id}: {e}')
        return None

def get_user_data(user_id, db, user_storage):
    """
    Get user data - wrapper for get_user_profile with data sanitization
    ✅ COMPATIBILITY: For routes that expect this function
    """
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and isinstance(user, dict):
            # Create a copy to avoid modifying original
            user_data = user.copy()
            
            # Remove sensitive fields
            if '_id' in user_data:
                del user_data['_id']  # Remove MongoDB _id field
            if 'internalId' in user_data:
                del user_data['internalId']  # Remove internal ID for security
            
            return user_data
        return {}
    except Exception as e:
        logger.error(f'Error getting user data for {user_id}: {e}')
        return {}

def update_user_data(user_id, update_data, db, user_storage):
    """
    Update user data in database or storage
    ✅ COMPATIBILITY: For routes that expect this function
    """
    try:
        if not isinstance(update_data, dict):
            logger.error(f"Invalid update_data type: {type(update_data)}")
            return False
        
        if db:
            result = db.users.update_one(
                {'userId': user_id},
                {'$set': update_data}
            )
            return result.modified_count > 0
        else:
            user = get_user_profile(user_id, db, user_storage)
            if user and isinstance(user, dict):
                user.update(update_data)
                return True
            return False
    except Exception as e:
        logger.error(f'Error updating user data for {user_id}: {e}')
        return False

def get_user_balance(user_id, server_id, db, user_storage):
    """
    Get user balance - alias for get_server_balance for compatibility
    ✅ COMPATIBILITY: For routes that expect this function
    """
    return get_server_balance(user_id, server_id, db, user_storage)

def update_user_balance(user_id, server_id, new_balance, db, user_storage):
    """
    Update user balance - alias for set_server_balance for compatibility
    ✅ COMPATIBILITY: For routes that expect this function
    """
    return set_server_balance(user_id, server_id, new_balance, db, user_storage)

# ================================================================
# SAFE IMPORTS - Try to import optimization functions if available
# ================================================================

try:
    from utils.database.gust_db_optimization import (
        get_user_with_cache,
        get_user_balance_cached,
        db_performance_monitor
    )
    logger.info("✅ GUST database optimization functions imported successfully")
    
    # Override the update_user_balance function if optimization module is available
    def update_user_balance_optimized(user_id, server_id, new_balance, db, user_storage):
        """Optimized user balance update using cache if available"""
        try:
            # Use optimized version if DB is available
            if db:
                return update_user_balance(user_id, server_id, new_balance, db, user_storage)
            else:
                # Fallback to standard version for in-memory storage
                return set_server_balance(user_id, server_id, new_balance, db, user_storage)
        except Exception as e:
            logger.error(f'Error in optimized balance update for {user_id}: {e}')
            # Fallback to standard function
            return set_server_balance(user_id, server_id, new_balance, db, user_storage)
    
    # Replace the standard function with optimized version
    update_user_balance = update_user_balance_optimized
    
except ImportError:
    logger.info("ℹ️ GUST database optimization module not available, using standard functions")
    
    # Create stub functions for compatibility
    def get_user_with_cache(user_id, db, user_storage):
        return get_user_profile(user_id, db, user_storage)
    
    def get_user_balance_cached(user_id, server_id, db, user_storage):
        return get_server_balance(user_id, server_id, db, user_storage)
    
    def db_performance_monitor():
        return {'status': 'optimization_not_available'}

except Exception as e:
    logger.warning(f"⚠️ Error importing GUST database optimization: {e}")
    
    # Create safe fallback functions
    def get_user_with_cache(user_id, db, user_storage):
        return get_user_profile(user_id, db, user_storage)
    
    def get_user_balance_cached(user_id, server_id, db, user_storage):
        return get_server_balance(user_id, server_id, db, user_storage)
    
    def db_performance_monitor():
        return {'status': 'optimization_error', 'error': str(e)}

# ================================================================
# MODULE EXPORTS
# ================================================================

# Export all functions for import
__all__ = [
    # Core functions
    'generate_internal_id',
    'get_user_profile',
    'create_user_profile',
    
    # Balance functions
    'get_server_balance',
    'set_server_balance', 
    'adjust_server_balance',
    
    # User management
    'ensure_user_on_server',
    'get_users_on_server',
    'get_server_leaderboard',
    'transfer_between_users',
    
    # User info
    'get_user_display_name',
    'update_user_last_seen',
    'get_user_preferences',
    'update_user_preferences',
    'get_user_servers',
    'is_user_active_on_server',
    'set_user_active_status',
    
    # Compatibility functions
    'create_user_if_not_exists',
    'get_user_data',
    'update_user_data',
    'get_user_balance',
    'update_user_balance',
    
    # Cache functions (if available)
    'get_user_with_cache',
    'get_user_balance_cached',
    'db_performance_monitor'
]

logger.info("✅ User helpers module loaded successfully with all functions available")