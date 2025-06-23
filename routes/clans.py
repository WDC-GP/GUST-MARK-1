"""
GUST Bot Enhanced - Clan Management Routes (ENHANCED)
===================================================
Integrated clan system with user database for server-specific clans
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
import logging
import secrets

from routes.auth import require_auth
from utils.user_helpers import (
    get_user_profile,
    get_users_on_server,
    create_user_if_not_exists,
    get_user_data,
    update_user_data
)

# GUST database optimization imports
from utils.database.gust_db_optimization import (
    get_user_with_cache,
    get_user_balance_cached,
    update_user_balance,
    db_performance_monitor,
    adjust_server_balance,
    get_server_balance
)

logger = logging.getLogger(__name__)

clans_bp = Blueprint('clans', __name__)

def init_clans_routes(app, db, clans_storage, user_storage):
    '''Initialize clan routes with user database integration'''
    
    @clans_bp.route('/api/clans')
    @require_auth
    def get_all_clans():
        '''Get all clans across all servers - ADDED TO FIX 404 ERROR'''
        try:
            if db:
                clans = list(db.clans.find({}, {'_id': 0}))
            else:
                # For in-memory storage, get all clans from all servers
                all_clans = []
                if hasattr(clans_storage, 'get_clans'):
                    # If using InMemoryUserStorage
                    all_clans = clans_storage.get_clans()  # Gets all clans
                else:
                    # If using simple list
                    all_clans = list(clans_storage) if clans_storage else []
            
            return jsonify(all_clans)
            
        except Exception as e:
            logger.error(f'❌ Error getting all clans: {e}')
            return jsonify([])  # Return empty array instead of error to prevent frontend crash
    
    @clans_bp.route('/api/clans/<server_id>')
    @require_auth
    def get_server_clans(server_id):
        '''Get all clans for a specific server with enhanced member info'''
        try:
            if db:
                clans = list(db.clans.find({'serverId': server_id}, {'_id': 0}))
            else:
                clans = [c for c in clans_storage if c.get('serverId') == server_id]
            
            # Enhance with user database info
            for clan in clans:
                enhanced_members = []
                for member_id in clan.get('members', []):
                    member_info = get_user_info(member_id, db, user_storage)
                    server_data = member_info.get('servers', {}).get(server_id, {})
                    enhanced_members.append({
                        'userId': member_id,
                        'displayName': member_info.get('nickname', member_id),
                        'isLeader': member_id == clan.get('leader'),
                        'joinedAt': server_data.get('joinedAt'),
                        'isActive': server_data.get('isActive', True),
                        'balance': server_data.get('balance', 0),
                        'clanTag': server_data.get('clanTag')
                    })
                clan['enhancedMembers'] = enhanced_members
                clan['activeMembers'] = len([m for m in enhanced_members if m['isActive']])
            
            return jsonify(clans)
            
        except Exception as e:
            logger.error(f'❌ Error getting clans: {e}')
            return jsonify({'error': 'Failed to get clans'}), 500
    
    @clans_bp.route('/api/clans/create', methods=['POST'])
    @require_auth  
    def create_clan():
        '''Create a new clan with user database integration'''
        try:
            data = request.get_json()
            user_id = data.get('userId')
            server_id = data.get('serverId')
            clan_name = data.get('name')
            clan_tag = data.get('tag')
            clan_description = data.get('description', '')
            
            if not all([user_id, server_id, clan_name, clan_tag]):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Ensure user exists on server
            ensure_user_on_server(user_id, server_id, db, user_storage)
            
            # Check if user already has a clan on this server
            user_info = get_user_info(user_id, db, user_storage)
            current_clan = user_info.get('servers', {}).get(server_id, {}).get('clanTag')
            if current_clan:
                return jsonify({'error': 'User already in a clan on this server'}), 400
            
            # Check if clan tag already exists on this server
            if db:
                existing_clan = db.clans.find_one({'serverId': server_id, 'tag': clan_tag})
            else:
                existing_clan = next((c for c in clans_storage 
                                    if c.get('serverId') == server_id and c.get('tag') == clan_tag), None)
            
            if existing_clan:
                return jsonify({'error': 'Clan tag already exists on this server'}), 400
            
            # Create clan
            clan_id = str(uuid.uuid4())
            clan_data = {
                'clanId': clan_id,
                'name': clan_name,
                'tag': clan_tag,
                'description': clan_description,
                'serverId': server_id,
                'leader': user_id,
                'members': [user_id],
                'memberCount': 1,
                'createdAt': datetime.now().isoformat(),
                'lastUpdated': datetime.now().isoformat(),
                'stats': {
                    'totalMembers': 1,
                    'totalWealth': get_server_balance(user_id, server_id, db, user_storage),
                    'averageBalance': get_server_balance(user_id, server_id, db, user_storage)
                }
            }
            
            if db:
                db.clans.insert_one(clan_data)
            else:
                clans_storage.append(clan_data)
            
            # Set user's clan tag in user database
            set_user_clan_tag(user_id, server_id, clan_tag, db, user_storage)
            
            logger.info(f'🛡️ Created clan {clan_name} ({clan_tag}) on server {server_id}')
            
            return jsonify({
                'success': True, 
                'clanId': clan_id,
                'clan': clan_data
            })
            
        except Exception as e:
            logger.error(f'❌ Error creating clan: {e}')
            return jsonify({'error': 'Failed to create clan'}), 500
    
    @clans_bp.route('/api/clans/join', methods=['POST'])
    @require_auth
    def join_clan():
        '''Join a clan with user database sync'''
        try:
            data = request.get_json()
            user_id = data.get('userId')
            server_id = data.get('serverId')
            clan_tag = data.get('clanTag')
            
            if not all([user_id, server_id, clan_tag]):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Ensure user exists on server
            ensure_user_on_server(user_id, server_id, db, user_storage)
            
            # Check if user already has a clan on this server
            user_info = get_user_info(user_id, db, user_storage)
            current_clan = user_info.get('servers', {}).get(server_id, {}).get('clanTag')
            if current_clan:
                return jsonify({'error': 'User already in a clan on this server'}), 400
            
            # Find clan
            if db:
                clan = db.clans.find_one({'serverId': server_id, 'tag': clan_tag})
            else:
                clan = next((c for c in clans_storage 
                           if c.get('serverId') == server_id and c.get('tag') == clan_tag), None)
            
            if not clan:
                return jsonify({'error': 'Clan not found'}), 404
            
            # Add user to clan
            if user_id not in clan['members']:
                clan['members'].append(user_id)
                clan['memberCount'] = len(clan['members'])
                clan['lastUpdated'] = datetime.now().isoformat()
                
                # Update clan stats
                update_clan_stats(clan, server_id, db, user_storage)
                
                # Save clan updates
                if db:
                    db.clans.update_one(
                        {'clanId': clan['clanId']},
                        {'$set': {
                            'members': clan['members'],
                            'memberCount': clan['memberCount'],
                            'lastUpdated': clan['lastUpdated'],
                            'stats': clan['stats']
                        }}
                    )
                
                # Set user's clan tag
                set_user_clan_tag(user_id, server_id, clan_tag, db, user_storage)
                
                logger.info(f'🛡️ User {user_id} joined clan {clan["name"]} on server {server_id}')
                
                return jsonify({
                    'success': True, 
                    'memberCount': clan['memberCount'],
                    'clan': clan
                })
            else:
                return jsonify({'error': 'User already in this clan'}), 400
            
        except Exception as e:
            logger.error(f'❌ Error joining clan: {e}')
            return jsonify({'error': 'Failed to join clan'}), 500
    
    @clans_bp.route('/api/clans/leave', methods=['POST'])
    @require_auth
    def leave_clan():
        '''Leave a clan with user database sync'''
        try:
            data = request.get_json()
            user_id = data.get('userId')
            server_id = data.get('serverId')
            
            if not all([user_id, server_id]):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Get user's current clan
            user_info = get_user_info(user_id, db, user_storage)
            clan_tag = user_info.get('servers', {}).get(server_id, {}).get('clanTag')
            
            if not clan_tag:
                return jsonify({'error': 'User not in a clan on this server'}), 400
            
            # Find clan
            if db:
                clan = db.clans.find_one({'serverId': server_id, 'tag': clan_tag})
            else:
                clan = next((c for c in clans_storage 
                           if c.get('serverId') == server_id and c.get('tag') == clan_tag), None)
            
            if not clan:
                return jsonify({'error': 'Clan not found'}), 404
            
            # Remove user from clan
            if user_id in clan['members']:
                clan['members'].remove(user_id)
                clan['memberCount'] = len(clan['members'])
                clan['lastUpdated'] = datetime.now().isoformat()
                
                # If user was leader, assign new leader or delete clan
                if clan['leader'] == user_id:
                    if clan['members']:
                        clan['leader'] = clan['members'][0]  # Assign first member as new leader
                        logger.info(f'🛡️ {clan["members"][0]} is now leader of clan {clan["name"]}')
                    else:
                        # No members left, delete clan
                        if db:
                            db.clans.delete_one({'clanId': clan['clanId']})
                        else:
                            clans_storage.remove(clan)
                        
                        # Remove user's clan tag
                        set_user_clan_tag(user_id, server_id, None, db, user_storage)
                        
                        logger.info(f'🛡️ Clan {clan["name"]} disbanded (no members left)')
                        return jsonify({'success': True, 'disbanded': True})
                
                # Update clan stats
                update_clan_stats(clan, server_id, db, user_storage)
                
                # Save clan updates
                if db:
                    db.clans.update_one(
                        {'clanId': clan['clanId']},
                        {'$set': {
                            'members': clan['members'],
                            'memberCount': clan['memberCount'],
                            'leader': clan['leader'],
                            'lastUpdated': clan['lastUpdated'],
                            'stats': clan['stats']
                        }}
                    )
                
                # Remove user's clan tag
                set_user_clan_tag(user_id, server_id, None, db, user_storage)
                
                logger.info(f'🛡️ User {user_id} left clan {clan["name"]}')
                
                return jsonify({
                    'success': True, 
                    'memberCount': clan['memberCount'],
                    'newLeader': clan['leader'] if clan['leader'] != user_id else None
                })
            else:
                return jsonify({'error': 'User not in this clan'}), 400
            
        except Exception as e:
            logger.error(f'❌ Error leaving clan: {e}')
            return jsonify({'error': 'Failed to leave clan'}), 500
    
    @clans_bp.route('/api/clans/stats/<server_id>')
    @require_auth
    def get_clan_stats(server_id):
        '''Get clan statistics for a server'''
        try:
            if db:
                clans = list(db.clans.find({'serverId': server_id}))
            else:
                clans = [c for c in clans_storage if c.get('serverId') == server_id]
            
            total_clans = len(clans)
            total_clan_members = sum(clan.get('memberCount', 0) for clan in clans)
            
            # Get server user count
            server_users = get_users_on_server(server_id, db, user_storage)
            total_server_users = len(server_users)
            
            # Calculate clan participation rate
            participation_rate = (total_clan_members / total_server_users * 100) if total_server_users > 0 else 0
            
            # Find largest and richest clans
            largest_clan = max(clans, key=lambda x: x.get('memberCount', 0)) if clans else None
            richest_clan = max(clans, key=lambda x: x.get('stats', {}).get('totalWealth', 0)) if clans else None
            
            stats = {
                'totalClans': total_clans,
                'totalClanMembers': total_clan_members,
                'totalServerUsers': total_server_users,
                'participationRate': round(participation_rate, 1),
                'largestClan': {
                    'name': largest_clan.get('name'),
                    'tag': largest_clan.get('tag'),
                    'memberCount': largest_clan.get('memberCount')
                } if largest_clan else None,
                'richestClan': {
                    'name': richest_clan.get('name'),
                    'tag': richest_clan.get('tag'),
                    'totalWealth': richest_clan.get('stats', {}).get('totalWealth', 0)
                } if richest_clan else None
            }
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f'❌ Error getting clan stats: {e}')
            return jsonify({'error': 'Failed to get clan stats'}), 500
    
    @clans_bp.route('/api/clans/user/<user_id>/<server_id>')
    @require_auth
    def get_user_clan_info(user_id, server_id):
        '''Get user's clan information for a specific server'''
        try:
            user_info = get_user_info(user_id, db, user_storage)
            server_data = user_info.get('servers', {}).get(server_id, {})
            clan_tag = server_data.get('clanTag')
            
            if not clan_tag:
                return jsonify({'inClan': False})
            
            # Find clan details
            if db:
                clan = db.clans.find_one({'serverId': server_id, 'tag': clan_tag})
            else:
                clan = next((c for c in clans_storage 
                           if c.get('serverId') == server_id and c.get('tag') == clan_tag), None)
            
            if not clan:
                # Clan doesn't exist but user has tag - clean up
                set_user_clan_tag(user_id, server_id, None, db, user_storage)
                return jsonify({'inClan': False})
            
            return jsonify({
                'inClan': True,
                'clan': clan,
                'isLeader': clan.get('leader') == user_id,
                'joinedAt': server_data.get('joinedAt')
            })
            
        except Exception as e:
            logger.error(f'❌ Error getting user clan info: {e}')
            return jsonify({'error': 'Failed to get user clan info'}), 500
    
    return clans_bp

# Helper functions for user database integration
def ensure_user_on_server(user_id, server_id, db, user_storage):
    '''Ensure user exists in user database and is on server'''
    try:
        if db:
            user = db.users.find_one({'userId': user_id})
            if not user:
                # Create user
                user_data = {
                    'userId': user_id,
                    'nickname': user_id,
                    'internalId': generate_internal_id(),
                    'registeredAt': datetime.now().isoformat(),
                    'lastSeen': datetime.now().isoformat(),
                    'servers': {},
                    'preferences': {'displayNickname': True, 'showInLeaderboards': True},
                    'totalServers': 0
                }
                db.users.insert_one(user_data)
                user = user_data
            
            # Ensure on server
            if server_id not in user.get('servers', {}):
                server_data = {
                    'balance': 0,
                    'clanTag': None,
                    'joinedAt': datetime.now().isoformat(),
                    'gamblingStats': {'totalWagered': 0, 'totalWon': 0, 'gamesPlayed': 0, 'lastPlayed': None},
                    'isActive': True
                }
                db.users.update_one(
                    {'userId': user_id},
                    {'$set': {f'servers.{server_id}': server_data}}
                )
        else:
            user = user_storage.get(user_id)
            if not user:
                user_data = {
                    'userId': user_id,
                    'nickname': user_id,
                    'internalId': generate_internal_id(),
                    'registeredAt': datetime.now().isoformat(),
                    'lastSeen': datetime.now().isoformat(),
                    'servers': {},
                    'preferences': {'displayNickname': True, 'showInLeaderboards': True},
                    'totalServers': 0
                }
                user_storage[user_id] = user_data
                user = user_data
            
            if server_id not in user.get('servers', {}):
                user['servers'][server_id] = {
                    'balance': 0,
                    'clanTag': None,
                    'joinedAt': datetime.now().isoformat(),
                    'gamblingStats': {'totalWagered': 0, 'totalWon': 0, 'gamesPlayed': 0, 'lastPlayed': None},
                    'isActive': True
                }
    except Exception as e:
        logger.error(f'❌ Error ensuring user on server: {e}')

def set_user_clan_tag(user_id, server_id, clan_tag, db, user_storage):
    '''Set user's clan tag for specific server'''
    try:
        if db:
            db.users.update_one(
                {'userId': user_id},
                {'$set': {f'servers.{server_id}.clanTag': clan_tag}}
            )
        else:
            user = user_storage.get(user_id)
            if user and server_id in user.get('servers', {}):
                user['servers'][server_id]['clanTag'] = clan_tag
    except Exception as e:
        logger.error(f'❌ Error setting clan tag: {e}')

def get_user_info(user_id, db, user_storage):
    '''Get user info from user database'''
    try:
        if db:
            return db.users.find_one({'userId': user_id}, {'_id': 0, 'internalId': 0}) or {}
        else:
            user = user_storage.get(user_id, {})
            return {k: v for k, v in user.items() if k != 'internalId'}
    except:
        return {}

def update_clan_stats(clan, server_id, db, user_storage):
    '''Update clan statistics based on member data'''
    try:
        total_wealth = 0
        active_members = 0
        
        for member_id in clan.get('members', []):
            member_info = get_user_info(member_id, db, user_storage)
            server_data = member_info.get('servers', {}).get(server_id, {})
            
            if server_data.get('isActive', True):
                active_members += 1
                total_wealth += server_data.get('balance', 0)
        
        average_balance = total_wealth / active_members if active_members > 0 else 0
        
        clan['stats'] = {
            'totalMembers': len(clan.get('members', [])),
            'activeMembers': active_members,
            'totalWealth': total_wealth,
            'averageBalance': round(average_balance, 2)
        }
    except Exception as e:
        logger.error(f'❌ Error updating clan stats: {e}')

def generate_internal_id():
    '''Generate unique internal ID'''
    return secrets.randbelow(999999999) + 1