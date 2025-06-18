"""
GUST Bot Enhanced - Main Flask Application
=========================================
Main application class that combines all components
"""

import os
from app_backup_20250618_014324 import InMemoryUserStorage
import json
from app_backup_20250618_014324 import InMemoryUserStorage
import time
from app_backup_20250618_014324 import InMemoryUserStorage
import threading
from app_backup_20250618_014324 import InMemoryUserStorage
import schedule
from app_backup_20250618_014324 import InMemoryUserStorage
import secrets
from app_backup_20250618_014324 import InMemoryUserStorage
from datetime import datetime, timedelta
from collections import deque
from flask import Flask, render_template, session, redirect, url_for, jsonify
import logging

# Import configuration and utilities
from config import Config, WEBSOCKETS_AVAILABLE, MONGODB_AVAILABLE, ensure_directories, ensure_data_files
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
from routes.user_database import init_user_database_routes
from routes.logs import init_logs_routes
# Import WebSocket components
if WEBSOCKETS_AVAILABLE:
    from websocket.manager import WebSocketManager

logger = logging.getLogger(__name__)

class GustBotEnhanced:
    """Main GUST Bot Enhanced application class"""
    
    def __init__(self):
        """Initialize the enhanced GUST bot application"""
        self.user_storage = InMemoryUserStorage()
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
        self.gambling = []
        self.users = []
        self.live_connections = {}
        
        # Database connection (optional)
        self.init_database()
        
        # Initialize systems
        self.vanilla_koth = VanillaKothSystem(self)
        
        # WebSocket manager for live console (only if websockets available)
        if WEBSOCKETS_AVAILABLE:
            self.websocket_manager = WebSocketManager(self)
            self.live_connections = {}
            # Start WebSocket manager
            self.websocket_manager.start()
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
    
    def init_database(self):
        """Initialize MongoDB connection with bulletproof user storage"""
        self.db = None
        
        try:
            from pymongo import MongoClient
            client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
            client.server_info()
            self.db = client.gust_bot
            print('[OK] MongoDB connected successfully')
            
            try:
                from utils.user_helpers import UserStorage
                self.user_storage = UserStorage(self.db)
                print('[OK] MongoDB UserStorage initialized')
            except ImportError:
                print('[WARNING] UserStorage not found, using InMemoryUserStorage')
                # Keep the existing InMemoryUserStorage from __init__
                
        except Exception as e:
            print(f'[WARNING] MongoDB connection failed: {e}')
            print('[RETRY] Falling back to in-memory storage (demo mode)')
            # Keep the existing InMemoryUserStorage from __init__
        
        # BULLETPROOF: Ensure user_storage is NEVER None
        if self.user_storage is None:
            print('[FIX] Emergency: user_storage was None, creating InMemoryUserStorage')
            self.user_storage = InMemoryUserStorage()
        
        # BULLETPROOF: Ensure register method exists
        if not hasattr(self.user_storage, 'register'):
            print('[FIX] Adding missing register method')
            def register_compatibility(user_id, nickname=None, server_id='default_server'):
                if nickname is None:
                    nickname = user_id
                if hasattr(self.user_storage, 'register_user'):
                    return self.user_storage.register_user(user_id, nickname, server_id)
                else:
                    return {'success': False, 'error': 'Storage system broken'}
            self.user_storage.register = register_compatibility
        
        print(f'[OK] User storage type: {type(self.user_storage).__name__}')
        print('[OK] User storage initialization complete')
    def setup_routes(self):
        """Setup Flask routes and blueprints"""                # Register authentication blueprint
        self.app.register_blueprint(auth_bp)

        # Register other route blueprints
        servers_bp = init_servers_routes(self.app, self.db, self.servers)
        self.app.register_blueprint(servers_bp)

        events_bp = init_events_routes(self.app, self.db, self.events, self.vanilla_koth, self.console_output)
        self.app.register_blueprint(events_bp)

        economy_bp = init_economy_routes(self.app, self.db, self.economy)
        self.app.register_blueprint(economy_bp)

        gambling_bp = init_gambling_routes(self.app, self.db, self.gambling)
        self.app.register_blueprint(gambling_bp)

        clans_bp = init_clans_routes(self.app, self.db, self.clans, self.user_storage)
        self.app.register_blueprint(clans_bp)

        users_bp = init_users_routes(self.app, self.db, self.users, self.console_output)
        self.app.register_blueprint(users_bp)

        # Register user database routes (registration, profiles, etc.)
        user_database_bp = init_user_database_routes(self.app, self.db, self.user_storage)
        self.app.register_blueprint(user_database_bp)
        # Logs routes
        logs_bp = init_logs_routes(self.app, self.db, self.logs)
        self.app.register_blueprint(logs_bp)
        
        # Setup main routes
        @self.app.route('/')
        def index():
            if 'logged_in' not in session:
                return redirect(url_for('auth.login'))
            return render_template('enhanced_dashboard.html')
        
        # Console routes
        self.setup_console_routes()
        
        # Event routes
        self.setup_event_routes()
        
        # Economy routes
        self.setup_economy_routes()
        
        # Gambling routes
        self.setup_gambling_routes()
        
        # Clan routes
        self.setup_clan_routes()
        
        # User management routes
        self.setup_user_management_routes()
        
        # Miscellaneous routes
        self.setup_misc_routes()
    
    def setup_console_routes(self):
        """Setup console-related routes"""
        
        @self.app.route('/api/console/send', methods=['POST'])
        def send_console_command():
            """Send console command to server"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            from flask import request
            data = request.json
            command = data.get('command', '')
            server_id = data.get('serverId', '')
            region = data.get('region', 'US')
            
            # Check if in demo mode
            if session.get('demo_mode', True):
                # Demo mode - simulate command
                self.console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'command': command,
                    'server_id': server_id,
                    'status': 'sent',
                    'source': 'demo',
                    'type': 'command'
                })
                
                # Simulate response in separate thread
                def simulate_response():
                    time.sleep(1)
                    self.console_output.append({
                        'timestamp': datetime.now().isoformat(),
                        'message': f"[DEMO] Command executed: {command}",
                        'status': 'server_response',
                        'server_id': server_id,
                        'source': 'demo_simulation',
                        'type': 'system'
                    })
                
                threading.Thread(target=simulate_response, daemon=True).start()
                return jsonify({'success': True, 'demo_mode': True})
            
            # Real mode - send command
            result = self.send_console_command_graphql(command, server_id, region)
            return jsonify({'success': result, 'demo_mode': False})
        
        @self.app.route('/api/console/output')
        def get_console_output():
            """Get recent console output"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Return last 50 entries
            return jsonify(list(self.console_output)[-50:])
        
        # Live Console Routes (only if WebSockets are available)
        if WEBSOCKETS_AVAILABLE:
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
            
            from flask import request
            data = request.json
            server_id = data.get('serverId')
            region = data.get('region', 'US')
            
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
                    'connected_at': datetime.now().isoformat()
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
            
            from flask import request
            data = request.json
            server_id = data.get('serverId')
            
            if server_id in self.live_connections:
                self.websocket_manager.remove_connection(server_id)
                del self.live_connections[server_id]
                
                return jsonify({
                    'success': True,
                    'message': f'Live console disconnected for server {server_id}'
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
                status = self.websocket_manager.get_connection_status()
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
            
            from flask import request
            server_id = request.args.get('serverId')
            limit = int(request.args.get('limit', 50))
            message_type = request.args.get('type')
            
            if message_type == 'all':
                message_type = None
            
            # Get WebSocket messages (live server console) if available
            ws_messages = []
            if self.websocket_manager:
                ws_messages = self.websocket_manager.get_messages(
                    server_id=server_id,
                    limit=limit,
                    message_type=message_type
                )
            
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
            
            # Sort by timestamp
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
                        messages = self.websocket_manager.get_messages(server_id, limit=10)
                        all_messages.extend(messages)
                    
                    return jsonify({
                        'success': True,
                        'websockets_available': WEBSOCKETS_AVAILABLE,
                        'connections': status,
                        'total_connections': len(status),
                        'recent_messages': all_messages[-10:],  # Last 10 messages
                        'message_count': len(all_messages),
                        'test_timestamp': datetime.now().isoformat()
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'WebSocket manager not available',
                        'websockets_available': WEBSOCKETS_AVAILABLE
                    })
                    
            except Exception as e:
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
            from flask import request
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
                'websockets_available': False
            })
    
    def setup_event_routes(self):
        """Setup event management routes"""
        
        @self.app.route('/api/events/koth/start', methods=['POST'])
        def start_koth_event():
            """Start KOTH event - FIXED VERSION"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            from flask import request
            data = request.json
            
            # Enhanced event data with vanilla-compatible settings
            event_config = {
                'serverId': data.get('serverId'),
                'region': data.get('region', 'US'),
                'duration': data.get('duration', 30),  # Default 30 minutes
                'reward_item': data.get('reward_item', 'scrap'),
                'reward_amount': data.get('reward_amount', 1000),
                'arena_location': data.get('arena_location', 'Launch Site'),
                'give_supplies': data.get('give_supplies', True)
            }
            
            if not event_config['serverId']:
                return jsonify({'success': False, 'error': 'Server ID required'})
            
            # Use the fixed KOTH system
            result = self.vanilla_koth.start_koth_event_fixed(event_config)
            
            if result:
                # Add to console output
                self.console_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': f"🎯 KOTH Event started on server {event_config['serverId']} at {event_config['arena_location']}",
                    'status': 'event',
                    'source': 'event_system',
                    'type': 'event'
                })
            
            return jsonify({'success': result})
        
        @self.app.route('/api/events')
        def get_events():
            """Get active events"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            if self.db:
                events = list(self.db.events.find({'status': 'active'}, {'_id': 0}))
                return jsonify(events)
            return jsonify([e for e in self.events if e.get('status') == 'active'])
    
    def setup_economy_routes(self):
        """Setup economy system routes"""
        
        @self.app.route('/api/economy/balance/<user_id>')
        def get_user_balance(user_id):
            """Get user's economy balance"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            if self.db:
                user = self.db.economy.find_one({'userId': user_id})
                if user:
                    return jsonify({'balance': user.get('balance', 0)})
            else:
                balance = self.economy.get(user_id, 0)
                return jsonify({'balance': balance})
            return jsonify({'balance': 0})
        
        @self.app.route('/api/economy/transfer', methods=['POST'])
        def transfer_coins():
            """Transfer coins between users"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            from flask import request
            data = request.json
            result = self.transfer_coins_api(
                data['fromUserId'], 
                data['toUserId'], 
                data['amount']
            )
            return jsonify({'success': result})
    
    def setup_gambling_routes(self):
        """Setup gambling system routes"""
        
        @self.app.route('/api/gambling/slots', methods=['POST'])
        def play_slots():
            """Play slot machine"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            from flask import request
            data = request.json
            result = self.play_slots_api(data['userId'], data['bet'])
            return jsonify(result)
        
        @self.app.route('/api/gambling/coinflip', methods=['POST'])
        def play_coinflip():
            """Play coinflip game"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            from flask import request
            data = request.json
            result = self.play_coinflip_api(
                data['userId'], 
                data['amount'], 
                data.get('choice', 'heads')
            )
            return jsonify(result)
    
    def setup_clan_routes(self):
        """Setup clan management routes"""
        
        @self.app.route('/api/clans')
        def get_clans():
            """Get list of clans"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            if self.db:
                clans = list(self.db.clans.find({}, {'_id': 0}))
                return jsonify(clans)
            return jsonify(self.clans)
        
        @self.app.route('/api/clans/create', methods=['POST'])
        def create_clan():
            """Create new clan"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            from flask import request
            data = request.json
            result = self.create_clan_api(data)
            return jsonify({'success': result})
    
    def setup_user_management_routes(self):
        """Setup user management routes"""
        
        @self.app.route('/api/bans/temp', methods=['POST'])
        def temp_ban_user():
            """Temporarily ban user"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            from flask import request
            data = request.json
            result = self.temp_ban_user_api(data)
            return jsonify({'success': result})
        
        @self.app.route('/api/items/give', methods=['POST'])
        def give_item():
            """Give item to player"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            from flask import request
            data = request.json
            result = self.give_item_api(data)
            return jsonify({'success': result})
    
    def setup_misc_routes(self):
        """Setup miscellaneous routes"""
        
        @self.app.route('/api/server/diagnostics/<server_id>')
        def get_server_diagnostics(server_id):
            """Get server diagnostics data"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            diagnostics = self.get_server_diagnostics_api(server_id)
            return jsonify(diagnostics)
        
        @self.app.route('/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected' if self.db else 'demo_mode',
                'koth_system': 'vanilla_compatible',
                'websockets_available': WEBSOCKETS_AVAILABLE,
                'active_events': len(self.vanilla_koth.get_active_events()),
                'live_connections': len(self.live_connections) if self.live_connections else 0,
                'features': {
                    'console_commands': True,
                    'event_management': True,
                    'koth_events_fixed': True,
                    'economy_system': True,
                    'clan_management': True,
                    'gambling_games': True,
                    'server_diagnostics': True,
                    'live_console': WEBSOCKETS_AVAILABLE
                }
            })
    
    def send_console_command_graphql(self, command, sid, region):
        """Send console command via GraphQL with rate limiting"""
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
                            'type': 'command'
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
    
    # Economy API methods (placeholder implementations)
    def transfer_coins_api(self, from_user, to_user, amount):
        """Transfer coins between users (placeholder)"""
        return True
    
    def play_slots_api(self, user_id, bet_amount):
        """Play slot machine (placeholder)"""
        return {'success': True, 'result': ['🍒', '🍒', '🍒'], 'winnings': bet_amount * 3}
    
    def play_coinflip_api(self, user_id, bet_amount, choice):
        """Play coinflip game (placeholder)"""
        return {'success': True, 'result': 'heads', 'won': True}
    
    def create_clan_api(self, clan_data):
        """Create new clan (placeholder)"""
        return True
    
    def temp_ban_user_api(self, ban_data):
        """Temporarily ban user (placeholder)"""
        return True
    
    def give_item_api(self, item_data):
        """Give item to player (placeholder)"""
        return True
    
    def get_server_diagnostics_api(self, server_id):
        """Get server diagnostics data (placeholder)"""
        return {
            'serverId': server_id,
            'status': 'online',
            'playerCount': 25,
            'maxPlayers': 100,
            'cpu': 45,
            'memory': 60,
            'uptime': 12345,
            'fps': 65,
            'lastUpdate': datetime.now().isoformat(),
            'koth_system': 'vanilla_compatible',
            'live_console': WEBSOCKETS_AVAILABLE
        }
    
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
                    start_time = datetime.fromisoformat(event['startTime'])
                    duration = event.get('duration', 60)
                    if (current_time - start_time).total_seconds() > duration * 60:
                        event['status'] = 'completed'
    
    def create_html_templates(self):
        """Create HTML templates for the web interface"""
        # Template creation would go here - simplified for space
        # In practice, you'd create the templates as separate files
        pass
    
    def run(self, host=None, port=None, debug=False):
        """Run the enhanced application with live console"""
        host = host or Config.DEFAULT_HOST
        port = port or Config.DEFAULT_PORT
        
        # Create templates (placeholder)
        self.create_html_templates()
        
        try:
            self.app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
        except KeyboardInterrupt:
            logger.info("\n👋 GUST Enhanced stopped by user")
            # Clean up WebSocket connections
            if self.websocket_manager:
                self.websocket_manager.stop()
        except Exception as e:
            logger.error(f"\n❌ Error: {e}")









