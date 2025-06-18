"""
User Database Helper Functions
=============================
Utility functions for user database operations
"""

from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def ensure_user_on_server(user_id, server_id, db, user_storage):
    '''Ensure user has entry for specific server, create if missing'''
    try:
        user = get_user_profile(user_id, db, user_storage)
        if not user:
            return False
        
        if server_id not in user.get('servers', {}):
            # Create server entry
            server_data = {
                'balance': 1000,  # Starting balance
                'clanTag': None,
                'joinedAt': datetime.now().isoformat(),
                'gamblingStats': {
                    'totalWagered': 0,
                    'totalWon': 0,
                    'gamesPlayed': 0,
                    'biggestWin': 0,
                    'lastPlayed': None
                },
                'isActive': True
            }
            
            if db:
                db.users.update_one(
                    {'userId': user_id},
                    {
                        '': {f'servers.{server_id}': server_data},
                        '': {'totalServers': 1}
                    }
                )
            else:
                if 'servers' not in user_storage[user_id]:
                    user_storage[user_id]['servers'] = {}
                user_storage[user_id]['servers'][server_id] = server_data
                user_storage[user_id]['totalServers'] = len(user_storage[user_id]['servers'])
            
            logger.info(f'👤 Auto-created server entry: {user_id} → {server_id}')
        
        return True
    except Exception as e:
        logger.error(f'❌ Error ensuring user on server: {str(e)}')
        return False

def get_user_profile(user_id, db, user_storage):
    '''Get user profile from database or storage'''
    try:
        if db:
            return db.users.find_one({'userId': user_id})
        else:
            return user_storage.get(user_id)
    except:
        return None

def get_users_on_server(server_id, db, user_storage):
    '''Get all users on a specific server'''
    try:
        users = []
        if db:
            cursor = db.users.find({f'servers.{server_id}': {'': True}})
            for user in cursor:
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
            for user_id, user_data in user_storage.items():
                if server_id in user_data.get('servers', {}):
                    server_data = user_data['servers'][server_id]
                    users.append({
                        'userId': user_id,
                        'nickname': user_data.get('nickname', user_id),
                        'balance': server_data.get('balance', 0),
                        'clanTag': server_data.get('clanTag'),
                        'joinedAt': server_data.get('joinedAt'),
                        'isActive': server_data.get('isActive', True)
                    })
        
        return users
    except Exception as e:
        logger.error(f'❌ Error getting users on server: {str(e)}')
        return []

def get_server_leaderboard(server_id, db, user_storage, limit=10):
    '''Get leaderboard for specific server'''
    try:
        users = get_users_on_server(server_id, db, user_storage)
        
        # Filter users who want to show in leaderboards
        if db:
            # Get preference data
            all_users = list(db.users.find({f'servers.{server_id}': {'': True}}))
            filtered_users = []
            for user in users:
                user_profile = next((u for u in all_users if u['userId'] == user['userId']), None)
                if user_profile and user_profile.get('preferences', {}).get('showInLeaderboards', True):
                    filtered_users.append(user)
            users = filtered_users
        
        # Sort by balance (descending)
        users.sort(key=lambda x: x['balance'], reverse=True)
        
        return users[:limit]
    except Exception as e:
        logger.error(f'❌ Error getting leaderboard: {str(e)}')
        return []

def transfer_between_users(from_user_id, to_user_id, amount, server_id, db, user_storage):
    '''Transfer coins between users on same server'''
    try:
        # Validate both users exist on server
        from_balance = get_server_balance(from_user_id, server_id, db, user_storage)
        to_balance = get_server_balance(to_user_id, server_id, db, user_storage)
        
        if from_balance < amount:
            return False, "Insufficient balance"
        
        if to_balance is None:
            return False, "Recipient not found on server"
        
        # Perform transfer
        if adjust_server_balance(from_user_id, server_id, -amount, db, user_storage):
            if adjust_server_balance(to_user_id, server_id, amount, db, user_storage):
                logger.info(f'💸 Transfer: {from_user_id} → {to_user_id}: {amount} on {server_id}')
                return True, "Transfer successful"
            else:
                # Rollback
                adjust_server_balance(from_user_id, server_id, amount, db, user_storage)
                return False, "Transfer failed (rollback completed)"
        
        return False, "Transfer failed"
    except Exception as e:
        logger.error(f'❌ Transfer error: {str(e)}')
        return False, "Transfer error"

# Import the functions from user_database.py to avoid duplication
from routes.user_database import (
    get_user_display_name,
    get_server_balance, 
    set_server_balance,
    adjust_server_balance,
    update_user_last_seen
)
