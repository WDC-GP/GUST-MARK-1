"""
GUST Bot Enhanced - User Management Routes
==========================================
Routes for user administration, bans, and item management
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import uuid

from routes.auth import require_auth
import logging

logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__)

def init_users_routes(app, gust_bot, db, console_output):
    """
    Initialize user management routes with dependencies
    
    Args:
        app: Flask app instance
        gust_bot: Main GUST bot instance for console commands
        db: Database connection (optional)
        console_output: Console output deque
    """
    
    @users_bp.route('/api/bans/temp', methods=['POST'])
    @require_auth
    def temp_ban_user():
        """Temporarily ban user"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            server_id = data.get('serverId', '').strip()
            duration = data.get('duration', 0)  # minutes
            reason = data.get('reason', '').strip()
            
            if not user_id or not server_id or not duration or not reason:
                return jsonify({'success': False, 'error': 'All fields are required'})
            
            if duration <= 0 or duration > 10080:  # Max 1 week
                return jsonify({'success': False, 'error': 'Duration must be between 1 and 10080 minutes'})
            
            # Get server region for command
            region = 'US'  # Default, should be retrieved from server data
            
            # Send ban command
            command = f'banid "{user_id}" "{reason}"'
            result = gust_bot.send_console_command_graphql(command, server_id, region)
            
            if result:
                # Calculate unban time
                unban_time = datetime.now() + timedelta(minutes=duration)
                
                # Store ban record
                ban_record = {
                    'banId': str(uuid.uuid4()),
                    'userId': user_id,
                    'serverId': server_id,
                    'reason': reason,
                    'duration': duration,
                    'bannedAt': datetime.now().isoformat(),
                    'unbanAt': unban_time.isoformat(),
                    'bannedBy': session.get('username', 'System'),
                    'status': 'active',
                    'type': 'temporary'
                }
                
                if db:
                    db.bans.insert_one(ban_record)
                
                # Add to console output
                console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': f"⚠️ Player {user_id} banned for {duration} minutes on server {server_id}. Reason: {reason}",
                    'status': 'ban',
                    'source': 'ban_system',
                    'type': 'ban'
                })
                
                logger.info(f"🚫 User {user_id} banned on server {server_id} for {duration}m: {reason}")
                
                # Schedule unban (in a real implementation, you'd need a background task)
                # For now, just record that it needs to be unbanned
                return jsonify({
                    'success': True,
                    'banId': ban_record['banId'],
                    'unbanAt': ban_record['unbanAt']
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to execute ban command'})
            
        except Exception as e:
            logger.error(f"❌ Error in temp ban: {e}")
            return jsonify({'success': False, 'error': 'Ban operation failed'}), 500
    
    @users_bp.route('/api/bans/permanent', methods=['POST'])
    @require_auth
    def permanent_ban_user():
        """Permanently ban user"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            server_id = data.get('serverId', '').strip()
            reason = data.get('reason', '').strip()
            
            if not user_id or not server_id or not reason:
                return jsonify({'success': False, 'error': 'User ID, server ID, and reason are required'})
            
            # Get server region for command
            region = 'US'  # Default, should be retrieved from server data
            
            # Send permanent ban command
            command = f'ban "{user_id}" "{reason}"'
            result = gust_bot.send_console_command_graphql(command, server_id, region)
            
            if result:
                # Store ban record
                ban_record = {
                    'banId': str(uuid.uuid4()),
                    'userId': user_id,
                    'serverId': server_id,
                    'reason': reason,
                    'bannedAt': datetime.now().isoformat(),
                    'bannedBy': session.get('username', 'System'),
                    'status': 'active',
                    'type': 'permanent'
                }
                
                if db:
                    db.bans.insert_one(ban_record)
                
                # Add to console output
                console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': f"🚫 Player {user_id} permanently banned on server {server_id}. Reason: {reason}",
                    'status': 'ban',
                    'source': 'ban_system',
                    'type': 'ban'
                })
                
                logger.info(f"🚫 User {user_id} permanently banned on server {server_id}: {reason}")
                
                return jsonify({
                    'success': True,
                    'banId': ban_record['banId']
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to execute ban command'})
            
        except Exception as e:
            logger.error(f"❌ Error in permanent ban: {e}")
            return jsonify({'success': False, 'error': 'Ban operation failed'}), 500
    
    @users_bp.route('/api/bans/unban', methods=['POST'])
    @require_auth
    def unban_user():
        """Unban a user"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            server_id = data.get('serverId', '').strip()
            
            if not user_id or not server_id:
                return jsonify({'success': False, 'error': 'User ID and server ID are required'})
            
            # Get server region for command
            region = 'US'  # Default, should be retrieved from server data
            
            # Send unban command
            command = f'unban "{user_id}"'
            result = gust_bot.send_console_command_graphql(command, server_id, region)
            
            if result:
                # Update ban record status
                if db:
                    db.bans.update_many(
                        {'userId': user_id, 'serverId': server_id, 'status': 'active'},
                        {'$set': {
                            'status': 'unbanned',
                            'unbannedAt': datetime.now().isoformat(),
                            'unbannedBy': session.get('username', 'System')
                        }}
                    )
                
                # Add to console output
                console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': f"✅ Player {user_id} unbanned on server {server_id}",
                    'status': 'unban',
                    'source': 'ban_system',
                    'type': 'ban'
                })
                
                logger.info(f"✅ User {user_id} unbanned on server {server_id}")
                
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Failed to execute unban command'})
            
        except Exception as e:
            logger.error(f"❌ Error in unban: {e}")
            return jsonify({'success': False, 'error': 'Unban operation failed'}), 500
    
    @users_bp.route('/api/items/give', methods=['POST'])
    @require_auth
    def give_item():
        """Give item to player"""
        try:
            data = request.json
            player_id = data.get('playerId', '').strip()
            server_id = data.get('serverId', '').strip()
            item = data.get('item', '').strip()
            amount = data.get('amount', 0)
            
            if not player_id or not server_id or not item or amount <= 0:
                return jsonify({'success': False, 'error': 'All fields are required and amount must be positive'})
            
            if amount > 10000:
                return jsonify({'success': False, 'error': 'Amount cannot exceed 10,000'})
            
            # Get server region for command
            region = 'US'  # Default, should be retrieved from server data
            
            # Send give item command
            command = f'give "{player_id}" "{item}" {amount}'
            result = gust_bot.send_console_command_graphql(command, server_id, region)
            
            if result:
                # Log the item give
                give_record = {
                    'giveId': str(uuid.uuid4()),
                    'playerId': player_id,
                    'serverId': server_id,
                    'item': item,
                    'amount': amount,
                    'givenAt': datetime.now().isoformat(),
                    'givenBy': session.get('username', 'System')
                }
                
                if db:
                    db.item_gives.insert_one(give_record)
                
                # Add to console output
                console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': f"🎁 Gave {amount}x {item} to player {player_id} on server {server_id}",
                    'status': 'item_give',
                    'source': 'item_system',
                    'type': 'system'
                })
                
                logger.info(f"🎁 Gave {amount}x {item} to {player_id} on server {server_id}")
                
                return jsonify({'success': True, 'giveId': give_record['giveId']})
            else:
                return jsonify({'success': False, 'error': 'Failed to execute give command'})
            
        except Exception as e:
            logger.error(f"❌ Error giving item: {e}")
            return jsonify({'success': False, 'error': 'Give item operation failed'}), 500
    
    @users_bp.route('/api/users/kick', methods=['POST'])
    @require_auth
    def kick_user():
        """Kick user from server"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            server_id = data.get('serverId', '').strip()
            reason = data.get('reason', 'Kicked by admin').strip()
            
            if not user_id or not server_id:
                return jsonify({'success': False, 'error': 'User ID and server ID are required'})
            
            # Get server region for command
            region = 'US'  # Default, should be retrieved from server data
            
            # Send kick command
            command = f'kick "{user_id}" "{reason}"'
            result = gust_bot.send_console_command_graphql(command, server_id, region)
            
            if result:
                # Add to console output
                console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': f"👢 Player {user_id} kicked from server {server_id}. Reason: {reason}",
                    'status': 'kick',
                    'source': 'moderation_system',
                    'type': 'system'
                })
                
                logger.info(f"👢 User {user_id} kicked from server {server_id}: {reason}")
                
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Failed to execute kick command'})
            
        except Exception as e:
            logger.error(f"❌ Error kicking user: {e}")
            return jsonify({'success': False, 'error': 'Kick operation failed'}), 500
    
    @users_bp.route('/api/users/teleport', methods=['POST'])
    @require_auth
    def teleport_user():
        """Teleport user to coordinates"""
        try:
            data = request.json
            user_id = data.get('userId', '').strip()
            server_id = data.get('serverId', '').strip()
            x = data.get('x', 0)
            y = data.get('y', 0)
            z = data.get('z', 0)
            
            if not user_id or not server_id:
                return jsonify({'success': False, 'error': 'User ID and server ID are required'})
            
            # Get server region for command
            region = 'US'  # Default, should be retrieved from server data
            
            # Send teleport command
            command = f'teleport "{user_id}" {x} {y} {z}'
            result = gust_bot.send_console_command_graphql(command, server_id, region)
            
            if result:
                # Add to console output
                console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': f"🌀 Player {user_id} teleported to ({x}, {y}, {z}) on server {server_id}",
                    'status': 'teleport',
                    'source': 'admin_system',
                    'type': 'system'
                })
                
                logger.info(f"🌀 User {user_id} teleported to ({x}, {y}, {z}) on server {server_id}")
                
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Failed to execute teleport command'})
            
        except Exception as e:
            logger.error(f"❌ Error teleporting user: {e}")
            return jsonify({'success': False, 'error': 'Teleport operation failed'}), 500
    
    @users_bp.route('/api/bans')
    @require_auth
    def get_bans():
        """Get list of active bans"""
        try:
            limit = int(request.args.get('limit', 50))
            server_id = request.args.get('serverId')
            
            bans = []
            if db:
                query = {'status': 'active'}
                if server_id:
                    query['serverId'] = server_id
                
                cursor = db.bans.find(query, {'_id': 0}).sort('bannedAt', -1).limit(limit)
                bans = list(cursor)
            
            logger.info(f"📋 Retrieved {len(bans)} active bans")
            return jsonify(bans)
            
        except Exception as e:
            logger.error(f"❌ Error retrieving bans: {e}")
            return jsonify({'error': 'Failed to retrieve bans'}), 500
    
    @users_bp.route('/api/users/<user_id>/history')
    @require_auth
    def get_user_history(user_id):
        """Get user's action history"""
        try:
            limit = int(request.args.get('limit', 20))
            
            history = []
            if db:
                # Get ban history
                bans = list(db.bans.find({'userId': user_id}, {'_id': 0}).sort('bannedAt', -1).limit(limit//2))
                for ban in bans:
                    ban['action_type'] = 'ban'
                
                # Get item give history
                gives = list(db.item_gives.find({'playerId': user_id}, {'_id': 0}).sort('givenAt', -1).limit(limit//2))
                for give in gives:
                    give['action_type'] = 'item_give'
                
                history = bans + gives
                history.sort(key=lambda x: x.get('bannedAt') or x.get('givenAt'), reverse=True)
                history = history[:limit]
            
            logger.info(f"📋 Retrieved {len(history)} history entries for user {user_id}")
            return jsonify(history)
            
        except Exception as e:
            logger.error(f"❌ Error retrieving user history for {user_id}: {e}")
            return jsonify({'error': 'Failed to retrieve user history'}), 500
    
    @users_bp.route('/api/users/search')
    @require_auth
    def search_users():
        """Search for users by ID or name"""
        try:
            query = request.args.get('q', '').strip()
            limit = int(request.args.get('limit', 10))
            
            if not query:
                return jsonify({'users': []})
            
            users = []
            if db:
                # Search in bans collection for user IDs
                ban_users = db.bans.distinct('userId', {'userId': {'$regex': query, '$options': 'i'}})
                
                # Search in item gives collection
                give_users = db.item_gives.distinct('playerId', {'playerId': {'$regex': query, '$options': 'i'}})
                
                # Combine and deduplicate
                all_users = list(set(ban_users + give_users))
                users = [{'userId': user_id} for user_id in all_users[:limit]]
            
            logger.info(f"🔍 User search for '{query}' returned {len(users)} results")
            return jsonify({'users': users})
            
        except Exception as e:
            logger.error(f"❌ Error searching users: {e}")
            return jsonify({'error': 'Failed to search users'}), 500
    
    @users_bp.route('/api/users/stats')
    @require_auth
    def get_user_stats():
        """Get user management statistics"""
        try:
            stats = {
                'total_bans': 0,
                'active_bans': 0,
                'temporary_bans': 0,
                'permanent_bans': 0,
                'total_items_given': 0,
                'unique_banned_users': 0,
                'most_banned_user': None
            }
            
            if db:
                # Ban statistics
                stats['total_bans'] = db.bans.count_documents({})
                stats['active_bans'] = db.bans.count_documents({'status': 'active'})
                stats['temporary_bans'] = db.bans.count_documents({'type': 'temporary'})
                stats['permanent_bans'] = db.bans.count_documents({'type': 'permanent'})
                
                # Item give statistics
                stats['total_items_given'] = db.item_gives.count_documents({})
                
                # Unique banned users
                stats['unique_banned_users'] = len(db.bans.distinct('userId'))
                
                # Most banned user
                pipeline = [
                    {'$group': {'_id': '$userId', 'ban_count': {'$sum': 1}}},
                    {'$sort': {'ban_count': -1}},
                    {'$limit': 1}
                ]
                
                result = list(db.bans.aggregate(pipeline))
                if result:
                    stats['most_banned_user'] = {
                        'userId': result[0]['_id'],
                        'banCount': result[0]['ban_count']
                    }
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"❌ Error getting user stats: {e}")
            return jsonify({'error': 'Failed to get user statistics'}), 500
    
    return users_bp
