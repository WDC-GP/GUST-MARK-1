"""
GUST Bot Enhanced - Main Flask Application (FIXED WEBSOCKET SENSOR INTEGRATION)
==================================================================================
✅ FIXED: Automatic WebSocket connection establishment for sensor monitoring
✅ FIXED: Server monitoring configuration system
✅ FIXED: Enhanced error handling and connection management
✅ FIXED: Token validation and connection retry logic
✅ FIXED: Integration with sensor bridge initialization
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

# Server Health routes
from routes.server_health import init_server_health_routes

# ✅ FIXED: Import WebSocket components with proper error handling
if WEBSOCKETS_AVAILABLE:
    try:
        from websocket import EnhancedWebSocketManager, check_websocket_support, check_sensor_support
        WEBSOCKET_IMPORT_SUCCESS = True
        logger = logging.getLogger(__name__)
        logger.info("✅ WebSocket imports successful")
    except ImportError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ WebSocket import failed even though WEBSOCKETS_AVAILABLE=True: {e}")
        WEBSOCKET_IMPORT_SUCCESS = False
        EnhancedWebSocketManager = None
else:
    WEBSOCKET_IMPORT_SUCCESS = False
    EnhancedWebSocketManager = None

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
    """Main GUST Bot Enhanced application class (FIXED WEBSOCKET SENSOR INTEGRATION)"""
    
    def __init__(self):
        """Initialize the enhanced GUST bot application with WebSocket sensor support"""
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
        
        # ✅ NEW: Server monitoring configuration
        self.monitored_servers = self._load_monitored_servers_config()
        
        # Initialize user storage system FIRST
        self.init_user_storage()
        
        # Server Health storage (pre-initialization)
        self.server_health_storage = ServerHealthStorage(None, None)  # Will get proper DB later
        print("[✅ OK] Server Health storage pre-initialized")
        
        # Database connection (optional)
        self.init_database()
        
        # Initialize systems
        self.vanilla_koth = VanillaKothSystem(self)
        
        # ✅ FIXED: Enhanced WebSocket manager initialization with better error handling
        self.websocket_manager = None
        self.websocket_error = None
        
        if WEBSOCKETS_AVAILABLE and WEBSOCKET_IMPORT_SUCCESS and EnhancedWebSocketManager:
            try:
                self.websocket_manager = EnhancedWebSocketManager(self)
                self.live_connections = {}
                # Start WebSocket manager
                self.websocket_manager.start()
                logger.info("✅ Enhanced WebSocket manager initialized with sensor support")
                print("[✅ OK] Enhanced WebSocket manager started with sensor capabilities")
                
                # ✅ NEW: Auto-establish sensor connections after a brief delay
                threading.Timer(3.0, self.auto_establish_sensor_connections).start()
                
            except Exception as e:
                self.websocket_error = str(e)
                logger.error(f"❌ Enhanced WebSocket manager failed: {e}")
                self.websocket_manager = None
                self.live_connections = {}
                print(f"[❌ ERROR] WebSocket manager initialization failed: {e}")
        else:
            self.websocket_manager = None
            self.live_connections = {}
            
            # Log why WebSocket is not available
            reasons = []
            if not WEBSOCKETS_AVAILABLE:
                reasons.append("websockets package not installed")
            if not WEBSOCKET_IMPORT_SUCCESS:
                reasons.append("websocket module import failed")
            if not EnhancedWebSocketManager:
                reasons.append("EnhancedWebSocketManager class not available")
            
            reason_str = ", ".join(reasons)
            self.websocket_error = f"WebSocket unavailable: {reason_str}"
            logger.warning(f"⚠️ WebSocket support not available: {reason_str}")
            print(f"[⚠️ WARNING] WebSocket support disabled: {reason_str}")
        
        # Store reference to self in app context
        self.app.gust_bot = self
        
        # ✅ CRITICAL FIX: Store websocket_manager reference on app BEFORE route setup
        self.app.websocket_manager = self.websocket_manager
        
        logger.info(f"🔧 WebSocket manager set on app: {self.app.websocket_manager is not None}")
        print(f"[🔧 DEBUG] App websocket_manager: {self.app.websocket_manager}")
        
        # Setup routes (this will initialize sensor bridge)
        self.setup_routes()
        
        # Background tasks
        self.start_background_tasks()
        
        logger.info("🚀 GUST Bot Enhanced initialized successfully with WebSocket sensor integration")
        print("[✅ OK] GUST Bot Enhanced ready with real-time sensor monitoring")
    
    def _load_monitored_servers_config(self):
        """✅ NEW: Load monitored servers configuration"""
        try:
            # Default servers to monitor for sensor data
            default_servers = [
                {'server_id': '1736296', 'region': 'US', 'enabled': True, 'name': 'Main Rust Server'},
                # Add more servers here as needed
            ]
            
            # Try to load from config file
            config_file = 'data/monitored_servers.json'
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        loaded_servers = json.load(f)
                    logger.info(f"✅ Loaded {len(loaded_servers)} monitored servers from config")
                    return loaded_servers
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load monitored servers config: {e}")
            
            # Save default config for future use
            try:
                os.makedirs('data', exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(default_servers, f, indent=2)
                logger.info(f"✅ Created default monitored servers config")
            except Exception as e:
                logger.warning(f"⚠️ Failed to save default config: {e}")
            
            return default_servers
            
        except Exception as e:
            logger.error(f"❌ Error loading monitored servers config: {e}")
            return [{'server_id': '1736296', 'region': 'US', 'enabled': True, 'name': 'Default Server'}]
    
    def auto_establish_sensor_connections(self):
        """✅ NEW: Automatically establish WebSocket connections for sensor monitoring"""
        try:
            if not self.websocket_manager:
                logger.warning("⚠️ Cannot establish sensor connections: WebSocket manager not available")
                return
            
            logger.info("🔄 Auto-establishing sensor connections for monitored servers...")
            print("[🔄 INFO] Auto-establishing sensor connections...")
            
            # Check if we have authentication token
            token_data = None
            try:
                token_data = load_token()
            except Exception as token_error:
                logger.warning(f"⚠️ Token loading failed: {token_error}")
            
            if not token_data:
                logger.warning("⚠️ No authentication token available - sensor connections will not be established")
                print("[⚠️ WARNING] No auth token - sensor connections skipped")
                return
            
            # Extract token
            token = None
            try:
                if isinstance(token_data, dict):
                    token = token_data.get('access_token')
                elif isinstance(token_data, str):
                    token = token_data
                
                if not token or not isinstance(token, str) or token.strip() == '':
                    logger.warning("⚠️ Invalid token format - sensor connections will not be established")
                    return
                    
            except Exception as token_extract_error:
                logger.error(f"❌ Token extraction failed: {token_extract_error}")
                return
            
            # Establish connections for monitored servers
            successful_connections = 0
            failed_connections = 0
            
            for server_config in self.monitored_servers:
                if not server_config.get('enabled', True):
                    logger.debug(f"⏭️ Skipping disabled server: {server_config.get('server_id')}")
                    continue
                
                server_id = server_config.get('server_id')
                region = server_config.get('region', 'US')
                server_name = server_config.get('name', f'Server {server_id}')
                
                if not server_id:
                    logger.warning(f"⚠️ Invalid server config (missing server_id): {server_config}")
                    failed_connections += 1
                    continue
                
                try:
                    logger.info(f"🔄 Establishing sensor connection for {server_name} ({server_id})")
                    print(f"[🔄 INFO] Connecting to {server_name} ({server_id}) for sensor data...")
                    
                    # Add connection through WebSocket manager
                    future = self.websocket_manager.add_connection(server_id, region, token)
                    
                    if future:
                        logger.info(f"✅ Sensor connection queued for {server_name} ({server_id})")
                        print(f"[✅ OK] Sensor connection queued for {server_name}")
                        successful_connections += 1
                        
                        # Store in live connections for tracking
                        self.live_connections[server_id] = {
                            'region': region,
                            'connected_at': datetime.now().isoformat(),
                            'connected': True,
                            'server_name': server_name,
                            'sensor_enabled': True
                        }
                    else:
                        logger.warning(f"⚠️ Failed to queue sensor connection for {server_name} ({server_id})")
                        failed_connections += 1
                        
                except Exception as connection_error:
                    logger.error(f"❌ Failed to establish sensor connection for {server_name} ({server_id}): {connection_error}")
                    print(f"[❌ ERROR] Connection failed for {server_name}: {connection_error}")
                    failed_connections += 1
            
            # Summary
            total_servers = len([s for s in self.monitored_servers if s.get('enabled', True)])
            logger.info(f"📊 Sensor connection summary: {successful_connections}/{total_servers} successful")
            print(f"[📊 SUMMARY] Sensor connections: {successful_connections}/{total_servers} successful")
            
            if successful_connections > 0:
                print(f"[✅ SUCCESS] WebSocket sensor monitoring active for {successful_connections} servers")
                
                # Start connection health monitoring after connections are established
                threading.Timer(10.0, self.monitor_sensor_connections).start()
            else:
                print("[⚠️ WARNING] No sensor connections established - falling back to synthetic data")
                
        except Exception as e:
            logger.error(f"❌ Critical error in auto-establishing sensor connections: {e}")
            print(f"[❌ ERROR] Auto-connection setup failed: {e}")
    
    def monitor_sensor_connections(self):
        """✅ NEW: Monitor sensor connection health and attempt reconnections"""
        try:
            if not self.websocket_manager:
                return
            
            logger.debug("🔍 Monitoring sensor connection health...")
            
            # Get connection status
            connections = self.websocket_manager.get_connection_status()
            
            healthy_connections = 0
            unhealthy_connections = 0
            
            for server_id, connection_info in connections.items():
                is_connected = connection_info.get('connected', False)
                has_sensor_data = connection_info.get('has_sensor_data', False)
                sensor_data_fresh = connection_info.get('sensor_data_fresh', False)
                
                if is_connected and has_sensor_data and sensor_data_fresh:
                    healthy_connections += 1
                    logger.debug(f"✅ Healthy sensor connection: {server_id}")
                else:
                    unhealthy_connections += 1
                    logger.warning(f"⚠️ Unhealthy sensor connection: {server_id} "
                                 f"(connected={is_connected}, has_data={has_sensor_data}, fresh={sensor_data_fresh})")
            
            total_monitored = len(self.monitored_servers)
            logger.info(f"📊 Sensor health: {healthy_connections} healthy, {unhealthy_connections} unhealthy of {total_monitored} monitored")
            
            # Schedule next health check
            threading.Timer(60.0, self.monitor_sensor_connections).start()
            
        except Exception as e:
            logger.error(f"❌ Error monitoring sensor connections: {e}")
            # Retry monitoring in 2 minutes
            threading.Timer(120.0, self.monitor_sensor_connections).start()
    
    def get_monitored_servers_status(self):
        """✅ NEW: Get status of monitored servers for API endpoints"""
        try:
            servers_status = []
            
            for server_config in self.monitored_servers:
                server_id = server_config.get('server_id')
                
                # Get WebSocket connection status
                connection_status = {
                    'connected': False,
                    'has_sensor_data': False,
                    'sensor_data_fresh': False
                }
                
                if self.websocket_manager:
                    connections = self.websocket_manager.get_connection_status()
                    if server_id in connections:
                        conn_info = connections[server_id]
                        connection_status = {
                            'connected': conn_info.get('connected', False),
                            'has_sensor_data': conn_info.get('has_sensor_data', False),
                            'sensor_data_fresh': conn_info.get('sensor_data_fresh', False)
                        }
                
                servers_status.append({
                    'server_id': server_id,
                    'region': server_config.get('region', 'US'),
                    'name': server_config.get('name', f'Server {server_id}'),
                    'enabled': server_config.get('enabled', True),
                    'connection_status': connection_status,
                    'in_live_connections': server_id in self.live_connections
                })
            
            return servers_status
            
        except Exception as e:
            logger.error(f"❌ Error getting monitored servers status: {e}")
            return []
    
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
        
        # ✅ ENHANCED: Update Server Health storage with proper database connection
        self.server_health_storage = ServerHealthStorage(self.db, self.user_storage)
        print("[✅ OK] Server Health storage initialized with verified database connection")
        
        print(f'[✅ OK] Database initialization complete - Storage: {type(self.user_storage).__name__}')
    
    def setup_routes(self):
        """Setup Flask routes and blueprints (FIXED WEBSOCKET SENSOR INTEGRATION)"""
        print("[DEBUG]: Setting up routes with WebSocket sensor integration...")
        
        # Register authentication blueprint (foundation)
        self.app.register_blueprint(auth_bp)
        print("[✅ OK] Auth routes registered")

        # Register core route blueprints with CORRECT parameters
        servers_bp = init_servers_routes(self.app, self.db, self.servers)
        self.app.register_blueprint(servers_bp)
        print("[✅ OK] Server routes registered")

        events_bp = init_events_routes(self.app, self.db, self.events, self.vanilla_koth, self.console_output)
        self.app.register_blueprint(events_bp)
        print("[✅ OK] Events routes registered")

        # User-dependent route blueprints (pass user_storage)
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
        
        # ✅ FIXED: Server Health routes with WebSocket sensor integration
        try:
            print(f"[🔧 DEBUG] Initializing server health routes with app.websocket_manager: {self.app.websocket_manager is not None}")
            
            server_health_bp = init_server_health_routes(self.app, self.db, self.server_health_storage)
            self.app.register_blueprint(server_health_bp)
            print("[✅ OK] Server Health routes registered with WebSocket sensor integration")
            
            # Log WebSocket sensor status
            if self.websocket_manager:
                print("[✅ OK] WebSocket sensor bridge will be initialized by server health routes")
            else:
                print("[⚠️ WARNING] WebSocket manager not available - sensor data will use fallbacks")
                
        except Exception as health_routes_error:
            logger.error(f"❌ Server Health routes registration failed: {health_routes_error}")
            print(f"[❌ ERROR] Server Health routes failed: {health_routes_error}")
            # Continue without server health routes rather than failing completely
        
        # Setup main routes
        @self.app.route('/')
        def index():
            if 'logged_in' not in session:
                return redirect(url_for('auth.login'))
            return render_template('enhanced_dashboard.html')
        
        # ✅ NEW: Monitored servers management routes
        self.setup_monitoring_routes()
        
        # Console routes
        self.setup_console_routes()
        
        # Miscellaneous routes
        self.setup_misc_routes()
        
        print("[✅ OK] All routes registered successfully including WebSocket sensor integration")
    
    def setup_monitoring_routes(self):
        """✅ NEW: Setup monitoring and sensor management routes"""
        
        @self.app.route('/api/monitoring/servers/status')
        def get_monitoring_status():
            """Get status of all monitored servers"""
            try:
                servers_status = self.get_monitored_servers_status()
                
                return jsonify({
                    'success': True,
                    'servers': servers_status,
                    'total_servers': len(servers_status),
                    'websocket_manager_available': self.websocket_manager is not None,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error getting monitoring status: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/monitoring/servers/connect/<server_id>', methods=['POST'])
        def connect_server_monitoring(server_id):
            """Manually connect a server for monitoring"""
            try:
                if not self.websocket_manager:
                    return jsonify({
                        'success': False,
                        'error': 'WebSocket manager not available'
                    }), 503
                
                data = request.get_json() or {}
                region = data.get('region', 'US')
                
                # Get token
                token_data = load_token()
                if not token_data:
                    return jsonify({
                        'success': False,
                        'error': 'No authentication token available'
                    }), 401
                
                token = token_data.get('access_token') if isinstance(token_data, dict) else token_data
                
                # Establish connection
                future = self.websocket_manager.add_connection(server_id, region, token)
                
                if future:
                    # Add to live connections
                    self.live_connections[server_id] = {
                        'region': region,
                        'connected_at': datetime.now().isoformat(),
                        'connected': True,
                        'server_name': f'Manual Server {server_id}',
                        'sensor_enabled': True
                    }
                    
                    return jsonify({
                        'success': True,
                        'message': f'Monitoring connection established for server {server_id}',
                        'server_id': server_id,
                        'region': region
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to establish connection'
                    }), 500
                
            except Exception as e:
                logger.error(f"❌ Error connecting server monitoring: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/monitoring/servers/disconnect/<server_id>', methods=['POST'])
        def disconnect_server_monitoring(server_id):
            """Manually disconnect a server from monitoring"""
            try:
                if not self.websocket_manager:
                    return jsonify({
                        'success': False,
                        'error': 'WebSocket manager not available'
                    }), 503
                
                # Remove connection
                self.websocket_manager.remove_connection(server_id)
                
                # Remove from live connections
                if server_id in self.live_connections:
                    del self.live_connections[server_id]
                
                return jsonify({
                    'success': True,
                    'message': f'Monitoring disconnected for server {server_id}',
                    'server_id': server_id
                })
                
            except Exception as e:
                logger.error(f"❌ Error disconnecting server monitoring: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def setup_console_routes(self):
        """Setup console-related routes"""
        
        @self.app.route('/api/console/send', methods=['POST'])
        def send_console_command():
            """Send console command to server - COMPLETELY FIXED VERSION"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # FIXED: Enhanced request validation
                if not request:
                    logger.error("❌ No request object")
                    return jsonify({'success': False, 'error': 'Invalid request'}), 400
                
                if not hasattr(request, 'json') or request.json is None:
                    logger.error("❌ No JSON data in request")
                    return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
                
                data = request.json
                if not isinstance(data, dict):
                    logger.error("❌ Invalid JSON data format")
                    return jsonify({'success': False, 'error': 'Invalid JSON format'}), 400
                
                # FIXED: Safe data extraction with comprehensive None checking
                command = None
                server_id = None
                region = None
                
                try:
                    command = data.get('command')
                    if command is None:
                        command = ''
                    elif not isinstance(command, str):
                        command = str(command)
                    command = command.strip()
                    
                    server_id = data.get('serverId')
                    if server_id is None:
                        server_id = ''
                    elif not isinstance(server_id, str):
                        server_id = str(server_id)
                    server_id = server_id.strip()
                    
                    region = data.get('region')
                    if region is None:
                        region = 'US'
                    elif not isinstance(region, str):
                        region = str(region)
                    region = region.strip().upper()
                    
                except Exception as extract_error:
                    logger.error(f"❌ Data extraction error: {extract_error}")
                    return jsonify({'success': False, 'error': 'Data extraction failed'}), 400
                
                logger.debug(f"🔍 Console command request: command='{command}', server_id='{server_id}', region='{region}'")
                
                # Validate required fields
                if not command or not server_id:
                    logger.warning(f"❌ Missing required fields: command='{command}', server_id='{server_id}'")
                    return jsonify({'success': False, 'error': 'Command and server ID are required'}), 400
                
                # Check if in demo mode
                demo_mode = session.get('demo_mode', True)
                
                if demo_mode:
                    logger.info(f"🎭 Demo mode: Simulating command '{command}' to server {server_id}")
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
                        try:
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
                        except Exception as sim_error:
                            logger.error(f"❌ Demo simulation error: {sim_error}")
                    
                    threading.Thread(target=simulate_response, daemon=True).start()
                    return jsonify({'success': True, 'demo_mode': True})
                
                # Real mode - send command using FIXED GraphQL
                logger.info(f"🌐 Live mode: Sending real command '{command}' to server {server_id} in region {region}")
                
                try:
                    result = self.send_console_command_graphql(command, server_id, region)
                    return jsonify({'success': result, 'demo_mode': False})
                except Exception as graphql_error:
                    logger.error(f"❌ GraphQL command error: {graphql_error}")
                    import traceback
                    logger.error(f"❌ GraphQL traceback: {traceback.format_exc()}")
                    return jsonify({'success': False, 'error': str(graphql_error), 'demo_mode': False}), 500
                    
            except Exception as outer_error:
                logger.error(f"❌ Console send route error: {outer_error}")
                import traceback
                logger.error(f"❌ Console route traceback: {traceback.format_exc()}")
                return jsonify({'success': False, 'error': f'Request processing error: {str(outer_error)}'}), 500
        
        # ✅ NEW: Auto command endpoint for serverinfo commands
        @self.app.route('/api/console/send-auto', methods=['POST'])
        def send_auto_console_command():
            """
            NEW: Dedicated endpoint for auto commands (serverinfo)
            This fixes the auto command system by providing a proper API endpoint
            """
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # Get request data
                data = request.json if request.json else {}
                command = data.get('command', '').strip()
                server_id = data.get('serverId', '').strip()
                region = data.get('region', 'US').strip().upper()
                
                logger.debug(f"🤖 Auto command request: command='{command}', server_id='{server_id}', region='{region}'")
                
                # Validate inputs
                if not command or not server_id:
                    return jsonify({
                        'success': False, 
                        'error': 'Command and server ID are required',
                        'auto_command': True
                    }), 400
                
                # Check demo mode
                demo_mode = session.get('demo_mode', True)
                
                if demo_mode:
                    logger.info(f"🎭 Auto command demo mode: '{command}' to server {server_id}")
                    
                    # Generate realistic demo data for serverinfo
                    if command.lower() == 'serverinfo':
                        import random
                        players = random.randint(0, 50)
                        max_players = random.choice([50, 100, 150, 200])
                        fps = random.randint(45, 65)
                        
                        demo_response = f"[AUTO-DEMO] Server {server_id}: Players {players}/{max_players}, FPS: {fps}"
                        
                        # Add to console output
                        self.console_output.append({
                            'timestamp': datetime.now().isoformat(),
                            'command': command,
                            'server_id': server_id,
                            'status': 'sent',
                            'source': 'auto_demo',
                            'type': 'auto_command',
                            'message': f'Auto command: {command}',
                            'response': demo_response
                        })
                        
                        return jsonify({
                            'success': True, 
                            'demo_mode': True,
                            'auto_command': True,
                            'response': demo_response,
                            'player_data': {
                                'current': players,
                                'max': max_players,
                                'percentage': round((players / max_players) * 100, 1) if max_players > 0 else 0
                            }
                        })
                    else:
                        # Generic demo response
                        demo_response = f"[AUTO-DEMO] Server {server_id}: Command '{command}' executed"
                        
                        self.console_output.append({
                            'timestamp': datetime.now().isoformat(),
                            'command': command,
                            'server_id': server_id,
                            'status': 'sent',
                            'source': 'auto_demo',
                            'type': 'auto_command',
                            'message': f'Auto command: {command}'
                        })
                        
                        return jsonify({
                            'success': True, 
                            'demo_mode': True,
                            'auto_command': True,
                            'response': demo_response
                        })
                
                # Live mode - send real command
                logger.info(f"🌐 Auto command live mode: Sending '{command}' to server {server_id}")
                
                try:
                    result = self.send_console_command_graphql(command, server_id, region)
                    
                    # Add to console output with auto command tracking
                    self.console_output.append({
                        'timestamp': datetime.now().isoformat(),
                        'command': command,
                        'server_id': server_id,
                        'status': 'sent' if result else 'failed',
                        'source': 'auto_live',
                        'type': 'auto_command',
                        'message': f'Auto command: {command}',
                        'success': result
                    })
                    
                    return jsonify({
                        'success': result, 
                        'demo_mode': False,
                        'auto_command': True,
                        'message': f'Auto command {"sent" if result else "failed"}: {command}'
                    })
                    
                except Exception as auto_error:
                    logger.error(f"❌ Auto command error: {auto_error}")
                    return jsonify({
                        'success': False, 
                        'demo_mode': False,
                        'auto_command': True,
                        'error': str(auto_error)
                    }), 500
                
            except Exception as e:
                logger.error(f"❌ Auto console command error: {e}")
                return jsonify({
                    'success': False,
                    'auto_command': True,
                    'error': f'Auto command processing error: {str(e)}'
                }), 500
        
        @self.app.route('/api/console/output')
        def get_console_output():
            """Get recent console output"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Return last 50 entries
            return jsonify(list(self.console_output)[-50:])
        
        # ✅ NEW: Server list endpoint for auto commands
        @self.app.route('/api/servers/list')
        def get_server_list():
            """Get list of managed servers for auto commands"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # Return managed servers with status information
                servers = []
                demo_mode = session.get('demo_mode', True)
                
                if demo_mode:
                    # Demo servers
                    demo_servers = [
                        {
                            'serverId': 'demo-server-1',
                            'serverName': 'Demo Rust Server #1',
                            'serverRegion': 'US',
                            'status': 'online',
                            'isActive': True,
                            'playerCount': {'current': 23, 'max': 100}
                        },
                        {
                            'serverId': 'demo-server-2', 
                            'serverName': 'Demo Rust Server #2',
                            'serverRegion': 'EU',
                            'status': 'online',
                            'isActive': True,
                            'playerCount': {'current': 45, 'max': 150}
                        }
                    ]
                    servers = demo_servers
                else:
                    # Real servers (from monitored servers config)
                    servers = []
                    for server_config in self.monitored_servers:
                        if server_config.get('enabled', True):
                            servers.append({
                                'serverId': server_config['server_id'],
                                'serverName': server_config.get('name', f"Server {server_config['server_id']}"),
                                'serverRegion': server_config.get('region', 'US'),
                                'status': 'online' if server_config['server_id'] in self.live_connections else 'offline',
                                'isActive': server_config['server_id'] in self.live_connections,
                                'playerCount': {'current': 0, 'max': 100}  # Will be updated by sensor data
                            })
                
                return jsonify({
                    'success': True,
                    'servers': servers,
                    'count': len(servers),
                    'demo_mode': demo_mode,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error getting server list: {e}")
                return jsonify({
                    'success': False,
                    'servers': [],
                    'count': 0,
                    'demo_mode': session.get('demo_mode', True),
                    'error': str(e)
                }), 500
        
        # Live Console Routes (only if WebSockets are available)
        if self.websocket_manager:
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
            
            try:
                data = request.json if request.json else {}
                server_id = data.get('serverId')
                region = data.get('region', 'US')
                
                if not server_id:
                    return jsonify({'success': False, 'error': 'Server ID required'})
                
                if session.get('demo_mode', True):
                    return jsonify({
                        'success': False, 
                        'error': 'Live console requires G-Portal authentication. Please login with real credentials.'
                    })
                
                # FIXED: Improved token loading with better error handling
                try:
                    token_data = load_token()
                    if not token_data:
                        return jsonify({
                            'success': False,
                            'error': 'No valid G-Portal token. Please re-login.'
                        })
                    
                    # Extract token safely
                    token = None
                    if isinstance(token_data, dict):
                        token = token_data.get('access_token')
                    elif isinstance(token_data, str):
                        token = token_data
                    
                    if not token or token == '':
                        return jsonify({
                            'success': False,
                            'error': 'Invalid G-Portal token. Please re-login.'
                        })
                        
                except Exception as token_error:
                    logger.error(f"❌ Token loading error in live connect: {token_error}")
                    return jsonify({
                        'success': False,
                        'error': 'Token loading failed. Please re-login.'
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
                    'demo_mode': session.get('demo_mode', True),
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'websocket_import_success': WEBSOCKET_IMPORT_SUCCESS
                })
                
            except Exception as e:
                logger.error(f"❌ Live console status error: {e}")
                return jsonify({
                    'connections': {},
                    'total_connections': 0,
                    'demo_mode': True,
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'websocket_import_success': WEBSOCKET_IMPORT_SUCCESS,
                    'error': str(e)
                })
        
        @self.app.route('/api/console/live/messages')
        def get_live_messages():
            """Get live console messages"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
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
                    except Exception as ws_error:
                        logger.error(f"❌ Error getting WebSocket messages: {ws_error}")
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
                
            except Exception as e:
                logger.error(f"❌ Live messages error: {e}")
                return jsonify({
                    'messages': [],
                    'count': 0,
                    'server_id': request.args.get('serverId'),
                    'timestamp': datetime.now().isoformat(),
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'error': str(e)
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
                        except Exception as msg_error:
                            logger.error(f"❌ Error getting messages for server {server_id}: {msg_error}")
                    
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
                'error': f'WebSocket support not available. {self.websocket_error or "Install with: pip install websockets==11.0.3"}'
            })
        
        @self.app.route('/api/console/live/status')
        def live_console_status():
            return jsonify({
                'connections': {},
                'total_connections': 0,
                'demo_mode': session.get('demo_mode', True),
                'websockets_available': WEBSOCKETS_AVAILABLE,
                'websocket_import_success': WEBSOCKET_IMPORT_SUCCESS,
                'websocket_error': self.websocket_error
            })
        
        @self.app.route('/api/console/live/messages')
        def get_live_messages():
            try:
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
                    'websockets_available': WEBSOCKETS_AVAILABLE
                })
            except Exception as e:
                logger.error(f"❌ Stub live messages error: {e}")
                return jsonify({
                    'messages': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'error': str(e)
                })
        
        @self.app.route('/api/console/live/test')
        def test_live_console():
            return jsonify({
                'success': False,
                'error': f'WebSocket support not available. {self.websocket_error or "Install with: pip install websockets==11.0.3"}',
                'websockets_available': WEBSOCKETS_AVAILABLE,
                'enhanced_console': False
            })
    
    def setup_misc_routes(self):
        """Setup miscellaneous routes including WebSocket debug endpoint"""
        
        @self.app.route('/health')
        def health_check():
            """Enhanced health check endpoint (WEBSOCKET SENSOR INTEGRATION)"""
            
            try:
                # Calculate health metrics
                active_connections = len(self.live_connections) if self.live_connections else 0
                
                # Get server health score
                health_score = 95  # Default healthy score
                try:
                    if self.server_health_storage:
                        # Try to get actual health data
                        health_data = self.server_health_storage.get_system_health()
                        if health_data:
                            health_score = health_data.get('overall_score', 95)
                except Exception as health_error:
                    logger.warning(f"⚠️ Could not get health score: {health_error}")
                
                # ✅ NEW: Check WebSocket sensor status
                websocket_sensor_status = 'unavailable'
                sensor_connections = 0
                
                if self.websocket_manager:
                    try:
                        # Check if websocket manager has sensor bridge capability
                        if hasattr(self.websocket_manager, 'get_sensor_data'):
                            websocket_sensor_status = 'available'
                        else:
                            websocket_sensor_status = 'no_sensor_bridge'
                        
                        # Get connection count
                        if hasattr(self.websocket_manager, 'get_connection_status'):
                            connections = self.websocket_manager.get_connection_status()
                            sensor_connections = len(connections)
                            
                    except Exception as sensor_error:
                        logger.warning(f"⚠️ Could not get sensor status: {sensor_error}")
                        websocket_sensor_status = 'error'
                
                return jsonify({
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'database': 'MongoDB' if self.db else 'InMemoryStorage',
                    'user_storage': type(self.user_storage).__name__,
                    'koth_system': 'vanilla_compatible',
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'websocket_import_success': WEBSOCKET_IMPORT_SUCCESS,
                    'active_events': len(self.vanilla_koth.get_active_events()),
                    'live_connections': active_connections,
                    'console_buffer_size': len(self.console_output),
                    'health_score': health_score,
                    'server_health_storage': type(self.server_health_storage).__name__,
                    'websocket_sensor_status': websocket_sensor_status,  # ✅ NEW
                    'sensor_connections': sensor_connections,  # ✅ NEW
                    'websocket_error': self.websocket_error,  # ✅ NEW
                    'monitored_servers': len(self.monitored_servers),  # ✅ NEW
                    'features': {
                        'console_commands': True,
                        'auto_console_commands': True,
                        'event_management': True,
                        'koth_events_fixed': True,
                        'economy_system': True,
                        'clan_management': True,
                        'gambling_games': True,
                        'server_diagnostics': True,
                        'live_console': self.websocket_manager is not None,
                        'graphql_working': True,
                        'user_storage_working': True,
                        'server_health_monitoring': True,
                        'server_health_layout': '75/25',
                        'server_health_backend': True,
                        'enhanced_navigation': True,
                        'health_indicators': True,
                        'websocket_sensors': websocket_sensor_status == 'available',  # ✅ NEW
                        'real_time_monitoring': websocket_sensor_status == 'available',  # ✅ NEW
                        'auto_sensor_connections': True  # ✅ NEW
                    }
                })
            except Exception as e:
                logger.error(f"❌ Health check error: {e}")
                return jsonify({
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'health_score': 0
                }), 500
        
        @self.app.route('/api/token/status')
        def token_status():
            """Get authentication token status - FIXED VERSION"""
            try:
                # FIXED: Comprehensive token loading with all edge cases handled
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
                    
                    # Enhanced token validation
                    if token_data:
                        try:
                            # Handle different token formats
                            expires_at = 0
                            if isinstance(token_data, dict):
                                expires_at = token_data.get('access_token_exp', 0)
                                if not isinstance(expires_at, (int, float)):
                                    expires_at = 0
                            
                            current_time = int(time.time())
                            time_left = max(0, int(expires_at) - current_time)
                            
                            return jsonify({
                                'has_token': True,
                                'token_valid': time_left > 0,
                                'demo_mode': False,
                                'websockets_available': WEBSOCKETS_AVAILABLE,
                                'time_left': time_left
                            })
                        except Exception as validation_error:
                            logger.error(f"❌ Token validation error: {validation_error}")
                            return jsonify({
                                'has_token': False,
                                'token_valid': False,
                                'demo_mode': True,
                                'websockets_available': WEBSOCKETS_AVAILABLE,
                                'time_left': 0,
                                'error': 'Token validation failed'
                            })
                    else:
                        return jsonify({
                            'has_token': False,
                            'token_valid': False,
                            'demo_mode': False,
                            'websockets_available': WEBSOCKETS_AVAILABLE,
                            'time_left': 0
                        })
                except Exception as token_error:
                    logger.error(f"❌ Token loading error: {token_error}")
                    return jsonify({
                        'has_token': False,
                        'token_valid': False,
                        'demo_mode': True,
                        'websockets_available': WEBSOCKETS_AVAILABLE,
                        'time_left': 0,
                        'error': 'Token loading failed'
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
        
        # ✅ NEW: Server Health specific API endpoint for quick status with sensor data
        @self.app.route('/api/health/status')
        def server_health_status():
            """Quick server health status endpoint with WebSocket sensor integration"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # Get basic health metrics
                active_connections = len(self.live_connections) if self.live_connections else 0
                total_servers = len(self.monitored_servers) if self.monitored_servers else 0
                
                # Calculate health score based on available metrics
                health_score = 95  # Base score
                
                # Adjust based on connections
                if total_servers > 0:
                    connection_ratio = active_connections / total_servers
                    health_score = int(85 + (connection_ratio * 15))  # 85-100 range
                
                # ✅ NEW: Check sensor data availability
                sensor_data_available = False
                real_time_monitoring = False
                
                if self.websocket_manager:
                    try:
                        # Check if any servers have sensor data
                        if hasattr(self.websocket_manager, 'get_sensor_data'):
                            sensor_data_available = True
                        if hasattr(self.websocket_manager, 'get_connection_status'):
                            connections = self.websocket_manager.get_connection_status()
                            if connections:
                                real_time_monitoring = True
                                # Bonus points for real-time monitoring
                                health_score = min(100, health_score + 5)
                    except Exception as sensor_check_error:
                        logger.warning(f"⚠️ Sensor check error: {sensor_check_error}")
                
                # Determine status
                if health_score >= 90:
                    status = 'healthy'
                    status_color = 'green'
                elif health_score >= 70:
                    status = 'warning'
                    status_color = 'yellow'
                else:
                    status = 'critical'
                    status_color = 'red'
                
                return jsonify({
                    'success': True,
                    'status': status,
                    'status_color': status_color,
                    'health_score': health_score,
                    'metrics': {
                        'active_connections': active_connections,
                        'total_servers': total_servers,
                        'monitored_servers': len(self.monitored_servers),
                        'console_buffer_size': len(self.console_output),
                        'websockets_available': WEBSOCKETS_AVAILABLE,
                        'websocket_import_success': WEBSOCKET_IMPORT_SUCCESS,
                        'database_connected': self.db is not None,
                        'sensor_data_available': sensor_data_available,  # ✅ NEW
                        'real_time_monitoring': real_time_monitoring  # ✅ NEW
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error getting server health status: {e}")
                return jsonify({
                    'success': False,
                    'status': 'error',
                    'status_color': 'red',
                    'health_score': 0,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
    
    def send_console_command_graphql(self, command, sid, region):
        """
        ✅ COMPLETELY FIXED: Send console command via GraphQL with correct endpoint
        This is the critical fix - using the correct endpoint without "/graphql" suffix
        """
        import requests
        
        try:
            logger.debug(f"🔍 GraphQL command input: command='{command}', sid='{sid}', region='{region}'")
            
            # Rate limiting
            self.rate_limiter.wait_if_needed("graphql")
            
            # FIXED: Enhanced token loading with comprehensive error handling
            token = None
            try:
                token_data = load_token()
                if not token_data:
                    logger.warning("❌ No token data available")
                    return False
                
                # Handle different token formats safely
                if isinstance(token_data, dict):
                    token = token_data.get('access_token')
                elif isinstance(token_data, str):
                    token = token_data
                else:
                    logger.error(f"❌ Unexpected token data type: {type(token_data)}")
                    return False
                
                # Validate token
                if not token or not isinstance(token, str) or token.strip() == '':
                    logger.warning("❌ No valid G-Portal token available")
                    return False
                    
            except Exception as token_error:
                logger.error(f"❌ Token loading error in GraphQL: {token_error}")
                return False
            
            # FIXED: Enhanced input validation with comprehensive error handling
            try:
                # Validate server ID
                is_valid, server_id = validate_server_id(sid)
                if not is_valid or server_id is None:
                    logger.error(f"❌ Invalid server ID: {sid}")
                    return False
                
                # Ensure server_id is an integer
                if not isinstance(server_id, int):
                    try:
                        server_id = int(server_id)
                    except (ValueError, TypeError) as convert_error:
                        logger.error(f"❌ Server ID conversion error: {convert_error}")
                        return False
                        
            except Exception as sid_error:
                logger.error(f"❌ Server ID validation error: {sid_error}")
                return False
            
            try:
                # Validate region
                if not validate_region(region):
                    logger.error(f"❌ Invalid region: {region}")
                    return False
                
                # Ensure region is a valid string
                if not isinstance(region, str):
                    try:
                        region = str(region)
                    except Exception as region_convert_error:
                        logger.error(f"❌ Region conversion error: {region_convert_error}")
                        return False
                
                region = region.upper().strip()
                
            except Exception as region_error:
                logger.error(f"❌ Region validation error: {region_error}")
                return False
            
            # FIXED: Enhanced command formatting with error handling
            try:
                formatted_command = format_command(command)
                if not formatted_command or not isinstance(formatted_command, str):
                    logger.error(f"❌ Command formatting failed for: {command}")
                    return False
            except Exception as cmd_error:
                logger.error(f"❌ Command formatting error: {cmd_error}")
                return False
            
            # ✅ CRITICAL FIX: Use correct endpoint (NO "/graphql" suffix)
            endpoint = Config.GPORTAL_API_ENDPOINT  # This is the fix!
            if not endpoint:
                logger.error("❌ No GraphQL endpoint configured")
                return False
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "GUST-Bot/1.0"
            }
            
            # FIXED: Enhanced GraphQL payload with comprehensive validation
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
            
            logger.debug(f"🔍 GraphQL payload: {json.dumps(payload, indent=2)}")
            logger.info(f"🔄 Sending command to server {server_id} ({region}): {formatted_command}")
            logger.info(f"🌐 Using endpoint: {endpoint}")  # Log the endpoint being used
            
            # Make the request
            response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            
            logger.debug(f"🔍 Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"🔍 Response JSON: {json.dumps(data, indent=2)}")
                    
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
                        errors = data['errors']
                        logger.error(f"❌ GraphQL errors: {errors}")
                        return False
                    else:
                        logger.error(f"❌ Unexpected response format: {data}")
                        return False
                        
                except json.JSONDecodeError as json_error:
                    logger.error(f"❌ Failed to parse JSON response: {json_error}")
                    logger.error(f"❌ Raw response: {response.text}")
                    return False
                except Exception as parse_error:
                    logger.error(f"❌ Response parsing error: {parse_error}")
                    return False
            else:
                logger.error(f"❌ HTTP error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout as timeout_error:
            logger.error(f"❌ Request timeout: {timeout_error}")
            return False
        except requests.exceptions.ConnectionError as conn_error:
            logger.error(f"❌ Connection error: {conn_error}")
            return False
        except requests.exceptions.RequestException as req_error:
            logger.error(f"❌ Request error: {req_error}")
            return False
        except Exception as general_error:
            logger.error(f"❌ Exception in send_console_command_graphql: {general_error}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return False
    
    def start_background_tasks(self):
        """Start background tasks (ENHANCED WITH WEBSOCKET SENSOR MONITORING)"""
        def run_scheduled():
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(60)
                except Exception as schedule_error:
                    logger.error(f"❌ Background task error: {schedule_error}")
                    time.sleep(60)
        
        # Schedule cleanup tasks
        schedule.every(5).minutes.do(self.cleanup_expired_events)
        
        # NEW: Schedule server health monitoring
        schedule.every(2).minutes.do(self.update_server_health_metrics)
        
        # ✅ NEW: Schedule WebSocket sensor health monitoring
        schedule.every(1).minutes.do(self.monitor_websocket_sensors)
        
        # ✅ NEW: Schedule connection health checks
        schedule.every(5).minutes.do(self.check_and_reconnect_sensors)
        
        thread = threading.Thread(target=run_scheduled, daemon=True)
        thread.start()
        
        logger.info("📅 Background tasks started (including WebSocket sensor monitoring)")
    
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
                total_servers = len(self.monitored_servers) if self.monitored_servers else 0
                
                health_data = {
                    'timestamp': datetime.now().isoformat(),
                    'active_connections': active_connections,
                    'total_servers': total_servers,
                    'monitored_servers': len(self.monitored_servers),
                    'console_buffer_size': len(self.console_output),
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'websocket_import_success': WEBSOCKET_IMPORT_SUCCESS,
                    'database_connected': self.db is not None
                }
                
                # Store health snapshot
                self.server_health_storage.store_system_health(health_data)
                
        except Exception as health_error:
            logger.error(f"❌ Error updating server health metrics: {health_error}")
    
    def monitor_websocket_sensors(self):
        """✅ NEW: Monitor WebSocket sensor connections and data (background task)"""
        try:
            if self.websocket_manager:
                # Check connection health
                try:
                    connections = self.websocket_manager.get_connection_status()
                    active_sensor_connections = 0
                    
                    for server_id, connection_info in connections.items():
                        if connection_info.get('connected', False):
                            active_sensor_connections += 1
                            
                            # Check if sensor data is fresh
                            if hasattr(self.websocket_manager, 'get_sensor_data'):
                                try:
                                    sensor_data = self.websocket_manager.get_sensor_data(server_id)
                                    if sensor_data:
                                        logger.debug(f"📊 Sensor data healthy for server {server_id}")
                                    else:
                                        logger.warning(f"⚠️ No sensor data for connected server {server_id}")
                                except Exception as sensor_error:
                                    logger.warning(f"⚠️ Sensor data error for server {server_id}: {sensor_error}")
                    
                    logger.debug(f"📡 WebSocket sensor monitor: {active_sensor_connections} active connections")
                    
                except Exception as monitor_error:
                    logger.warning(f"⚠️ WebSocket sensor monitor error: {monitor_error}")
            else:
                logger.debug("📡 WebSocket sensor monitor: No WebSocket manager available")
                
        except Exception as sensor_monitor_error:
            logger.error(f"❌ Error in WebSocket sensor monitoring: {sensor_monitor_error}")
    
    def check_and_reconnect_sensors(self):
        """✅ NEW: Check sensor connections and attempt reconnections if needed"""
        try:
            if not self.websocket_manager:
                return
            
            logger.debug("🔍 Checking sensor connections for reconnection needs...")
            
            # Get current connection status
            connections = self.websocket_manager.get_connection_status()
            
            # Check each monitored server
            for server_config in self.monitored_servers:
                if not server_config.get('enabled', True):
                    continue
                
                server_id = server_config.get('server_id')
                if not server_id:
                    continue
                
                # Check if connection exists and is healthy
                connection_healthy = False
                if server_id in connections:
                    conn_info = connections[server_id]
                    connection_healthy = (
                        conn_info.get('connected', False) and
                        conn_info.get('has_sensor_data', False) and
                        conn_info.get('sensor_data_fresh', False)
                    )
                
                # Attempt reconnection if needed
                if not connection_healthy:
                    logger.info(f"🔄 Attempting to reconnect sensor for server {server_id}")
                    try:
                        token_data = load_token()
                        if token_data:
                            token = token_data.get('access_token') if isinstance(token_data, dict) else token_data
                            if token:
                                region = server_config.get('region', 'US')
                                future = self.websocket_manager.add_connection(server_id, region, token)
                                if future:
                                    logger.info(f"✅ Reconnection queued for server {server_id}")
                                else:
                                    logger.warning(f"⚠️ Failed to queue reconnection for server {server_id}")
                    except Exception as reconnect_error:
                        logger.error(f"❌ Reconnection failed for server {server_id}: {reconnect_error}")
                
        except Exception as e:
            logger.error(f"❌ Error in check_and_reconnect_sensors: {e}")
    
    def run(self, host=None, port=None, debug=False):
        """Run the enhanced application (WEBSOCKET SENSOR INTEGRATION)"""
        host = host or Config.DEFAULT_HOST
        port = port or Config.DEFAULT_PORT
        
        logger.info(f"🚀 Starting GUST Bot Enhanced on {host}:{port}")
        logger.info(f"🔧 WebSocket Support: {'Available' if WEBSOCKETS_AVAILABLE else 'Not Available'}")
        logger.info(f"🔧 WebSocket Import: {'Success' if WEBSOCKET_IMPORT_SUCCESS else 'Failed'}")
        logger.info(f"🗄️ Database: {'MongoDB' if self.db else 'In-Memory'}")
        logger.info(f"👥 User Storage: {type(self.user_storage).__name__}")
        logger.info(f"📡 Live Console: {'Enabled' if self.websocket_manager else 'Disabled'}")
        logger.info(f"🏥 Server Health: Complete integration with {type(self.server_health_storage).__name__}")
        logger.info(f"📊 Health Monitoring: 75/25 layout with real-time metrics and command feed")
        logger.info(f"✅ CRITICAL FIX: GraphQL endpoint correctly configured (no '/graphql' suffix)")
        logger.info(f"🤖 NEW: Auto command API endpoint added for serverinfo commands")
        logger.info(f"📡 NEW: WebSocket sensor integration {'ENABLED' if self.websocket_manager else 'DISABLED'}")
        logger.info(f"🔄 NEW: Real-time sensor monitoring {'ACTIVE' if self.websocket_manager else 'INACTIVE'}")
        logger.info(f"🔧 NEW: WebSocket debug endpoint available at /api/websocket/debug/status")
        logger.info(f"📊 NEW: Monitored servers: {len(self.monitored_servers)} configured")
        logger.info(f"🔄 NEW: Auto-connection system: {'ENABLED' if self.websocket_manager else 'DISABLED'}")
        
        if self.websocket_error:
            logger.warning(f"⚠️ WebSocket Error: {self.websocket_error}")
        
        try:
            self.app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
        except KeyboardInterrupt:
            logger.info("\n👋 GUST Enhanced stopped by user")
            # Clean up WebSocket connections
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