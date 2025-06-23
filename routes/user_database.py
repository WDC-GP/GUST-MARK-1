"""
GUST Bot Enhanced - User Database Routes - COMPLETE FIX
======================================================
Fixed all issues: MongoDB syntax, user_storage access, error handling
✅ All MongoDB operations corrected
✅ User storage access patterns fixed
✅ Step 7 validation compliant
✅ Complete error handling implemented
"""

# Standard library imports
from datetime import datetime
import logging
import random

# Third-party imports
from flask import Blueprint, request, jsonify

# Local imports
from routes.auth import require_auth

# GUST database optimization imports
from utils.database.gust_db_optimization import (
    get_user_with_cache,
    get_user_balance_cached,
    update_user_balance,
    db_performance_monitor
)

logger = logging.getLogger(__name__)

user_database_bp = Blueprint('user_database', __name__)

def init_user_database_routes(app, db, user_storage):
    """Initialize user database routes"""
    
    # CRITICAL FIX: Bulletproof parameter validation
    if user_storage is None:
        logger.error("[ERROR] CRITICAL: user_storage is None in init_user_database_routes!")
        raise ValueError("user_storage cannot be None")
    
    if not hasattr(user_storage, 'users'):
        logger.error("[ERROR] CRITICAL: user_storage missing users attribute!")
        raise ValueError("user_storage must have users attribute")
    
    logger.info(f"[OK] init_user_database_routes called with user_storage: {type(user_storage)}")
    
    @user_database_bp.route('/api/users/register', methods=['POST'])
    @require_auth
    def register_user():
        """Register new user with G-Portal login + nickname"""
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
            
            # Save user - FIX: Use correct user_storage access
            if db:
                db.users.insert_one(user_data)
            else:
                user_storage.users[user_id] = user_data  # FIX: Use .users attribute
            
            logger.info(f'[INFO] New user registered: {user_id} ({nickname}) on {server_id}')
            return jsonify({
                'success': True, 
                'message': 'User registered successfully',
                'userId': user_id,
                'nickname': nickname,
                'internalId': internal_id,
                'serverId': server_id
            })
            
        except Exception as e:
            logger.error(f'[ERROR] User registration error: {str(e)}')
            return jsonify({'success': False, 'error': 'Registration failed'})
    
    @user_database_bp.route('/api/users/profile/<user_id>')
    @require_auth  
    def get_user_profile_route(user_id):
        """Get complete user profile"""
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
            logger.error(f'[ERROR] Profile retrieval error: {str(e)}')
            return jsonify({'success': False, 'error': 'Profile retrieval failed'})
    
    @user_database_bp.route('/api/users/profile/<user_id>', methods=['PUT'])
    @require_auth
    def update_user_profile(user_id):
        """Update user profile"""
        try:
            data = request.json
            updates = {}
            
            # Allowed profile updates
            if 'nickname' in data:
                nickname = data['nickname'].strip()
                if 3 <= len(nickname) <= 20 and nickname.replace('_', '').isalnum():
                    updates['nickname'] = nickname
                else:
                    return jsonify({'success': False, 'error': 'Invalid nickname format'})
            
            if 'preferences' in data:
                updates['preferences'] = data['preferences']
            
            updates['lastSeen'] = datetime.now().isoformat()
            
            # Apply updates - FIX: Correct MongoDB syntax and user_storage access
            if db:
                result = db.users.update_one(
                    {'userId': user_id},
                    {'$set': updates}  # FIX: Use proper MongoDB operator
                )
                if result.matched_count == 0:
                    return jsonify({'success': False, 'error': 'User not found'})
            else:
                if user_id in user_storage.users:  # FIX: Use .users attribute
                    user_storage.users[user_id].update(updates)
                else:
                    return jsonify({'success': False, 'error': 'User not found'})
            
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
            
        except Exception as e:
            logger.error(f'[ERROR] Profile update error: {str(e)}')
            return jsonify({'success': False, 'error': 'Profile update failed'})
    
    @user_database_bp.route('/api/users/servers/<user_id>')
    @require_auth
    def get_user_servers(user_id):
        """Get list of servers user is registered on"""
        try:
            user = get_user_profile(user_id, db, user_storage)
            if not user:
                return jsonify({'success': False, 'error': 'User not found'})
            
            servers = user.get('servers', {})
            server_list = []
            
            for server_id, server_data in servers.items():
                server_list.append({
                    'serverId': server_id,
                    'balance': server_data.get('balance', 0),
                    'joinedAt': server_data.get('joinedAt'),
                    'isActive': server_data.get('isActive', True),
                    'clanTag': server_data.get('clanTag')
                })
            
            return jsonify({'success': True, 'servers': server_list})
            
        except Exception as e:
            logger.error(f'[ERROR] Server list error: {str(e)}')
            return jsonify({'success': False, 'error': 'Server list retrieval failed'})
    
    @user_database_bp.route('/api/users/join-server/<user_id>/<server_id>', methods=['POST'])
    @require_auth
    def join_server(user_id, server_id):
        """Add user to a new server"""
        try:
            user = get_user_profile(user_id, db, user_storage)
            if not user:
                return jsonify({'success': False, 'error': 'User not found'})
            
            # Check if already on server
            if 'servers' in user and server_id in user['servers']:
                return jsonify({'success': False, 'error': 'Already on this server'})
            
            # Create server data
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
            
            # Add to database - FIX: Correct MongoDB syntax and user_storage access
            if db:
                db.users.update_one(
                    {'userId': user_id},
                    {
                        '$set': {  # FIX: Use proper MongoDB operator
                            f'servers.{server_id}': server_data,
                            'lastSeen': datetime.now().isoformat()
                        },
                        '$inc': {'totalServers': 1}  # FIX: Use proper MongoDB operator
                    }
                )
            else:
                if 'servers' not in user_storage.users[user_id]:  # FIX: Use .users attribute
                    user_storage.users[user_id]['servers'] = {}
                user_storage.users[user_id]['servers'][server_id] = server_data
                user_storage.users[user_id]['totalServers'] = len(user_storage.users[user_id]['servers'])
                user_storage.users[user_id]['lastSeen'] = datetime.now().isoformat()
            
            logger.info(f'[INFO] User joined server: {user_id} -> {server_id}')
            return jsonify({'success': True, 'message': 'Joined server successfully'})
            
        except Exception as e:
            logger.error(f'[ERROR] Join server error: {str(e)}')
            return jsonify({'success': False, 'error': 'Join server failed'})
    
    @user_database_bp.route('/api/users/leaderboard/<server_id>')
    @require_auth
    def get_server_leaderboard(server_id):
        """Get leaderboard for specific server"""
        try:
            leaderboard = []
            
            if db:
                users = db.users.find({f'servers.{server_id}': {'$exists': True}})
            else:
                users = [user for user in user_storage.users.values()  # FIX: Use .users attribute
                        if 'servers' in user and server_id in user['servers']]
            
            for user in users:
                if 'servers' in user and server_id in user['servers']:
                    server_data = user['servers'][server_id]
                    if server_data.get('isActive', True) and user.get('preferences', {}).get('showInLeaderboards', True):
                        leaderboard.append({
                            'userId': user['userId'],
                            'nickname': user.get('nickname', user['userId']),
                            'balance': server_data.get('balance', 0),
                            'joinedAt': server_data.get('joinedAt'),
                            'clanTag': server_data.get('clanTag')
                        })
            
            # Sort by balance (descending)
            leaderboard.sort(key=lambda x: x['balance'], reverse=True)
            
            # Add ranks
            for i, user in enumerate(leaderboard):
                user['rank'] = i + 1
            
            return jsonify({'success': True, 'leaderboard': leaderboard[:50]})  # Top 50
            
        except Exception as e:
            logger.error(f'[ERROR] Leaderboard error: {str(e)}')
            return jsonify({'success': False, 'error': 'Leaderboard retrieval failed'})
    
    @user_database_bp.route('/api/users/stats/<server_id>')
    @require_auth
    def get_server_user_stats(server_id):
        """Get user statistics for a server"""
        try:
            stats = {
                'totalUsers': 0,
                'activeUsers': 0,
                'bannedUsers': 0,
                'totalBalance': 0,
                'averageBalance': 0
            }
            
            if db:
                # MongoDB aggregation would be better, but this works
                users = list(db.users.find({f'servers.{server_id}': {'$exists': True}}))
            else:
                users = [user for user in user_storage.users.values()  # FIX: Use .users attribute
                        if 'servers' in user and server_id in user['servers']]
            
            total_balance = 0
            for user in users:
                if 'servers' in user and server_id in user['servers']:
                    stats['totalUsers'] += 1
                    server_data = user['servers'][server_id]
                    
                    if server_data.get('isActive', True):
                        stats['activeUsers'] += 1
                    else:
                        stats['bannedUsers'] += 1
                    
                    balance = server_data.get('balance', 0)
                    total_balance += balance
            
            stats['totalBalance'] = total_balance
            if stats['totalUsers'] > 0:
                stats['averageBalance'] = round(total_balance / stats['totalUsers'], 2)
            
            return jsonify({'success': True, 'stats': stats})
            
        except Exception as e:
            logger.error(f'[ERROR] Stats error: {str(e)}')
            return jsonify({'success': False, 'error': 'Stats retrieval failed'})
    
    @user_database_bp.route('/api/users/search')
    @require_auth
    def search_users():
        """Search for users"""
        try:
            query = request.args.get('q', '').strip().lower()
            limit = int(request.args.get('limit', 10))
            
            if not query:
                return jsonify({'success': True, 'users': []})
            
            users = []
            if db:
                # Search in database
                cursor = db.users.find({
                    '$or': [
                        {'userId': {'$regex': query, '$options': 'i'}},
                        {'nickname': {'$regex': query, '$options': 'i'}}
                    ]
                }, {'_id': 0}).limit(limit)
                users = list(cursor)
            else:
                # Search in memory storage - FIX: Use .users attribute
                for user_id, user_data in user_storage.users.items():
                    if (query in user_id.lower() or 
                        query in user_data.get('nickname', '').lower()):
                        users.append(user_data)
                        if len(users) >= limit:
                            break
            
            # Remove internal IDs from response
            for user in users:
                if 'internalId' in user:
                    del user['internalId']
            
            return jsonify({'success': True, 'users': users})
            
        except Exception as e:
            logger.error(f'[ERROR] Search error: {str(e)}')
            return jsonify({'success': False, 'error': 'Search failed'})
    
    return user_database_bp

# Helper functions - FIX: All use correct user_storage access
def get_user_profile(user_id, db, user_storage):
    """Get user profile from database or storage"""
    try:
        if db:
            return db.users.find_one({'userId': user_id})
        else:
            return user_storage.users.get(user_id)  # FIX: Use .users attribute
    except:
        return None

def update_user_last_seen(user_id, db, user_storage):
    """Update user's last seen timestamp"""
    try:
        timestamp = datetime.now().isoformat()
        if db:
            db.users.update_one(
                {'userId': user_id},
                {'$set': {'lastSeen': timestamp}}  # FIX: Use proper MongoDB operator
            )
        else:
            if user_id in user_storage.users:  # FIX: Use .users attribute
                user_storage.users[user_id]['lastSeen'] = timestamp
    except:
        pass

def get_user_display_name(user_id, db, user_storage):
    """Get user's display name (nickname or userId)"""
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and user.get('preferences', {}).get('displayNickname', True):
            return user.get('nickname', user_id)
        return user_id
    except:
        return user_id

def get_server_balance(user_id, server_id, db, user_storage):
    """Get user's balance for specific server"""
    try:
        user = get_user_profile(user_id, db, user_storage)
        if user and 'servers' in user and server_id in user['servers']:
            return user['servers'][server_id].get('balance', 0)
        return 0
    except:
        return 0

def set_server_balance(user_id, server_id, amount, db, user_storage):
    """Set user's balance for specific server"""
    try:
        if db:
            db.users.update_one(
                {'userId': user_id},
                {'$set': {f'servers.{server_id}.balance': amount}}  # FIX: Use proper MongoDB operator
            )
        else:
            if user_id in user_storage.users and 'servers' in user_storage.users[user_id]:  # FIX: Use .users
                if server_id in user_storage.users[user_id]['servers']:
                    user_storage.users[user_id]['servers'][server_id]['balance'] = amount
        return True
    except:
        return False

def adjust_server_balance(user_id, server_id, change, db, user_storage):
    """Adjust user's balance for specific server (+ or -)"""
    try:
        current_balance = get_server_balance(user_id, server_id, db, user_storage)
        new_balance = max(0, current_balance + change)  # Don't allow negative balances
        return set_server_balance(user_id, server_id, new_balance, db, user_storage)
    except:
        return False
