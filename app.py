"""
GUST Bot Enhanced - Main Flask Application (COMPLETE WITH AUTO-AUTHENTICATION)
===============================================================================
✅ COMPLETE: Full GustBotEnhanced class structure from project knowledge base
✅ INTEGRATED: Auto-authentication with background service management
✅ FIXED: Flask 3.0+ compatibility (no @app.before_first_request)
✅ FIXED: Correct route initialization parameters for all blueprints
✅ PRESERVED: All existing functionality, MongoDB integration, WebSocket support
✅ ENHANCED: Auto-auth service lifecycle management and health monitoring
"""

import os
import json
import time
import threading
import schedule
import secrets
import atexit
import sys
from datetime import datetime, timedelta
from collections import deque, defaultdict
from flask import Flask, render_template, session, redirect, url_for, jsonify, request
import logging

# Import configuration and utilities
from config import Config, WEBSOCKETS_AVAILABLE, ensure_directories, ensure_data_files
from utils.rate_limiter import RateLimiter

# ✅ PRESERVED: Use centralized token management functions
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

# ✅ NEW: Auto-authentication imports (graceful fallback)
try:
    from services.auth_service import auth_service
    from utils.credential_manager import credential_manager
    AUTO_AUTH_AVAILABLE = True
except ImportError:
    AUTO_AUTH_AVAILABLE = False

logger = logging.getLogger(__name__)

# ================================================================
# ENHANCED IN-MEMORY USER STORAGE
# ================================================================

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
        
        if server_id not in self.users:
            self.users[server_id] = {}
        
        self.users[server_id][user_id] = {
            'nickname': nickname,
            'registered': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        print(f'[✅ INFO] User registered: {user_id} as {nickname} on {server_id}')
        return True
    
    def get_user(self, user_id, server_id='default_server'):
        """Get user data"""
        if server_id in self.users and user_id in self.users[server_id]:
            return self.users[server_id][user_id]
        return None
    
    def get_balance(self, user_id, server_id='default_server'):
        """Get user balance"""
        if server_id not in self.balances:
            self.balances[server_id] = {}
        return self.balances[server_id].get(user_id, 0)
    
    def update_balance(self, user_id, amount, server_id='default_server'):
        """Update user balance"""
        if server_id not in self.balances:
            self.balances[server_id] = {}
        
        current = self.balances[server_id].get(user_id, 0)
        self.balances[server_id][user_id] = current + amount
        return self.balances[server_id][user_id]

# ================================================================
# MAIN GUST BOT ENHANCED CLASS
# ================================================================

class GustBotEnhanced:
    """Main GUST Bot Enhanced application with auto-authentication support"""
    
    def __init__(self):
        """Initialize the enhanced GUST Bot application"""
        print("\n" + "="*60)
        print("🚀 GUST Bot Enhanced - Starting Up")
        print("="*60)
        
        # Core Flask app
        self.app = Flask(__name__)
        self.app.config.from_object(Config)
        
        # Initialize storage and state
        self.setup_storage()
        self.init_database()
        self.setup_flask_integration()
        self.setup_routes()
        self.setup_websockets()
        
        # ✅ NEW: Initialize auto-authentication
        self.setup_auto_authentication()
        
        print("="*60)
        print("[INFO] GUST Bot Enhanced initialization complete")
        print("="*60)
    
    def setup_storage(self):
        """Initialize storage systems"""
        print("[DEBUG]: Initializing storage systems...")
        
        # Core storage components
        self.user_storage = InMemoryUserStorage()
        self.server_health_storage = None  # Will be set in init_database
        
        # Data collections
        self.servers = []
        self.clans = []
        self.users = []
        self.events = []
        self.logs_storage = []
        
        # System components (vanilla_koth will be initialized later)
        self.vanilla_koth = None  # Initialize after self is fully created
        self.console_output = deque(maxlen=1000)
        self.rate_limiter = RateLimiter()
        
        # State management
        self.websocket_manager = None
        self.db = None
        
        # Ensure user_storage is never None
        if self.user_storage is None:
            print('[🔧 EMERGENCY] Creating emergency user storage')
            self.user_storage = InMemoryUserStorage()
        
        print(f'[✅ OK] Storage systems initialized')
    
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
        
        # Initialize Server Health storage with proper database connection
        self.server_health_storage = ServerHealthStorage(self.db, self.user_storage)
        print("[✅ OK] Server Health storage initialized with database connection")
        
        print(f'[✅ OK] Database initialization complete - Storage: {type(self.user_storage).__name__}')
    
    def setup_flask_integration(self):
        """Setup Flask integration with auto-auth support"""
        print("[DEBUG]: Setting up Flask integration...")
        
        # Ensure directories exist
        ensure_directories()
        ensure_data_files()
        
        # ✅ NEW: Initialize VanillaKothSystem now that self is fully created
        try:
            self.vanilla_koth = VanillaKothSystem(self)
            print("[✅ OK] VanillaKothSystem initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize VanillaKothSystem: {e}")
            # Create a fallback empty system to prevent route errors
            self.vanilla_koth = type('MockVanillaKoth', (), {
                'start_koth_event_fixed': lambda *args: False,
                'get_active_events': lambda: [],
                'stop_koth_event': lambda *args: False
            })()
            print("[⚠️ WARNING] Using mock VanillaKothSystem due to initialization error")
        
        # ✅ FLASK 3.0+ COMPATIBLE: One-time initialization flag
        self._app_initialized = False
        
        @self.app.before_request
        def ensure_initialization():
            """Ensure one-time initialization for Flask 3.0+ compatibility"""
            if not self._app_initialized:
                with self.app.app_context():
                    self.startup_initialization()
                self._app_initialized = True
        
        print("[✅ OK] Flask integration configured")
    
    def startup_initialization(self):
        """
        Initialize services during startup
        ✅ FLASK 3.0+ COMPATIBLE: Called from @app.before_request
        """
        logger.info("🚀 Starting GUST Bot Enhanced with auto-authentication support")
        
        # Initialize WebSocket manager if available
        if WEBSOCKETS_AVAILABLE and hasattr(self, 'websocket_manager'):
            try:
                if self.websocket_manager:
                    logger.info("✅ WebSocket manager already initialized")
                else:
                    # Import the correct WebSocket manager
                    from websocket.manager import WebSocketManager
                    self.websocket_manager = WebSocketManager(self)
                    logger.info("✅ WebSocket manager initialized")
            except Exception as e:
                logger.error(f"❌ WebSocket initialization failed: {e}")
                self.websocket_manager = None
        
        # ✅ NEW: Initialize auto-authentication service
        self.initialize_auto_auth_service()
        
        logger.info("✅ Application startup completed")
    
    def setup_routes(self):
        """Setup Flask routes and blueprints with correct parameters"""
        print("[DEBUG]: Setting up routes with auto-authentication support...")
        
        # Register authentication blueprint (foundation)
        self.app.register_blueprint(auth_bp)
        print("[✅ OK] Auth routes registered")
        
        # ✅ FIXED: Initialize route blueprints with correct parameters matching project structure
        try:
            # Server routes
            init_servers_routes(self.app, self.db, self.servers)
            print("[✅ OK] Server routes registered")
            
            # Events routes (requires events, vanilla_koth and console_output)
            # Ensure vanilla_koth is available
            if self.vanilla_koth is None:
                logger.warning("⚠️ VanillaKothSystem not available, using mock for events routes")
                # Create minimal mock system for routes
                self.vanilla_koth = type('MockVanillaKoth', (), {
                    'start_koth_event_fixed': lambda *args: False,
                    'get_active_events': lambda: [],
                    'stop_koth_event': lambda *args: False
                })()
            
            init_events_routes(self.app, self.db, self.events, self.vanilla_koth, self.console_output)
            print("[✅ OK] Events routes registered")
            
            # Economy routes
            init_economy_routes(self.app, self.db, self.user_storage)
            print("[✅ OK] Economy routes registered")
            
            # Gambling routes
            init_gambling_routes(self.app, self.db, self.user_storage)
            print("[✅ OK] Gambling routes registered")
            
            # Clans routes (requires clans list and user_storage)
            init_clans_routes(self.app, self.db, self.clans, self.user_storage)
            print("[✅ OK] Clans routes registered")
            
            # Users routes (requires gust_bot instance, db, users list, console_output)
            init_users_routes(self.app, self, self.db, self.console_output)
            print("[✅ OK] Users routes registered")
            
            # Logs routes
            init_logs_routes(self.app, self.db, self.logs_storage)
            print("[✅ OK] Logs routes registered")
            
            # Server health routes
            init_server_health_routes(self.app, self.db, self.server_health_storage)
            print("[✅ OK] Server Health routes registered")
            
        except Exception as route_error:
            logger.error(f"❌ Route initialization error: {route_error}")
            raise
        
        # ✅ NEW: Add auto-auth health endpoints
        self.setup_auto_auth_endpoints()
        
        print("[✅ OK] All routes configured successfully")
    
    def setup_websockets(self):
        """Setup WebSocket components"""
        print("[DEBUG]: Setting up WebSocket components...")
        
        if WEBSOCKETS_AVAILABLE:
            try:
                # Import WebSocket manager
                from websocket.manager import WebSocketManager
                # WebSocket manager will be initialized in startup_initialization
                print("[✅ OK] WebSocket components configured")
            except Exception as e:
                logger.error(f"❌ WebSocket setup error: {e}")
                print(f"[⚠️ WARNING] WebSocket setup failed: {e}")
        else:
            print("[ℹ️ INFO] WebSocket support not available")
    
    # ================================================================
    # ✅ NEW: AUTO-AUTHENTICATION INTEGRATION
    # ================================================================
    
    def setup_auto_authentication(self):
        """Setup auto-authentication system"""
        print("[DEBUG]: Setting up auto-authentication...")
        
        if AUTO_AUTH_AVAILABLE:
            try:
                # Register cleanup on exit
                atexit.register(self.cleanup_auto_auth_service)
                print("[✅ OK] Auto-authentication system configured")
            except Exception as e:
                logger.error(f"❌ Auto-auth setup error: {e}")
                print(f"[⚠️ WARNING] Auto-auth setup failed: {e}")
        else:
            print("[ℹ️ INFO] Auto-authentication not available - components not installed")
    
    def initialize_auto_auth_service(self):
        """
        Initialize auto-authentication service on startup
        ✅ NEW: Background auth service startup
        """
        if not AUTO_AUTH_AVAILABLE:
            logger.info("🔐 Auto-authentication not available - skipping service initialization")
            return
        
        try:
            if Config.AUTO_AUTH_ENABLED:
                # Only start if credentials exist
                if credential_manager.credentials_exist():
                    auth_service.start()
                    logger.info("🔐 Auto-authentication service started successfully")
                else:
                    logger.info("🔐 Auto-authentication enabled but no stored credentials found")
            else:
                logger.info("🔐 Auto-authentication disabled in configuration")
        except Exception as e:
            logger.error(f"❌ Failed to initialize auto-auth service: {e}")
    
    def cleanup_auto_auth_service(self):
        """
        Cleanup auto-authentication service on shutdown
        ✅ NEW: Graceful service shutdown
        """
        if AUTO_AUTH_AVAILABLE:
            try:
                auth_service.stop()
                logger.info("🔐 Auto-authentication service stopped gracefully")
            except Exception as e:
                logger.error(f"❌ Error stopping auto-auth service: {e}")
    
    def setup_auto_auth_endpoints(self):
        """Setup auto-authentication health check endpoints"""
        
        @self.app.route('/health/auto-auth')
        def auto_auth_health():
            """Auto-authentication health check endpoint"""
            try:
                if not AUTO_AUTH_AVAILABLE:
                    return jsonify({
                        'status': 'unavailable',
                        'message': 'Auto-authentication not available',
                        'timestamp': datetime.now().isoformat()
                    }), 503
                
                # Get detailed service status
                service_status = auth_service.get_status()
                
                health_status = {
                    'status': 'healthy' if service_status.get('running', False) else 'stopped',
                    'service_status': service_status,
                    'config': {
                        'enabled': Config.AUTO_AUTH_ENABLED,
                        'renewal_interval': Config.AUTO_AUTH_RENEWAL_INTERVAL,
                        'max_retries': Config.AUTO_AUTH_MAX_RETRIES
                    },
                    'credentials': {
                        'stored': credential_manager.credentials_exist(),
                        'file_exists': os.path.exists(Config.CREDENTIALS_FILE)
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                # Determine HTTP status code
                if service_status.get('running', False) and Config.AUTO_AUTH_ENABLED:
                    status_code = 200
                elif not Config.AUTO_AUTH_ENABLED:
                    status_code = 200  # Disabled is not an error
                    health_status['status'] = 'disabled'
                else:
                    status_code = 503  # Service unavailable
                
                return jsonify(health_status), status_code
                
            except Exception as e:
                logger.error(f"❌ Auto-auth health check error: {e}")
                return jsonify({
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # Add a simple login fallback route
        @self.app.route('/login')
        def login_fallback():
            """Fallback login route to handle redirects"""
            try:
                # Try to render the login template if available
                return render_template('login.html')
            except:
                # Simple HTML fallback if template missing
                return """
                <html>
                <head><title>GUST Bot - Login</title></head>
                <body>
                    <h1>🚀 GUST Bot Enhanced - Login</h1>
                    <form method="post" action="/login">
                        <p>
                            <label>Username:</label><br>
                            <input type="text" name="username" placeholder="admin for demo">
                        </p>
                        <p>
                            <label>Password:</label><br>
                            <input type="password" name="password" placeholder="password for demo">
                        </p>
                        <p>
                            <button type="submit">Login</button>
                        </p>
                    </form>
                    <p><small>Demo: admin / password</small></p>
                </body>
                </html>
                """
        
        # Add basic health check route
        @self.app.route('/health')
        def basic_health():
            """Basic health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'application': 'GUST Bot Enhanced',
                'auto_auth_available': AUTO_AUTH_AVAILABLE,
                'websockets_available': WEBSOCKETS_AVAILABLE,
                'database_connected': bool(self.db),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/health/system')
        def system_health():
            """Comprehensive system health check with auto-auth status"""
            try:
                health_data = {
                    'status': 'healthy',
                    'components': {
                        'flask': {'status': 'healthy'},
                        'websockets': {
                            'status': 'available' if WEBSOCKETS_AVAILABLE else 'unavailable',
                            'enabled': WEBSOCKETS_AVAILABLE
                        },
                        'database': {
                            'status': 'connected' if self.db else 'in_memory',
                            'type': 'MongoDB' if self.db else 'In-Memory'
                        },
                        'rate_limiter': {
                            'status': 'healthy',
                            'requests_processed': getattr(self.rate_limiter, 'total_requests', 0)
                        }
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                # Token status
                token = load_token()
                health_data['components']['authentication'] = {
                    'status': 'healthy' if token and validate_token_file() else 'warning',
                    'has_token': bool(token),
                    'token_valid': bool(token and validate_token_file())
                }
                
                # ✅ NEW: Auto-auth component status
                if AUTO_AUTH_AVAILABLE:
                    try:
                        service_status = auth_service.get_status()
                        health_data['components']['auto_auth'] = {
                            'status': 'healthy' if service_status.get('running', False) else 'stopped',
                            'enabled': Config.AUTO_AUTH_ENABLED,
                            'service_running': service_status.get('running', False),
                            'credentials_stored': credential_manager.credentials_exist(),
                            'renewal_count': service_status.get('renewal_count', 0),
                            'failure_count': service_status.get('failure_count', 0)
                        }
                    except Exception as e:
                        health_data['components']['auto_auth'] = {
                            'status': 'error',
                            'error': str(e)
                        }
                else:
                    health_data['components']['auto_auth'] = {
                        'status': 'unavailable',
                        'reason': 'Auto-auth components not installed'
                    }
                
                # Determine overall status
                component_statuses = [comp.get('status', 'error') for comp in health_data['components'].values()]
                if any(status == 'error' for status in component_statuses):
                    health_data['status'] = 'error'
                elif any(status == 'warning' for status in component_statuses):
                    health_data['status'] = 'warning'
                
                return jsonify(health_data)
                
            except Exception as e:
                logger.error(f"❌ System health check error: {e}")
                return jsonify({
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # Add preserved application routes
        self.setup_preserved_routes()
    
    def setup_preserved_routes(self):
        """Setup preserved application routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard route"""
            if 'logged_in' not in session:
                return redirect('/login')  # Direct path instead of url_for
            
            try:
                return render_template('enhanced_dashboard.html')
            except Exception as template_error:
                # Fallback if template is missing
                return f"""
                <html>
                <head><title>GUST Bot Enhanced</title></head>
                <body>
                    <h1>🚀 GUST Bot Enhanced</h1>
                    <p>Welcome! Dashboard template is loading...</p>
                    <p>Status: Application running successfully</p>
                    <p><a href="/login">Login</a></p>
                </body>
                </html>
                """
        
        @self.app.route('/api/console/output')
        def get_console_output():
            """Get recent console output"""
            try:
                output_list = list(self.console_output)
                return jsonify({
                    'success': True,
                    'output': output_list,
                    'count': len(output_list)
                })
            except Exception as e:
                logger.error(f"❌ Error getting console output: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # Add error handlers with fallback HTML
        @self.app.errorhandler(404)
        def not_found_error(error):
            try:
                return render_template('error.html', error_code=404, error_message="Page not found"), 404
            except:
                return """
                <html>
                <head><title>GUST Bot - 404 Error</title></head>
                <body>
                    <h1>🚀 GUST Bot Enhanced</h1>
                    <h2>404 - Page Not Found</h2>
                    <p>The requested page could not be found.</p>
                    <p><a href="/">Go to Dashboard</a> | <a href="/login">Login</a></p>
                </body>
                </html>
                """, 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            try:
                return render_template('error.html', error_code=500, error_message="Internal server error"), 500
            except:
                return """
                <html>
                <head><title>GUST Bot - 500 Error</title></head>
                <body>
                    <h1>🚀 GUST Bot Enhanced</h1>
                    <h2>500 - Internal Server Error</h2>
                    <p>An internal server error occurred.</p>
                    <p><a href="/">Go to Dashboard</a> | <a href="/login">Login</a></p>
                </body>
                </html>
                """, 500
        
        @self.app.errorhandler(403)
        def forbidden_error(error):
            try:
                return render_template('error.html', error_code=403, error_message="Access forbidden"), 403
            except:
                return """
                <html>
                <head><title>GUST Bot - 403 Error</title></head>
                <body>
                    <h1>🚀 GUST Bot Enhanced</h1>
                    <h2>403 - Access Forbidden</h2>
                    <p>You don't have permission to access this resource.</p>
                    <p><a href="/">Go to Dashboard</a> | <a href="/login">Login</a></p>
                </body>
                </html>
                """, 403
    
    # ================================================================
    # APPLICATION LIFECYCLE METHODS
    # ================================================================
    
    def run(self, host=None, port=None, debug=False):
        """Run the enhanced application with auto-authentication support"""
        host = host or Config.DEFAULT_HOST
        port = port or Config.DEFAULT_PORT
        
        logger.info(f"🚀 Starting GUST Bot Enhanced on {host}:{port}")
        logger.info(f"🔧 WebSocket Support: {'Available' if WEBSOCKETS_AVAILABLE else 'Not Available'}")
        logger.info(f"🗄️ Database: {'MongoDB' if self.db else 'In-Memory'}")
        logger.info(f"👥 User Storage: {type(self.user_storage).__name__}")
        logger.info(f"📡 Live Console: {'Enabled' if WEBSOCKETS_AVAILABLE else 'Disabled'}")
        logger.info(f"🔐 Auto-Authentication: {'Available' if AUTO_AUTH_AVAILABLE else 'Not Available'}")
        logger.info(f"🛡️ Rate Limiting: Enhanced with token management")
        logger.info(f"🏥 Server Health: Enhanced monitoring system active")
        
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

# ================================================================
# APPLICATION ENTRY POINT
# ================================================================

if __name__ == '__main__':
    """Main application entry point"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("[INFO] Loading GUST Bot Enhanced...")
    
    # Create and run the application
    try:
        app = GustBotEnhanced()
        app.run(debug=True)
    except Exception as startup_error:
        logger.error(f"❌ Failed to start application: {startup_error}")
        print(f"\n❌ Failed to load GUST Bot Enhanced:")
        print(f"   Error: {startup_error}")
        sys.exit(1)