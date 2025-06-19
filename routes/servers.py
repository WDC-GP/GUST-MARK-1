"""
GUST Bot Enhanced - Server Management Routes
===========================================
Routes for server management operations
"""

# Standard library imports
from datetime import datetime
import logging

# Third-party imports
from flask import Blueprint, request, jsonify

# Utility imports
from utils.helpers import create_server_data, validate_server_id, validate_region

# Local imports
from routes.auth import require_auth


# GUST database optimization imports
from utils.gust_db_optimization import (
    get_user_with_cache,
    get_user_balance_cached,
    update_user_balance,
    db_performance_monitor
)



logger = logging.getLogger(__name__)

servers_bp = Blueprint('servers', __name__)

def init_servers_routes(app, db, servers_storage):
    """
    Initialize server routes with dependencies
    
    Args:
        app: Flask app instance
        db: Database connection (optional)
        servers_storage: In-memory server storage
    """
    
    @servers_bp.route('/api/servers')
    @require_auth
    def get_servers():
        """Get list of servers"""
        try:
            if db:
                servers = list(db.servers.find({}, {'_id': 0}))
            else:
                servers = servers_storage
            
            logger.info(f"ðŸ“‹ Retrieved {len(servers)} servers")
            return jsonify(servers)
        except Exception as e:
            logger.error(f"âŒ Error retrieving servers: {e}")
            return jsonify({'error': 'Failed to retrieve servers'}), 500
    
    @servers_bp.route('/api/servers/add', methods=['POST'])
    @require_auth
    def add_server():
        """Add new server"""
        try:
            data = request.json
            
            # Validate required fields
            if not data.get('serverId') or not data.get('serverName'):
                return jsonify({'success': False, 'error': 'Server ID and Server Name are required'})
            
            # Validate server ID format
            is_valid, clean_id = validate_server_id(data['serverId'])
            if not is_valid:
                return jsonify({'success': False, 'error': 'Invalid server ID format'})
            
            # Validate region
            if not validate_region(data.get('serverRegion', 'US')):
                return jsonify({'success': False, 'error': 'Invalid server region'})
            
            # Create server data
            server_data = create_server_data(data)
            
            # Check if server already exists
            existing_server = None
            if db:
                existing_server = db.servers.find_one({'serverId': data['serverId']})
            else:
                existing_server = next((s for s in servers_storage if s['serverId'] == data['serverId']), None)
            
            if existing_server:
                return jsonify({'success': False, 'error': 'Server ID already exists'})
            
            # Add server
            if db:
                db.servers.insert_one(server_data)
                logger.info(f"âœ… Server added to database: {data['serverName']} ({data['serverId']})")
            else:
                servers_storage.append(server_data)
                logger.info(f"âœ… Server added to memory: {data['serverName']} ({data['serverId']})")
                
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"âŒ Error adding server: {e}")
            return jsonify({'success': False, 'error': 'Failed to add server'}), 500
    
    @servers_bp.route('/api/servers/update/<server_id>', methods=['POST'])
    @require_auth
    def update_server(server_id):
        """Update server information"""
        try:
            data = request.json
            
            # Validate region if provided
            if data.get('serverRegion') and not validate_region(data['serverRegion']):
                return jsonify({'success': False, 'error': 'Invalid server region'})
            
            update_data = {
                'serverName': data.get('serverName'),
                'serverRegion': data.get('serverRegion'),
                'serverType': data.get('serverType', 'Standard'),
                'description': data.get('description', ''),
                'isFavorite': data.get('isFavorite', False),
                'isActive': data.get('isActive', True),
                'last_updated': datetime.now().isoformat()
            }
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            if db:
                result = db.servers.update_one(
                    {'serverId': server_id},
                    {'$set': update_data}
                )
                success = result.modified_count > 0
            else:
                server = next((s for s in servers_storage if s['serverId'] == server_id), None)
                if server:
                    server.update(update_data)
                    success = True
                else:
                    success = False
            
            if success:
                logger.info(f"âœ… Server updated: {server_id}")
            else:
                logger.warning(f"âš ï¸ Server not found for update: {server_id}")
            
            return jsonify({'success': success})
            
        except Exception as e:
            logger.error(f"âŒ Error updating server {server_id}: {e}")
            return jsonify({'success': False, 'error': 'Failed to update server'}), 500
    
    @servers_bp.route('/api/servers/delete/<server_id>', methods=['DELETE'])
    @require_auth
    def delete_server(server_id):
        """Delete server"""
        try:
            # Get server name for logging
            server_name = "Unknown"
            if db:
                server = db.servers.find_one({'serverId': server_id})
                if server:
                    server_name = server.get('serverName', 'Unknown')
            else:
                server = next((s for s in servers_storage if s['serverId'] == server_id), None)
                if server:
                    server_name = server.get('serverName', 'Unknown')
            
            # Delete server
            if db:
                result = db.servers.delete_one({'serverId': server_id})
                success = result.deleted_count > 0
            else:
                original_count = len(servers_storage)
                servers_storage[:] = [s for s in servers_storage if s['serverId'] != server_id]
                success = len(servers_storage) < original_count
            
            if success:
                logger.info(f"ðŸ—‘ï¸ Server deleted: {server_name} ({server_id})")
            else:
                logger.warning(f"âš ï¸ Server not found for deletion: {server_id}")
            
            return jsonify({'success': success})
            
        except Exception as e:
            logger.error(f"âŒ Error deleting server {server_id}: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete server'}), 500
    
    @servers_bp.route('/api/servers/ping/<server_id>', methods=['POST'])
    @require_auth
    def ping_server(server_id):
        """Ping server to check status"""
        try:
            # Get the main app context to access the console command function
            from flask import current_app
            
            # Try to get the send command function from the app
            gust_bot = getattr(current_app, 'gust_bot', None)
            if not gust_bot:
                return jsonify({'success': False, 'error': 'GUST bot not available'})
            
            # Get server info to determine region
            server = None
            if db:
                server = db.servers.find_one({'serverId': server_id})
            else:
                server = next((s for s in servers_storage if s['serverId'] == server_id), None)
            
            if not server:
                return jsonify({'success': False, 'error': 'Server not found'})
            
            region = server.get('serverRegion', 'US')
            
            # Simple ping using serverinfo command
            result = gust_bot.send_console_command_graphql('serverinfo', server_id, region)
            
            status_data = {
                'status': 'online' if result else 'offline',
                'lastPing': datetime.now().isoformat()
            }
            
            # Update server status
            if db:
                db.servers.update_one(
                    {'serverId': server_id},
                    {'$set': status_data}
                )
            else:
                if server:
                    server.update(status_data)
            
            logger.info(f"ðŸ“¡ Server ping: {server.get('serverName', server_id)} - {status_data['status']}")
            
            return jsonify({'success': True, 'status': status_data['status']})
            
        except Exception as e:
            logger.error(f"âŒ Error pinging server {server_id}: {e}")
            return jsonify({'success': False, 'error': 'Failed to ping server'})
    
    @servers_bp.route('/api/servers/bulk-action', methods=['POST'])
    @require_auth
    def bulk_server_action():
        """Perform bulk actions on servers"""
        try:
            data = request.json
            action = data.get('action')
            server_ids = data.get('serverIds', [])
            
            if not action or not server_ids:
                return jsonify({'success': False, 'error': 'Action and server IDs required'})
            
            results = {}
            
            for server_id in server_ids:
                try:
                    if action == 'delete':
                        # Delete server
                        if db:
                            result = db.servers.delete_one({'serverId': server_id})
                            success = result.deleted_count > 0
                        else:
                            original_count = len(servers_storage)
                            servers_storage[:] = [s for s in servers_storage if s['serverId'] != server_id]
                            success = len(servers_storage) < original_count
                    
                    elif action in ['activate', 'deactivate']:
                        # Update server active status
                        is_active = action == 'activate'
                        update_data = {'isActive': is_active, 'last_updated': datetime.now().isoformat()}
                        
                        if db:
                            result = db.servers.update_one({'serverId': server_id}, {'$set': update_data})
                            success = result.modified_count > 0
                        else:
                            server = next((s for s in servers_storage if s['serverId'] == server_id), None)
                            if server:
                                server.update(update_data)
                                success = True
                            else:
                                success = False
                    
                    elif action == 'ping':
                        # Ping server (simplified version for bulk)
                        success = True  # For bulk operations, assume success
                    
                    else:
                        success = False
                    
                    results[server_id] = success
                    
                except Exception as e:
                    logger.error(f"âŒ Bulk action error for server {server_id}: {e}")
                    results[server_id] = False
            
            successful_count = sum(1 for success in results.values() if success)
            logger.info(f"ðŸ“Š Bulk action '{action}': {successful_count}/{len(server_ids)} successful")
            
            return jsonify({'success': True, 'results': results})
            
        except Exception as e:
            logger.error(f"âŒ Error in bulk server action: {e}")
            return jsonify({'success': False, 'error': 'Bulk action failed'}), 500
    
    @servers_bp.route('/api/servers/<server_id>')
    @require_auth
    def get_server(server_id):
        """Get specific server information"""
        try:
            server = None
            if db:
                server = db.servers.find_one({'serverId': server_id}, {'_id': 0})
            else:
                server = next((s for s in servers_storage if s['serverId'] == server_id), None)
            
            if not server:
                return jsonify({'error': 'Server not found'}), 404
            
            return jsonify(server)
            
        except Exception as e:
            logger.error(f"âŒ Error retrieving server {server_id}: {e}")
            return jsonify({'error': 'Failed to retrieve server'}), 500
    
    @servers_bp.route('/api/servers/stats')
    @require_auth
    def get_server_stats():
        """Get server statistics"""
        try:
            if db:
                total_servers = db.servers.count_documents({})
                active_servers = db.servers.count_documents({'isActive': True})
                online_servers = db.servers.count_documents({'status': 'online'})
            else:
                total_servers = len(servers_storage)
                active_servers = len([s for s in servers_storage if s.get('isActive', True)])
                online_servers = len([s for s in servers_storage if s.get('status') == 'online'])
            
            stats = {
                'total_servers': total_servers,
                'active_servers': active_servers,
                'online_servers': online_servers,
                'offline_servers': total_servers - online_servers
            }
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"âŒ Error getting server stats: {e}")
            return jsonify({'error': 'Failed to get server stats'}), 500
    
    return servers_bp

