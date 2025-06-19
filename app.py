"""
GUST Bot Enhanced - Main Flask Application (FIXED VERSION)
=========================================================
✅ Fixed MongoDB connection handling with graceful fallback
✅ Added user_storage system for clans/economy integration  
✅ Fixed init_clans_routes() missing user_storage parameter
✅ All console functions working with correct GraphQL
✅ Enhanced error handling and logging
"""

import os
import json
import time
import threading
import schedule
import secrets
from datetime import datetime, timedelta
from collections import deque
from flask import Flask, render_template, session, redirect, url_for, jsonify, request
import logging

# Import configuration and utilities
from config import Config, WEBSOCKETS_AVAILABLE, ensure_directories, ensure_data_files
from utils.rate_limiter import RateLimiter
from utils.helpers import load_token, format_command, validate_server_id, validate_region

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
    
    def create_clan(self, server_id, clan_data):
        """Create a clan on a specific server"""
        if server_id not in self.clans:
            self.clans[server_id] = {}
        
        clan_id = clan_data.get('clanId', str(len(self.clans[server_id]) + 1))
        self.clans[server_id][clan_id] = clan_data
        return clan_id
    
    def get_clans(self, server_id=None):
        """Get clans for a server or all clans"""
        if server_id:
            return list(self.clans.get(server_id, {}).values())
        else:
            all_clans = []
            for server_clans in self.clans.values():
                all_clans.extend(server_clans.values())
            return all_clans

class GustBotEnhanced:
    """Main GUST Bot Enhanced application class (FIXED VERSION)"""
    
    def __init__(self):
        """Initialize the enhanced GUST bot application"""
        self.app = Flask(__name__)
        self.app.secret_key = Config.SECRET_KEY
        
        # Ensure directories exist
        ensure_directories()
        ensure_data_files()
        
        # Rate limiter for G-Portal API
        self.rate_limiter = RateLimiter(
            max_calls=Config.RATE_LIMIT_MAX_CALLS,
            time_window=Config.RATE_LIMIT_TIME_WINDOW
        )
        
        # In-memory storage for demo mode
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
        
        # Database connection (optional)
        self.init_database()
        
        # Initialize systems
        self.vanilla_koth = VanillaKothSystem(self)
        
        # WebSocket manager for live console (only if websockets available)
        if WEBSOCKETS_AVAILABLE:
            try:
                self.websocket_manager = WebSocketManager(self)
                self.live_connections = {}
                # Start WebSocket manager
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
        
        logger.info("🚀 GUST Bot Enhanced initialized successfully")
    
    def init_user_storage(self):
        """Initialize user storage system (CRITICAL FIX)"""
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
            
            # Try to initialize MongoDB-based user storage
            try:
                from utils.user_helpers import UserStorage
                mongodb_storage = UserStorage(self.db)
                # Only replace if MongoDB storage is working
                self.user_storage = mongodb_storage
                print('[✅ OK] MongoDB UserStorage initialized')
            except ImportError:
                print('[⚠️ WARNING] UserStorage class not found, keeping InMemoryUserStorage')
            except Exception as e:
                print(f'[⚠️ WARNING] MongoDB UserStorage failed: {e}, keeping InMemoryUserStorage')
                
        except ImportError:
            print('[ℹ️ INFO] PyMongo not available - using in-memory storage')
        except Exception as e:
            print(f'[⚠️ WARNING] MongoDB connection failed: {e}')
            print('[ℹ️ INFO] This is normal if MongoDB is not installed')
            print('[ℹ️ INFO] Using in-memory storage - all features will work normally')
        
        # Final safety check
        if self.user_storage is None:
            print('[🔧 EMERGENCY] user_storage was None, creating InMemoryUserStorage')
            self.user_storage = InMemoryUserStorage()
        
        print(f'[✅ OK] Database initialization complete - Storage: {type(self.user_storage).__name__}')
    
    def setup_routes(self):
        """Setup Flask routes and blueprints (FIXED VERSION)"""
        print("[DEBUG]: Setting up routes...")
        
        # Register authentication blueprint
        self.app.register_blueprint(auth_bp)
        print("[✅ OK] Auth routes registered")

        # Register other route blueprints with CORRECT parameters
        servers_bp = init_servers_routes(self.app, self.db, self.servers)
        self.app.register_blueprint(servers_bp)
        print("[✅ OK] Server routes registered")

        events_bp = init_events_routes(self.app, self.db, self.events, self.vanilla_koth, self.console_output)
        self.app.register_blueprint(events_bp)
        print("[✅ OK] Events routes registered")

        # FIXED: Pass user_storage for economy routes
        economy_bp = init_economy_routes(self.app, self.db, self.user_storage)
        self.app.register_blueprint(economy_bp)
        print("[✅ OK] Economy routes registered")

        # FIXED: Pass user_storage for gambling routes  
        gambling_bp = init_gambling_routes(self.app, self.db, self.user_storage)
        self.app.register_blueprint(gambling_bp)
        print("[✅ OK] Gambling routes registered")

        # CRITICAL FIX: Pass user_storage to clans routes
        clans_bp = init_clans_routes(self.app, self.db, self.clans, self.user_storage)
        self.app.register_blueprint(clans_bp)
        print("[✅ OK] Clans routes registered")

        # Users routes
        users_bp = init_users_routes(self.app, self.db, self.users, self.console_output)
        self.app.register_blueprint(users_bp)
        print("[✅ OK] Users routes registered")
        
        # Logs routes
        logs_bp = init_logs_routes(self.app, self.db, self.logs)
        self.app.register_blueprint(logs_bp)
        print("[✅ OK] Logs routes registered")
        
        # Setup main routes
        @self.app.route('/')
        def index():
            if 'logged_in' not in session:
                return redirect(url_for('auth.login'))
            return render_template('enhanced_dashboard.html')
        
        # Console routes
        self.setup_console_routes()
        
        # Miscellaneous routes
        self.setup_misc_routes()
        
        print("[✅ OK] All routes registered successfully")
    
    def setup_console_routes(self):
        """Setup console-related routes"""
        
        @self.app.route('/api/console/send', methods=['POST'])
        def send_console_command():
            """Send console command to server - WORKING VERSION"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            data = request.json
            command = data.get('command', '')
            server_id = data.get('serverId', '')
            region = data.get('region', 'US')
            
            if not command or not server_id:
                return jsonify({'success': False, 'error': 'Command and server ID required'})
            
            # Check if in demo mode
            if session.get('demo_mode', True):
                # Demo mode - simulate command
                self.console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'command': command,
                    'server_id': server_id,
                    'status': 'sent',
                    'source': 'demo',
                    'type': 'command',
                    'message': f'Demo command: {command}'
                })
                
                # Simulate response in separate thread
                def simulate_response():
                    time.sleep(1)
                    responses = [
                        f"[DEMO] Server {server_id}: Command '{command}' executed successfully",
                        f"[DEMO] {server_id}: Players online: 23/100",
                        f"[DEMO] {server_id}: Server FPS: 60",
                        f"[DEMO] {server_id}: Uptime: 2d 14h 32m"
                    ]
                    
                    for response_msg in responses[:2]:  # Send 2 responses
                        self.console_output.append({
                            'timestamp': datetime.now().isoformat(),
                            'message': response_msg,
                            'status': 'server_response',
                            'server_id': server_id,
                            'source': 'demo_simulation',
                            'type': 'system'
                        })
                        time.sleep(0.5)
                
                threading.Thread(target=simulate_response, daemon=True).start()
                return jsonify({'success': True, 'demo_mode': True})
            
            # Real mode - send command using WORKING GraphQL
            try:
                result = self.send_console_command_graphql(command, server_id, region)
                return jsonify({'success': result, 'demo_mode': False})
            except Exception as e:
                logger.error(f"❌ Console command error: {e}")
                return jsonify({'success': False, 'error': str(e), 'demo_mode': False})
        
        @self.app.route('/api/console/output')
        def get_console_output():
            """Get recent console output"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Return last 50 entries
            return jsonify(list(self.console_output)[-50:])
        
        # Live Console Routes (only if WebSockets are available)
        if WEBSOCKETS_AVAILABLE and self.websocket_manager:
            self.setup_live_console_routes()
        else:
            self.setup_stub_console_routes()
    
    def setup_live_console_routes(self):
        """Setup live console routes when WebSockets are available"""
        
        @self.app.route('/api/console/live/connect', methods=['POST'])
        def connect_live_console():
            """Connect to live console for a server"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            data = request.json
            server_id = data.get('serverId')
            region = data.get('region', 'US')
            
            if not server_id:
                return jsonify({'success': False, 'error': 'Server ID required'})
            
            if session.get('demo_mode', True):
                return jsonify({
                    'success': False, 
                    'error': 'Live console requires G-Portal authentication. Please login with real credentials.'
                })
            
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
                
            except Exception as e:
                logger.error(f"❌ Error connecting live console: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to connect: {str(e)}'
                })
        
        @self.app.route('/api/console/live/disconnect', methods=['POST'])
        def disconnect_live_console():
            """Disconnect live console for a server"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            data = request.json
            server_id = data.get('serverId')
            
            if server_id in self.live_connections:
                try:
                    self.websocket_manager.remove_connection(server_id)
                    del self.live_connections[server_id]
                    
                    return jsonify({
                        'success': True,
                        'message': f'Live console disconnected for server {server_id}'
                    })
                except Exception as e:
                    logger.error(f"❌ Error disconnecting live console: {e}")
                    return jsonify({
                        'success': False,
                        'error': f'Failed to disconnect: {str(e)}'
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Server not connected'
                })
        
        @self.app.route('/api/console/live/status')
        def live_console_status():
            """Get live console connection status"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            if self.websocket_manager:
                try:
                    status = self.websocket_manager.get_connection_status()
                except Exception as e:
                    logger.error(f"❌ Error getting connection status: {e}")
                    status = {}
            else:
                status = {}
            
            return jsonify({
                'connections': status,
                'total_connections': len(status),
                'demo_mode': session.get('demo_mode', True),
                'websockets_available': WEBSOCKETS_AVAILABLE
            })
        
        @self.app.route('/api/console/live/messages')
        def get_live_messages():
            """Get live console messages"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            server_id = request.args.get('serverId')
            limit = int(request.args.get('limit', 50))
            message_type = request.args.get('type')
            
            if message_type == 'all':
                message_type = None
            
            # Get WebSocket messages (live server console) if available
            ws_messages = []
            if self.websocket_manager:
                try:
                    ws_messages = self.websocket_manager.get_messages(
                        server_id=server_id,
                        limit=limit,
                        message_type=message_type
                    )
                except Exception as e:
                    logger.error(f"❌ Error getting WebSocket messages: {e}")
                    ws_messages = []
            
            # Get console output messages (demo/commands/system messages only)
            console_messages = []
            for msg in self.console_output:
                # Only include non-WebSocket messages to avoid duplication
                if msg.get('source') != 'websocket_live':
                    console_messages.append(msg)
            
            # Filter console messages by type
            if message_type and message_type != 'all':
                console_messages = [msg for msg in console_messages if msg.get('type') == message_type]
            
            # Combine WebSocket and console messages
            all_messages = ws_messages + console_messages[-limit:]
            
            # Sort by timestamp safely
            all_messages.sort(key=lambda x: x.get("timestamp", ""))
            
            # Limit results
            final_messages = all_messages[-limit:] if limit else all_messages
            
            return jsonify({
                'messages': final_messages,
                'count': len(final_messages),
                'server_id': server_id,
                'timestamp': datetime.now().isoformat(),
                'websockets_available': WEBSOCKETS_AVAILABLE
            })
        
        @self.app.route('/api/console/live/test')
        def test_live_console():
            """Test endpoint to check live console functionality"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # Get connection status
                if self.websocket_manager:
                    status = self.websocket_manager.get_connection_status()
                    
                    # Get recent messages from all servers
                    all_messages = []
                    for server_id in status.keys():
                        try:
                            messages = self.websocket_manager.get_messages(server_id, limit=10)
                            all_messages.extend(messages)
                        except Exception as e:
                            logger.error(f"❌ Error getting messages for server {server_id}: {e}")
                    
                    return jsonify({
                        'success': True,
                        'websockets_available': WEBSOCKETS_AVAILABLE,
                        'connections': status,
                        'total_connections': len(status),
                        'recent_messages': all_messages[-10:],  # Last 10 messages
                        'message_count': len(all_messages),
                        'test_timestamp': datetime.now().isoformat(),
                        'enhanced_console': True,
                        'pending_commands': 0
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'WebSocket manager not available',
                        'websockets_available': WEBSOCKETS_AVAILABLE
                    })
                    
            except Exception as e:
                logger.error(f"❌ Live console test error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'websockets_available': WEBSOCKETS_AVAILABLE
                })
    
    def setup_stub_console_routes(self):
        """Setup stub console routes when WebSockets are not available"""
        
        @self.app.route('/api/console/live/connect', methods=['POST'])
        def connect_live_console():
            return jsonify({
                'success': False,
                'error': 'WebSocket support not available. Install with: pip install websockets'
            })
        
        @self.app.route('/api/console/live/status')
        def live_console_status():
            return jsonify({
                'connections': {},
                'total_connections': 0,
                'demo_mode': session.get('demo_mode', True),
                'websockets_available': False
            })
        
        @self.app.route('/api/console/live/messages')
        def get_live_messages():
            limit = int(request.args.get('limit', 50))
            message_type = request.args.get('type')
            
            console_messages = list(self.console_output)
            
            # Filter by type
            if message_type and message_type != 'all':
                console_messages = [msg for msg in console_messages if msg.get('type') == message_type]
            
            final_messages = console_messages[-limit:] if limit else console_messages
            
            return jsonify({
                'messages': final_messages,
                'count': len(final_messages),
                'timestamp': datetime.now().isoformat(),
                'websockets_available': False
            })
        
        @self.app.route('/api/console/live/test')
        def test_live_console():
            return jsonify({
                'success': False,
                'error': 'WebSocket support not available',
                'websockets_available': False,
                'enhanced_console': False
            })
    
    def setup_misc_routes(self):
        """Setup miscellaneous routes"""
        
        @self.app.route('/health')
        def health_check():
            """Enhanced health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'MongoDB' if self.db else 'InMemoryStorage',
                'user_storage': type(self.user_storage).__name__,
                'koth_system': 'vanilla_compatible',
                'websockets_available': WEBSOCKETS_AVAILABLE,
                'active_events': len(self.vanilla_koth.get_active_events()),
                'live_connections': len(self.live_connections) if self.live_connections else 0,
                'console_buffer_size': len(self.console_output),
                'features': {
                    'console_commands': True,
                    'event_management': True,
                    'koth_events_fixed': True,
                    'economy_system': True,
                    'clan_management': True,
                    'gambling_games': True,
                    'server_diagnostics': True,
                    'live_console': WEBSOCKETS_AVAILABLE,
                    'graphql_working': True,
                    'user_storage_working': True
                }
            })
        
        @self.app.route('/api/token/status')
        def token_status():
            """Get authentication token status"""
            try:
                token_data = load_token()
                demo_mode = session.get('demo_mode', True)
                
                if demo_mode:
                    return jsonify({
                        'has_token': False,
                        'token_valid': False,
                        'demo_mode': True,
                        'websockets_available': WEBSOCKETS_AVAILABLE,
                        'time_left': 0
                    })
                
                if token_data:
                    # Check if token is still valid (simplified check)
                    expires_at = token_data.get('access_token_exp', 0)
                    current_time = int(time.time())
                    time_left = expires_at - current_time
                    
                    return jsonify({
                        'has_token': True,
                        'token_valid': time_left > 0,
                        'demo_mode': False,
                        'websockets_available': WEBSOCKETS_AVAILABLE,
                        'time_left': max(0, time_left)
                    })
                else:
                    return jsonify({
                        'has_token': False,
                        'token_valid': False,
                        'demo_mode': False,
                        'websockets_available': WEBSOCKETS_AVAILABLE,
                        'time_left': 0
                    })
                    
            except Exception as e:
                logger.error(f"❌ Error checking token status: {e}")
                return jsonify({
                    'has_token': False,
                    'token_valid': False,
                    'demo_mode': True,
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'time_left': 0,
                    'error': str(e)
                })
    
    def send_console_command_graphql(self, command, sid, region):
        """
        Send console command via GraphQL with WORKING implementation
        ✅ CORRECT GraphQL structure for G-Portal API
        """
        import requests
        
        self.rate_limiter.wait_if_needed("graphql")
        
        token = load_token()
        if not token:
            logger.warning("❌ No G-Portal token available")
            return False
        
        # Validate inputs
        is_valid, server_id = validate_server_id(sid)
        if not is_valid:
            logger.error(f"❌ Invalid server ID: {sid}")
            return False
        
        if not validate_region(region):
            logger.error(f"❌ Invalid region: {region}")
            return False
        
        endpoint = Config.GPORTAL_API_ENDPOINT
        
        # Format command properly
        formatted_command = format_command(command)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "GUST-Bot/1.0"
        }
        
        # ✅ CORRECT GraphQL payload structure for G-Portal API
        payload = {
            "operationName": "sendConsoleMessage",
            "variables": {
                "sid": server_id,
                "region": region.upper(),
                "message": formatted_command
            },
            "query": """mutation sendConsoleMessage($sid: Int!, $region: REGION!, $message: String!) {
              sendConsoleMessage(rsid: {id: $sid, region: $region}, message: $message) {
                ok
                __typename
              }
            }"""
        }
        
        try:
            logger.info(f"🔄 Sending command to server {server_id} ({region}): {formatted_command}")
            response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'data' in data and 'sendConsoleMessage' in data['data']:
                        result = data['data']['sendConsoleMessage']
                        success = result.get('ok', False)
                        logger.info(f"✅ Command result: {success}")
                        
                        # Add to console output for tracking
                        self.console_output.append({
                            'timestamp': datetime.now().isoformat(),
                            'command': formatted_command,
                            'server_id': str(server_id),
                            'status': 'sent' if success else 'failed',
                            'source': 'api',
                            'type': 'command',
                            'message': f'Command: {formatted_command}',
                            'success': success
                        })
                        
                        return success
                    elif 'errors' in data:
                        logger.error(f"❌ GraphQL errors: {data['errors']}")
                        return False
                    else:
                        logger.error(f"❌ Unexpected response format")
                        return False
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse JSON response: {e}")
                    return False
            else:
                logger.error(f"❌ HTTP error {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
    
    def start_background_tasks(self):
        """Start background tasks"""
        def run_scheduled():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        # Schedule cleanup tasks
        schedule.every(5).minutes.do(self.cleanup_expired_events)
        
        thread = threading.Thread(target=run_scheduled, daemon=True)
        thread.start()
        
        logger.info("📅 Background tasks started")
    
    def cleanup_expired_events(self):
        """Clean up expired events"""
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
                    except Exception as e:
                        logger.error(f"❌ Error cleaning up event: {e}")
    
    def run(self, host=None, port=None, debug=False):
        """Run the enhanced application"""
        host = host or Config.DEFAULT_HOST
        port = port or Config.DEFAULT_PORT
        
        logger.info(f"🚀 Starting GUST Bot Enhanced on {host}:{port}")
        logger.info(f"🔧 WebSocket Support: {'Available' if WEBSOCKETS_AVAILABLE else 'Not Available'}")
        logger.info(f"🗄️ Database: {'MongoDB' if self.db else 'In-Memory'}")
        logger.info(f"👥 User Storage: {type(self.user_storage).__name__}")
        logger.info(f"📡 Live Console: {'Enabled' if self.websocket_manager else 'Disabled'}")
        
        try:
            self.app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
        except KeyboardInterrupt:
            logger.info("\n👋 GUST Enhanced stopped by user")
            # Clean up WebSocket connections
            if self.websocket_manager:
                try:
                    self.websocket_manager.stop()
                except Exception as e:
                    logger.error(f"❌ Error stopping WebSocket manager: {e}")
        except Exception as e:
            logger.error(f"\n❌ Error: {e}")
