"""
GUST Bot Enhanced - Server Management Routes (COMPLETE FIXED VERSION)
======================================================================
✅ FIXED: Added missing Service ID endpoints (fixes 405 errors)
✅ FIXED: Variable scoping issue resolved
✅ FIXED: All existing functionality preserved
✅ ADDED: set-service-id, discover-service-id endpoints
✅ PRESERVED: All Service ID Auto-Discovery functionality
✅ PRESERVED: All existing server management features
"""

# Standard library imports
from datetime import datetime
import logging
import json
import requests

# Third-party imports
from flask import Blueprint, request, jsonify, session

# Utility imports
from utils.helpers import create_server_data, validate_server_id, validate_region, load_token

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
            
            # ✅ SERVICE ID AUTO-DISCOVERY: Try automatic discovery
            service_id = None
            discovery_status = 'pending'
            discovery_message = ''
            
            if SERVICE_ID_DISCOVERY_AVAILABLE:
                try:
                    logger.info(f"🔍 Attempting Service ID discovery for server {server_id}")
                    mapper = ServiceIDMapper()
                    success, discovered_service_id, error_msg = mapper.discover_service_id(
                        server_id, 
                        data.get('serverRegion', 'US')
                    )
                    
                    if success and discovered_service_id:
                        service_id = discovered_service_id
                        discovery_status = 'success'
                        discovery_message = f'Service ID {service_id} discovered automatically'
                        logger.info(f"✅ Service ID discovered: {service_id}")
                    else:
                        discovery_status = 'failed'
                        discovery_message = f'Service ID discovery failed: {error_msg}'
                        logger.warning(f"⚠️ Service ID discovery failed: {error_msg}")
                        
                except Exception as discovery_error:
                    discovery_status = 'error'
                    discovery_message = f'Service ID discovery error: {discovery_error}'
                    logger.error(f"❌ Service ID discovery error: {discovery_error}")
            else:
                discovery_status = 'unavailable'
                discovery_message = 'Service ID discovery system not available'
                logger.info("🔧 Service ID discovery not available - manual configuration required")
            
            # ✅ FIXED: Create server data with correct parameters
            server_data = create_server_data(
                server_id=data['serverId'],
                server_name=data['serverName'], 
                server_region=data.get('serverRegion', 'US'),
                service_id=service_id,
                discovery_status=discovery_status,
                discovery_message=discovery_message,
                serverType=data.get('serverType', 'Rust'),
                description=data.get('description', '')
            )
            
            # ✅ FIXED: Safe storage operations
            try:
                if storage_refs['db']:
                    # Store in database
                    storage_refs['db'].servers.insert_one(server_data.copy())
                    logger.info(f"💾 Server {server_id} saved to database")
                else:
                    # Store in memory
                    storage_refs['servers'].append(server_data)
                    logger.info(f"💾 Server {server_id} saved to memory")
                
                logger.info(f"✅ Server addition completed successfully: {data['serverName']}")
                
                return jsonify({
                    'success': True,
                    'message': f'Server {data["serverName"]} added successfully',
                    'server': server_data,
                    'service_id_discovered': service_id is not None,
                    'discovery_status': discovery_status,
                    'discovery_message': discovery_message
                })
                
            except Exception as storage_error:
                logger.error(f"❌ Storage error: {storage_error}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to save server: {storage_error}'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Server addition error: {e}")
            return jsonify({
                'success': False,
                'error': f'Server addition failed: {str(e)}'
            }), 500

    # ✅ FIX: Add missing Service ID configuration endpoint (fixes 405 error)
    @servers_bp.route('/api/servers/set-service-id', methods=['POST'])
    @require_auth
    def set_service_id():
        """Manually set Service ID for a server"""
        try:
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            server_id = data.get('serverId', '').strip()
            service_id = data.get('serviceId', '').strip()
            
            if not server_id or not service_id:
                return jsonify({
                    'success': False,
                    'error': 'Both Server ID and Service ID are required'
                }), 400
            
            # Validate Service ID format
            try:
                service_id_int = int(service_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Service ID must be a valid number'
                }), 400
            
            # Find and update server
            server_found = False
            
            if storage_refs['db']:
                # Update in database
                result = storage_refs['db'].servers.update_one(
                    {'serverId': server_id},
                    {
                        '$set': {
                            'serviceId': service_id,
                            'discovery_status': 'manual',
                            'discovery_message': f'Service ID {service_id} set manually',
                            'capabilities.command_execution': True,
                            'last_updated': datetime.now().isoformat()
                        }
                    }
                )
                server_found = result.modified_count > 0
            else:
                # Update in memory
                for server in storage_refs['servers']:
                    if server.get('serverId') == server_id:
                        server['serviceId'] = service_id
                        server['discovery_status'] = 'manual'
                        server['discovery_message'] = f'Service ID {service_id} set manually'
                        server['capabilities']['command_execution'] = True
                        server['last_updated'] = datetime.now().isoformat()
                        server_found = True
                        break
            
            if not server_found:
                return jsonify({
                    'success': False,
                    'error': f'Server with ID {server_id} not found'
                }), 404
            
            logger.info(f"✅ Service ID manually set: Server {server_id} → Service {service_id}")
            
            return jsonify({
                'success': True,
                'message': f'Service ID {service_id} set for server {server_id}',
                'server_id': server_id,
                'service_id': service_id
            })
            
        except Exception as e:
            logger.error(f"❌ Error setting Service ID: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # ✅ FIX: Add Service ID discovery endpoint (fixes missing endpoints)
    @servers_bp.route('/api/servers/discover-service-id/<server_id>', methods=['POST'])
    @require_auth
    def discover_service_id_manual(server_id):
        """Manual Service ID discovery for a specific server"""
        try:
            if not SERVICE_ID_DISCOVERY_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': 'Service ID discovery system not available'
                }), 503
            
            # Get region from request
            data = request.json if request.json else {}
            region = data.get('region', 'US').upper()
            
            logger.info(f"🔍 Manual Service ID discovery for server {server_id} in region {region}")
            
            # Perform discovery
            mapper = ServiceIDMapper()
            success, service_id, error_msg = mapper.discover_service_id(server_id, region)
            
            if success and service_id:
                # Update server with discovered Service ID
                server_found = False
                
                if storage_refs['db']:
                    result = storage_refs['db'].servers.update_one(
                        {'serverId': server_id},
                        {
                            '$set': {
                                'serviceId': service_id,
                                'discovery_status': 'success',
                                'discovery_message': f'Service ID {service_id} discovered manually',
                                'capabilities.command_execution': True,
                                'last_updated': datetime.now().isoformat()
                            }
                        }
                    )
                    server_found = result.modified_count > 0
                else:
                    for server in storage_refs['servers']:
                        if server.get('serverId') == server_id:
                            server['serviceId'] = service_id
                            server['discovery_status'] = 'success'
                            server['discovery_message'] = f'Service ID {service_id} discovered manually'
                            server['capabilities']['command_execution'] = True
                            server['last_updated'] = datetime.now().isoformat()
                            server_found = True
                            break
                
                logger.info(f"✅ Service ID discovered and updated: {service_id}")
                
                return jsonify({
                    'success': True,
                    'service_id': service_id,
                    'message': f'Service ID {service_id} discovered for server {server_id}',
                    'updated': server_found
                })
            else:
                logger.warning(f"⚠️ Service ID discovery failed: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': error_msg or 'Service ID discovery failed'
                }), 404
                
        except Exception as e:
            logger.error(f"❌ Service ID discovery error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # ✅ FIX: Add enhanced debug discovery endpoint
    @servers_bp.route('/api/servers/discover-service-id-debug/<server_id>', methods=['POST'])
    @require_auth
    def discover_service_id_debug(server_id):
        """Enhanced Service ID discovery with detailed debugging"""
        try:
            if not SERVICE_ID_DISCOVERY_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': 'Service ID discovery system not available',
                    'debug_info': {'discovery_system': 'unavailable'}
                }), 503
            
            data = request.json if request.json else {}
            region = data.get('region', 'US').upper()
            
            logger.info(f"🔍 Debug Service ID discovery for server {server_id} in region {region}")
            
            # Get authentication token
            token = load_token()
            if not token:
                return jsonify({
                    'success': False,
                    'error': 'No authentication token available',
                    'debug_info': {'token_status': 'missing'}
                }), 401
            
            # Extract token safely
            auth_token = None
            if isinstance(token, dict):
                auth_token = token.get('access_token')
            elif isinstance(token, str):
                auth_token = token
            
            if not auth_token:
                return jsonify({
                    'success': False,
                    'error': 'Invalid authentication token format',
                    'debug_info': {'token_status': 'invalid_format'}
                }), 401
            
            # Enhanced GraphQL discovery with debug info
            debug_info = {
                'server_id': server_id,
                'region': region,
                'token_status': 'available',
                'discovery_steps': []
            }
            
            try:
                # Step 1: Validate server ID
                server_id_int = int(server_id)
                debug_info['discovery_steps'].append('✅ Server ID validation passed')
                
                # Step 2: GraphQL query
                query = """
                query GetServerConfig($serverId: Int!, $region: REGION!) {
                    cfgContext(rsid: {id: $serverId, region: $region}) {
                        ns {
                            sys {
                                gameServer {
                                    serviceId
                                    serverId  
                                    serverName
                                    serverIp
                                }
                            }
                            service {
                                config {
                                    rsid {
                                        id
                                        region
                                    }
                                    hwId
                                    type
                                    ipAddress
                                }
                            }
                        }
                    }
                }
                """
                
                payload = {
                    'query': query,
                    'variables': {
                        'serverId': server_id_int,
                        'region': region
                    }
                }
                
                headers = {
                    'Authorization': f'Bearer {auth_token}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'GUST-Bot-Enhanced/1.0'
                }
                
                debug_info['discovery_steps'].append('✅ GraphQL query prepared')
                
                # Step 3: Make request
                response = requests.post(
                    'https://www.g-portal.com/ngpapi/',
                    json=payload,
                    headers=headers,
                    timeout=15
                )
                
                debug_info['discovery_steps'].append(f'✅ HTTP request completed: {response.status_code}')
                
                if response.status_code != 200:
                    debug_info['discovery_steps'].append(f'❌ HTTP error: {response.status_code}')
                    return jsonify({
                        'success': False,
                        'error': f'HTTP {response.status_code}: {response.text[:200]}',
                        'debug_info': debug_info
                    }), response.status_code
                
                # Step 4: Parse response
                data = response.json()
                debug_info['discovery_steps'].append('✅ JSON response parsed')
                debug_info['raw_response'] = data
                
                # Step 5: Extract Service ID
                service_id = None
                if 'data' in data and data['data']:
                    cfg_context = data['data'].get('cfgContext')
                    if cfg_context and cfg_context.get('ns'):
                        ns = cfg_context['ns']
                        
                        # Try multiple extraction paths
                        if ns.get('sys', {}).get('gameServer', {}).get('serviceId'):
                            service_id = str(ns['sys']['gameServer']['serviceId'])
                            debug_info['discovery_steps'].append('✅ Service ID found in gameServer')
                        elif ns.get('service', {}).get('config', {}).get('rsid', {}).get('id'):
                            service_id = str(ns['service']['config']['rsid']['id'])
                            debug_info['discovery_steps'].append('✅ Service ID found in service config')
                
                if service_id:
                    debug_info['discovery_steps'].append(f'✅ Service ID extracted: {service_id}')
                    
                    # Update server record
                    if storage_refs['db']:
                        storage_refs['db'].servers.update_one(
                            {'serverId': server_id},
                            {
                                '$set': {
                                    'serviceId': service_id,
                                    'discovery_status': 'debug_success',
                                    'discovery_message': f'Service ID {service_id} discovered via debug',
                                    'capabilities.command_execution': True,
                                    'last_updated': datetime.now().isoformat()
                                }
                            }
                        )
                    else:
                        for server in storage_refs['servers']:
                            if server.get('serverId') == server_id:
                                server['serviceId'] = service_id
                                server['discovery_status'] = 'debug_success'
                                server['discovery_message'] = f'Service ID {service_id} discovered via debug'
                                server['capabilities']['command_execution'] = True
                                server['last_updated'] = datetime.now().isoformat()
                                break
                    
                    return jsonify({
                        'success': True,
                        'service_id': service_id,
                        'message': f'Service ID {service_id} discovered via debug method',
                        'debug_info': debug_info
                    })
                else:
                    debug_info['discovery_steps'].append('❌ Service ID not found in response')
                    return jsonify({
                        'success': False,
                        'error': 'Service ID not found in GraphQL response',
                        'debug_info': debug_info
                    }), 404
                    
            except ValueError as ve:
                debug_info['discovery_steps'].append(f'❌ Invalid server ID: {ve}')
                return jsonify({
                    'success': False,
                    'error': f'Invalid server ID: {ve}',
                    'debug_info': debug_info
                }), 400
            except requests.exceptions.RequestException as re:
                debug_info['discovery_steps'].append(f'❌ Request error: {re}')
                return jsonify({
                    'success': False,
                    'error': f'Request error: {re}',
                    'debug_info': debug_info
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Debug discovery error: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'debug_info': debug_info if 'debug_info' in locals() else {}
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
    def discover_service_id_alt(server_id):
        """Alternative endpoint for Service ID discovery"""
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
            success, service_id, discovery_error = service_id_mapper.discover_service_id(
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
                
                logger.info(f"✅ Service ID discovered via alternative endpoint: {service_id}")
                return jsonify({
                    'success': True,
                    'service_id': service_id,
                    'message': f'Service ID {service_id} discovered for server {server_id}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': discovery_error or 'Service ID discovery failed'
                }), 404
                
        except Exception as e:
            logger.error(f"❌ Alternative Service ID discovery error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # ✅ Bulk operations and status endpoints
    @servers_bp.route('/api/servers/import', methods=['POST'])
    @require_auth
    def import_servers():
        """Import multiple servers with Service ID discovery - SCOPING FIXED"""
        try:
            data = request.get_json()
            if not data or 'servers' not in data:
                return jsonify({'success': False, 'error': 'No servers data provided'}), 400
            
            servers_to_import = data['servers']
            imported_count = 0
            service_ids_discovered = 0
            errors = []
            
            for server_info in servers_to_import:
                try:
                    # Validate server info
                    if not server_info.get('serverId') or not server_info.get('serverName'):
                        errors.append(f"Server missing required fields: {server_info}")
                        continue
                    
                    # Check if server already exists
                    server_id = server_info['serverId']
                    existing = False
                    
                    if storage_refs['db']:
                        existing = storage_refs['db'].servers.find_one({'serverId': server_id}) is not None
                    else:
                        existing = any(s.get('serverId') == server_id for s in storage_refs['servers'])
                    
                    if existing:
                        errors.append(f"Server {server_id} already exists")
                        continue
                    
                    # Try Service ID discovery
                    service_id = None
                    if SERVICE_ID_DISCOVERY_AVAILABLE:
                        try:
                            mapper = ServiceIDMapper()
                            success, discovered_id, _ = mapper.discover_service_id(
                                server_id, 
                                server_info.get('serverRegion', 'US')
                            )
                            if success:
                                service_id = discovered_id
                                service_ids_discovered += 1
                        except Exception:
                            pass  # Continue without Service ID
                    
                    # Create server data
                    server_data = create_server_data(
                        server_id=server_info['serverId'],
                        server_name=server_info['serverName'],
                        server_region=server_info.get('serverRegion', 'US'),
                        service_id=service_id,
                        discovery_status='success' if service_id else 'failed',
                        **{k: v for k, v in server_info.items() if k not in ['serverId', 'serverName', 'serverRegion']}
                    )
                    
                    # Store server
                    if storage_refs['db']:
                        storage_refs['db'].servers.insert_one(server_data.copy())
                    else:
                        storage_refs['servers'].append(server_data)
                    
                    imported_count += 1
                    
                except Exception as server_error:
                    errors.append(f"Error importing server {server_info.get('serverId', 'unknown')}: {server_error}")
            
            logger.info(f"📥 Bulk import completed: {imported_count} imported, {service_ids_discovered} Service IDs discovered.")
            
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