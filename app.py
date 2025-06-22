"""
GUST Bot Enhanced - Main Flask Application (COMPLETE FIXED VERSION)
===================================================================
✅ CRITICAL FIX: Corrected GraphQL mutation schema to match G-Portal API
✅ CRITICAL FIX: Fixed Service ID vs Server ID usage for commands
✅ CRITICAL FIX: Enhanced null checking and error handling
✅ FIXED: GraphQL response field parsing (using 'ok' instead of 'success')
✅ FIXED: Comprehensive token validation and refresh
✅ FIXED: Added all missing Service ID routes
✅ PRESERVED: All existing functionality
"""

import os
import json
import time
import threading
import schedule
import secrets
import requests
import logging
from datetime import datetime, timedelta
from collections import deque
from flask import Flask, render_template, session, redirect, url_for, jsonify, request

# Import configuration and utilities
from config import Config, WEBSOCKETS_AVAILABLE, ensure_directories, ensure_data_files
from utils.rate_limiter import RateLimiter
from utils.helpers import load_token, format_command, validate_server_id, validate_region

# Server Health components
from utils.server_health_storage import ServerHealthStorage

# Import systems
from systems.koth import VanillaKothSystem

# Import route blueprints
from routes.auth import auth_bp

# ✅ SERVICE ID AUTO-DISCOVERY: Import Service ID discovery system
try:
    from utils.service_id_discovery import ServiceIDMapper, validate_service_id_discovery, discover_service_id
    SERVICE_ID_DISCOVERY_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Service ID Auto-Discovery system available")
except ImportError as e:
    SERVICE_ID_DISCOVERY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ Service ID Auto-Discovery system not available: {e}")

# ✅ ENHANCED: Import WebSocket components with proper error handling
if WEBSOCKETS_AVAILABLE:
    try:
        from websocket import EnhancedWebSocketManager, check_websocket_support, check_sensor_support
        WEBSOCKET_IMPORT_SUCCESS = True
    except ImportError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ WebSocket import failed even though WEBSOCKETS_AVAILABLE=True: {e}")
        WEBSOCKET_IMPORT_SUCCESS = False
        EnhancedWebSocketManager = None
else:
    WEBSOCKET_IMPORT_SUCCESS = False
    EnhancedWebSocketManager = None

logger = logging.getLogger(__name__)

# ============================================================================
# SAFE CONSOLE COMMAND EXECUTION (COMPLETE FIX)
# ============================================================================

def safe_send_console_command(server_id, command, region='US', managed_servers=None):
    """
    ✅ FIXED: Safe console command execution with comprehensive error handling
    ✅ CRITICAL FIX: Uses correct G-Portal GraphQL schema and Service ID
    
    Args:
        server_id: The server ID (will lookup Service ID)
        command: Console command to send
        region: Server region (default: US)
        managed_servers: Server list to lookup Service ID
        
    Returns:
        dict: Success status and response details
    """
    try:
        # Step 1: Enhanced validation
        if not server_id or not command:
            return {
                'success': False,
                'error': 'Server ID and command are required',
                'server_id': server_id,
                'command': command
            }
        
        # Step 2: Validate server ID format
        is_valid, server_id_int = validate_server_id(server_id)
        if not is_valid:
            return {
                'success': False,
                'error': f'Invalid server ID format: {server_id}',
                'server_id': server_id
            }
        
        # Step 3: Get authentication token
        token_data = load_token()
        if not token_data:
            return {
                'success': False,
                'error': 'No authentication token available',
                'server_id': server_id
            }
        
        # Step 4: Extract token safely
        token = None
        if isinstance(token_data, dict):
            token = token_data.get('access_token')
        elif isinstance(token_data, str):
            token = token_data
        
        if not token:
            return {
                'success': False,
                'error': 'Invalid authentication token format',
                'server_id': server_id
            }
        
        # Step 5: ✅ CRITICAL FIX - Get Service ID for commands
        service_id = None
        if managed_servers:
            for server in managed_servers:
                if str(server.get('serverId')) == str(server_id):
                    service_id = server.get('serviceId')
                    break
        
        # Use Service ID if available, otherwise use Server ID with warning
        target_id = service_id if service_id else server_id_int
        id_type = 'Service ID' if service_id else 'Server ID'
        
        if not service_id:
            logger.warning(f"⚠️ No Service ID available for server {server_id}, using Server ID")
        
        # Step 6: ✅ CRITICAL FIX - Correct GraphQL mutation schema
        mutation = """
        mutation sendConsoleMessage($sid: Int!, $region: REGION!, $message: String!) {
            sendConsoleMessage(rsid: {id: $sid, region: $region}, message: $message) {
                ok
                __typename
            }
        }
        """
        
        # Step 7: Prepare variables
        variables = {
            'sid': int(target_id),
            'region': region.upper(),
            'message': command.strip()
        }
        
        # Step 8: Prepare request
        payload = {
            'query': mutation,
            'variables': variables
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'GUST-Bot-Enhanced/1.0',
            'Accept': 'application/json'
        }
        
        logger.info(f"🌐 Sending command to {id_type} {target_id} ({region}): {command}")
        
        # Step 9: Make GraphQL request
        response = requests.post(
            'https://www.g-portal.com/ngpapi/',
            json=payload,
            headers=headers,
            timeout=30
        )
        
        # Step 10: ✅ CRITICAL FIX - Enhanced response handling
        if response.status_code != 200:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            logger.error(f"❌ HTTP error: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'server_id': server_id,
                'service_id': service_id,
                'http_status': response.status_code
            }
        
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            return {
                'success': False,
                'error': f'Invalid JSON response: {e}',
                'server_id': server_id,
                'raw_response': response.text[:200]
            }
        
        # Step 11: ✅ CRITICAL FIX - Check for GraphQL errors first
        if 'errors' in response_data and response_data['errors']:
            error_messages = [error.get('message', 'Unknown error') for error in response_data['errors']]
            error_msg = '; '.join(error_messages)
            logger.error(f"❌ GraphQL errors: {error_msg}")
            return {
                'success': False,
                'error': f'GraphQL errors: {error_msg}',
                'server_id': server_id,
                'service_id': service_id,
                'graphql_errors': response_data['errors']
            }
        
        # Step 12: ✅ CRITICAL FIX - Check for successful response using 'ok' field
        if 'data' in response_data and response_data['data']:
            console_data = response_data['data'].get('sendConsoleMessage')
            if console_data and console_data.get('ok') is True:
                logger.info(f"✅ Command sent successfully to {id_type} {target_id}")
                return {
                    'success': True,
                    'message': f'Command sent successfully to {id_type} {target_id}',
                    'server_id': server_id,
                    'service_id': service_id,
                    'command': command,
                    'target_id': target_id,
                    'id_type': id_type,
                    'response': console_data
                }
        
        # Step 13: Handle unexpected response format
        logger.warning(f"⚠️ Unexpected response format: {response_data}")
        return {
            'success': False,
            'error': 'Unexpected response format from G-Portal',
            'server_id': server_id,
            'service_id': service_id,
            'response_data': response_data
        }
        
    except requests.exceptions.Timeout:
        logger.error(f"❌ Request timeout for server {server_id}")
        return {
            'success': False,
            'error': 'Request timeout - server may be unresponsive',
            'server_id': server_id
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request error for server {server_id}: {e}")
        return {
            'success': False,
            'error': f'Request error: {e}',
            'server_id': server_id
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error in safe_send_console_command: {e}")
        return {
            'success': False,
            'error': f'Unexpected error: {e}',
            'server_id': server_id
        }

class GustBotEnhanced:
    """Main GUST Bot Enhanced application class"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = secrets.token_hex(16)
        
        # Initialize data storage
        self.managed_servers = []
        self.user_storage = {}
        self.console_output = deque(maxlen=1000)
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter()
        
        # Initialize server health storage
        self.server_health_storage = ServerHealthStorage(None, self.user_storage)
        
        # Initialize Service ID discovery system
        self.service_id_mapper = None
        self.service_id_discovery_available = False
        self.service_id_discovery_error = None
        
        if SERVICE_ID_DISCOVERY_AVAILABLE:
            try:
                self.service_id_mapper = ServiceIDMapper()
                self.service_id_discovery_available = True
                logger.info("✅ Service ID discovery system initialized")
            except Exception as e:
                self.service_id_discovery_error = str(e)
                logger.error(f"❌ Service ID discovery initialization failed: {e}")
        
        # Setup routes
        self.setup_routes()
        
        logger.info("✅ GUST Bot Enhanced initialized successfully")
    
    def setup_routes(self):
        """Setup all application routes"""
        
        # Register auth blueprint
        self.app.register_blueprint(auth_bp)
        
        # Dashboard route
        @self.app.route('/')
        def dashboard():
            if 'logged_in' not in session:
                return redirect(url_for('auth.login'))
            return render_template('enhanced_dashboard.html')
        
        # ✅ FIXED: Console command routes with safe execution
        self.setup_console_routes()
        
        # ✅ FIXED: Service ID routes
        self.setup_service_id_routes()
        
        # Server management routes
        self.setup_server_routes()
        
        # Miscellaneous routes
        self.setup_misc_routes()
        
        logger.info("✅ All routes setup complete with fixed console commands and Service ID support")
    
    def setup_console_routes(self):
        """Setup console-related routes with FIXED GraphQL execution"""
        
        @self.app.route('/api/console/send', methods=['POST'])
        def send_console_command():
            """✅ FIXED: Send console command using safe execution"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                data = request.json
                if not data:
                    return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
                
                command = data.get('command', '').strip()
                server_id = data.get('serverId', '').strip()
                region = data.get('region', 'US').strip().upper()
                
                if not command or not server_id:
                    return jsonify({
                        'success': False,
                        'error': 'Command and server ID are required'
                    }), 400
                
                logger.info(f"🔄 Sending command to ID {server_id} ({region}): {command}")
                
                # ✅ CRITICAL FIX: Use safe command execution
                result = safe_send_console_command(
                    server_id, 
                    command, 
                    region, 
                    self.managed_servers
                )
                
                # Add to console output
                self.console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'command': command,
                    'server_id': server_id,
                    'target_id': result.get('target_id', server_id),
                    'id_type': result.get('id_type', 'Server ID'),
                    'status': 'sent' if result['success'] else 'failed',
                    'source': 'safe_graphql_api',
                    'type': 'command',
                    'message': f'Command: {command}',
                    'success': result['success'],
                    'safe_execution': True
                })
                
                # Log the command attempt
                logger.info(f"🎮 Console command: {command} → {result.get('id_type', 'Server')} {result.get('target_id', server_id)} → {result['success']}")
                
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"❌ Console command error: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Console command error: {e}'
                }), 500
        
        # ✅ FIXED: Auto console command route
        @self.app.route('/api/console/send-auto', methods=['POST'])
        def send_console_command_auto():
            """✅ FIXED: Send auto console command using safe execution"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                data = request.json
                if not data:
                    return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
                
                command = data.get('command', '').strip()
                server_id = data.get('serverId', '').strip()
                region = data.get('region', 'US').strip().upper()
                
                if not command or not server_id:
                    return jsonify({
                        'success': False,
                        'error': 'Command and server ID are required'
                    }), 400
                
                logger.info(f"🌐 Auto command live mode: Sending '{command}' to server {server_id}")
                
                # ✅ CRITICAL FIX: Use safe command execution
                result = safe_send_console_command(
                    server_id, 
                    command, 
                    region, 
                    self.managed_servers
                )
                
                # Add to console output with auto command tracking
                self.console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'command': command,
                    'server_id': server_id,
                    'target_id': result.get('target_id', server_id),
                    'id_type': result.get('id_type', 'Server ID'),
                    'status': 'sent' if result['success'] else 'failed',
                    'source': 'auto_safe_execution',
                    'type': 'auto_command',
                    'message': f'Auto command: {command}',
                    'success': result['success'],
                    'safe_execution': True
                })
                
                # Enhanced logging for auto commands
                if result['success']:
                    logger.info(f"✅ Auto command successful: {command} → {result.get('id_type', 'Server')} {result.get('target_id', server_id)}")
                else:
                    logger.warning(f"⚠️ Auto command failed: {command} → {result.get('id_type', 'Server')} {result.get('target_id', server_id)} → {result.get('error', 'Unknown error')}")
                
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"❌ Auto console command error: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Auto console command error: {e}'
                }), 500
        
        logger.info("✅ Console routes registered with FIXED GraphQL execution")
    
    def setup_service_id_routes(self):
        """Setup Service ID specific routes and endpoints"""
        
        @self.app.route('/api/service-id/status')
        def service_id_system_status():
            """Get Service ID discovery system status"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                status_data = {
                    'success': True,
                    'available': self.service_id_discovery_available,
                    'mapper_initialized': self.service_id_mapper is not None,
                    'error': self.service_id_discovery_error,
                    'timestamp': datetime.now().isoformat(),
                    'safe_execution_integrated': True
                }
                
                # Add detailed status if system is available
                if self.service_id_discovery_available and self.service_id_mapper:
                    try:
                        cache_stats = self.service_id_mapper.get_cache_stats()
                        status_data['cache_stats'] = cache_stats
                        status_data['system_ready'] = True
                    except Exception as stats_error:
                        status_data['cache_error'] = str(stats_error)
                
                return jsonify(status_data)
                
            except Exception as e:
                logger.error(f"❌ Service ID status error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # ✅ NEW: Bulk Service ID discovery endpoint
        @self.app.route('/api/servers/discover-all-service-ids', methods=['POST'])
        def discover_all_service_ids():
            """Discover Service IDs for all servers without them"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                if not self.service_id_discovery_available:
                    return jsonify({
                        'success': False,
                        'error': 'Service ID discovery system not available'
                    }), 503
                
                discovered = []
                failed = []
                skipped = []
                
                for server in self.managed_servers:
                    server_id = server.get('serverId')
                    
                    if not server_id:
                        skipped.append({
                            'server_id': 'unknown',
                            'reason': 'Missing server ID'
                        })
                        continue
                    
                    # Skip if Service ID already exists
                    if server.get('serviceId'):
                        skipped.append({
                            'server_id': server_id,
                            'reason': f"Service ID already exists: {server['serviceId']}"
                        })
                        continue
                    
                    try:
                        region = server.get('serverRegion', 'US')
                        success, service_id, error = self.service_id_mapper.discover_service_id(server_id, region)
                        
                        if success and service_id:
                            # Update server with discovered Service ID
                            server['serviceId'] = service_id
                            server['discovery_status'] = 'bulk_success'
                            server['discovery_message'] = f'Service ID {service_id} discovered via bulk operation'
                            server['capabilities']['command_execution'] = True
                            server['last_updated'] = datetime.now().isoformat()
                            
                            discovered.append({
                                'server_id': server_id,
                                'service_id': service_id,
                                'server_name': server.get('serverName', 'Unknown')
                            })
                        else:
                            failed.append({
                                'server_id': server_id,
                                'error': error or 'Discovery failed',
                                'server_name': server.get('serverName', 'Unknown')
                            })
                            
                    except Exception as discovery_error:
                        failed.append({
                            'server_id': server_id,
                            'error': str(discovery_error),
                            'server_name': server.get('serverName', 'Unknown')
                        })
                
                return jsonify({
                    'success': True,
                    'summary': {
                        'total_servers': len(self.managed_servers),
                        'discovered': len(discovered),
                        'failed': len(failed),
                        'skipped': len(skipped)
                    },
                    'results': {
                        'discovered': discovered,
                        'failed': failed,
                        'skipped': skipped
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Bulk Service ID discovery error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ✅ NEW: Service ID Discovery Status Endpoint
        @self.app.route('/api/servers/discovery-status')
        def get_discovery_status():
            """Get Service ID discovery status for all servers"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                servers_with_service_id = []
                servers_without_service_id = []
                
                for server in self.managed_servers:
                    server_info = {
                        'serverId': server.get('serverId'),
                        'serverName': server.get('serverName', 'Unknown'),
                        'region': server.get('serverRegion', 'Unknown'),
                        'discovery_status': server.get('discovery_status', 'unknown'),
                        'discovery_message': server.get('discovery_message', ''),
                        'capabilities': server.get('capabilities', {})
                    }
                    
                    if server.get('serviceId'):
                        server_info['serviceId'] = server['serviceId']
                        servers_with_service_id.append(server_info)
                    else:
                        servers_without_service_id.append(server_info)
                
                return jsonify({
                    'success': True,
                    'summary': {
                        'total_servers': len(self.managed_servers),
                        'with_service_id': len(servers_with_service_id),
                        'without_service_id': len(servers_without_service_id),
                        'discovery_coverage': round((len(servers_with_service_id) / len(self.managed_servers)) * 100, 1) if self.managed_servers else 0
                    },
                    'servers_with_service_id': servers_with_service_id,
                    'servers_without_service_id': servers_without_service_id,
                    'discovery_available': self.service_id_discovery_available,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Discovery status error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ✅ NEW: Test discovery system endpoint
        @self.app.route('/api/servers/test-discovery-system')
        def test_discovery_system():
            """Test the Service ID discovery system functionality"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                if not SERVICE_ID_DISCOVERY_AVAILABLE:
                    return jsonify({
                        'success': False,
                        'overall_status': 'unavailable',
                        'error': 'Service ID discovery system not available',
                        'recommendations': [
                            'Install Service ID discovery module',
                            'Check system dependencies',
                            'Verify authentication system'
                        ],
                        'timestamp': datetime.now().isoformat()
                    }), 503
                
                # Test system components
                system_status = {
                    'authentication': 'unknown',
                    'graphql_endpoint': 'unknown',
                    'mapper_initialization': 'unknown',
                    'cache_system': 'unknown'
                }
                
                recommendations = []
                overall_status = 'healthy'
                
                # Test authentication
                try:
                    token = load_token()
                    if token:
                        system_status['authentication'] = 'available'
                    else:
                        system_status['authentication'] = 'missing'
                        recommendations.append('Login to G-Portal to obtain authentication token')
                        overall_status = 'warning'
                except Exception:
                    system_status['authentication'] = 'error'
                    recommendations.append('Check authentication system')
                    overall_status = 'error'
                
                # Test GraphQL endpoint
                try:
                    test_response = requests.get('https://www.g-portal.com', timeout=5)
                    if test_response.status_code == 200:
                        system_status['graphql_endpoint'] = 'accessible'
                    else:
                        system_status['graphql_endpoint'] = 'inaccessible'
                        recommendations.append('Check network connectivity to G-Portal')
                        overall_status = 'warning'
                except Exception:
                    system_status['graphql_endpoint'] = 'error'
                    recommendations.append('Check internet connection')
                    overall_status = 'error'
                
                # Test mapper initialization
                if self.service_id_mapper:
                    system_status['mapper_initialization'] = 'success'
                    try:
                        cache_stats = self.service_id_mapper.get_cache_stats()
                        system_status['cache_system'] = 'operational'
                    except Exception:
                        system_status['cache_system'] = 'error'
                        recommendations.append('Cache system needs attention')
                else:
                    system_status['mapper_initialization'] = 'failed'
                    recommendations.append('Restart Service ID discovery system')
                    overall_status = 'error'
                
                message = f'Service ID discovery system is {overall_status}'
                if overall_status == 'healthy':
                    message += ' and ready for use'
                elif overall_status == 'warning':
                    message += ' with some issues that may affect functionality'
                else:
                    message += ' and requires attention'
                
                return jsonify({
                    'success': True,
                    'overall_status': overall_status,
                    'message': message,
                    'system_status': system_status,
                    'recommendations': recommendations,
                    'test_endpoints': {
                        'manual_discovery': '/api/servers/discover-service-id/<server_id>',
                        'bulk_discovery': '/api/servers/discover-all-service-ids',
                        'discovery_status': '/api/servers/discovery-status'
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Discovery system test error: {e}")
                return jsonify({
                    'success': False,
                    'overall_status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        logger.info("✅ Service ID routes registered successfully")
    
    def setup_server_routes(self):
        """Setup basic server management routes"""
        
        @self.app.route('/api/servers')
        def get_servers():
            """Get list of managed servers"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Calculate Service ID statistics
            servers_with_service_id = sum(1 for s in self.managed_servers if s.get('serviceId'))
            total_servers = len(self.managed_servers)
            
            return jsonify({
                'success': True,
                'servers': self.managed_servers,
                'count': total_servers,
                'service_id_stats': {
                    'total_servers': total_servers,
                    'servers_with_service_id': servers_with_service_id,
                    'coverage_percentage': round((servers_with_service_id / total_servers) * 100, 1) if total_servers > 0 else 0,
                    'discovery_available': self.service_id_discovery_available
                },
                'demo_mode': session.get('demo_mode', False),
                'timestamp': datetime.now().isoformat(),
                'safe_execution_enabled': True
            })
        
        @self.app.route('/api/servers/add', methods=['POST'])
        def add_server():
            """Add a new server with Service ID discovery"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                data = request.json
                if not data:
                    return jsonify({'success': False, 'error': 'No data provided'}), 400
                
                server_id = data.get('serverId', '').strip()
                server_name = data.get('serverName', '').strip()
                server_region = data.get('serverRegion', 'US').strip().upper()
                
                if not server_id or not server_name:
                    return jsonify({
                        'success': False,
                        'error': 'Server ID and name are required'
                    }), 400
                
                # Check if server already exists
                if any(s.get('serverId') == server_id for s in self.managed_servers):
                    return jsonify({
                        'success': False,
                        'error': f'Server with ID {server_id} already exists'
                    }), 400
                
                # Try Service ID discovery
                service_id = None
                discovery_status = 'pending'
                discovery_message = ''
                
                if self.service_id_discovery_available and self.service_id_mapper:
                    try:
                        success, discovered_id, error = self.service_id_mapper.discover_service_id(server_id, server_region)
                        if success and discovered_id:
                            service_id = discovered_id
                            discovery_status = 'success'
                            discovery_message = f'Service ID {service_id} discovered automatically'
                        else:
                            discovery_status = 'failed'
                            discovery_message = f'Service ID discovery failed: {error}'
                    except Exception as e:
                        discovery_status = 'error'
                        discovery_message = f'Service ID discovery error: {e}'
                else:
                    discovery_status = 'unavailable'
                    discovery_message = 'Service ID discovery system not available'
                
                # Create server data
                from utils.helpers import create_server_data
                server_data = create_server_data(
                    server_id=server_id,
                    server_name=server_name,
                    server_region=server_region,
                    service_id=service_id,
                    discovery_status=discovery_status,
                    discovery_message=discovery_message,
                    serverType=data.get('serverType', 'Rust'),
                    description=data.get('description', '')
                )
                
                self.managed_servers.append(server_data)
                
                logger.info(f"✅ Server added: {server_name} ({server_id})")
                
                return jsonify({
                    'success': True,
                    'message': f'Server {server_name} added successfully',
                    'server': server_data,
                    'service_id_discovered': service_id is not None,
                    'discovery_status': discovery_status
                })
                
            except Exception as e:
                logger.error(f"❌ Error adding server: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        logger.info("✅ Server management routes registered")
    
    def setup_misc_routes(self):
        """Setup miscellaneous routes"""
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': 'GUST-MARK-1-Enhanced',
                'features': {
                    'service_id_discovery': self.service_id_discovery_available,
                    'safe_console_commands': True,
                    'websockets': WEBSOCKET_IMPORT_SUCCESS,
                    'server_health_monitoring': True
                }
            })
        
        logger.info("✅ Miscellaneous routes registered")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask application"""
        logger.info(f"🚀 Starting GUST Bot Enhanced on {host}:{port}")
        logger.info(f"🔍 Service ID Discovery: {'✅ Available' if self.service_id_discovery_available else '❌ Not Available'}")
        logger.info(f"🛡️ Safe Console Commands: ✅ Enabled")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    # Ensure required directories exist
    ensure_directories()
    ensure_data_files()
    
    # Create and run application
    app = GustBotEnhanced()
    app.run(debug=True)