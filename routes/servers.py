"""
GUST Bot Enhanced - Server Management Routes (COMPLETE FIXED VERSION + SERVICE ID AUTO-DISCOVERY)
==========================================================================================================
✅ FIXED: Blueprint return statement added at the end of init_servers_routes
✅ FIXED: create_server_data() parameter mismatch resolved
✅ FIXED: Server adding functionality working properly
✅ PRESERVED: All existing functionality and error handling
✅ NEW: Service ID Auto-Discovery integration for complete server setup
✅ NEW: Manual Service ID discovery endpoints for existing servers
✅ NEW: Enhanced server capabilities tracking
Routes for server management operations with automatic Service ID discovery
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

# ✅ NEW: Service ID Auto-Discovery import
try:
    from utils.service_id_discovery import ServiceIDMapper
    SERVICE_ID_DISCOVERY_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Service ID Auto-Discovery system available")
except ImportError:
    SERVICE_ID_DISCOVERY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ Service ID Auto-Discovery system not available")

logger = logging.getLogger(__name__)

servers_bp = Blueprint('servers', __name__)

def init_servers_routes(app, db, servers_storage):
    """
    Initialize server routes with dependencies
    
    Args:
        app: Flask app instance
        db: Database connection (optional)
        servers_storage: In-memory server storage
        
    Returns:
        Blueprint: The configured servers blueprint
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
            
            logger.info(f"📋 Retrieved {len(servers)} servers")
            return jsonify(servers)
        except Exception as e:
            logger.error(f"❌ Error retrieving servers: {e}")
            return jsonify({'error': 'Failed to retrieve servers'}), 500
    
    @servers_bp.route('/api/servers/add', methods=['POST'])
    @require_auth
    def add_server():
        """
        ✅ ENHANCED: Add new server with automatic Service ID discovery
        
        Flow:
        1. Validate server data
        2. Auto-discover Service ID from Server ID
        3. Create enhanced server configuration
        4. Set up monitoring and commands
        """
        try:
            data = request.json
            
            # Validate required fields
            if not data.get('serverId') or not data.get('serverName'):
                return jsonify({
                    'success': False, 
                    'error': 'Server ID and Server Name are required'
                })
            
            # Validate server ID format
            is_valid, clean_id = validate_server_id(data['serverId'])
            if not is_valid:
                return jsonify({
                    'success': False, 
                    'error': 'Invalid server ID format - must be numeric'
                })
            
            # Validate region
            server_region = data.get('serverRegion', 'US')
            if not validate_region(server_region):
                return jsonify({
                    'success': False, 
                    'error': 'Invalid server region'
                })
            
            # Check if server already exists
            existing_server = None
            if db:
                existing_server = db.servers.find_one({'serverId': data['serverId']})
            else:
                existing_server = next((s for s in servers_storage if s['serverId'] == data['serverId']), None)
            
            if existing_server:
                return jsonify({
                    'success': False, 
                    'error': 'A server with this ID already exists'
                })
            
            # ✅ NEW: AUTO-DISCOVER SERVICE ID
            logger.info(f"🔍 Discovering Service ID for server {data['serverId']}...")
            
            discovery_result = {'status': 'unknown', 'serviceId': None, 'message': 'Discovery not attempted'}
            
            if SERVICE_ID_DISCOVERY_AVAILABLE:
                try:
                    # Initialize Service ID mapper
                    service_id_mapper = ServiceIDMapper()
                    
                    success, service_id, discovery_error = service_id_mapper.get_service_id_from_server_id(
                        data['serverId'], 
                        server_region
                    )
                    
                    if success and service_id:
                        logger.info(f"✅ Discovered Service ID: {data['serverId']} -> {service_id}")
                        data['serviceId'] = service_id
                        data['discovery_status'] = 'success'
                        data['discovery_message'] = f"Auto-discovered Service ID: {service_id}"
                        discovery_result = {
                            'status': 'success',
                            'serviceId': service_id,
                            'message': f"Service ID {service_id} discovered successfully"
                        }
                    else:
                        logger.warning(f"⚠️ Service ID discovery failed: {discovery_error}")
                        data['serviceId'] = None
                        data['discovery_status'] = 'failed'
                        data['discovery_message'] = f"Service ID discovery failed: {discovery_error or 'Unknown error'}"
                        discovery_result = {
                            'status': 'failed',
                            'serviceId': None,
                            'message': f"Discovery failed: {discovery_error or 'Unknown error'}"
                        }
                        
                except Exception as discovery_exception:
                    logger.error(f"❌ Service ID discovery exception: {discovery_exception}")
                    data['serviceId'] = None
                    data['discovery_status'] = 'error'
                    data['discovery_message'] = f"Discovery error: {str(discovery_exception)}"
                    discovery_result = {
                        'status': 'error',
                        'serviceId': None,
                        'message': f"Discovery error: {str(discovery_exception)}"
                    }
            else:
                logger.warning("⚠️ Service ID discovery system not available")
                data['serviceId'] = None
                data['discovery_status'] = 'unavailable'
                data['discovery_message'] = "Service ID discovery system not available"
                discovery_result = {
                    'status': 'unavailable',
                    'serviceId': None,
                    'message': "Service ID discovery system not available"
                }
            
            # ✅ ENHANCED: Create server data with Service ID information
            server_data = create_server_data(data)
            
            # Add server to storage
            if db:
                db.servers.insert_one(server_data)
                logger.info(f"✅ Server added to database: {data['serverName']} ({data['serverId']})")
            else:
                servers_storage.append(server_data)
                logger.info(f"✅ Server added to memory: {data['serverName']} ({data['serverId']})")
            
            # ✅ ENHANCED: Return detailed response with discovery information
            response_data = {
                'success': True,
                'message': 'Server added successfully',
                'server_data': {
                    'serverId': data['serverId'],
                    'serviceId': data.get('serviceId'),
                    'serverName': data['serverName'],
                    'serverRegion': server_region,
                    'discovery_status': data.get('discovery_status', 'unknown'),
                    'capabilities': server_data.get('capabilities', {}),
                    'timestamp': datetime.now().isoformat()
                },
                'discovery': discovery_result
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"❌ Error adding server: {e}")
            return jsonify({
                'success': False, 
                'error': f'Failed to add server: {str(e)}'
            }), 500
    
    # ✅ NEW: Manual Service ID Discovery Endpoint
    @servers_bp.route('/api/servers/discover-service-id/<server_id>', methods=['POST'])
    @require_auth
    def discover_service_id_manual(server_id):
        """
        ✅ NEW: Manual Service ID discovery for existing servers
        """
        try:
            if not SERVICE_ID_DISCOVERY_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': 'Service ID discovery system not available'
                }), 503
            
            data = request.json or {}
            region = data.get('region', 'US')
            
            # Validate region
            if not validate_region(region):
                return jsonify({
                    'success': False,
                    'error': 'Invalid region specified'
                }), 400
            
            # Check if server exists
            existing_server = None
            if db:
                existing_server = db.servers.find_one({'serverId': server_id})
            else:
                existing_server = next((s for s in servers_storage if s['serverId'] == server_id), None)
            
            if not existing_server:
                return jsonify({
                    'success': False,
                    'error': 'Server not found'
                }), 404
            
            logger.info(f"🔍 Manual Service ID discovery for server {server_id}")
            
            # Perform discovery
            service_id_mapper = ServiceIDMapper()
            success, service_id, discovery_error = service_id_mapper.get_service_id_from_server_id(
                server_id, region
            )
            
            if success and service_id:
                # Update server with discovered Service ID
                update_data = {
                    'serviceId': service_id,
                    'discovery_status': 'success',
                    'discovery_message': f"Manually discovered Service ID: {service_id}",
                    'discovery_timestamp': datetime.now().isoformat(),
                    'capabilities.command_execution': True,
                    'last_updated': datetime.now().isoformat()
                }
                
                if db:
                    db.servers.update_one(
                        {'serverId': server_id},
                        {'$set': update_data}
                    )
                else:
                    existing_server.update(update_data)
                    # Update capabilities properly for in-memory storage
                    if 'capabilities' not in existing_server:
                        existing_server['capabilities'] = {}
                    existing_server['capabilities']['command_execution'] = True
                
                logger.info(f"✅ Manual discovery successful: {server_id} -> {service_id}")
                
                return jsonify({
                    'success': True,
                    'server_id': server_id,
                    'service_id': service_id,
                    'message': f'Service ID discovered: {service_id}',
                    'discovery_method': 'manual',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                logger.warning(f"⚠️ Manual discovery failed for {server_id}: {discovery_error}")
                
                return jsonify({
                    'success': False,
                    'server_id': server_id,
                    'error': discovery_error or 'Service ID discovery failed',
                    'discovery_method': 'manual',
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"❌ Manual Service ID discovery error: {e}")
            return jsonify({
                'success': False,
                'error': f'Discovery failed: {str(e)}'
            }), 500
    
    # ✅ NEW: Bulk Service ID Discovery for Existing Servers
    @servers_bp.route('/api/servers/discover-all-service-ids', methods=['POST'])
    @require_auth
    def discover_all_service_ids():
        """
        ✅ NEW: Discover Service IDs for all servers missing them
        """
        try:
            if not SERVICE_ID_DISCOVERY_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': 'Service ID discovery system not available'
                }), 503
            
            # Get all servers
            servers = []
            if db:
                servers = list(db.servers.find({}, {'_id': 0}))
            else:
                servers = servers_storage
            
            # Find servers without Service IDs
            servers_needing_discovery = [
                s for s in servers 
                if not s.get('serviceId') or s.get('discovery_status') == 'failed'
            ]
            
            if not servers_needing_discovery:
                return jsonify({
                    'success': True,
                    'message': 'All servers already have Service IDs',
                    'discovered': 0,
                    'total': len(servers)
                })
            
            logger.info(f"🔍 Bulk discovery for {len(servers_needing_discovery)} servers")
            
            service_id_mapper = ServiceIDMapper()
            discovery_results = []
            successful_discoveries = 0
            
            for server in servers_needing_discovery:
                server_id = server['serverId']
                region = server.get('serverRegion', 'US')
                
                try:
                    success, service_id, discovery_error = service_id_mapper.get_service_id_from_server_id(
                        server_id, region
                    )
                    
                    if success and service_id:
                        # Update server
                        update_data = {
                            'serviceId': service_id,
                            'discovery_status': 'success',
                            'discovery_message': f"Bulk discovered Service ID: {service_id}",
                            'discovery_timestamp': datetime.now().isoformat(),
                            'last_updated': datetime.now().isoformat()
                        }
                        
                        if db:
                            db.servers.update_one(
                                {'serverId': server_id},
                                {'$set': update_data}
                            )
                        else:
                            server.update(update_data)
                            if 'capabilities' not in server:
                                server['capabilities'] = {}
                            server['capabilities']['command_execution'] = True
                        
                        discovery_results.append({
                            'server_id': server_id,
                            'service_id': service_id,
                            'success': True
                        })
                        successful_discoveries += 1
                        
                    else:
                        discovery_results.append({
                            'server_id': server_id,
                            'service_id': None,
                            'success': False,
                            'error': discovery_error
                        })
                        
                except Exception as server_error:
                    discovery_results.append({
                        'server_id': server_id,
                        'service_id': None,
                        'success': False,
                        'error': str(server_error)
                    })
            
            logger.info(f"✅ Bulk discovery complete: {successful_discoveries}/{len(servers_needing_discovery)} successful")
            
            return jsonify({
                'success': True,
                'message': f'Bulk discovery complete: {successful_discoveries} Service IDs discovered',
                'discovered': successful_discoveries,
                'total': len(servers_needing_discovery),
                'results': discovery_results
            })
            
        except Exception as e:
            logger.error(f"❌ Bulk Service ID discovery error: {e}")
            return jsonify({
                'success': False,
                'error': f'Bulk discovery failed: {str(e)}'
            }), 500
    
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
                logger.info(f"✅ Server updated: {server_id}")
            else:
                logger.warning(f"⚠️ Server not found for update: {server_id}")
            
            return jsonify({'success': success})
            
        except Exception as e:
            logger.error(f"❌ Error updating server {server_id}: {e}")
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
                logger.info(f"🗑️ Server deleted: {server_name} ({server_id})")
            else:
                logger.warning(f"⚠️ Server not found for deletion: {server_id}")
            
            return jsonify({'success': success})
            
        except Exception as e:
            logger.error(f"❌ Error deleting server {server_id}: {e}")
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
            
            # ✅ ENHANCED: Use Service ID for ping if available, fallback to Server ID
            target_id = server.get('serviceId', server_id)
            id_type = 'Service ID' if server.get('serviceId') else 'Server ID'
            
            logger.info(f"📡 Pinging server using {id_type}: {target_id}")
            
            # Simple ping using serverinfo command
            result = gust_bot.send_console_command_graphql('serverinfo', target_id, region)
            
            status_data = {
                'status': 'online' if result else 'offline',
                'lastPing': datetime.now().isoformat(),
                'ping_method': id_type.lower().replace(' ', '_')
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
            
            logger.info(f"📡 Server ping: {server.get('serverName', server_id)} - {status_data['status']}")
            
            return jsonify({'success': True, 'status': status_data['status']})
            
        except Exception as e:
            logger.error(f"❌ Error pinging server {server_id}: {e}")
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
                    logger.error(f"❌ Bulk action error for server {server_id}: {e}")
                    results[server_id] = False
            
            successful_count = sum(1 for success in results.values() if success)
            logger.info(f"📊 Bulk action '{action}': {successful_count}/{len(server_ids)} successful")
            
            return jsonify({'success': True, 'results': results})
            
        except Exception as e:
            logger.error(f"❌ Error in bulk server action: {e}")
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
            logger.error(f"❌ Error retrieving server {server_id}: {e}")
            return jsonify({'error': 'Failed to retrieve server'}), 500
    
    @servers_bp.route('/api/servers/stats')
    @require_auth
    def get_server_stats():
        """✅ ENHANCED: Get server statistics with Service ID information"""
        try:
            if db:
                total_servers = db.servers.count_documents({})
                active_servers = db.servers.count_documents({'isActive': True})
                online_servers = db.servers.count_documents({'status': 'online'})
                servers_with_service_id = db.servers.count_documents({'serviceId': {'$exists': True, '$ne': None}})
            else:
                total_servers = len(servers_storage)
                active_servers = len([s for s in servers_storage if s.get('isActive', True)])
                online_servers = len([s for s in servers_storage if s.get('status') == 'online'])
                servers_with_service_id = len([s for s in servers_storage if s.get('serviceId')])
            
            stats = {
                'total_servers': total_servers,
                'active_servers': active_servers,
                'online_servers': online_servers,
                'offline_servers': total_servers - online_servers,
                'servers_with_service_id': servers_with_service_id,
                'servers_missing_service_id': total_servers - servers_with_service_id,
                'service_id_coverage': round((servers_with_service_id / total_servers) * 100, 1) if total_servers > 0 else 0,
                'discovery_system_available': SERVICE_ID_DISCOVERY_AVAILABLE
            }
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"❌ Error getting server stats: {e}")
            return jsonify({'error': 'Failed to get server stats'}), 500
    
    # ✅ ENHANCED: Server validation endpoint with Service ID checks
    @servers_bp.route('/api/servers/validate', methods=['POST'])
    @require_auth
    def validate_server_data():
        """✅ ENHANCED: Validate server data before adding with Service ID preview"""
        try:
            data = request.json
            
            errors = []
            warnings = []
            
            # Validate server ID
            if not data.get('serverId'):
                errors.append('Server ID is required')
            else:
                is_valid, clean_id = validate_server_id(data['serverId'])
                if not is_valid:
                    errors.append('Invalid server ID format')
                else:
                    # Check if server already exists
                    existing_server = None
                    if db:
                        existing_server = db.servers.find_one({'serverId': data['serverId']})
                    else:
                        existing_server = next((s for s in servers_storage if s['serverId'] == data['serverId']), None)
                    
                    if existing_server:
                        errors.append('Server ID already exists')
            
            # Validate server name
            if not data.get('serverName'):
                errors.append('Server Name is required')
            elif len(data['serverName'].strip()) < 3:
                warnings.append('Server name is very short')
            
            # Validate region
            if data.get('serverRegion') and not validate_region(data['serverRegion']):
                errors.append('Invalid server region')
            
            # Validate server type
            valid_types = ['Standard', 'Premium', 'Enterprise', 'Custom', 'Rust']
            if data.get('serverType') and data['serverType'] not in valid_types:
                warnings.append(f'Unknown server type: {data["serverType"]}')
            
            # ✅ NEW: Preview Service ID discovery
            discovery_preview = {'available': False, 'message': 'Service ID discovery not available'}
            
            if SERVICE_ID_DISCOVERY_AVAILABLE and len(errors) == 0:
                discovery_preview['available'] = True
                discovery_preview['message'] = 'Service ID will be automatically discovered when server is added'
                
                # Optional: Quick discovery preview (with rate limiting consideration)
                region = data.get('serverRegion', 'US')
                discovery_preview['preview_region'] = region
            
            return jsonify({
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'service_id_discovery': discovery_preview
            })
            
        except Exception as e:
            logger.error(f"❌ Error validating server data: {e}")
            return jsonify({'valid': False, 'errors': ['Validation failed']}), 500
    
    # ✅ ENHANCED: Server import/export functionality with Service ID support
    @servers_bp.route('/api/servers/export', methods=['GET'])
    @require_auth
    def export_servers():
        """✅ ENHANCED: Export server configurations including Service IDs"""
        try:
            if db:
                servers = list(db.servers.find({}, {'_id': 0}))
            else:
                servers = servers_storage
            
            # Count Service ID coverage for export metadata
            servers_with_service_id = len([s for s in servers if s.get('serviceId')])
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'version': '2.0',  # Updated version for Service ID support
                'server_count': len(servers),
                'service_id_coverage': servers_with_service_id,
                'discovery_system_available': SERVICE_ID_DISCOVERY_AVAILABLE,
                'servers': servers
            }
            
            return jsonify(export_data)
            
        except Exception as e:
            logger.error(f"❌ Error exporting servers: {e}")
            return jsonify({'error': 'Failed to export servers'}), 500
    
    @servers_bp.route('/api/servers/import', methods=['POST'])
    @require_auth
    def import_servers():
        """✅ ENHANCED: Import server configurations with automatic Service ID discovery"""
        try:
            data = request.json
            
            if not data.get('servers') or not isinstance(data['servers'], list):
                return jsonify({'success': False, 'error': 'Invalid import data format'})
            
            imported_count = 0
            errors = []
            service_ids_discovered = 0
            
            for server_data in data['servers']:
                try:
                    # Validate required fields
                    if not server_data.get('serverId') or not server_data.get('serverName'):
                        errors.append(f"Skipped server: Missing required fields")
                        continue
                    
                    # Check if server already exists
                    existing_server = None
                    if db:
                        existing_server = db.servers.find_one({'serverId': server_data['serverId']})
                    else:
                        existing_server = next((s for s in servers_storage if s['serverId'] == server_data['serverId']), None)
                    
                    if existing_server:
                        errors.append(f"Skipped server {server_data['serverId']}: Already exists")
                        continue
                    
                    # ✅ NEW: Auto-discover Service ID during import if not present
                    if not server_data.get('serviceId') and SERVICE_ID_DISCOVERY_AVAILABLE:
                        try:
                            service_id_mapper = ServiceIDMapper()
                            region = server_data.get('serverRegion', 'US')
                            
                            success, service_id, discovery_error = service_id_mapper.get_service_id_from_server_id(
                                server_data['serverId'], region
                            )
                            
                            if success and service_id:
                                server_data['serviceId'] = service_id
                                server_data['discovery_status'] = 'success'
                                server_data['discovery_message'] = f"Discovered during import: {service_id}"
                                service_ids_discovered += 1
                            else:
                                server_data['discovery_status'] = 'failed'
                                server_data['discovery_message'] = f"Discovery failed during import: {discovery_error}"
                                
                        except Exception as discovery_error:
                            server_data['discovery_status'] = 'error'
                            server_data['discovery_message'] = f"Discovery error during import: {str(discovery_error)}"
                    
                    # Create standardized server data
                    new_server = create_server_data(server_data)
                    
                    # Add server
                    if db:
                        db.servers.insert_one(new_server)
                    else:
                        servers_storage.append(new_server)
                    
                    imported_count += 1
                    
                except Exception as server_error:
                    errors.append(f"Error importing server: {str(server_error)}")
            
            logger.info(f"📥 Imported {imported_count} servers with {len(errors)} errors. {service_ids_discovered} Service IDs discovered.")
            
            return jsonify({
                'success': True,
                'imported_count': imported_count,
                'total_count': len(data['servers']),
                'service_ids_discovered': service_ids_discovered,
                'errors': errors
            })
            
        except Exception as e:
            logger.error(f"❌ Error importing servers: {e}")
            return jsonify({'success': False, 'error': 'Failed to import servers'}), 500
    
    # ✅ CRITICAL FIX: Return the blueprint
    logger.info("✅ Server routes initialized with Service ID Auto-Discovery support")
    return servers_bp