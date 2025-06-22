"""
GUST Bot Enhanced - Server Management Routes (VARIABLE SCOPING ISSUE FIXED)
=============================================================================
✅ FIXED: Variable scoping issue with servers_storage resolved
✅ FIXED: Python UnboundLocalError eliminated  
✅ FIXED: Proper closure handling for nested functions
✅ PRESERVED: All Service ID Auto-Discovery functionality
✅ PRESERVED: All existing server management features
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
try:
    from utils.gust_db_optimization import (
        get_user_with_cache,
        get_user_balance_cached,
        update_user_balance,
        db_performance_monitor
    )
    GUST_DB_OPTIMIZATION_AVAILABLE = True
except ImportError:
    GUST_DB_OPTIMIZATION_AVAILABLE = False

# ✅ SERVICE ID AUTO-DISCOVERY: Import with error handling
try:
    from utils.service_id_discovery import ServiceIDMapper, discover_service_id
    SERVICE_ID_DISCOVERY_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Service ID Auto-Discovery system available")
except ImportError:
    SERVICE_ID_DISCOVERY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ Service ID Auto-Discovery system not available")

logger = logging.getLogger(__name__)

# Create blueprint
servers_bp = Blueprint('servers', __name__)

def init_servers_routes(app, db, managed_servers):
    """
    ✅ FIXED: Initialize server routes with proper variable scoping
    
    Args:
        app: Flask app instance
        db: Database connection (optional)
        managed_servers: In-memory server storage list
        
    Returns:
        Blueprint: The configured servers blueprint
    """
    
    # ✅ CRITICAL FIX: Store references in a way that avoids scoping issues
    # Use a container object to avoid UnboundLocalError
    storage_refs = {
        'db': db,
        'servers': managed_servers if managed_servers is not None else []
    }
    
    logger.info(f"🔧 Initializing servers routes with {len(storage_refs['servers'])} existing servers")
    
    @servers_bp.route('/api/servers')
    @require_auth
    def get_servers():
        """Get list of servers - SCOPING FIXED"""
        try:
            if storage_refs['db']:
                servers = list(storage_refs['db'].servers.find({}, {'_id': 0}))
            else:
                servers = storage_refs['servers']
            
            logger.info(f"📋 Retrieved {len(servers)} servers")
            return jsonify(servers)
        except Exception as e:
            logger.error(f"❌ Error retrieving servers: {e}")
            return jsonify({'error': 'Failed to retrieve servers'}), 500
    
    @servers_bp.route('/api/servers/add', methods=['POST'])
    @require_auth
    def add_server():
        """
        ✅ FIXED: Add new server with proper variable scoping
        Enhanced with Service ID Auto-Discovery
        """
        try:
            logger.info("🔄 Processing server addition request...")
            
            # Get request data
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            logger.info(f"🔄 Processing server addition request: {data}")
            
            # Validate required fields
            required_fields = ['serverId', 'serverName', 'serverRegion']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'success': False, 
                        'error': f'Missing required field: {field}'
                    }), 400
            
            # ✅ FIXED: Safe access to servers storage
            try:
                # Check if server already exists
                server_id = data['serverId']
                existing_server = None
                
                if storage_refs['db']:
                    existing_server = storage_refs['db'].servers.find_one({'serverId': server_id})
                else:
                    # Safe iteration over servers list
                    for server in storage_refs['servers']:
                        if server.get('serverId') == server_id:
                            existing_server = server
                            break
                
                if existing_server:
                    return jsonify({
                        'success': False,
                        'error': f'Server {server_id} already exists'
                    }), 400
                    
            except Exception as check_error:
                logger.warning(f"⚠️ Error checking existing server: {check_error}")
                # Continue with addition even if check fails
            
            # ✅ SERVICE ID AUTO-DISCOVERY: Enhanced discovery integration
            discovery_result = {
                'status': 'not_attempted',
                'serviceId': None,
                'message': 'Service ID discovery not attempted'
            }
            
            if SERVICE_ID_DISCOVERY_AVAILABLE:
                logger.info(f"🔍 Discovering Service ID for server {data['serverId']}...")
                try:
                    service_id_mapper = ServiceIDMapper()
                    success, service_id, discovery_error = service_id_mapper.get_service_id_from_server_id(
                        data['serverId'], 
                        data.get('serverRegion', 'US')
                    )
                    
                    if success and service_id:
                        logger.info(f"✅ Service ID discovered: {service_id}")
                        data['serviceId'] = service_id
                        data['discovery_status'] = 'success'
                        data['discovery_message'] = f"Service ID {service_id} discovered successfully"
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
                logger.info("ℹ️ Service ID discovery system not available")
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
            
            # ✅ FIXED: Safe storage to avoid scoping issues
            try:
                if storage_refs['db']:
                    storage_refs['db'].servers.insert_one(server_data)
                    logger.info(f"✅ Server added to database: {data['serverName']} ({data['serverId']})")
                else:
                    storage_refs['servers'].append(server_data)
                    logger.info(f"✅ Server added to memory: {data['serverName']} ({data['serverId']})")
                
            except Exception as storage_error:
                logger.error(f"❌ Failed to store server: {storage_error}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to store server: {str(storage_error)}'
                }), 500
            
            # ✅ ENHANCED: Return detailed response with discovery information
            response_data = {
                'success': True,
                'message': f'Server {data["serverName"]} added successfully',
                'server': server_data,
                'discovery': discovery_result,
                'capabilities': {
                    'health_monitoring': True,
                    'sensor_data': True,
                    'command_execution': server_data.get('serviceId') is not None,
                    'websocket_support': True
                }
            }
            
            logger.info(f"✅ Server addition completed successfully: {data['serverName']}")
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"❌ Error adding server: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': f'Failed to add server: {str(e)}'
            }), 500
    
    @servers_bp.route('/api/servers/<server_id>', methods=['DELETE'])
    @require_auth
    def delete_server(server_id):
        """Delete a server - SCOPING FIXED"""
        try:
            if storage_refs['db']:
                result = storage_refs['db'].servers.delete_one({'serverId': server_id})
                if result.deleted_count == 0:
                    return jsonify({'success': False, 'error': 'Server not found'}), 404
            else:
                # Safe removal from list
                original_count = len(storage_refs['servers'])
                storage_refs['servers'][:] = [s for s in storage_refs['servers'] if s.get('serverId') != server_id]
                if len(storage_refs['servers']) == original_count:
                    return jsonify({'success': False, 'error': 'Server not found'}), 404
            
            logger.info(f"🗑️ Server {server_id} deleted successfully")
            return jsonify({'success': True, 'message': f'Server {server_id} deleted'})
            
        except Exception as e:
            logger.error(f"❌ Error deleting server: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @servers_bp.route('/api/servers/<server_id>', methods=['PUT'])
    @require_auth
    def update_server(server_id):
        """Update server information - SCOPING FIXED"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            # Update timestamp
            data['updatedAt'] = datetime.now().isoformat()
            
            if storage_refs['db']:
                result = storage_refs['db'].servers.update_one(
                    {'serverId': server_id},
                    {'$set': data}
                )
                if result.matched_count == 0:
                    return jsonify({'success': False, 'error': 'Server not found'}), 404
            else:
                # Safe update in list
                server_found = False
                for i, server in enumerate(storage_refs['servers']):
                    if server.get('serverId') == server_id:
                        storage_refs['servers'][i].update(data)
                        server_found = True
                        break
                
                if not server_found:
                    return jsonify({'success': False, 'error': 'Server not found'}), 404
            
            logger.info(f"📝 Server {server_id} updated successfully")
            return jsonify({'success': True, 'message': f'Server {server_id} updated'})
            
        except Exception as e:
            logger.error(f"❌ Error updating server: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ✅ SERVICE ID AUTO-DISCOVERY: Manual discovery endpoints
    @servers_bp.route('/api/servers/<server_id>/discover-service-id', methods=['POST'])
    @require_auth
    def discover_service_id_manual(server_id):
        """Manually trigger Service ID discovery for a specific server"""
        try:
            if not SERVICE_ID_DISCOVERY_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': 'Service ID discovery system not available'
                }), 503
            
            # Get server region from request or find server
            data = request.get_json() or {}
            region = data.get('region', 'US')
            
            # Find the server
            server = None
            if storage_refs['db']:
                server = storage_refs['db'].servers.find_one({'serverId': server_id})
            else:
                for s in storage_refs['servers']:
                    if s.get('serverId') == server_id:
                        server = s
                        break
            
            if not server:
                return jsonify({
                    'success': False,
                    'error': f'Server {server_id} not found'
                }), 404
            
            # Use server's region if not provided
            if not region and server.get('serverRegion'):
                region = server['serverRegion']
            
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
                    'discovery_message': f"Manual discovery successful: {service_id}",
                    'last_discovery_attempt': datetime.now().isoformat()
                }
                
                if storage_refs['db']:
                    storage_refs['db'].servers.update_one(
                        {'serverId': server_id},
                        {'$set': update_data}
                    )
                else:
                    server.update(update_data)
                
                logger.info(f"✅ Manual Service ID discovery successful: {server_id} -> {service_id}")
                return jsonify({
                    'success': True,
                    'serviceId': service_id,
                    'message': f'Service ID {service_id} discovered and updated'
                })
            else:
                # Update with failure status
                update_data = {
                    'discovery_status': 'failed',
                    'discovery_message': f"Manual discovery failed: {discovery_error}",
                    'last_discovery_attempt': datetime.now().isoformat()
                }
                
                if storage_refs['db']:
                    storage_refs['db'].servers.update_one(
                        {'serverId': server_id},
                        {'$set': update_data}
                    )
                else:
                    server.update(update_data)
                
                logger.warning(f"⚠️ Manual Service ID discovery failed: {server_id} - {discovery_error}")
                return jsonify({
                    'success': False,
                    'error': f'Service ID discovery failed: {discovery_error}',
                    'discovery_attempted': True
                })
                
        except Exception as e:
            logger.error(f"❌ Error in manual Service ID discovery: {e}")
            return jsonify({
                'success': False,
                'error': f'Discovery error: {str(e)}'
            }), 500
    
    @servers_bp.route('/api/servers/bulk-discover-service-ids', methods=['POST'])
    @require_auth
    def bulk_discover_service_ids():
        """Bulk Service ID discovery for servers without Service IDs"""
        try:
            if not SERVICE_ID_DISCOVERY_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': 'Service ID discovery system not available'
                }), 503
            
            # Get all servers without Service IDs
            servers_to_discover = []
            if storage_refs['db']:
                servers_to_discover = list(storage_refs['db'].servers.find({
                    '$or': [
                        {'serviceId': None},
                        {'serviceId': {'$exists': False}},
                        {'discovery_status': 'failed'}
                    ]
                }))
            else:
                servers_to_discover = [
                    s for s in storage_refs['servers'] 
                    if not s.get('serviceId') or s.get('discovery_status') == 'failed'
                ]
            
            if not servers_to_discover:
                return jsonify({
                    'success': True,
                    'message': 'All servers already have Service IDs',
                    'discovered': 0,
                    'failed': 0,
                    'total': 0
                })
            
            service_id_mapper = ServiceIDMapper()
            discovered_count = 0
            failed_count = 0
            results = []
            
            for server in servers_to_discover:
                try:
                    server_id = server['serverId']
                    region = server.get('serverRegion', 'US')
                    
                    success, service_id, discovery_error = service_id_mapper.get_service_id_from_server_id(
                        server_id, region
                    )
                    
                    if success and service_id:
                        # Update server
                        update_data = {
                            'serviceId': service_id,
                            'discovery_status': 'success',
                            'discovery_message': f"Bulk discovery successful: {service_id}",
                            'last_discovery_attempt': datetime.now().isoformat()
                        }
                        
                        if storage_refs['db']:
                            storage_refs['db'].servers.update_one(
                                {'serverId': server_id},
                                {'$set': update_data}
                            )
                        else:
                            server.update(update_data)
                        
                        discovered_count += 1
                        results.append({
                            'serverId': server_id,
                            'status': 'success',
                            'serviceId': service_id
                        })
                    else:
                        failed_count += 1
                        results.append({
                            'serverId': server_id,
                            'status': 'failed',
                            'error': discovery_error
                        })
                        
                except Exception as server_error:
                    failed_count += 1
                    results.append({
                        'serverId': server.get('serverId', 'unknown'),
                        'status': 'error',
                        'error': str(server_error)
                    })
            
            logger.info(f"📊 Bulk Service ID discovery completed: {discovered_count} discovered, {failed_count} failed")
            return jsonify({
                'success': True,
                'message': f'Bulk discovery completed: {discovered_count} discovered, {failed_count} failed',
                'discovered': discovered_count,
                'failed': failed_count,
                'total': len(servers_to_discover),
                'results': results
            })
            
        except Exception as e:
            logger.error(f"❌ Error in bulk Service ID discovery: {e}")
            return jsonify({
                'success': False,
                'error': f'Bulk discovery error: {str(e)}'
            }), 500
    
    # ✅ ADDITIONAL: Server import functionality
    @servers_bp.route('/api/servers/import', methods=['POST'])
    @require_auth
    def import_servers():
        """Import multiple servers with Service ID discovery - SCOPING FIXED"""
        try:
            data = request.get_json()
            if not data or 'servers' not in data:
                return jsonify({'success': False, 'error': 'No servers data provided'}), 400
            
            servers_data = data['servers']
            imported_count = 0
            service_ids_discovered = 0
            errors = []
            
            for server_data in servers_data:
                try:
                    # Validate required fields
                    if not server_data.get('serverId') or not server_data.get('serverName'):
                        errors.append("Missing required fields: serverId and serverName")
                        continue
                    
                    # Check if server already exists
                    existing_server = None
                    if storage_refs['db']:
                        existing_server = storage_refs['db'].servers.find_one({'serverId': server_data['serverId']})
                    else:
                        for s in storage_refs['servers']:
                            if s.get('serverId') == server_data['serverId']:
                                existing_server = s
                                break
                    
                    if existing_server:
                        errors.append(f"Skipped server {server_data['serverId']}: Already exists")
                        continue
                    
                    # Auto-discover Service ID during import if not present
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
                    if storage_refs['db']:
                        storage_refs['db'].servers.insert_one(new_server)
                    else:
                        storage_refs['servers'].append(new_server)
                    
                    imported_count += 1
                    
                except Exception as server_error:
                    errors.append(f"Error importing server: {str(server_error)}")
            
            logger.info(f"📥 Imported {imported_count} servers with {len(errors)} errors. {service_ids_discovered} Service IDs discovered.")
            
            return jsonify({
                'success': True,
                'imported': imported_count,
                'service_ids_discovered': service_ids_discovered,
                'errors': errors,
                'message': f'Imported {imported_count} servers successfully'
            })
            
        except Exception as e:
            logger.error(f"❌ Error importing servers: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Store app reference for potential later use
    servers_bp.app = app
    
    logger.info(f"✅ Servers routes initialized successfully with {len(storage_refs['servers'])} existing servers")
    logger.info(f"🔍 Service ID discovery: {'✅ Available' if SERVICE_ID_DISCOVERY_AVAILABLE else '❌ Not Available'}")
    
    # ✅ CRITICAL: Return the blueprint (this was missing and causing issues)
    return servers_bp