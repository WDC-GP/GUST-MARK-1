"""
GUST Bot Enhanced - Main Flask Application (COMPREHENSIVE AUTHENTICATION FIX)
================================================================================
✅ FIXED: Centralized token management with consistent authentication patterns
✅ FIXED: Simplified token handling removing complex format checking
✅ FIXED: Authentication-safe rate limiting that doesn't interfere with tokens
✅ FIXED: Enhanced error handling and logging for authentication issues
✅ FIXED: Consistent session validation across all routes
✅ ENHANCED: Better request throttling and performance monitoring
✅ ENHANCED: Comprehensive health checks and diagnostics
✅ ENHANCED: Background task optimization for token management
✅ PRESERVED: All existing functionality and features
"""

import os
import json
import time
import threading
import schedule
import secrets
from datetime import datetime, timedelta
from collections import deque, defaultdict
from flask import Flask, render_template, session, redirect, url_for, jsonify, request
import logging

# Import configuration and utilities
from config import Config, WEBSOCKETS_AVAILABLE, ensure_directories, ensure_data_files
from utils.rate_limiter import RateLimiter

# ✅ FIXED: Use centralized token management functions
from utils.helpers import (
    load_token, 
    refresh_token,
    monitor_token_health, 
    validate_token_file,
    format_command, 
    validate_server_id, 
    validate_region,
    parse_console_response
)

# Server Health components
from utils.server_health_storage import ServerHealthStorage

# Import systems
from systems.koth import VanillaKothSystem

# Import route blueprints
from routes.auth import auth_bp
from routes.servers import init_servers_routes
from routes.events import init_events_routes
from routes.economy import init_economy_routes
from routes.gambling import init_gambling_routes
from routes.clans import init_clans_routes
from routes.users import init_users_routes
from routes.logs import init_logs_routes
from routes.server_health import init_server_health_routes

# Import WebSocket components
if WEBSOCKETS_AVAILABLE:
    from websocket.manager import WebSocketManager

logger = logging.getLogger(__name__)

class InMemoryUserStorage:
    """Enhanced in-memory user storage for demo mode and user management"""
    
    def __init__(self):
        self.users = {}
        self.balances = {}  # server_id -> user_id -> balance
        self.clans = {}     # server_id -> clan_data
        print('[✅ INFO] In-memory user storage initialized')
    
    def register(self, user_id, nickname=None, server_id='default_server'):
        """Register method for compatibility"""
        if nickname is None:
            nickname = user_id
        return self.register_user(user_id, nickname, server_id)
    
    def register_user(self, user_id, nickname=None, server_id='default_server'):
        """Register a user with proper structure"""
        if nickname is None:
            nickname = user_id
            
        # Initialize user if not exists
        if user_id not in self.users:
            self.users[user_id] = {
                'userId': user_id,
                'nickname': nickname,
                'servers': {},
                'createdAt': datetime.now().isoformat()
            }
        
        # Initialize server data if not exists
        if server_id not in self.users[user_id]['servers']:
            self.users[user_id]['servers'][server_id] = {
                'serverId': server_id,
                'nickname': nickname,
                'balance': 1000,  # Starting balance
                'joinedAt': datetime.now().isoformat(),
                'lastActive': datetime.now().isoformat(),
                'clanTag': None,
                'clanRole': None
            }
        
        # Initialize balance tracking
        if server_id not in self.balances:
            self.balances[server_id] = {}
        if user_id not in self.balances[server_id]:
            self.balances[server_id][user_id] = 1000
        
        print(f"[✅ OK] User {user_id} registered on server {server_id}")
        return {'success': True, 'user_id': user_id, 'nickname': nickname}
    
    def get_user(self, user_id):
        """Get user data"""
        return self.users.get(user_id)
    
    def get_server_balance(self, user_id, server_id):
        """Get user balance for a specific server"""
        if server_id in self.balances and user_id in self.balances[server_id]:
            return self.balances[server_id][user_id]
        return 0
    
    def update_server_balance(self, user_id, server_id, new_balance):
        """Update user balance for a specific server"""
        if server_id not in self.balances:
            self.balances[server_id] = {}
        self.balances[server_id][user_id] = new_balance
        
        # Also update in user structure
        if user_id in self.users and server_id in self.users[user_id]['servers']:
            self.users[user_id]['servers'][server_id]['balance'] = new_balance
        
        return True

class GustBotEnhanced:
    """
    ✅ COMPREHENSIVE FIX: Main GUST Bot Enhanced application with centralized authentication
    """
    
    def __init__(self):
        """Initialize the enhanced GUST bot application"""
        self.app = Flask(__name__)
        self.app.secret_key = Config.SECRET_KEY
        
        # Ensure directories exist
        ensure_directories()
        ensure_data_files()
        
        # ✅ FIXED: Authentication-safe rate limiter configuration
        self.rate_limiter = RateLimiter(
            max_calls=8,  # Increased from 3 to 8 to prevent token conflicts
            time_window=10  # Increased from 1 to 10 seconds
        )
        
        # ✅ ENHANCED: Request tracking with authentication-safe limits
        self.request_timestamps = defaultdict(list)
        self.rate_limit_window = 120  # Increased to 2 minutes
        self.max_requests_per_window = 50  # Increased limit
        
        # Application state
        self.servers = []
        self.events = []
        self.economy = {}
        self.clans = []
        self.console_output = deque(maxlen=Config.CONSOLE_MESSAGE_BUFFER_SIZE)
        self.gambling_history = []
        self.managed_servers = []
        self.event_history = []
        self.transaction_history = []
        self.logs = []
        self.gambling = []
        self.users = []
        self.live_connections = {}
        
        # Initialize user storage system FIRST
        self.init_user_storage()
        
        # Server Health storage (pre-initialization)
        self.server_health_storage = ServerHealthStorage(None, None)
        print("[✅ OK] Server Health storage pre-initialized")
        
        # Database connection (optional)
        self.init_database()
        
        # Initialize systems
        self.vanilla_koth = VanillaKothSystem(self)
        
        # WebSocket manager for live console (only if websockets available)
        if WEBSOCKETS_AVAILABLE:
            try:
                self.websocket_manager = WebSocketManager(self)
                self.live_connections = {}
                self.websocket_manager.start()
                logger.info("✅ WebSocket manager initialized")
            except Exception as e:
                logger.error(f"❌ WebSocket manager failed: {e}")
                self.websocket_manager = None
                self.live_connections = {}
        else:
            self.websocket_manager = None
            self.live_connections = {}
        
        # Store reference to self in app context
        self.app.gust_bot = self
        
        # Setup routes
        self.setup_routes()
        
        # Background tasks
        self.start_background_tasks()
        
        logger.info("🚀 GUST Bot Enhanced initialized with centralized authentication")
    
    def check_rate_limit(self, endpoint='default'):
        """
        ✅ ENHANCED: Authentication-safe rate limiting
        
        Args:
            endpoint (str): Endpoint identifier for tracking
            
        Returns:
            bool: True if request is allowed, False if rate limited
        """
        current_time = time.time()
        
        # Clean old timestamps outside window
        cutoff_time = current_time - self.rate_limit_window
        self.request_timestamps[endpoint] = [
            ts for ts in self.request_timestamps[endpoint] 
            if ts > cutoff_time
        ]
        
        # Check if under limit
        if len(self.request_timestamps[endpoint]) < self.max_requests_per_window:
            self.request_timestamps[endpoint].append(current_time)
            return True
        
        logger.warning(f"⚠️ Rate limit exceeded for endpoint: {endpoint}")
        return False
    
    def get_rate_limit_stats(self):
        """Get comprehensive rate limiting statistics"""
        current_time = time.time()
        cutoff_time = current_time - self.rate_limit_window
        
        stats = {}
        for endpoint, timestamps in self.request_timestamps.items():
            # Clean old timestamps
            recent_timestamps = [ts for ts in timestamps if ts > cutoff_time]
            stats[endpoint] = {
                'requests_last_window': len(recent_timestamps),
                'limit': self.max_requests_per_window,
                'time_window': self.rate_limit_window,
                'last_request': max(recent_timestamps) if recent_timestamps else 0,
                'requests_per_minute': len([ts for ts in recent_timestamps if ts > current_time - 60])
            }
        
        return stats
    
    def init_user_storage(self):
        """Initialize user storage system"""
        print("[DEBUG]: Initializing user storage system...")
        
        # Always start with in-memory storage
        self.user_storage = InMemoryUserStorage()
        
        # Ensure user_storage is never None
        if self.user_storage is None:
            print('[🔧 EMERGENCY] Creating emergency user storage')
            self.user_storage = InMemoryUserStorage()
        
        print(f'[✅ OK] User storage initialized: {type(self.user_storage).__name__}')
    
    def init_database(self):
        """Initialize MongoDB connection with improved error handling"""
        print("[DEBUG]: Attempting MongoDB connection...")
        self.db = None
        
        try:
            # Check if MongoDB is available
            from pymongo import MongoClient
            
            # Try to connect with short timeout
            client = MongoClient(
                'mongodb://localhost:27017/', 
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000
            )
            
            # Test the connection
            client.server_info()
            self.db = client.gust_bot
            print('[✅ OK] MongoDB connected successfully')
            
        except ImportError:
            print('[ℹ️ INFO] PyMongo not available - using in-memory storage')
        except Exception as e:
            print(f'[⚠️ WARNING] MongoDB connection failed: {e}')
            print('[ℹ️ INFO] Using in-memory storage - all features will work normally')
        
        # Update Server Health storage with proper database connection
        self.server_health_storage = ServerHealthStorage(self.db, self.user_storage)
        print("[✅ OK] Server Health storage initialized with database connection")
        
        print(f'[✅ OK] Database initialization complete - Storage: {type(self.user_storage).__name__}')
    
    def setup_routes(self):
        """Setup Flask routes and blueprints"""
        print("[DEBUG]: Setting up routes with centralized authentication...")
        
        # Register authentication blueprint (foundation)
        self.app.register_blueprint(auth_bp)
        print("[✅ OK] Auth routes registered")

        # Register core route blueprints
        servers_bp = init_servers_routes(self.app, self.db, self.servers)
        self.app.register_blueprint(servers_bp)
        print("[✅ OK] Server routes registered")

        events_bp = init_events_routes(self.app, self.db, self.events, self.vanilla_koth, self.console_output)
        self.app.register_blueprint(events_bp)
        print("[✅ OK] Events routes registered")

        # User-dependent route blueprints
        economy_bp = init_economy_routes(self.app, self.db, self.user_storage)
        self.app.register_blueprint(economy_bp)
        print("[✅ OK] Economy routes registered")

        gambling_bp = init_gambling_routes(self.app, self.db, self.user_storage)
        self.app.register_blueprint(gambling_bp)
        print("[✅ OK] Gambling routes registered")

        clans_bp = init_clans_routes(self.app, self.db, self.clans, self.user_storage)
        self.app.register_blueprint(clans_bp)
        print("[✅ OK] Clans routes registered")

        # Management route blueprints
        users_bp = init_users_routes(self.app, self.db, self.users, self.console_output)
        self.app.register_blueprint(users_bp)
        print("[✅ OK] Users routes registered")
        
        logs_bp = init_logs_routes(self.app, self.db, self.logs)
        self.app.register_blueprint(logs_bp)
        print("[✅ OK] Logs routes registered")
        
        # Server Health routes
        server_health_bp = init_server_health_routes(self.app, self.db, self.server_health_storage)
        self.app.register_blueprint(server_health_bp)
        print("[✅ OK] Server Health routes registered")
        
        # Setup main routes
        @self.app.route('/')
        def index():
            if 'logged_in' not in session:
                return redirect(url_for('auth.login'))
            return render_template('enhanced_dashboard.html')
        
        # Console routes
        self.setup_console_routes()
        
        # Debug and monitoring routes
        self.setup_debug_routes()
        
        print("[✅ OK] All routes registered successfully")
    
    def setup_debug_routes(self):
        """Setup debug and monitoring routes"""
        
        @self.app.route('/api/debug/token-status')
        def debug_token_status():
            """Get comprehensive token health information"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # Get comprehensive token health
                token_health = monitor_token_health()
                token_validation = validate_token_file()
                
                return jsonify({
                    'success': True,
                    'token_health': token_health,
                    'token_validation': token_validation,
                    'session_info': {
                        'logged_in': session.get('logged_in', False),
                        'demo_mode': session.get('demo_mode', False),
                        'username': session.get('username', 'unknown')
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error in debug token status: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/debug/connection-health')
        def debug_connection_health():
            """Get WebSocket connection health status"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                connection_status = {}
                websocket_available = WEBSOCKETS_AVAILABLE and self.websocket_manager is not None
                
                if websocket_available:
                    try:
                        connection_status = self.websocket_manager.get_connection_status()
                    except Exception as ws_error:
                        logger.error(f"❌ WebSocket status error: {ws_error}")
                        connection_status = {}
                
                return jsonify({
                    'success': True,
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'websocket_manager_available': self.websocket_manager is not None,
                    'active_connections': len(connection_status),
                    'connection_details': connection_status,
                    'live_connections': self.live_connections,
                    'console_buffer_size': len(self.console_output),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error in debug connection health: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/debug/rate-limits')
        def debug_rate_limits():
            """Get rate limiting statistics"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                rate_stats = self.get_rate_limit_stats()
                
                return jsonify({
                    'success': True,
                    'rate_limits': rate_stats,
                    'configuration': {
                        'max_requests_per_window': self.max_requests_per_window,
                        'window_seconds': self.rate_limit_window,
                        'api_rate_limit_max_calls': Config.RATE_LIMIT_MAX_CALLS,
                        'api_rate_limit_time_window': Config.RATE_LIMIT_TIME_WINDOW
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error in debug rate limits: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
    
    def setup_console_routes(self):
        """
        ✅ COMPREHENSIVE FIX: Setup console routes with centralized authentication
        """
        
        @self.app.route('/api/console/send', methods=['POST'])
        def send_console_command():
            """✅ FIXED: Send console command with centralized authentication"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Authentication-safe rate limiting
            if not self.check_rate_limit('console_send'):
                return jsonify({
                    'success': False, 
                    'error': 'Rate limit exceeded. Please wait before sending another command.'
                }), 429
            
            try:
                # Enhanced request validation
                if not request or not request.json:
                    logger.error("❌ No JSON data in console command request")
                    return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
                
                data = request.json
                if not isinstance(data, dict):
                    logger.error("❌ Invalid JSON data format in console command")
                    return jsonify({'success': False, 'error': 'Invalid JSON format'}), 400
                
                # Safe data extraction
                command = data.get('command', '').strip()
                server_id = data.get('serverId', '').strip()
                region = data.get('region', 'US').strip().upper()
                
                logger.debug(f"🔍 Console command: '{command}', server: '{server_id}', region: '{region}'")
                
                # Validate required fields
                if not command or not server_id:
                    return jsonify({
                        'success': False, 
                        'error': 'Command and server ID are required'
                    }), 400
                
                # Check demo mode
                demo_mode = session.get('demo_mode', False)
                
                if demo_mode:
                    logger.info(f"🎭 Demo mode: Simulating command '{command}' to server {server_id}")
                    # Demo mode simulation
                    self.console_output.append({
                        'timestamp': datetime.now().isoformat(),
                        'command': command,
                        'server_id': server_id,
                        'status': 'sent',
                        'source': 'demo',
                        'type': 'command',
                        'message': f'Demo command: {command}'
                    })
                    
                    # Simulate response
                    def simulate_response():
                        try:
                            time.sleep(1)
                            responses = [
                                f"[DEMO] Server {server_id}: Command '{command}' executed successfully",
                                f"[DEMO] {server_id}: Server status: Online",
                            ]
                            
                            for response_msg in responses[:2]:
                                self.console_output.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'message': response_msg,
                                    'status': 'server_response',
                                    'server_id': server_id,
                                    'source': 'demo_simulation',
                                    'type': 'system'
                                })
                                time.sleep(0.5)
                        except Exception as sim_error:
                            logger.error(f"❌ Demo simulation error: {sim_error}")
                    
                    threading.Thread(target=simulate_response, daemon=True).start()
                    return jsonify({'success': True, 'demo_mode': True})
                
                # Real mode - send command using centralized GraphQL
                logger.info(f"🌐 Live mode: Sending command '{command}' to server {server_id}")
                
                try:
                    result = self.send_console_command_graphql(command, server_id, region)
                    return jsonify({'success': result, 'demo_mode': False})
                except Exception as graphql_error:
                    logger.error(f"❌ GraphQL command error: {graphql_error}")
                    return jsonify({
                        'success': False, 
                        'error': str(graphql_error), 
                        'demo_mode': False
                    }), 500
                    
            except Exception as outer_error:
                logger.error(f"❌ Console send route error: {outer_error}")
                return jsonify({
                    'success': False, 
                    'error': f'Request processing error: {str(outer_error)}'
                }), 500
        
        @self.app.route('/api/console/output')
        def get_console_output():
            """Get recent console output"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Return last 50 entries
            return jsonify(list(self.console_output)[-50:])
        
        # WebSocket routes setup
        if WEBSOCKETS_AVAILABLE and self.websocket_manager:
            self.setup_live_console_routes()
        else:
            self.setup_stub_console_routes()
    
    def send_console_command_graphql(self, command, sid, region):
        """
        ✅ COMPREHENSIVE FIX: Send console command with centralized token management
        
        Args:
            command (str): Console command to send
            sid (str): Server ID
            region (str): Server region
            
        Returns:
            bool: True if command successful, False otherwise
        """
        try:
            logger.debug(f"🔍 GraphQL command: command='{command}', sid='{sid}', region='{region}'")
            
            # Authentication-safe rate limiting
            self.rate_limiter.wait_if_needed("graphql")
            
            # ✅ FIXED: Use centralized token loading (simplified)
            token = load_token()
            if not token:
                logger.warning("❌ No valid G-Portal token available for GraphQL")
                return False
                
            # Enhanced validation
            try:
                is_valid, server_id = validate_server_id(sid)
                if not is_valid or server_id is None:
                    logger.error(f"❌ Invalid server ID: {sid}")
                    return False
                
                if not validate_region(region):
                    logger.error(f"❌ Invalid region: {region}")
                    return False
                
                formatted_command = format_command(command)
                if not formatted_command:
                    logger.error(f"❌ Command formatting failed for: {command}")
                    return False
                    
            except Exception as validation_error:
                logger.error(f"❌ Input validation error: {validation_error}")
                return False
            
            # Get endpoint
            endpoint = Config.GPORTAL_API_ENDPOINT + "graphql"
            
            # Enhanced headers for better G-Portal compatibility
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Origin": "https://www.g-portal.com",
                "Referer": "https://www.g-portal.com/",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache"
            }
            
            # GraphQL payload
            payload = {
                "operationName": "sendConsoleMessage",
                "variables": {
                    "sid": server_id,
                    "region": region,
                    "message": formatted_command
                },
                "query": """mutation sendConsoleMessage($sid: Int!, $region: REGION!, $message: String!) {
                  sendConsoleMessage(rsid: {id: $sid, region: $region}, message: $message) {
                    ok
                    __typename
                  }
                }"""
            }
            
            logger.info(f"🔄 Sending command to server {server_id} ({region}): {formatted_command}")
            
            # Make the request with enhanced error handling
            import requests
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            
            logger.debug(f"🔍 GraphQL response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Use centralized response parsing
                    success, message = parse_console_response(data)
                    
                    logger.info(f"✅ Command result: {success} - {message}")
                    
                    # Add to console output for tracking
                    self.console_output.append({
                        'timestamp': datetime.now().isoformat(),
                        'command': formatted_command,
                        'server_id': str(server_id),
                        'status': 'sent' if success else 'failed',
                        'source': 'graphql_api',
                        'type': 'command',
                        'message': f'Command: {formatted_command}',
                        'response': message,
                        'success': success
                    })
                    
                    return success
                    
                except json.JSONDecodeError as json_error:
                    logger.error(f"❌ Failed to parse GraphQL JSON response: {json_error}")
                    return False
                    
            elif response.status_code == 401:
                logger.warning("🔐 GraphQL authentication failed, attempting token refresh")
                
                # Attempt token refresh
                if refresh_token():
                    logger.info("✅ Token refresh successful, command should be retried")
                    # Don't retry automatically to avoid recursion, let caller handle
                    return False
                else:
                    logger.error("❌ Token refresh failed")
                    return False
                    
            elif response.status_code == 429:
                logger.error("❌ GraphQL rate limited")
                return False
            else:
                logger.error(f"❌ GraphQL HTTP error {response.status_code}: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ GraphQL request timeout")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ GraphQL connection error")
            return False
        except Exception as general_error:
            logger.error(f"❌ Exception in GraphQL command: {general_error}")
            return False
    
    def setup_live_console_routes(self):
        """Setup live console routes when WebSockets are available"""
        
        @self.app.route('/api/console/live/connect', methods=['POST'])
        def connect_live_console():
            """Connect to live console for a server"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                data = request.json if request.json else {}
                server_id = data.get('serverId')
                region = data.get('region', 'US')
                
                if not server_id:
                    return jsonify({'success': False, 'error': 'Server ID required'})
                
                if session.get('demo_mode', False):
                    return jsonify({
                        'success': False, 
                        'error': 'Live console requires G-Portal authentication. Please login with real credentials.'
                    })
                
                # ✅ FIXED: Use centralized token loading
                token = load_token()
                if not token:
                    return jsonify({
                        'success': False,
                        'error': 'No valid G-Portal token. Please re-login.'
                    })
                
                try:
                    # Add WebSocket connection
                    future = self.websocket_manager.add_connection(server_id, region, token)
                    self.live_connections[server_id] = {
                        'region': region,
                        'connected_at': datetime.now().isoformat(),
                        'connected': True
                    }
                    
                    return jsonify({
                        'success': True,
                        'message': f'Live console connected for server {server_id}',
                        'server_id': server_id
                    })
                    
                except Exception as connect_error:
                    logger.error(f"❌ Error connecting live console: {connect_error}")
                    return jsonify({
                        'success': False,
                        'error': f'Failed to connect: {str(connect_error)}'
                    })
                    
            except Exception as e:
                logger.error(f"❌ Live console connect error: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/console/live/disconnect', methods=['POST'])
        def disconnect_live_console():
            """Disconnect live console for a server"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                data = request.json if request.json else {}
                server_id = data.get('serverId')
                
                if server_id in self.live_connections:
                    try:
                        self.websocket_manager.remove_connection(server_id)
                        del self.live_connections[server_id]
                        
                        return jsonify({
                            'success': True,
                            'message': f'Live console disconnected for server {server_id}'
                        })
                    except Exception as disconnect_error:
                        logger.error(f"❌ Error disconnecting live console: {disconnect_error}")
                        return jsonify({
                            'success': False,
                            'error': f'Failed to disconnect: {str(disconnect_error)}'
                        })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Server not connected'
                    })
                    
            except Exception as e:
                logger.error(f"❌ Live console disconnect error: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/console/live/status')
        def live_console_status():
            """Get live console connection status"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                if self.websocket_manager:
                    try:
                        status = self.websocket_manager.get_connection_status()
                    except Exception as status_error:
                        logger.error(f"❌ Error getting connection status: {status_error}")
                        status = {}
                else:
                    status = {}
                
                return jsonify({
                    'connections': status,
                    'total_connections': len(status),
                    'demo_mode': session.get('demo_mode', False),
                    'websockets_available': WEBSOCKETS_AVAILABLE
                })
                
            except Exception as e:
                logger.error(f"❌ Live console status error: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/console/live/messages')
        def live_console_messages():
            """Get live console messages"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                if self.websocket_manager:
                    status = self.websocket_manager.get_connection_status()
                    all_messages = []
                    for server_id in status.keys():
                        try:
                            messages = self.websocket_manager.get_messages(server_id, limit=10)
                            all_messages.extend(messages)
                        except Exception as msg_error:
                            logger.error(f"❌ Error getting messages for server {server_id}: {msg_error}")
                    
                    return jsonify({
                        'success': True,
                        'websockets_available': WEBSOCKETS_AVAILABLE,
                        'connections': status,
                        'total_connections': len(status),
                        'recent_messages': all_messages[-10:],
                        'message_count': len(all_messages),
                        'test_timestamp': datetime.now().isoformat(),
                        'centralized_auth': True,
                        'pending_commands': 0
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'WebSocket manager not available',
                        'websockets_available': WEBSOCKETS_AVAILABLE
                    })
                    
            except Exception as e:
                logger.error(f"❌ Live console messages error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'websockets_available': WEBSOCKETS_AVAILABLE
                })
    
    def setup_stub_console_routes(self):
        """Setup stub console routes when WebSockets are not available"""
        
        @self.app.route('/api/console/live/connect', methods=['POST'])
        def connect_live_console():
            """Stub route when WebSockets not available"""
            return jsonify({
                'success': False,
                'error': 'WebSocket support not available. Install with: pip install websockets',
                'websockets_available': False,
                'demo_mode': session.get('demo_mode', False)
            })
        
        @self.app.route('/api/console/live/disconnect', methods=['POST'])
        def disconnect_live_console():
            """Stub route when WebSockets not available"""
            return jsonify({
                'success': False,
                'error': 'WebSocket support not available. Install with: pip install websockets',
                'websockets_available': False
            })
        
        @self.app.route('/api/console/live/status')
        def live_console_status():
            """Stub route when WebSockets not available"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            return jsonify({
                'connections': {},
                'total_connections': 0,
                'demo_mode': session.get('demo_mode', False),
                'websockets_available': False,
                'message': 'WebSocket support not available'
            })
        
        @self.app.route('/api/console/live/messages')
        def live_console_messages():
            """Stub route when WebSockets not available"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            return jsonify({
                'success': False,
                'messages': [],
                'websockets_available': False,
                'error': 'WebSocket support not available'
            })
    
    def start_background_tasks(self):
        """✅ ENHANCED: Start background tasks with token health monitoring"""
        def run_scheduled():
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(60)
                except Exception as schedule_error:
                    logger.error(f"❌ Background task error: {schedule_error}")
                    time.sleep(60)
        
        # Schedule cleanup tasks (staggered to avoid conflicts)
        schedule.every(5).minutes.at(":00").do(self.cleanup_expired_events)
        
        # Schedule server health monitoring
        schedule.every(3).minutes.at(":30").do(self.update_server_health_metrics)
        
        # ✅ NEW: Schedule token health monitoring
        schedule.every(2).minutes.at(":15").do(self.monitor_token_health_background)
        
        # Schedule rate limit cleanup
        schedule.every(30).minutes.at(":45").do(self.cleanup_rate_limit_data)
        
        thread = threading.Thread(target=run_scheduled, daemon=True)
        thread.start()
        
        logger.info("📅 Enhanced background tasks started with token monitoring")
    
    def cleanup_expired_events(self):
        """Clean up expired events"""
        try:
            current_time = datetime.now()
            if not self.db:
                # Clean in-memory events
                for event in self.events:
                    if event.get('status') == 'active':
                        try:
                            start_time = datetime.fromisoformat(event['startTime'])
                            duration = event.get('duration', 60)
                            if (current_time - start_time).total_seconds() > duration * 60:
                                event['status'] = 'completed'
                        except Exception as event_error:
                            logger.error(f"❌ Error cleaning up event: {event_error}")
        except Exception as cleanup_error:
            logger.error(f"❌ Event cleanup error: {cleanup_error}")
    
    def update_server_health_metrics(self):
        """Update server health metrics (background task)"""
        try:
            if self.server_health_storage:
                # Calculate current health metrics
                active_connections = len(self.live_connections) if self.live_connections else 0
                total_servers = len(self.servers) if self.servers else 0
                
                health_data = {
                    'timestamp': datetime.now().isoformat(),
                    'active_connections': active_connections,
                    'total_servers': total_servers,
                    'console_buffer_size': len(self.console_output),
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'database_connected': self.db is not None,
                    'centralized_auth': True
                }
                
                # Store health snapshot
                self.server_health_storage.store_system_health(health_data)
                
        except Exception as health_error:
            logger.error(f"❌ Error updating server health metrics: {health_error}")
    
    def monitor_token_health_background(self):
        """✅ ENHANCED: Monitor token health in background with proactive refresh"""
        try:
            # Check token health
            token_health = monitor_token_health()
            
            if not token_health['healthy']:
                if token_health['action'] == 'refresh_now':
                    logger.warning("⚠️ Background token refresh needed")
                    
                    # Attempt proactive refresh
                    if refresh_token():
                        logger.info("✅ Background token refresh successful")
                    else:
                        logger.error("❌ Background token refresh failed")
                        
                elif token_health['action'] == 'login_required':
                    logger.error("❌ Background detected expired tokens - re-login required")
                    
        except Exception as monitor_error:
            logger.error(f"❌ Error in background token monitoring: {monitor_error}")
    
    def cleanup_rate_limit_data(self):
        """Cleanup old rate limit data"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (self.rate_limit_window * 2)
            
            cleaned_endpoints = 0
            for endpoint in list(self.request_timestamps.keys()):
                old_count = len(self.request_timestamps[endpoint])
                self.request_timestamps[endpoint] = [
                    ts for ts in self.request_timestamps[endpoint] 
                    if ts > cutoff_time
                ]
                new_count = len(self.request_timestamps[endpoint])
                
                if old_count != new_count:
                    cleaned_endpoints += 1
                
                if not self.request_timestamps[endpoint]:
                    del self.request_timestamps[endpoint]
            
            if cleaned_endpoints > 0:
                logger.debug(f"🧹 Cleaned rate limit data for {cleaned_endpoints} endpoints")
                
        except Exception as cleanup_error:
            logger.error(f"❌ Rate limit cleanup error: {cleanup_error}")
    
    def run(self, host=None, port=None, debug=False):
        """Run the enhanced application with centralized authentication"""
        host = host or Config.DEFAULT_HOST
        port = port or Config.DEFAULT_PORT
        
        logger.info(f"🚀 Starting GUST Bot Enhanced on {host}:{port}")
        logger.info(f"🔧 WebSocket Support: {'Available' if WEBSOCKETS_AVAILABLE else 'Not Available'}")
        logger.info(f"🗄️ Database: {'MongoDB' if self.db else 'In-Memory'}")
        logger.info(f"👥 User Storage: {type(self.user_storage).__name__}")
        logger.info(f"📡 Live Console: {'Enabled' if self.websocket_manager else 'Disabled'}")
        logger.info(f"🛡️ Centralized Authentication: Enhanced rate limiting and token management")
        logger.info(f"🏥 Server Health: Enhanced monitoring with token health checks")
        
        try:
            self.app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
        except KeyboardInterrupt:
            logger.info("\n👋 GUST Enhanced stopped by user")
            if self.websocket_manager:
                try:
                    self.websocket_manager.stop()
                except Exception as cleanup_error:
                    logger.error(f"❌ Error stopping WebSocket manager: {cleanup_error}")
        except Exception as run_error:
            logger.error(f"\n❌ Error: {run_error}")

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    """Main application entry point"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run the application
    try:
        app = GustBotEnhanced()
        app.run(debug=True)
    except Exception as startup_error:
        logger.error(f"❌ Failed to start application: {startup_error}")
        exit(1)
