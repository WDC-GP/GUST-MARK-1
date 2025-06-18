#!/usr/bin/env python3
"""
Debug app.py to find where user_storage becomes None
====================================================
Adds extensive debugging to track the user_storage issue
"""

import os
import shutil
from datetime import datetime

def create_debug_app():
    """Create debug version of app.py with extensive logging"""
    
    print("🔍 Creating debug version of app.py...")
    
    # Create backup
    if os.path.exists("app.py"):
        backup_file = f"app_backup_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy2("app.py", backup_file)
        print(f"✅ Created backup: {backup_file}")
    
    debug_content = '''"""
GUST Bot Enhanced - DEBUG VERSION
=================================
Debug version with extensive user_storage tracking
"""

import os
import json
import time
import threading
import schedule
import secrets
from datetime import datetime, timedelta
from collections import deque
from flask import Flask, render_template, session, redirect, url_for, jsonify
import logging

# Debug function to track user_storage
def debug_user_storage(location, user_storage_obj):
    """Debug function to track user_storage state"""
    print(f"🔍 DEBUG [{location}]: user_storage = {type(user_storage_obj)} | Is None: {user_storage_obj is None}")
    if user_storage_obj is not None:
        has_register = hasattr(user_storage_obj, 'register')
        print(f"🔍 DEBUG [{location}]: Has register method: {has_register}")
    return user_storage_obj

# Import configuration and utilities
from config import Config, WEBSOCKETS_AVAILABLE, MONGODB_AVAILABLE, ensure_directories, ensure_data_files
from utils.rate_limiter import RateLimiter
from utils.helpers import load_token, format_command, validate_server_id, validate_region

# Import systems
from systems.koth import VanillaKothSystem

# Import route blueprints
from routes.auth import auth_bp

print("🔍 DEBUG: Importing route modules...")
try:
    from routes.servers import init_servers_routes
    print("✅ Imported servers routes")
except Exception as e:
    print(f"❌ Error importing servers: {e}")

try:
    from routes.events import init_events_routes
    print("✅ Imported events routes")
except Exception as e:
    print(f"❌ Error importing events: {e}")

try:
    from routes.economy import init_economy_routes
    print("✅ Imported economy routes")
except Exception as e:
    print(f"❌ Error importing economy: {e}")

try:
    from routes.gambling import init_gambling_routes
    print("✅ Imported gambling routes")
except Exception as e:
    print(f"❌ Error importing gambling: {e}")

try:
    from routes.clans import init_clans_routes
    print("✅ Imported clans routes")
except Exception as e:
    print(f"❌ Error importing clans: {e}")

try:
    from routes.users import init_users_routes
    print("✅ Imported users routes")
except Exception as e:
    print(f"❌ Error importing users: {e}")

try:
    from routes.user_database import init_user_database_routes
    print("✅ Imported user_database routes")
except Exception as e:
    print(f"❌ Error importing user_database: {e}")

try:
    from routes.logs import init_logs_routes
    print("✅ Imported logs routes")
except Exception as e:
    print(f"❌ Error importing logs: {e}")

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
        print(f"🔍 DEBUG: register() called with user_id={user_id}, nickname={nickname}")
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
            'registered_at': datetime.now().isoformat()
        }
        
        print(f'[INFO] User registered: {nickname} ({user_id})')
        return {'success': True, 'message': f'User {nickname} registered successfully'}

class GustBotEnhanced:
    """Main GUST Bot Enhanced application class"""
    
    def __init__(self):
        """Initialize the enhanced GUST bot application"""
        print("🔍 DEBUG: Starting GustBotEnhanced.__init__()")
        
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
        
        print("🔍 DEBUG: About to call init_database()")
        # Database connection (optional)
        self.init_database()
        debug_user_storage("After init_database", self.user_storage)
        
        print("🔍 DEBUG: About to initialize VanillaKothSystem")
        # Initialize systems
        self.vanilla_koth = VanillaKothSystem(self)
        debug_user_storage("After VanillaKothSystem", self.user_storage)
        
        print("🔍 DEBUG: About to initialize WebSocket manager")
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
        
        print("🔍 DEBUG: About to call setup_routes()")
        debug_user_storage("Before setup_routes", self.user_storage)
        # Setup routes
        self.setup_routes()
        debug_user_storage("After setup_routes", self.user_storage)
        
        print("🔍 DEBUG: About to start background tasks")
        # Background tasks
        self.start_background_tasks()
        debug_user_storage("After start_background_tasks", self.user_storage)
        
        print("🔍 DEBUG: About to log success message")
        debug_user_storage("Before logger.info", self.user_storage)
        logger.info("🚀 GUST Bot Enhanced initialized successfully")
        debug_user_storage("After logger.info", self.user_storage)

    def init_database(self):
        """Initialize MongoDB connection with bulletproof user storage"""
        print("🔍 DEBUG: Starting init_database()")
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
        print("🔍 DEBUG: Starting setup_routes()")
        debug_user_storage("Start of setup_routes", self.user_storage)
        
        # Register authentication blueprint
        print("🔍 DEBUG: Registering auth blueprint")
        self.app.register_blueprint(auth_bp)
        debug_user_storage("After auth blueprint", self.user_storage)

        # Register other route blueprints
        print("🔍 DEBUG: Registering servers blueprint")
        try:
            servers_bp = init_servers_routes(self.app, self.db, self.servers)
            self.app.register_blueprint(servers_bp)
            debug_user_storage("After servers blueprint", self.user_storage)
        except Exception as e:
            print(f"❌ Error with servers blueprint: {e}")

        print("🔍 DEBUG: Registering events blueprint")
        try:
            events_bp = init_events_routes(self.app, self.db, self.events, self.vanilla_koth, self.console_output)
            self.app.register_blueprint(events_bp)
            debug_user_storage("After events blueprint", self.user_storage)
        except Exception as e:
            print(f"❌ Error with events blueprint: {e}")

        print("🔍 DEBUG: Registering economy blueprint")
        try:
            economy_bp = init_economy_routes(self.app, self.db, self.economy)
            self.app.register_blueprint(economy_bp)
            debug_user_storage("After economy blueprint", self.user_storage)
        except Exception as e:
            print(f"❌ Error with economy blueprint: {e}")

        print("🔍 DEBUG: Registering gambling blueprint")
        try:
            gambling_bp = init_gambling_routes(self.app, self.db, self.gambling)
            self.app.register_blueprint(gambling_bp)
            debug_user_storage("After gambling blueprint", self.user_storage)
        except Exception as e:
            print(f"❌ Error with gambling blueprint: {e}")

        print("🔍 DEBUG: Registering clans blueprint")
        try:
            clans_bp = init_clans_routes(self.app, self.db, self.clans, self.user_storage)
            self.app.register_blueprint(clans_bp)
            debug_user_storage("After clans blueprint", self.user_storage)
        except Exception as e:
            print(f"❌ Error with clans blueprint: {e}")

        print("🔍 DEBUG: Registering users blueprint")
        try:
            users_bp = init_users_routes(self.app, self, self.db, self.console_output)
            self.app.register_blueprint(users_bp)
            debug_user_storage("After users blueprint", self.user_storage)
        except Exception as e:
            print(f"❌ Error with users blueprint: {e}")

        print("🔍 DEBUG: Registering user_database blueprint")
        try:
            user_database_bp = init_user_database_routes(self.app, self.db, self.user_storage)
            self.app.register_blueprint(user_database_bp)
            debug_user_storage("After user_database blueprint", self.user_storage)
        except Exception as e:
            print(f"❌ Error with user_database blueprint: {e}")
        
        print("🔍 DEBUG: Registering logs blueprint")
        try:
            logs_bp = init_logs_routes(self.app, self.db, self.logs)
            self.app.register_blueprint(logs_bp)
            debug_user_storage("After logs blueprint", self.user_storage)
        except Exception as e:
            print(f"❌ Error with logs blueprint: {e}")
        
        print("🔍 DEBUG: Setting up main route")
        # Setup main routes
        @self.app.route('/')
        def index():
            if 'logged_in' not in session:
                return redirect(url_for('auth.login'))
            return render_template('enhanced_dashboard.html')
        
        debug_user_storage("After main route", self.user_storage)
        
        # Skip other route setups for now to isolate the issue
        print("🔍 DEBUG: Completed setup_routes()")

    def run(self, host=None, port=None, debug=False):
        """Run the enhanced application"""
        print("🔍 DEBUG: Starting run method")
        debug_user_storage("Start of run method", self.user_storage)
        
        host = host or Config.DEFAULT_HOST
        port = port or Config.DEFAULT_PORT
        
        try:
            self.app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
        except KeyboardInterrupt:
            logger.info("\\n👋 GUST Enhanced stopped by user")
            if self.websocket_manager:
                self.websocket_manager.stop()
        except Exception as e:
            print(f"🔍 DEBUG: Exception in run method: {e}")
            debug_user_storage("During exception in run", self.user_storage)
            logger.error(f"\\n❌ Error: {e}")

    def start_background_tasks(self):
        """Start background tasks"""
        print("🔍 DEBUG: Starting background tasks")
        debug_user_storage("Start of background tasks", self.user_storage)
        
        def run_scheduled():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        schedule.every(5).minutes.do(self.cleanup_expired_events)
        
        thread = threading.Thread(target=run_scheduled, daemon=True)
        thread.start()
        
        logger.info("📅 Background tasks started")
        debug_user_storage("End of background tasks", self.user_storage)
    
    def cleanup_expired_events(self):
        """Clean up expired events"""
        pass  # Simplified for debugging
'''
    
    # Write the debug app
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(debug_content)
    
    print("✅ Debug app.py created!")
    print("🔄 Now run: python main.py")
    print("   This will show exactly where user_storage becomes None")

if __name__ == "__main__":
    create_debug_app()
