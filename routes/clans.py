"""
GUST Bot Enhanced - Clan Management Routes
==========================================
Routes for clan creation, management, and member operations
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid

from routes.auth import require_auth
import logging

logger = logging.getLogger(__name__)

clans_bp = Blueprint('clans', __name__)

def init_clans_routes(app, db, clans_storage):
    """
    Initialize clan routes with dependencies
    
    Args:
        app: Flask app instance
        db: Database connection (optional)
        clans_storage: In-memory clans storage
    """
    
    @clans_bp.route('/api/clans')
    @require_auth
    def get_clans():
        """Get list of clans"""
        try:
            if db:
                clans = list(db.clans.find({}, {'_id': 0}))
            else:
                clans = clans_storage
            
            logger.info(f"🛡️ Retrieved {len(clans)} clans")
            return jsonify(clans)
            
        except Exception as e:
            logger.error(f"❌ Error retrieving clans: {e}")
            return jsonify({'error': 'Failed to retrieve clans'}), 500
    
    @clans_bp.route('/api/clans/create', methods=['POST'])
    @require_auth
    def create_clan():
        """Create new clan"""
        try:
            data = request.json
            name = data.get('name', '').strip()
            leader = data.get('leader', '').strip()
            server_id = data.get('serverId', '').strip()
            description = data.get('description', '').strip()
            
            if not name or not leader or not server_id:
                return jsonify({'success': False, 'error': 'Name, leader, and server ID are required'})
            
            # Check if clan name already exists
            existing_clan = None
            if db:
                existing_clan = db.clans.find_one({'name': name})
            else:
                existing_clan = next((c for c in clans_storage if c['name'] == name), None)
            
            if existing_clan:
                return jsonify({'success': False, 'error': 'Clan name already exists'})
            
            # Create clan data
            clan = {
                'clanId': str(uuid.uuid4()),
                'name': name,
                'leader': leader,
                'members': [leader],
                'createdDate': datetime.now().isoformat(),
                'serverId': server_id,
                'description': description,
                'isActive': True,
                'memberCount': 1,
                'level': 1,
                'experience': 0,
                'bank': 0,
                'settings': {
                    'public': True,
                    'autoAccept': False,
                    'requireApproval': True
                }
            }
            
            # Save clan
            if db:
                db.clans.insert_one(clan)
                logger.info(f"🛡️ Clan created in database: {name} by {leader}")
            else:
                clans_storage.append(clan)
                logger.info(f"🛡️ Clan created in memory: {name} by {leader}")
            
            return jsonify({'success': True, 'clanId': clan['clanId']})
            
        except Exception as e:
            logger.error(f"❌ Error creating clan: {e}")
            return jsonify({'success': False, 'error': 'Failed to create clan'}), 500
    
    @clans_bp.route('/api/clans/<clan_id>')
    @require_auth
    def get_clan(clan_id):
        """Get specific clan information"""
        try:
            clan = None
            if db:
                clan = db.clans.find_one({'clanId': clan_id}, {'_id': 0})
            else:
                clan = next((c for c in clans_storage if c['clanId'] == clan_id), None)
            
            if not clan:
                return jsonify({'error': 'Clan not found'}), 404
            
            return jsonify(clan)
            
        except Exception as e:
            logger.error(f"❌ Error retrieving clan {clan_id}: {e}")
            return jsonify({'error': 'Failed to retrieve clan'}), 500
    
    @clans_bp.route('/api/clans/<clan_id>/join', methods=['POST'])
    @require_auth
    def join_clan(clan_id):
        """Join a clan"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID is required'})
            
            # Find clan
            clan = None
            if db:
                clan = db.clans.find_one({'clanId': clan_id})
            else:
                clan = next((c for c in clans_storage if c['clanId'] == clan_id), None)
            
            if not clan:
                return jsonify({'success': False, 'error': 'Clan not found'})
            
            # Check if user is already a member
            if user_id in clan.get('members', []):
                return jsonify({'success': False, 'error': 'User is already a member'})
            
            # Add user to clan
            clan['members'].append(user_id)
            clan['memberCount'] = len(clan['members'])
            clan['lastUpdated'] = datetime.now().isoformat()
            
            # Update clan
            if db:
                db.clans.update_one(
                    {'clanId': clan_id},
                    {'$set': {
                        'members': clan['members'],
                        'memberCount': clan['memberCount'],
                        'lastUpdated': clan['lastUpdated']
                    }}
                )
            
            logger.info(f"🛡️ User {user_id} joined clan {clan['name']}")
            
            return jsonify({'success': True, 'memberCount': clan['memberCount']})
            
        except Exception as e:
            logger.error(f"❌ Error joining clan {clan_id}: {e}")
            return jsonify({'success': False, 'error': 'Failed to join clan'}), 500
    
    @clans_bp.route('/api/clans/<clan_id>/leave', methods=['POST'])
    @require_auth
    def leave_clan(clan_id):
        """Leave a clan"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID is required'})
            
            # Find clan
            clan = None
            if db:
                clan = db.clans.find_one({'clanId': clan_id})
            else:
                clan = next((c for c in clans_storage if c['clanId'] == clan_id), None)
            
            if not clan:
                return jsonify({'success': False, 'error': 'Clan not found'})
            
            # Check if user is a member
            if user_id not in clan.get('members', []):
                return jsonify({'success': False, 'error': 'User is not a member'})
            
            # Check if user is the leader
            if user_id == clan.get('leader'):
                # If clan has other members, transfer leadership
                if len(clan['members']) > 1:
                    new_leader = next(member for member in clan['members'] if member != user_id)
                    clan['leader'] = new_leader
                    logger.info(f"🛡️ Leadership transferred to {new_leader} in clan {clan['name']}")
                else:
                    # Delete clan if leader is the only member
                    if db:
                        db.clans.delete_one({'clanId': clan_id})
                    else:
                        clans_storage[:] = [c for c in clans_storage if c['clanId'] != clan_id]
                    
                    logger.info(f"🛡️ Clan {clan['name']} deleted (last member left)")
                    return jsonify({'success': True, 'clanDeleted': True})
            
            # Remove user from clan
            clan['members'].remove(user_id)
            clan['memberCount'] = len(clan['members'])
            clan['lastUpdated'] = datetime.now().isoformat()
            
            # Update clan
            if db:
                db.clans.update_one(
                    {'clanId': clan_id},
                    {'$set': {
                        'members': clan['members'],
                        'memberCount': clan['memberCount'],
                        'leader': clan['leader'],
                        'lastUpdated': clan['lastUpdated']
                    }}
                )
            
            logger.info(f"🛡️ User {user_id} left clan {clan['name']}")
            
            return jsonify({'success': True, 'memberCount': clan['memberCount']})
            
        except Exception as e:
            logger.error(f"❌ Error leaving clan {clan_id}: {e}")
            return jsonify({'success': False, 'error': 'Failed to leave clan'}), 500
    
    @clans_bp.route('/api/clans/<clan_id>/kick', methods=['POST'])
    @require_auth
    def kick_member(clan_id):
        """Kick a member from clan (leader only)"""
        try:
            data = request.json
            leader_id = data.get('leaderId', '').strip()
            target_id = data.get('targetId', '').strip()
            
            if not leader_id or not target_id:
                return jsonify({'success': False, 'error': 'Leader ID and target ID are required'})
            
            # Find clan
            clan = None
            if db:
                clan = db.clans.find_one({'clanId': clan_id})
            else:
                clan = next((c for c in clans_storage if c['clanId'] == clan_id), None)
            
            if not clan:
                return jsonify({'success': False, 'error': 'Clan not found'})
            
            # Check if requester is the leader
            if leader_id != clan.get('leader'):
                return jsonify({'success': False, 'error': 'Only clan leader can kick members'})
            
            # Check if target is a member
            if target_id not in clan.get('members', []):
                return jsonify({'success': False, 'error': 'Target is not a member'})
            
            # Cannot kick yourself
            if leader_id == target_id:
                return jsonify({'success': False, 'error': 'Cannot kick yourself'})
            
            # Remove target from clan
            clan['members'].remove(target_id)
            clan['memberCount'] = len(clan['members'])
            clan['lastUpdated'] = datetime.now().isoformat()
            
            # Update clan
            if db:
                db.clans.update_one(
                    {'clanId': clan_id},
                    {'$set': {
                        'members': clan['members'],
                        'memberCount': clan['memberCount'],
                        'lastUpdated': clan['lastUpdated']
                    }}
                )
            
            logger.info(f"🛡️ User {target_id} kicked from clan {clan['name']} by {leader_id}")
            
            return jsonify({'success': True, 'memberCount': clan['memberCount']})
            
        except Exception as e:
            logger.error(f"❌ Error kicking member from clan {clan_id}: {e}")
            return jsonify({'success': False, 'error': 'Failed to kick member'}), 500
    
    @clans_bp.route('/api/clans/<clan_id>/update', methods=['POST'])
    @require_auth
    def update_clan(clan_id):
        """Update clan settings (leader only)"""
        try:
            data = request.json
            leader_id = data.get('leaderId', '').strip()
            
            if not leader_id:
                return jsonify({'success': False, 'error': 'Leader ID is required'})
            
            # Find clan
            clan = None
            if db:
                clan = db.clans.find_one({'clanId': clan_id})
            else:
                clan = next((c for c in clans_storage if c['clanId'] == clan_id), None)
            
            if not clan:
                return jsonify({'success': False, 'error': 'Clan not found'})
            
            # Check if requester is the leader
            if leader_id != clan.get('leader'):
                return jsonify({'success': False, 'error': 'Only clan leader can update settings'})
            
            # Update allowed fields
            update_data = {}
            if 'description' in data:
                update_data['description'] = data['description'].strip()
            if 'settings' in data:
                update_data['settings'] = data['settings']
            
            update_data['lastUpdated'] = datetime.now().isoformat()
            
            # Apply updates
            clan.update(update_data)
            
            # Save changes
            if db:
                db.clans.update_one(
                    {'clanId': clan_id},
                    {'$set': update_data}
                )
            
            logger.info(f"🛡️ Clan {clan['name']} updated by {leader_id}")
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"❌ Error updating clan {clan_id}: {e}")
            return jsonify({'success': False, 'error': 'Failed to update clan'}), 500
    
    @clans_bp.route('/api/clans/<clan_id>/delete', methods=['DELETE'])
    @require_auth
    def delete_clan(clan_id):
        """Delete clan (leader only)"""
        try:
            data = request.json
            leader_id = data.get('leaderId', '').strip()
            
            if not leader_id:
                return jsonify({'success': False, 'error': 'Leader ID is required'})
            
            # Find clan
            clan = None
            if db:
                clan = db.clans.find_one({'clanId': clan_id})
            else:
                clan = next((c for c in clans_storage if c['clanId'] == clan_id), None)
            
            if not clan:
                return jsonify({'success': False, 'error': 'Clan not found'})
            
            # Check if requester is the leader
            if leader_id != clan.get('leader'):
                return jsonify({'success': False, 'error': 'Only clan leader can delete clan'})
            
            # Delete clan
            if db:
                result = db.clans.delete_one({'clanId': clan_id})
                success = result.deleted_count > 0
            else:
                original_count = len(clans_storage)
                clans_storage[:] = [c for c in clans_storage if c['clanId'] != clan_id]
                success = len(clans_storage) < original_count
            
            if success:
                logger.info(f"🗑️ Clan {clan['name']} deleted by {leader_id}")
            
            return jsonify({'success': success})
            
        except Exception as e:
            logger.error(f"❌ Error deleting clan {clan_id}: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete clan'}), 500
    
    @clans_bp.route('/api/clans/user/<user_id>')
    @require_auth
    def get_user_clan(user_id):
        """Get clan that user belongs to"""
        try:
            user_clan = None
            
            if db:
                user_clan = db.clans.find_one({'members': user_id}, {'_id': 0})
            else:
                user_clan = next((c for c in clans_storage if user_id in c.get('members', [])), None)
            
            if not user_clan:
                return jsonify({'clan': None})
            
            return jsonify({'clan': user_clan})
            
        except Exception as e:
            logger.error(f"❌ Error getting clan for user {user_id}: {e}")
            return jsonify({'error': 'Failed to get user clan'}), 500
    
    @clans_bp.route('/api/clans/server/<server_id>')
    @require_auth
    def get_server_clans(server_id):
        """Get all clans for a specific server"""
        try:
            if db:
                clans = list(db.clans.find({'serverId': server_id}, {'_id': 0}))
            else:
                clans = [c for c in clans_storage if c.get('serverId') == server_id]
            
            logger.info(f"🛡️ Retrieved {len(clans)} clans for server {server_id}")
            return jsonify(clans)
            
        except Exception as e:
            logger.error(f"❌ Error getting clans for server {server_id}: {e}")
            return jsonify({'error': 'Failed to get server clans'}), 500
    
    @clans_bp.route('/api/clans/stats')
    @require_auth
    def get_clan_stats():
        """Get clan system statistics"""
        try:
            stats = {
                'total_clans': 0,
                'total_members': 0,
                'average_clan_size': 0,
                'largest_clan': None,
                'most_active_server': None
            }
            
            if db:
                # Get basic stats
                stats['total_clans'] = db.clans.count_documents({})
                
                # Get member statistics
                pipeline = [
                    {
                        '$group': {
                            '_id': None,
                            'total_members': {'$sum': '$memberCount'},
                            'average_size': {'$avg': '$memberCount'},
                            'max_size': {'$max': '$memberCount'}
                        }
                    }
                ]
                
                result = list(db.clans.aggregate(pipeline))
                if result:
                    data = result[0]
                    stats['total_members'] = data.get('total_members', 0)
                    stats['average_clan_size'] = round(data.get('average_size', 0), 2)
                
                # Find largest clan
                largest = db.clans.find_one({}, sort=[('memberCount', -1)])
                if largest:
                    stats['largest_clan'] = {
                        'name': largest['name'],
                        'memberCount': largest['memberCount']
                    }
                
                # Find most active server
                server_pipeline = [
                    {
                        '$group': {
                            '_id': '$serverId',
                            'clan_count': {'$sum': 1}
                        }
                    },
                    {'$sort': {'clan_count': -1}},
                    {'$limit': 1}
                ]
                
                server_result = list(db.clans.aggregate(server_pipeline))
                if server_result:
                    stats['most_active_server'] = {
                        'serverId': server_result[0]['_id'],
                        'clanCount': server_result[0]['clan_count']
                    }
                
            else:
                # Calculate from in-memory storage
                stats['total_clans'] = len(clans_storage)
                if clans_storage:
                    stats['total_members'] = sum(c.get('memberCount', 0) for c in clans_storage)
                    stats['average_clan_size'] = round(stats['total_members'] / stats['total_clans'], 2)
                    
                    # Find largest clan
                    largest = max(clans_storage, key=lambda c: c.get('memberCount', 0))
                    stats['largest_clan'] = {
                        'name': largest['name'],
                        'memberCount': largest['memberCount']
                    }
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"❌ Error getting clan stats: {e}")
            return jsonify({'error': 'Failed to get clan statistics'}), 500
    
    return clans_bp
