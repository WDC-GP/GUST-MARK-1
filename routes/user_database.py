"""
GUST Bot Enhanced - User Database Routes
========================================
Comprehensive user management with server-specific data
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import secrets
import random

from routes.auth import require_auth
import logging

logger = logging.getLogger(__name__)

user_database_bp = Blueprint('user_database', __name__)

def init_user_database_routes(app, db, user_storage):
    '''Initialize user database routes'''
    
    @user_database_bp.route('/api/users/register', methods=['POST'])
    @require_auth
    def register_user():
        '''Register new user with G-Portal login + nickname'''
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            nickname = data.get('nickname', '').strip()
            server_id = data.get('serverId', 'default_server')
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID required'})
            
            if not nickname:
                nickname = user_id  # Default to user ID if no nickname provided
            
            # Validate nickname (3-20 chars, alphanumeric + underscore)
            if not (3 <= len(nickname) <= 20) or not nickname.replace('_', '').isalnum():
                return jsonify({'success': False, 'error': 'Nickname must be 3-20 alphanumeric characters'})
            
            # Check if user already exists
            existing_user = get_user_profile(user_id, db, user_storage)
            if existing_user:
                return jsonify({'success': False, 'error': 'User already registered'})
            
            # Generate internal ID (1-9 digits for admin use)
            internal_id = random.randint(100000000, 999999999)
            
            # Create user document
            user_data = {
                'userId': user_id,
                'nickname': nickname,
                'internalId': internal_id,
                'registeredAt': datetime.now().isoformat(),
                'lastSeen': datetime.now().isoformat(),
                'servers': {
                    server_id: {
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
                },
                'preferences': {
                    'displayNickname': True,
                    'showInLeaderboards': True
                },
                'totalServers': 1
            }
            
            # Save user
            if db:
                db.users.insert_one(user_data)
            else:
                user_storage[user_id] = user_data
            
            logger.info(f'👤 New user registered: {user_id} ({nickname}) on {server_id}')
            return jsonify({
                'success': True, 
                'message': 'User registered successfully',
                'userId': user_id,
                'nickname': nickname,
                'internalId': internal_id,
                'serverId': server_id
            })
            
        except Exception as e:
            logger.error(f'❌ User registration error: {str(e)}')
            return jsonify({'success': False, 'error': 'Registration failed'})
    
    @user_database_bp.route('/api/users/profile/<user_id>')
    @require_auth  
    def get_user_profile_route(user_id):
        '''Get complete user profile'''
        try:
            user_profile = get_user_profile(user_id, db, user_storage)
            if not user_profile:
                return jsonify({'success': False, 'error': 'User not found'})
            
            # Update last seen
            update_user_last_seen(user_id, db, user_storage)
            
            # Remove internal ID from public response
            public_profile = user_profile.copy()
            if 'internalId' in public_profile:
                del public_profile['internalId']
            
            return jsonify({'success': True, 'profile': public_profile})
            
        except Exception as e:
            logger.error(f'❌ Profile retrieval error: {str(e)}')
            return jsonify({'success': False, 'error': 'Profile retrieval failed'})
    
    @user_database_bp.route('/api/users/profile/<user_id>', methods=['PUT'])
    @require_auth
    def update_user_profile(user_id):
        '''Update user profile/nickname'''
        try:
            data = request.json
            nickname = data.get('nickname', '').strip()
            
            if not nickname:
                return jsonify({'success': False, 'error': 'Nickname required'})
            
            # Validate nickname
            if not (3 <= len(nickname) <= 20) or not nickname.replace('_', '').isalnum():
                return jsonify({'success': False, 'error': 'Nickname must be 3-20 alphanumeric characters'})
            
            # Update user
            if db:
                result = db.users.update_one(
                    {'userId': user_id},
                    {'': {'nickname': nickname, 'lastSeen': datetime.now().isoformat()}}
                )
                if result.matched_count == 0:
                    return jsonify({'success': False, 'error': 'User not found'})
            else:
                if user_id not in user_storage:
                    return jsonify({'success': False, 'error': 'User not found'})
                user_storage[user_id]['nickname'] = nickname
                user_storage[user_id]['lastSeen'] = datetime.now().isoformat()
            
            logger.info(f'👤 Profile updated: {user_id} → {nickname}')
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
            
        except Exception as e:
            logger.error(f'❌ Profile update error: {str(e)}')
            return jsonify({'success': False, 'error': 'Profile update failed'})
    
    @user_database_bp.route('/api/users/servers/<user_id>')
    @require_auth
    def get_user_servers(user_id):
        '''Get user's server list with balances'''
        try:
            user_profile = get_user_profile(user_id, db, user_storage)
            if not user_profile:
                return jsonify({'success': False, 'error': 'User not found'})
            
            servers = user_profile.get('servers', {})
            server_list = []
            
            for server_id, server_data in servers.items():
                server_list.append({
                    'serverId': server_id,
                    'balance': server_data.get('balance', 0),
                    'clanTag': server_data.get('clanTag'),
                    'joinedAt': server_data.get('joinedAt'),
                    'isActive': server_data.get('isActive', True)
                })
            
            return jsonify({
                'success': True,
                'servers': server_list,
                'totalServers': len(server_list)
            })
            
        except Exception as e:
            logger.error(f'❌ Server list error: {str(e)}')
            return jsonify({'success': False, 'error': 'Server list retrieval failed'})
    
    @user_database_bp.route('/api/users/join-server/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def join_server(user_id, server_id):
        '''Join new server (create server entry)'''
        try:
            user_profile = get_user_profile(user_id, db, user_storage)
            if not user_profile:
                return jsonify({'success': False, 'error': 'User not found'})
            
            # Check if already on server
            if server_id in user_profile.get('servers', {}):
                return jsonify({'success': False, 'error': 'Already on this server'})
            
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
            
            # Update user
            if db:
                db.users.update_one(
                    {'userId': user_id},
                    {
                        '': {
                            f'servers.{server_id}': server_data,
                            'lastSeen': datetime.now().isoformat()
                        },
                        '': {'totalServers': 1}
                    }
                )
            else:
                if 'servers' not in user_storage[user_id]:
                    user_storage[user_id]['servers'] = {}
                user_storage[user_id]['servers'][server_id] = server_data
                user_storage[user_id]['totalServers'] = len(user_storage[user_id]['servers'])
                user_storage[user_id]['lastSeen'] = datetime.now().isoformat()
            
            logger.info(f'👤 User joined server: {user_id} → {server_id}')
            return jsonify({'success': True, 'message': 'Joined server successfully'})
            
        except Exception as e:
            logger.error(f'❌ Join server error: {str(e)}')
            return jsonify({'success': False, 'error': 'Join server failed'})

# Helper functions
def get_user_profile(user_id, db, user_storage):
    '''Get user profile from database or storage'''
    try:
        if db:
            return db.users.find_one({'userId': user_id})
        else:
            return user_storage.get(user_id)
    except:
        return None

def update_user_last_seen(user_id, db, user_storage):
    '''Update user's last seen timestamp'''
    try:
        timestamp = datetime.now().isoformat()
        if db:
            db.users.update_one(
                {'userId': user_id},
                {'': {'lastSeen': timestamp}}
            )
        else:
            if user_id in user_storage:
                user_storage[user_id]['lastSeen'] = timestamp
    except:
        pass

def get_user_display_name(user_id, db, user_storage):
    '''Get user's display name (nickname or userId)'''
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and user.get('preferences', {}).get('displayNickname', True):
            return user.get('nickname', user_id)
        return user_id
    except:
        return user_id

def get_server_balance(user_id, server_id, db, user_storage):
    '''Get user's balance for specific server'''
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and 'servers' in user and server_id in user['servers']:
            return user['servers'][server_id].get('balance', 0)
        return 0
    except:
        return 0

def set_server_balance(user_id, server_id, amount, db, user_storage):
    '''Set user's balance for specific server'''
    try:
        if db:
            db.users.update_one(
                {'userId': user_id},
                {'': {f'servers.{server_id}.balance': amount}}
            )
        else:
            user = user_storage.get(user_id)
            if user and server_id in user.get('servers', {}):
                user['servers'][server_id]['balance'] = amount
        return True
    except:
        return False

def adjust_server_balance(user_id, server_id, amount, db, user_storage):
    '''Adjust user's balance for specific server (add/subtract)'''
    try:
        current_balance = get_server_balance(user_id, server_id, db, user_storage)
        new_balance = max(0, current_balance + amount)  # Don't allow negative balances
        return set_server_balance(user_id, server_id, new_balance, db, user_storage)
    except:
        return False
