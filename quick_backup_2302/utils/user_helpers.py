"""
User Database Helper Functions
=============================
Helper functions for user management and server-specific operations
"""

# Standard library imports
from datetime import datetime
import logging
import random

logger = logging.getLogger(__name__)

def generate_internal_id():
    '''Generate unique 9-digit internal ID'''
    return random.randint(100000000, 999999999)

def get_user_profile(user_id, db, user_storage):
    '''Get complete user profile'''
    try:
        if db:
            user = db.users.find_one({'userId': user_id})
            return user
        else:
            return user_storage.get(user_id)
    except Exception as e:
        logger.error(f'Error getting user profile for {user_id}: {e}')
        return None

def get_server_balance(user_id, server_id, db, user_storage):
    '''Get user's balance for specific server'''
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and 'servers' in user and server_id in user['servers']:
            return user['servers'][server_id].get('balance', 0)
        return 0
    except Exception as e:
        logger.error(f'Error getting server balance for {user_id} on {server_id}: {e}')
        return 0

def set_server_balance(user_id, server_id, new_balance, db, user_storage):
    '''Set user's balance for specific server'''
    try:
        # Ensure user exists on server first
        ensure_user_on_server(user_id, server_id, db, user_storage)
        
        if db:
            result = db.users.update_one(
                {'userId': user_id},
                {'$set': {f'servers.{server_id}.balance': new_balance}}
            )
            return result.modified_count > 0
        else:
            user = user_storage.get(user_id)
            if user:
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
    '''Adjust user's balance for specific server (add/subtract amount)'''
    try:
        current_balance = get_server_balance(user_id, server_id, db, user_storage)
        new_balance = max(0, current_balance + amount)  # Prevent negative balances
        return set_server_balance(user_id, server_id, new_balance, db, user_storage)
    except Exception as e:
        logger.error(f'Error adjusting server balance for {user_id} on {server_id}: {e}')
        return False

def ensure_user_on_server(user_id, server_id, db, user_storage):
    '''Ensure user has an entry for the specified server'''
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
                user_storage[user_id] = user_data
            
            user = user_data
        
        # Ensure server entry exists
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
    '''Get all users on a specific server'''
    try:
        users = []
        if db:
            cursor = db.users.find({f'servers.{server_id}': {'$exists': True}})
            for user in cursor:
                server_data = user['servers'][server_id]
                users.append({
                    'userId': user['userId'],
                    'nickname': user['nickname'],
                    'balance': server_data.get('balance', 0),
                    'clanTag': server_data.get('clanTag'),
                    'joinedAt': server_data.get('joinedAt'),
                    'isActive': server_data.get('isActive', True)
                })
        else:
            for user_id, user in user_storage.items():
                if 'servers' in user and server_id in user['servers']:
                    server_data = user['servers'][server_id]
                    users.append({
                        'userId': user_id,
                        'nickname': user['nickname'],
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
    '''Get server-specific leaderboard sorted by balance'''
    try:
        users = get_users_on_server(server_id, db, user_storage)
        # Sort by balance (descending)
        users.sort(key=lambda x: x['balance'], reverse=True)
        return users[:limit]
    except Exception as e:
        logger.error(f'Error getting server leaderboard for {server_id}: {e}')
        return []

def transfer_between_users(from_user_id, to_user_id, amount, server_id, db, user_storage):
    '''Transfer coins between users on the same server'''
    try:
        # Check sender has sufficient balance
        from_balance = get_server_balance(from_user_id, server_id, db, user_storage)
        if from_balance < amount:
            return False, 'Insufficient funds for transfer'
        
        # Ensure both users exist on server
        ensure_user_on_server(from_user_id, server_id, db, user_storage)
        ensure_user_on_server(to_user_id, server_id, db, user_storage)
        
        # Perform transfer
        if (adjust_server_balance(from_user_id, server_id, -amount, db, user_storage) and
            adjust_server_balance(to_user_id, server_id, amount, db, user_storage)):
            return True, f'Successfully transferred {amount} coins'
        else:
            return False, 'Transfer failed'
            
    except Exception as e:
        logger.error(f'Error transferring between {from_user_id} and {to_user_id}: {e}')
        return False, 'Transfer failed due to error'

def get_user_display_name(user_id, db, user_storage):
    '''Get user's display name (nickname or user_id)'''
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user:
            return user.get('nickname', user_id)
        return user_id
    except Exception as e:
        logger.error(f'Error getting display name for {user_id}: {e}')
        return user_id

def update_user_last_seen(user_id, db, user_storage):
    '''Update user's last seen timestamp'''
    try:
        timestamp = datetime.now().isoformat()
        if db:
            db.users.update_one(
                {'userId': user_id},
                {'$set': {'lastSeen': timestamp}}
            )
        else:
            user = user_storage.get(user_id)
            if user:
                user['lastSeen'] = timestamp
    except Exception as e:
        logger.error(f'Error updating last seen for {user_id}: {e}')

# ================================================================
# MISSING FUNCTIONS - Added to resolve import errors
# ================================================================

def create_user_if_not_exists(user_id, server_id, db, user_storage):
    '''Create user if not exists - wrapper for ensure_user_on_server'''
    try:
        # Use existing ensure_user_on_server function which already does this
        result = ensure_user_on_server(user_id, server_id, db, user_storage)
        if result:
            # Return the user data for compatibility
            return get_user_profile(user_id, db, user_storage)
        return None
    except Exception as e:
        logger.error(f'Error in create_user_if_not_exists for {user_id}: {e}')
        return None

def get_user_data(user_id, db, user_storage):
    '''Get user data - wrapper for get_user_profile with data sanitization'''
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user:
            # Create a copy to avoid modifying original
            user_data = user.copy() if isinstance(user, dict) else {}
            
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
    '''Update user data in database or storage'''
    try:
        if db:
            result = db.users.update_one(
                {'userId': user_id},
                {'$set': update_data}
            )
            return result.modified_count > 0
        else:
            user = user_storage.get(user_id)
            if user:
                user.update(update_data)
                return True
            return False
    except Exception as e:
        logger.error(f'Error updating user data for {user_id}: {e}')
        return False

def get_user_balance(user_id, server_id, db, user_storage):
    '''Get user balance - alias for get_server_balance for compatibility'''
    return get_server_balance(user_id, server_id, db, user_storage)

def update_user_balance(user_id, server_id, new_balance, db, user_storage):
    '''Update user balance - alias for set_server_balance for compatibility'''
    return set_server_balance(user_id, server_id, new_balance, db, user_storage)

def create_user_profile(user_id, nickname=None, db=None, user_storage=None):
    '''Create a new user profile with default settings'''
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
            user_storage[user_id] = user_data
        
        return user_data
    except Exception as e:
        logger.error(f'Error creating user profile for {user_id}: {e}')
        return None

def get_user_preferences(user_id, db, user_storage):
    '''Get user's preferences'''
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user:
            return user.get('preferences', {
                'displayNickname': True,
                'showInLeaderboards': True
            })
        return {}
    except Exception as e:
        logger.error(f'Error getting preferences for {user_id}: {e}')
        return {}

def update_user_preferences(user_id, preferences, db, user_storage):
    '''Update user's preferences'''
    try:
        if db:
            result = db.users.update_one(
                {'userId': user_id},
                {'$set': {'preferences': preferences}}
            )
            return result.modified_count > 0
        else:
            user = user_storage.get(user_id)
            if user:
                user['preferences'] = preferences
                return True
            return False
    except Exception as e:
        logger.error(f'Error updating preferences for {user_id}: {e}')
        return False

def get_user_servers(user_id, db, user_storage):
    '''Get list of servers user is on'''
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and 'servers' in user:
            return list(user['servers'].keys())
        return []
    except Exception as e:
        logger.error(f'Error getting servers for {user_id}: {e}')
        return []

def is_user_active_on_server(user_id, server_id, db, user_storage):
    '''Check if user is active on a specific server'''
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and 'servers' in user and server_id in user['servers']:
            return user['servers'][server_id].get('isActive', True)
        return False
    except Exception as e:
        logger.error(f'Error checking if user {user_id} is active on {server_id}: {e}')
        return False

def set_user_active_status(user_id, server_id, is_active, db, user_storage):
    '''Set user's active status on a server'''
    try:
        if db:
            result = db.users.update_one(
                {'userId': user_id},
                {'$set': {f'servers.{server_id}.isActive': is_active}}
            )
            return result.modified_count > 0
        else:
            user = user_storage.get(user_id)
            if user and 'servers' in user and server_id in user['servers']:
                user['servers'][server_id]['isActive'] = is_active
                return True
            return False
    except Exception as e:
        logger.error(f'Error setting active status for {user_id} on {server_id}: {e}')
        return False

# DO NOT import from routes.user_database here - this would create circular import
# All necessary functions are implemented above

# GUST database optimization imports
from utils.gust_db_optimization import (
    get_user_with_cache,
    get_user_balance_cached,
    update_user_balance,
    db_performance_monitor
)