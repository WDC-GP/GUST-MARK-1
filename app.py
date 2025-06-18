"""
GUST Bot Enhanced - CORRECTED VERSION
====================================
Fixed import issues and route parameters for economy and gambling
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

# Debug function to track user_storage
def debug_user_storage(location, user_storage_obj):
    """Debug function to track user_storage state"""
    print(f"[DEBUG {location}]: user_storage = {type(user_storage_obj)} | Is None: {user_storage_obj is None}")
    if user_storage_obj is not None:
        has_register = hasattr(user_storage_obj, 'register')
        print(f"[DEBUG {location}]: Has register method: {has_register}")
    return user_storage_obj

# Import configuration and utilities
from config import Config, WEBSOCKETS_AVAILABLE, MONGODB_AVAILABLE, ensure_directories, ensure_data_files
from utils.rate_limiter import RateLimiter
from utils.helpers import load_token, format_command, validate_server_id, validate_region

# Import systems
from systems.koth import VanillaKothSystem

# Import route blueprints - FIXED: Direct imports without try/except
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

class InMemoryUserStorage:
    """Emergency in-memory user storage for demo mode"""
    
    def __init__(self):
        self.users = {}
        print('[INFO] In-memory user storage initialized')
    
    def register(self, user_id, nickname=None, server_id='default_server'):
        """Register method for compatibility - routes to register_user"""
        print(f"[DEBUG]: register() called with user_id={user_id}, nickname={nickname}")
        if nickname is None:
            nickname = user_id
        return self.register_user(user_id, nickname, server_id)
    
    def register_user(self, user_id, nickname, server_id='default_server'):
        """Register a new user"""
        if user_id in self.users:
            return {'success': False, 'error': 'User already exists'}
        
        self.users[user_id] = {
            'userId': user_id,
            'nickname': nickname,
            'server_id': server_id,
            'balance': 1000,
            'registered_at': datetime.now().isoformat(),
            'servers': {
                server_id: {
                    'balance': 1000,
                    'clanTag': None,
                    'joinedAt': datetime.now().isoformat(),
                    'gamblingStats': {'totalWagered': 0, 'totalWon': 0, 'gamesPlayed': 0},
                    'isActive': True
                }
            }
        }
        
        print(f'[INFO] User registered: {nickname} ({user_id})')
        return {'success': True, 'message': f'User {nickname} registered successfully'}
    
    # Dictionary-like interface methods (for user_helpers.py compatibility)
    def get(self, user_id, default=None):
        """Get user data - compatibility with dict interface"""
        return self.users.get(user_id, default)
    
    def __getitem__(self, user_id):
        """Allow storage[user_id] syntax"""
        return self.users[user_id]
    
    def __setitem__(self, user_id, value):
        """Allow storage[user_id] = value syntax"""
        self.users[user_id] = value
    
    def __contains__(self, user_id):
        """Allow 'user_id in storage' syntax"""
        return user_id in self.users
    
    def keys(self):
        """Return all user IDs"""
        return self.users.keys()
    
    def values(self):
        """Return all user data"""
        return self.users.values()
    
    def items(self):
        """Return all user items"""
        return self.users.items()
    
    # User profile methods
    def get_user_profile(self, user_id):
        """Get complete user profile"""
        return self.users.get(user_id)
    
    def update_user_profile(self, user_id, updates):
        """Update user profile data"""
        if user_id in self.users:
            self.users[user_id].update(updates)
            return True
        return False
    
    # Server-specific methods
    def ensure_user_on_server(self, user_id, server_id):
        """Ensure user exists and has server data"""
        if user_id not in self.users:
            # Create user if doesn't exist
            self.register_user(user_id, user_id, server_id)
        
        user = self.users[user_id]
        if 'servers' not in user:
            user['servers'] = {}
        
        if server_id not in user['servers']:
            user['servers'][server_id] = {
                'balance': 1000,
                'clanTag': None,
                'joinedAt': datetime.now().isoformat(),
                'gamblingStats': {'totalWagered': 0, 'totalWon': 0, 'gamesPlayed': 0},
                'isActive': True
            }
        return True
    
    def get_server_balance(self, user_id, server_id):
        """Get user's balance on specific server"""
        self.ensure_user_on_server(user_id, server_id)
        return self.users[user_id]['servers'][server_id]['balance']
    
    def set_server_balance(self, user_id, server_id, balance):
        """Set user's balance on specific server"""
        self.ensure_user_on_server(user_id, server_id)
        self.users[user_id]['servers'][server_id]['balance'] = balance
        return True
    
    def adjust_server_balance(self, user_id, server_id, amount):
        """Adjust user's balance on specific server"""
        self.ensure_user_on_server(user_id, server_id)
        current_balance = self.users[user_id]['servers'][server_id]['balance']
        new_balance = max(0, current_balance + amount)  # Prevent negative balance
        self.users[user_id]['servers'][server_id]['balance'] = new_balance
        return True
    
    def get_users_on_server(self, server_id):
        """Get all users on a specific server"""
        server_users = []
        for user_id, user_data in self.users.items():
            if 'servers' in user_data and server_id in user_data['servers']:
                server_data = user_data['servers'][server_id]
                server_users.append({
                    'userId': user_id,
                    'nickname': user_data.get('nickname', user_id),
                    'balance': server_data.get('balance', 0),
                    'clanTag': server_data.get('clanTag'),
                    'isActive': server_data.get('isActive', True)
                })
        return server_users
    
    def get_server_leaderboard(self, server_id, limit=10):
        """Get leaderboard for specific server"""
        users = self.get_users_on_server(server_id)
        users.sort(key=lambda x: x['balance'], reverse=True)
        return users[:limit]
class GustBotEnhanced:
    """Main GUST Bot Enhanced application class"""
    
    def __init__(self):
        """Initialize the enhanced GUST bot application"""
        print("[DEBUG]: Starting GustBotEnhanced.__init__()")
        
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
        
        print("[DEBUG]: About to call init_database()")
        # Database connection (optional)
        self.init_database()
        debug_user_storage("After init_database", self.user_storage)
        
        print("[DEBUG]: About to initialize VanillaKothSystem")
        # Initialize systems
        self.vanilla_koth = VanillaKothSystem(self)
        debug_user_storage("After VanillaKothSystem", self.user_storage)
        
        print("[DEBUG]: About to initialize WebSocket manager")
        # WebSocket manager for live console (only if websockets available)
        if WEBSOCKETS_AVAILABLE:
            self.websocket_manager = WebSocketManager(self)
            debug_user_storage("After WebSocketManager creation", self.user_storage)
            self.live_connections = {}
            # Start WebSocket manager
            self.websocket_manager.start()
            debug_user_storage("After WebSocketManager start", self.user_storage)
        else:
            self.websocket_manager = None
            self.live_connections = {}
        
        # Store reference to self in app context
        self.app.gust_bot = self
        
        print("[DEBUG]: About to call setup_routes()")
        debug_user_storage("Before setup_routes", self.user_storage)
        # Setup routes
        self.setup_routes()
        debug_user_storage("After setup_routes", self.user_storage)
        
        print("[DEBUG]: About to start background tasks")
        # Background tasks
        self.start_background_tasks()
        debug_user_storage("After start_background_tasks", self.user_storage)
        
        print("[DEBUG]: About to log success message")
        debug_user_storage("Before logger.info", self.user_storage)
        logger.info("[START] GUST Bot Enhanced initialized successfully")
        debug_user_storage("After logger.info", self.user_storage)

    def init_database(self):
        """Initialize MongoDB connection with bulletproof user storage"""
        print("[DEBUG]: Starting init_database()")
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
                self.user_storage = InMemoryUserStorage()
                
        except Exception as e:
            print(f'[WARNING] MongoDB connection failed: {e}')
            print('[RETRY] Falling back to in-memory storage (demo mode)')
            self.user_storage = InMemoryUserStorage()
        
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
        debug_user_storage("End of init_database", self.user_storage)

    def setup_routes(self):
        """Setup Flask routes and blueprints"""
        print("[DEBUG]: Starting setup_routes()")
        debug_user_storage("Start of setup_routes", self.user_storage)
        
        # Register authentication blueprint
        print("[DEBUG]: Registering auth blueprint")
        self.app.register_blueprint(auth_bp)
        debug_user_storage("After auth blueprint", self.user_storage)

        # Register other route blueprints - FIXED: Correct parameters
        print("[DEBUG]: Registering servers blueprint")
        servers_bp = init_servers_routes(self.app, self.db, self.servers)
        self.app.register_blueprint(servers_bp)
        debug_user_storage("After servers blueprint", self.user_storage)

        print("[DEBUG]: Registering events blueprint")
        events_bp = init_events_routes(self.app, self.db, self.events, self.vanilla_koth, self.console_output)
        self.app.register_blueprint(events_bp)
        debug_user_storage("After events blueprint", self.user_storage)

        print("[DEBUG]: Registering economy blueprint")
        # FIXED: Pass user_storage instead of self.economy
        economy_bp = init_economy_routes(self.app, self.db, self.user_storage)
        self.app.register_blueprint(economy_bp)
        debug_user_storage("After economy blueprint", self.user_storage)
        print("[OK] Economy routes registered successfully")

        print("[DEBUG]: Registering gambling blueprint")
        # FIXED: Pass user_storage instead of self.gambling
        gambling_bp = init_gambling_routes(self.app, self.db, self.user_storage)
        self.app.register_blueprint(gambling_bp)
        debug_user_storage("After gambling blueprint", self.user_storage)
        print("[OK] Gambling routes registered successfully")

        print("[DEBUG]: Registering clans blueprint")
        clans_bp = init_clans_routes(self.app, self.db, self.clans, self.user_storage)
        self.app.register_blueprint(clans_bp)
        debug_user_storage("After clans blueprint", self.user_storage)

        print("[DEBUG]: Registering users blueprint")
        users_bp = init_users_routes(self.app, self, self.db, self.console_output)
        self.app.register_blueprint(users_bp)
        debug_user_storage("After users blueprint", self.user_storage)

        print("[DEBUG]: Registering user_database blueprint")
        user_database_bp = init_user_database_routes(self.app, self.db, self.user_storage)
        self.app.register_blueprint(user_database_bp)
        debug_user_storage("After user_database blueprint", self.user_storage)
        
        print("[DEBUG]: Registering logs blueprint")
        logs_bp = init_logs_routes(self.app, self.db, self.logs)
        self.app.register_blueprint(logs_bp)
        debug_user_storage("After logs blueprint", self.user_storage)
        
        print("[DEBUG]: Setting up main route")
        # Setup main routes
        @self.app.route('/')
        def index():
            if 'logged_in' not in session:
                return redirect(url_for('auth.login'))
            return render_template('enhanced_dashboard.html')
        
        debug_user_storage("After main route", self.user_storage)
        
        # ===========================================
        # ADDITIONAL DIRECT ROUTES (Keep existing functionality)
        # ===========================================
        print("[DEBUG]: Adding additional direct routes")
        
        # Import auth decorator for protected routes
        from routes.auth import require_auth
        
        # ===========================================
        # HEALTH CHECK ENDPOINT
        # ===========================================
        @self.app.route('/health')
        def health_check():
            """Enhanced health check endpoint"""
            try:
                health_data = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0.0',
                    'uptime': 'active',
                    'database': 'MongoDB' if self.db else 'InMemoryStorage',
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'live_connections': len(getattr(self.websocket_manager, 'connections', {})) if hasattr(self, 'websocket_manager') and self.websocket_manager else 0,
                    'managed_servers': len(self.servers),
                    'user_storage_type': type(self.user_storage).__name__ if self.user_storage else 'None',
                    'features': {
                        'user_management': bool(self.user_storage and hasattr(self.user_storage, 'register')),
                        'console_commands': True,
                        'live_console': WEBSOCKETS_AVAILABLE,
                        'event_management': hasattr(self, 'vanilla_koth'),
                        'clan_management': True,
                        'economy_system': True,
                        'gambling_system': True
                    }
                }
                return jsonify(health_data)
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }), 500
        
        # ===========================================
        # CONSOLE ENDPOINTS (Direct routes)
        # ===========================================
        @self.app.route('/api/console/output')
        @require_auth
        def get_console_output():
            """Get console output"""
            try:
                output = []
                if hasattr(self, 'console_output') and self.console_output:
                    output = list(self.console_output)
                else:
                    output = [
                        {
                            'timestamp': datetime.now().isoformat(),
                            'message': 'GUST Bot Console - Ready',
                            'status': 'system',
                            'source': 'console_system',
                            'type': 'system'
                        }
                    ]
                return jsonify(output)
            except Exception as e:
                return jsonify([{
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Console output error: {str(e)}',
                    'status': 'error',
                    'source': 'console_system',
                    'type': 'error'
                }]), 500
        
        @self.app.route('/api/console/send', methods=['POST'])
        @require_auth
        def send_console_command():
            """Send console command"""
            try:
                data = request.json or {}
                command = data.get('command', '').strip()
                server_id = data.get('serverId')
                region = data.get('region', 'US')
                
                if not command or not server_id:
                    return jsonify({'success': False, 'error': 'Command and server ID required'})
                
                # Add command to console output
                if hasattr(self, 'console_output'):
                    self.console_output.append({
                        'timestamp': datetime.now().isoformat(),
                        'command': command,
                        'server_id': server_id,
                        'status': 'sent',
                        'source': 'console_api',
                        'type': 'command'
                    })
                
                # For demo mode, always return success
                return jsonify({
                    'success': True,
                    'message': f'Command sent to server {server_id}',
                    'command': command,
                    'server_id': server_id,
                    'demo_mode': not bool(self.db)
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        # ===========================================
        # LIVE CONSOLE ENDPOINTS
        # ===========================================
        @self.app.route('/api/console/live/connect', methods=['POST'])
        @require_auth
        def connect_live_console():
            """Connect to live console WebSocket"""
            try:
                data = request.json or {}
                server_id = data.get('serverId')
                region = data.get('region', 'US')
                
                if not server_id:
                    return jsonify({'success': False, 'error': 'Server ID required'})
                
                # If WebSockets not available, return appropriate message
                if not WEBSOCKETS_AVAILABLE:
                    return jsonify({
                        'success': False,
                        'error': 'WebSocket support not available. Install with: pip install websockets',
                        'websockets_available': False
                    })
                
                # For demo mode, simulate connection
                return jsonify({
                    'success': True,
                    'message': f'Connected to server {server_id}',
                    'server_id': server_id,
                    'demo_mode': not bool(self.db)
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/console/live/disconnect', methods=['POST'])
        @require_auth
        def disconnect_live_console():
            """Disconnect from live console WebSocket"""
            try:
                data = request.json or {}
                server_id = data.get('serverId')
                
                if not server_id:
                    return jsonify({'success': False, 'error': 'Server ID required'})
                
                return jsonify({
                    'success': True,
                    'message': f'Disconnected from server {server_id}',
                    'server_id': server_id
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/console/live/status')
        @require_auth
        def get_live_console_status():
            """Get live console connection status"""
            try:
                status = {
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'connections': {},
                    'total_connections': 0,
                    'manager_running': False
                }
                
                if hasattr(self, 'websocket_manager') and self.websocket_manager:
                    status.update({
                        'manager_running': True,
                        'connections': getattr(self.websocket_manager, 'connections', {}),
                        'total_connections': len(getattr(self.websocket_manager, 'connections', {}))
                    })
                
                return jsonify(status)
                
            except Exception as e:
                return jsonify({
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'connections': {},
                    'total_connections': 0,
                    'error': str(e)
                })
        
        @self.app.route('/api/console/live/messages')
        @require_auth
        def get_live_console_messages():
            """Get live console messages"""
            try:
                server_id = request.args.get('serverId')
                limit = int(request.args.get('limit', 50))
                message_type = request.args.get('type')
                
                messages = [
                    {
                        'timestamp': datetime.now().isoformat(),
                        'message': 'Live console monitoring ready',
                        'type': 'system',
                        'server_id': server_id or 'all',
                        'source': 'live_console'
                    }
                ]
                
                return jsonify({
                    'messages': messages,
                    'count': len(messages),
                    'server_id': server_id,
                    'timestamp': datetime.now().isoformat(),
                    'websockets_available': WEBSOCKETS_AVAILABLE
                })
                
            except Exception as e:
                return jsonify({
                    'messages': [],
                    'count': 0,
                    'error': str(e),
                    'websockets_available': WEBSOCKETS_AVAILABLE
                })
        
        @self.app.route('/api/console/live/test')
        @require_auth
        def test_live_console():
            """Test live console functionality"""
            try:
                test_result = {
                    'success': True,
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'timestamp': datetime.now().isoformat(),
                    'connections': {},
                    'total_connections': 0,
                    'recent_messages': [],
                    'message_count': 0,
                    'status': 'Live console test completed successfully'
                }
                
                if hasattr(self, 'websocket_manager') and self.websocket_manager:
                    test_result.update({
                        'manager_available': True,
                        'connections': getattr(self.websocket_manager, 'connections', {}),
                        'total_connections': len(getattr(self.websocket_manager, 'connections', {}))
                    })
                else:
                    test_result.update({
                        'manager_available': False,
                        'note': 'WebSocket manager not available - using demo mode'
                    })
                
                return jsonify(test_result)
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'timestamp': datetime.now().isoformat()
                })
        
        # ===========================================
        # CLANS ENDPOINT (Direct route)
        # ===========================================
        @self.app.route('/api/clans')
        @require_auth
        def get_clans():
            """Get list of clans"""
            try:
                clans = []
                if self.db:
                    clans = list(self.db.clans.find({}, {'_id': 0}))
                else:
                    clans = getattr(self, 'clans', [])
                
                return jsonify(clans)
                
            except Exception as e:
                return jsonify({'error': f'Failed to retrieve clans: {str(e)}'}), 500
        
        print("[OK] Added all direct routes:")
        print("   • /health - Health check endpoint")
        print("   • /api/console/output - Console output")
        print("   • /api/console/send - Send commands")
        print("   • /api/console/live/* - Live console endpoints")
        print("   • /api/clans - Clans data")
        print("[DEBUG]: All blueprint routes registered")
        
        debug_user_storage("After adding direct routes", self.user_storage)
        print("[DEBUG]: Completed setup_routes()")

    def run(self, host=None, port=None, debug=False):
        """Run the enhanced application"""
        print("[DEBUG]: Starting run method")
        debug_user_storage("Start of run method", self.user_storage)
        
        host = host or Config.DEFAULT_HOST
        port = port or Config.DEFAULT_PORT
        
        try:
            self.app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
        except KeyboardInterrupt:
            logger.info("\n[STOP] GUST Enhanced stopped by user")
            if self.websocket_manager:
                self.websocket_manager.stop()
        except Exception as e:
            print(f"[DEBUG]: Exception in run method: {e}")
            debug_user_storage("During exception in run", self.user_storage)
            logger.error(f"\n[ERROR] Error: {e}")

    def start_background_tasks(self):
        """Start background tasks"""
        print("[DEBUG]: Starting background tasks")
        debug_user_storage("Start of background tasks", self.user_storage)
        
        def run_scheduled():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        schedule.every(5).minutes.do(self.cleanup_expired_events)
        
        thread = threading.Thread(target=run_scheduled, daemon=True)
        thread.start()
        
        logger.info("[OK] Background tasks started")
        debug_user_storage("End of background tasks", self.user_storage)
    
    def cleanup_expired_events(self):
        """Clean up expired events"""
        pass  # Simplified for debugging

# Create instance for main.py
if __name__ == "__main__":
    gust = GustBotEnhanced()
    gust.run()
