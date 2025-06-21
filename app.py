"""
GUST Bot Enhanced - Main Flask Application (SERVICE ID AUTO-DISCOVERY INTEGRATION COMPLETE)
=============================================================================================
✅ FIXED: Complete Service ID Auto-Discovery integration
✅ FIXED: Enhanced server routes initialization with Service ID support
✅ FIXED: WebSocket sensor integration with dual ID system
✅ FIXED: Service ID discovery system validation and initialization
✅ FIXED: Enhanced error handling and logging for Service ID operations
✅ FIXED: Proper integration with all Service ID components
✅ NEW: Service ID discovery system status monitoring
✅ NEW: Enhanced server health integration with Service ID context
✅ NEW: Comprehensive Service ID debugging and validation endpoints
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
    """Main GUST Bot Enhanced application class (SERVICE ID AUTO-DISCOVERY INTEGRATION COMPLETE)"""
    
    def __init__(self):
        """Initialize the enhanced GUST bot application with complete Service ID Auto-Discovery integration"""
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
        
        # Server Health storage (pre-initialization)
        self.server_health_storage = ServerHealthStorage(None, None)  # Will get proper DB later
        print("[✅ OK] Server Health storage pre-initialized")
        
        # Database connection (optional)
        self.init_database()
        
        # ✅ SERVICE ID AUTO-DISCOVERY: Initialize Service ID discovery system
        self.init_service_id_discovery()
        
        # Initialize systems
        self.vanilla_koth = VanillaKothSystem(self)
        
        # ✅ ENHANCED: WebSocket manager initialization with Service ID awareness
        self.websocket_manager = None
        self.websocket_error = None
        
        if WEBSOCKETS_AVAILABLE and WEBSOCKET_IMPORT_SUCCESS and EnhancedWebSocketManager:
            try:
                self.websocket_manager = EnhancedWebSocketManager(self)
                self.live_connections = {}
                # Start WebSocket manager
                self.websocket_manager.start()
                logger.info("✅ Enhanced WebSocket manager initialized with Service ID awareness")
                print("[✅ OK] Enhanced WebSocket manager started with Service ID integration")
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
        
        # ✅ SERVICE ID AUTO-DISCOVERY: Store Service ID discovery system in app context
        if SERVICE_ID_DISCOVERY_AVAILABLE:
            self.app.service_id_discovery_available = True
            self.app.service_id_mapper = getattr(self, 'service_id_mapper', None)
        else:
            self.app.service_id_discovery_available = False
            self.app.service_id_mapper = None
        
        # ✅ ENHANCED: Store websocket_manager reference in app for sensor bridge access
        self.app.websocket_manager = self.websocket_manager
        
        # Setup routes (this will initialize sensor bridge with Service ID support)
        self.setup_routes()
        
        # Background tasks
        self.start_background_tasks()
        
        logger.info("🚀 GUST Bot Enhanced initialized successfully with complete Service ID Auto-Discovery integration")
        print("[✅ OK] GUST Bot Enhanced ready with Service ID Auto-Discovery and real-time sensor monitoring")
    
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
    
    def init_service_id_discovery(self):
        """✅ SERVICE ID AUTO-DISCOVERY: Initialize Service ID discovery system"""
        print("[🔍 SERVICE ID] Initializing Service ID Auto-Discovery system...")
        
        self.service_id_discovery_available = SERVICE_ID_DISCOVERY_AVAILABLE
        self.service_id_mapper = None
        self.service_id_discovery_error = None
        
        if SERVICE_ID_DISCOVERY_AVAILABLE:
            try:
                # Validate the Service ID discovery system
                validation_result = validate_service_id_discovery()
                
                if validation_result['valid']:
                    print("[✅ OK] Service ID discovery system validation passed")
                    print(f"[🔍 CAPABILITIES] {', '.join(validation_result.get('capabilities', []))}")
                    
                    # Initialize Service ID mapper
                    self.service_id_mapper = ServiceIDMapper()
                    
                    # Test basic functionality
                    cache_stats = self.service_id_mapper.get_cache_stats()
                    print(f"[🔍 CACHE] Service ID mapper initialized - {cache_stats['total_entries']} cached entries")
                    
                    print("[🚀 READY] Service ID Auto-Discovery system fully operational")
                    
                else:
                    print(f"[❌ FAILED] Service ID discovery validation failed: {validation_result.get('error')}")
                    self.service_id_discovery_error = validation_result.get('error')
                    
                    # Still try to initialize for basic functionality
                    try:
                        self.service_id_mapper = ServiceIDMapper()
                        print("[⚠️ LIMITED] Service ID mapper initialized with limited functionality")
                    except Exception as mapper_error:
                        print(f"[❌ ERROR] Service ID mapper initialization failed: {mapper_error}")
                        self.service_id_discovery_error = f"Mapper initialization failed: {mapper_error}"
                        
            except Exception as discovery_error:
                print(f"[❌ ERROR] Service ID discovery system initialization failed: {discovery_error}")
                self.service_id_discovery_error = f"Discovery system initialization failed: {discovery_error}"
                self.service_id_discovery_available = False
                
        else:
            print("[⚠️ WARNING] Service ID discovery system not available")
            self.service_id_discovery_error = "Service ID discovery module not found"
            print("[💡 SOLUTION] Install Service ID discovery module for enhanced functionality")
        
        # Store status in app context for route access
        self.app.service_id_discovery_status = {
            'available': self.service_id_discovery_available,
            'mapper_initialized': self.service_id_mapper is not None,
            'error': self.service_id_discovery_error,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"[📊 STATUS] Service ID discovery: {'✅ Available' if self.service_id_discovery_available else '❌ Not Available'}")
    
    def setup_routes(self):
        """Setup Flask routes and blueprints (SERVICE ID AUTO-DISCOVERY INTEGRATION)"""
        print("[DEBUG]: Setting up routes with complete Service ID Auto-Discovery integration...")
        
        # Register authentication blueprint (foundation)
        self.app.register_blueprint(auth_bp)
        print("[✅ OK] Auth routes registered")

        # ✅ SERVICE ID AUTO-DISCOVERY: Initialize routes using enhanced initialization
        try:
            # Use enhanced route initialization that supports Service ID discovery
            from routes import init_all_routes_enhanced
            
            # Initialize all routes with complete Service ID integration
            init_all_routes_enhanced(
                self.app, 
                self.db, 
                self.user_storage,
                economy_storage=self.economy,
                logs_storage=self.logs,
                server_health_storage=self.server_health_storage,
                servers_storage=self.managed_servers,  # Use managed_servers for Service ID integration
                clans=self.clans,
                users=self.users,
                events=self.events,
                vanilla_koth=self.vanilla_koth,
                console_output=self.console_output
            )
            
            print("[✅ OK] All routes registered with complete Service ID Auto-Discovery integration")
            
        except ImportError:
            # Fallback to standard route initialization
            print("[⚠️ WARNING] Enhanced route initialization not available, using standard initialization")
            self.setup_routes_standard()
        except Exception as route_error:
            print(f"[❌ ERROR] Enhanced route initialization failed: {route_error}")
            print("[🔄 FALLBACK] Attempting standard route initialization...")
            self.setup_routes_standard()
        
        # Setup main routes
        @self.app.route('/')
        def index():
            if 'logged_in' not in session:
                return redirect(url_for('auth.login'))
            return render_template('enhanced_dashboard.html')
        
        # Console routes
        self.setup_console_routes()
        
        # ✅ SERVICE ID AUTO-DISCOVERY: Service ID specific routes
        self.setup_service_id_routes()
        
        # Miscellaneous routes
        self.setup_misc_routes()
        
        print("[✅ OK] All routes registered successfully with complete Service ID Auto-Discovery integration")
    
    def setup_routes_standard(self):
        """Fallback to standard route initialization"""
        try:
            # Import route blueprints individually
            from routes.servers import init_servers_routes
            from routes.events import init_events_routes
            from routes.economy import init_economy_routes
            from routes.gambling import init_gambling_routes
            from routes.clans import init_clans_routes
            from routes.users import init_users_routes
            from routes.logs import init_logs_routes
            from routes.server_health import init_server_health_routes

            # Register individual route blueprints
            servers_bp = init_servers_routes(self.app, self.db, self.managed_servers)
            self.app.register_blueprint(servers_bp)
            print("[✅ OK] Server routes registered (standard)")

            events_bp = init_events_routes(self.app, self.db, self.events, self.vanilla_koth, self.console_output)
            self.app.register_blueprint(events_bp)
            print("[✅ OK] Events routes registered (standard)")

            economy_bp = init_economy_routes(self.app, self.db, self.user_storage)
            self.app.register_blueprint(economy_bp)
            print("[✅ OK] Economy routes registered (standard)")

            gambling_bp = init_gambling_routes(self.app, self.db, self.user_storage)
            self.app.register_blueprint(gambling_bp)
            print("[✅ OK] Gambling routes registered (standard)")

            clans_bp = init_clans_routes(self.app, self.db, self.clans, self.user_storage)
            self.app.register_blueprint(clans_bp)
            print("[✅ OK] Clans routes registered (standard)")

            users_bp = init_users_routes(self.app, self.db, self.users, self.console_output)
            self.app.register_blueprint(users_bp)
            print("[✅ OK] Users routes registered (standard)")
            
            logs_bp = init_logs_routes(self.app, self.db, self.logs)
            self.app.register_blueprint(logs_bp)
            print("[✅ OK] Logs routes registered (standard)")
            
            # Server Health routes with WebSocket sensor integration
            server_health_bp = init_server_health_routes(self.app, self.db, self.server_health_storage, self.managed_servers)
            self.app.register_blueprint(server_health_bp)
            print("[✅ OK] Server Health routes registered (standard)")
            
        except Exception as standard_error:
            logger.error(f"❌ Standard route initialization failed: {standard_error}")
            print(f"[❌ ERROR] Standard route initialization failed: {standard_error}")
    
    def setup_service_id_routes(self):
        """✅ SERVICE ID AUTO-DISCOVERY: Setup Service ID specific routes and endpoints"""
        
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
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add detailed status if system is available
                if self.service_id_discovery_available and self.service_id_mapper:
                    try:
                        cache_stats = self.service_id_mapper.get_cache_stats()
                        status_data['cache_stats'] = cache_stats
                        status_data['system_ready'] = True
                    except Exception as stats_error:
                        status_data['system_ready'] = False
                        status_data['stats_error'] = str(stats_error)
                else:
                    status_data['system_ready'] = False
                
                # Count servers with Service IDs
                if self.managed_servers:
                    total_servers = len(self.managed_servers)
                    servers_with_service_id = len([s for s in self.managed_servers if s.get('serviceId')])
                    status_data['server_stats'] = {
                        'total_servers': total_servers,
                        'servers_with_service_id': servers_with_service_id,
                        'coverage_percentage': round((servers_with_service_id / total_servers) * 100, 1) if total_servers > 0 else 0
                    }
                else:
                    status_data['server_stats'] = {
                        'total_servers': 0,
                        'servers_with_service_id': 0,
                        'coverage_percentage': 0
                    }
                
                return jsonify(status_data)
                
            except Exception as e:
                logger.error(f"❌ Error getting Service ID system status: {e}")
                return jsonify({
                    'success': False,
                    'available': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/service-id/test/<server_id>')
        def test_service_id_discovery(server_id):
            """Test Service ID discovery for a specific server"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                if not self.service_id_discovery_available:
                    return jsonify({
                        'success': False,
                        'error': 'Service ID discovery system not available',
                        'system_error': self.service_id_discovery_error
                    }), 503
                
                # Get region from query params
                region = request.args.get('region', 'US')
                
                # Test discovery
                result = discover_service_id(server_id, region)
                
                return jsonify({
                    'success': True,
                    'test_result': result,
                    'server_id': server_id,
                    'region': region,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error testing Service ID discovery: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'server_id': server_id,
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/service-id/validate')
        def validate_service_id_system():
            """Validate Service ID discovery system"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                if not SERVICE_ID_DISCOVERY_AVAILABLE:
                    return jsonify({
                        'valid': False,
                        'error': 'Service ID discovery module not available',
                        'recommendations': [
                            'Install Service ID discovery module',
                            'Check utils/service_id_discovery.py exists',
                            'Verify dependencies are installed'
                        ]
                    })
                
                # Run comprehensive validation
                validation_result = validate_service_id_discovery()
                return jsonify(validation_result)
                
            except Exception as e:
                logger.error(f"❌ Error validating Service ID system: {e}")
                return jsonify({
                    'valid': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
    
    def setup_console_routes(self):
        """Setup console-related routes (ENHANCED WITH SERVICE ID SUPPORT)"""
        
        @self.app.route('/api/console/send', methods=['POST'])
        def send_console_command():
            """Send console command to server - SERVICE ID ENHANCED VERSION"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # Enhanced request validation
                if not request or not hasattr(request, 'json') or request.json is None:
                    logger.error("❌ No JSON data in request")
                    return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
                
                data = request.json
                if not isinstance(data, dict):
                    logger.error("❌ Invalid JSON data format")
                    return jsonify({'success': False, 'error': 'Invalid JSON format'}), 400
                
                # Safe data extraction with comprehensive None checking
                try:
                    command = data.get('command', '').strip()
                    server_id = data.get('serverId', '').strip()
                    region = data.get('region', 'US').strip().upper()
                    
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
                
                # ✅ SERVICE ID AUTO-DISCOVERY: Enhanced real mode command sending
                logger.info(f"🌐 Live mode: Sending real command '{command}' to server {server_id} in region {region}")
                
                try:
                    # Find the server to get both Server ID and Service ID
                    server_config = None
                    for server in self.managed_servers:
                        if server.get('serverId') == server_id:
                            server_config = server
                            break
                    
                    if server_config:
                        # ✅ SERVICE ID: Use Service ID for commands if available
                        service_id = server_config.get('serviceId')
                        if service_id:
                            logger.info(f"🔍 Using Service ID {service_id} for command execution (Server ID: {server_id})")
                            result = self.send_console_command_graphql(command, service_id, region)
                        else:
                            logger.warning(f"⚠️ No Service ID available for server {server_id}, using Server ID")
                            result = self.send_console_command_graphql(command, server_id, region)
                    else:
                        logger.warning(f"⚠️ Server {server_id} not found in managed servers, using Server ID")
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
        
        # ✅ ENHANCED: Auto command endpoint for serverinfo commands with Service ID support
        @self.app.route('/api/console/send-auto', methods=['POST'])
        def send_auto_console_command():
            """
            SERVICE ID ENHANCED: Dedicated endpoint for auto commands (serverinfo)
            Uses Service ID for command execution when available
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
                
                # ✅ SERVICE ID ENHANCED: Live mode with Service ID support
                logger.info(f"🌐 Auto command live mode: Sending '{command}' to server {server_id}")
                
                try:
                    # Find server configuration for Service ID
                    server_config = None
                    for server in self.managed_servers:
                        if server.get('serverId') == server_id:
                            server_config = server
                            break
                    
                    target_id = server_id  # Default to Server ID
                    id_type = 'Server ID'
                    
                    if server_config and server_config.get('serviceId'):
                        # Use Service ID for command execution
                        target_id = server_config['serviceId']
                        id_type = 'Service ID'
                        logger.info(f"🔍 Using {id_type} {target_id} for auto command (Server ID: {server_id})")
                    else:
                        logger.warning(f"⚠️ No Service ID available for server {server_id}, using Server ID")
                    
                    result = self.send_console_command_graphql(command, target_id, region)
                    
                    # Add to console output with auto command tracking
                    self.console_output.append({
                        'timestamp': datetime.now().isoformat(),
                        'command': command,
                        'server_id': server_id,
                        'service_id': target_id if id_type == 'Service ID' else None,
                        'id_type_used': id_type,
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
                        'id_type_used': id_type,
                        'target_id': target_id,
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
        
        # Server list endpoint for auto commands (with Service ID information)
        @self.app.route('/api/servers/list')
        def get_server_list():
            """Get list of managed servers for auto commands (SERVICE ID ENHANCED)"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                servers = []
                demo_mode = session.get('demo_mode', True)
                
                if demo_mode:
                    # Demo servers with Service ID examples
                    demo_servers = [
                        {
                            'serverId': 'demo-server-1',
                            'serviceId': 'demo-service-1',
                            'serverName': 'Demo Rust Server #1',
                            'serverRegion': 'US',
                            'status': 'online',
                            'isActive': True,
                            'discovery_status': 'success',
                            'capabilities': {'command_execution': True, 'health_monitoring': True},
                            'playerCount': {'current': 23, 'max': 100}
                        },
                        {
                            'serverId': 'demo-server-2', 
                            'serviceId': None,  # Example of server without Service ID
                            'serverName': 'Demo Rust Server #2',
                            'serverRegion': 'EU',
                            'status': 'online',
                            'isActive': True,
                            'discovery_status': 'failed',
                            'capabilities': {'command_execution': False, 'health_monitoring': True},
                            'playerCount': {'current': 45, 'max': 150}
                        }
                    ]
                    servers = demo_servers
                else:
                    # Real servers from managed_servers
                    servers = self.managed_servers if self.managed_servers else []
                
                # Count Service ID coverage
                total_servers = len(servers)
                servers_with_service_id = len([s for s in servers if s.get('serviceId')])
                
                return jsonify({
                    'success': True,
                    'servers': servers,
                    'count': total_servers,
                    'service_id_stats': {
                        'total_servers': total_servers,
                        'servers_with_service_id': servers_with_service_id,
                        'coverage_percentage': round((servers_with_service_id / total_servers) * 100, 1) if total_servers > 0 else 0,
                        'discovery_available': self.service_id_discovery_available
                    },
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
        """Setup live console routes when WebSockets are available (SERVICE ID ENHANCED)"""
        
        @self.app.route('/api/console/live/connect', methods=['POST'])
        def connect_live_console():
            """Connect to live console for a server (SERVICE ID ENHANCED)"""
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
                
                # Enhanced token loading with better error handling
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
                    # ✅ SERVICE ID: Use Server ID for WebSocket connections (sensors)
                    # WebSocket connections always use Server ID, not Service ID
                    future = self.websocket_manager.add_connection(server_id, region, token)
                    self.live_connections[server_id] = {
                        'region': region,
                        'connected_at': datetime.now().isoformat(),
                        'connected': True,
                        'connection_type': 'websocket_sensors',
                        'uses_server_id': True  # WebSocket always uses Server ID
                    }
                    
                    logger.info(f"📡 WebSocket connection established for Server ID {server_id} (for sensors)")
                    
                    return jsonify({
                        'success': True,
                        'message': f'Live console connected for server {server_id}',
                        'server_id': server_id,
                        'connection_type': 'websocket_sensors',
                        'note': 'WebSocket uses Server ID for sensor data'
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
                        
                        logger.info(f"📡 WebSocket connection disconnected for Server ID {server_id}")
                        
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
            """Get live console connection status (SERVICE ID ENHANCED)"""
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
                
                # ✅ SERVICE ID: Add Service ID information to status
                enhanced_status = {}
                for server_id, connection_info in status.items():
                    # Find server configuration for Service ID information
                    server_config = None
                    for server in self.managed_servers:
                        if server.get('serverId') == server_id:
                            server_config = server
                            break
                    
                    enhanced_info = dict(connection_info)
                    if server_config:
                        enhanced_info.update({
                            'server_name': server_config.get('serverName', 'Unknown'),
                            'service_id': server_config.get('serviceId'),
                            'has_service_id': bool(server_config.get('serviceId')),
                            'discovery_status': server_config.get('discovery_status', 'unknown'),
                            'capabilities': server_config.get('capabilities', {}),
                            'websocket_uses_server_id': True,  # Always true for WebSocket
                            'commands_use_service_id': bool(server_config.get('serviceId'))
                        })
                    else:
                        enhanced_info.update({
                            'server_name': 'Unknown',
                            'service_id': None,
                            'has_service_id': False,
                            'discovery_status': 'unknown',
                            'capabilities': {},
                            'websocket_uses_server_id': True,
                            'commands_use_service_id': False
                        })
                    
                    enhanced_status[server_id] = enhanced_info
                
                return jsonify({
                    'connections': enhanced_status,
                    'total_connections': len(enhanced_status),
                    'demo_mode': session.get('demo_mode', True),
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'websocket_import_success': WEBSOCKET_IMPORT_SUCCESS,
                    'service_id_discovery_available': self.service_id_discovery_available,
                    'dual_id_info': {
                        'websocket_connections_use': 'Server ID',
                        'command_execution_uses': 'Service ID (when available)',
                        'health_monitoring_uses': 'Server ID',
                        'sensor_data_uses': 'Server ID'
                    }
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
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'service_id_note': 'WebSocket messages use Server ID for connection'
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
            """Test endpoint to check live console functionality (SERVICE ID ENHANCED)"""
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
                        'pending_commands': 0,
                        'service_id_integration': {
                            'websocket_uses': 'Server ID',
                            'discovery_available': self.service_id_discovery_available,
                            'dual_id_system': True
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'WebSocket manager not available',
                        'websockets_available': WEBSOCKETS_AVAILABLE,
                        'service_id_discovery_available': self.service_id_discovery_available
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
                'websocket_error': self.websocket_error,
                'service_id_discovery_available': self.service_id_discovery_available
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
                'enhanced_console': False,
                'service_id_discovery_available': self.service_id_discovery_available
            })
    
    def setup_misc_routes(self):
        """Setup miscellaneous routes including Service ID debug endpoints"""
        
        @self.app.route('/health')
        def health_check():
            """Enhanced health check endpoint (SERVICE ID AUTO-DISCOVERY INTEGRATION)"""
            
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
                
                # ✅ SERVICE ID AUTO-DISCOVERY: Check Service ID system status
                service_id_status = 'unavailable'
                service_id_stats = {
                    'total_servers': 0,
                    'servers_with_service_id': 0,
                    'coverage_percentage': 0
                }
                
                if self.service_id_discovery_available:
                    try:
                        service_id_status = 'available'
                        
                        # Count Service ID coverage
                        if self.managed_servers:
                            total_servers = len(self.managed_servers)
                            servers_with_service_id = len([s for s in self.managed_servers if s.get('serviceId')])
                            coverage_percentage = (servers_with_service_id / total_servers * 100) if total_servers > 0 else 0
                            
                            service_id_stats = {
                                'total_servers': total_servers,
                                'servers_with_service_id': servers_with_service_id,
                                'coverage_percentage': round(coverage_percentage, 1)
                            }
                            
                    except Exception as service_error:
                        logger.warning(f"⚠️ Could not get Service ID stats: {service_error}")
                        service_id_status = 'error'
                
                # Check WebSocket sensor status
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
                    'websocket_sensor_status': websocket_sensor_status,
                    'sensor_connections': sensor_connections,
                    'websocket_error': self.websocket_error,
                    'service_id_discovery_status': service_id_status,  # ✅ NEW
                    'service_id_stats': service_id_stats,  # ✅ NEW
                    'service_id_discovery_available': self.service_id_discovery_available,  # ✅ NEW
                    'service_id_discovery_error': self.service_id_discovery_error,  # ✅ NEW
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
                        'websocket_sensors': websocket_sensor_status == 'available',
                        'real_time_monitoring': websocket_sensor_status == 'available',
                        'service_id_auto_discovery': service_id_status == 'available',  # ✅ NEW
                        'dual_id_system': service_id_status == 'available',  # ✅ NEW
                        'enhanced_server_management': service_id_status == 'available'  # ✅ NEW
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
            """Get authentication token status - SERVICE ID ENHANCED VERSION"""
            try:
                # Enhanced token loading with all edge cases handled
                try:
                    token_data = load_token()
                    demo_mode = session.get('demo_mode', True)
                    
                    if demo_mode:
                        return jsonify({
                            'has_token': False,
                            'token_valid': False,
                            'demo_mode': True,
                            'websockets_available': WEBSOCKETS_AVAILABLE,
                            'service_id_discovery_available': self.service_id_discovery_available,
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
                                'service_id_discovery_available': self.service_id_discovery_available,
                                'time_left': time_left
                            })
                        except Exception as validation_error:
                            logger.error(f"❌ Token validation error: {validation_error}")
                            return jsonify({
                                'has_token': False,
                                'token_valid': False,
                                'demo_mode': True,
                                'websockets_available': WEBSOCKETS_AVAILABLE,
                                'service_id_discovery_available': self.service_id_discovery_available,
                                'time_left': 0,
                                'error': 'Token validation failed'
                            })
                    else:
                        return jsonify({
                            'has_token': False,
                            'token_valid': False,
                            'demo_mode': False,
                            'websockets_available': WEBSOCKETS_AVAILABLE,
                            'service_id_discovery_available': self.service_id_discovery_available,
                            'time_left': 0
                        })
                except Exception as token_error:
                    logger.error(f"❌ Token loading error: {token_error}")
                    return jsonify({
                        'has_token': False,
                        'token_valid': False,
                        'demo_mode': True,
                        'websockets_available': WEBSOCKETS_AVAILABLE,
                        'service_id_discovery_available': self.service_id_discovery_available,
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
                    'service_id_discovery_available': self.service_id_discovery_available,
                    'time_left': 0,
                    'error': str(e)
                })
        
        # ✅ SERVICE ID AUTO-DISCOVERY: Enhanced server health status endpoint
        @self.app.route('/api/health/status')
        def server_health_status():
            """Quick server health status endpoint with Service ID integration"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # Get basic health metrics
                active_connections = len(self.live_connections) if self.live_connections else 0
                total_servers = len(self.managed_servers) if self.managed_servers else 0
                
                # Calculate health score based on available metrics
                health_score = 95  # Base score
                
                # Adjust based on connections
                if total_servers > 0:
                    connection_ratio = active_connections / total_servers
                    health_score = int(85 + (connection_ratio * 15))  # 85-100 range
                
                # Check sensor data availability
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
                
                # ✅ SERVICE ID AUTO-DISCOVERY: Check Service ID system health
                service_id_health = False
                service_id_coverage = 0
                
                if self.service_id_discovery_available:
                    try:
                        if self.managed_servers:
                            servers_with_service_id = len([s for s in self.managed_servers if s.get('serviceId')])
                            service_id_coverage = (servers_with_service_id / total_servers * 100) if total_servers > 0 else 0
                            service_id_health = True
                            
                            # Bonus points for good Service ID coverage
                            if service_id_coverage >= 80:
                                health_score = min(100, health_score + 3)
                                
                    except Exception as service_check_error:
                        logger.warning(f"⚠️ Service ID check error: {service_check_error}")
                
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
                        'console_buffer_size': len(self.console_output),
                        'websockets_available': WEBSOCKETS_AVAILABLE,
                        'websocket_import_success': WEBSOCKET_IMPORT_SUCCESS,
                        'database_connected': self.db is not None,
                        'sensor_data_available': sensor_data_available,
                        'real_time_monitoring': real_time_monitoring,
                        'service_id_discovery_available': self.service_id_discovery_available,  # ✅ NEW
                        'service_id_system_health': service_id_health,  # ✅ NEW
                        'service_id_coverage_percentage': round(service_id_coverage, 1)  # ✅ NEW
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
        
        # ✅ SERVICE ID AUTO-DISCOVERY: WebSocket Debug Endpoint (enhanced)
        @self.app.route('/api/websocket/debug/status')
        def websocket_debug_status():
            """✅ SERVICE ID ENHANCED: Comprehensive WebSocket system debugging endpoint"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                debug_info = {
                    'timestamp': datetime.now().isoformat(),
                    'tests': {},
                    'summary': {},
                    'recommendations': []
                }
                
                # Test 1: Package Installation
                try:
                    import websockets
                    debug_info['tests']['websockets_package'] = {
                        'status': 'pass',
                        'version': websockets.__version__,
                        'message': 'WebSocket package installed correctly'
                    }
                except ImportError:
                    debug_info['tests']['websockets_package'] = {
                        'status': 'fail',
                        'message': 'WebSocket package not installed',
                        'fix': 'Run: pip install websockets==11.0.3'
                    }
                    debug_info['recommendations'].append('Install websockets package')
                
                # Test 2: Configuration Detection
                debug_info['tests']['config_detection'] = {
                    'status': 'pass' if WEBSOCKETS_AVAILABLE else 'fail',
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'import_success': WEBSOCKET_IMPORT_SUCCESS,
                    'message': 'Configuration detects WebSocket support' if WEBSOCKETS_AVAILABLE else 'Configuration shows WebSocket as unavailable'
                }
                
                if not WEBSOCKETS_AVAILABLE:
                    debug_info['recommendations'].append('Verify websockets package installation')
                
                # Test 3: Service ID Integration Test
                try:
                    debug_info['tests']['service_id_integration'] = {
                        'status': 'pass' if self.service_id_discovery_available else 'fail',
                        'discovery_available': self.service_id_discovery_available,
                        'mapper_initialized': self.service_id_mapper is not None,
                        'error': self.service_id_discovery_error
                    }
                    
                    if not self.service_id_discovery_available:
                        debug_info['recommendations'].append('Enable Service ID discovery for enhanced functionality')
                        
                except Exception as service_test_error:
                    debug_info['tests']['service_id_integration'] = {
                        'status': 'error',
                        'message': f'Service ID integration test failed: {service_test_error}'
                    }
                
                # Test 4: WebSocket Package Status
                try:
                    if WEBSOCKETS_AVAILABLE and WEBSOCKET_IMPORT_SUCCESS:
                        from websocket import get_websocket_status, check_websocket_support, check_sensor_support
                        
                        ws_status = get_websocket_status()
                        debug_info['tests']['package_status'] = {
                            'status': 'pass' if ws_status['websockets_available'] else 'fail',
                            'details': ws_status,
                            'websocket_support': check_websocket_support(),
                            'sensor_support': check_sensor_support()
                        }
                        
                        if not check_sensor_support():
                            debug_info['recommendations'].append('Enable sensor support by fixing WebSocket imports')
                    else:
                        debug_info['tests']['package_status'] = {
                            'status': 'fail',
                            'message': 'WebSocket package not importable',
                            'websockets_available': WEBSOCKETS_AVAILABLE,
                            'import_success': WEBSOCKET_IMPORT_SUCCESS
                        }
                        debug_info['recommendations'].append('Fix WebSocket package imports')
                        
                except Exception as e:
                    debug_info['tests']['package_status'] = {
                        'status': 'error',
                        'message': f'Package status check failed: {e}'
                    }
                    debug_info['recommendations'].append('Fix WebSocket package imports')
                
                # Test 5: Manager Status (Enhanced with Service ID context)
                manager_status = 'not_available'
                manager_info = {}
                
                if self.websocket_manager:
                    try:
                        manager_status = 'available'
                        manager_info = {
                            'running': getattr(self.websocket_manager, 'running', False),
                            'connections': len(getattr(self.websocket_manager, 'connections', {})),
                            'has_sensor_bridge': hasattr(self.websocket_manager, 'sensor_bridge') and self.websocket_manager.sensor_bridge is not None,
                            'service_id_aware': True  # This implementation is Service ID aware
                        }
                        
                        # Test sensor bridge
                        if hasattr(self.websocket_manager, 'sensor_bridge') and self.websocket_manager.sensor_bridge:
                            bridge_stats = self.websocket_manager.sensor_bridge.get_sensor_statistics()
                            manager_info['sensor_bridge_stats'] = bridge_stats
                            
                        debug_info['tests']['manager_status'] = {
                            'status': 'pass',
                            'manager_available': True,
                            'details': manager_info
                        }
                        
                    except Exception as e:
                        debug_info['tests']['manager_status'] = {
                            'status': 'error',
                            'manager_available': True,
                            'error': str(e)
                        }
                else:
                    debug_info['tests']['manager_status'] = {
                        'status': 'fail',
                        'manager_available': False,
                        'message': 'WebSocket manager not initialized',
                        'websocket_error': self.websocket_error
                    }
                    debug_info['recommendations'].append('Restart application to initialize WebSocket manager')
                
                # Generate Summary
                passed_tests = sum(1 for test in debug_info['tests'].values() if test.get('status') == 'pass')
                total_tests = len(debug_info['tests'])
                
                debug_info['summary'] = {
                    'tests_passed': passed_tests,
                    'tests_total': total_tests,
                    'success_rate': round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0,
                    'overall_status': 'healthy' if passed_tests >= total_tests - 1 else 'needs_attention',  # Allow 1 failure
                    'websocket_ready': passed_tests >= 3,  # Need at least 3/5 tests passing
                    'sensor_ready': manager_status == 'available' and manager_info.get('has_sensor_bridge', False),
                    'service_id_integration_ready': self.service_id_discovery_available,  # ✅ NEW
                    'dual_id_system_ready': self.service_id_discovery_available and passed_tests >= 3,  # ✅ NEW
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'websocket_import_success': WEBSOCKET_IMPORT_SUCCESS
                }
                
                # Priority Recommendations
                if not debug_info['recommendations']:
                    debug_info['recommendations'] = ['All systems operational with Service ID Auto-Discovery!']
                
                return jsonify({
                    'success': True,
                    'debug_info': debug_info,
                    'quick_status': {
                        'websockets_working': debug_info['summary']['websocket_ready'],
                        'sensors_working': debug_info['summary']['sensor_ready'],
                        'service_id_working': debug_info['summary']['service_id_integration_ready'],  # ✅ NEW
                        'dual_id_system_working': debug_info['summary']['dual_id_system_ready'],  # ✅ NEW
                        'needs_restart': 'Restart application' in debug_info['recommendations'],
                        'needs_package_install': any('websockets' in rec for rec in debug_info['recommendations']),
                        'websocket_error': self.websocket_error,
                        'service_id_error': self.service_id_discovery_error  # ✅ NEW
                    }
                })
                
            except Exception as e:
                logger.error(f"❌ WebSocket debug status error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'debug_info': {
                        'timestamp': datetime.now().isoformat(),
                        'error_type': 'debug_endpoint_failure'
                    }
                }), 500
    
    def send_console_command_graphql(self, command, sid, region):
        """
        ✅ SERVICE ID ENHANCED: Send console command via GraphQL with Service ID support
        This method can accept either Server ID or Service ID depending on use case
        """
        import requests
        
        try:
            logger.debug(f"🔍 GraphQL command input: command='{command}', sid='{sid}', region='{region}'")
            
            # Rate limiting
            self.rate_limiter.wait_if_needed("graphql")
            
            # Enhanced token loading with comprehensive error handling
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
            
            # Enhanced input validation with comprehensive error handling
            try:
                # Validate server/service ID
                is_valid, clean_id = validate_server_id(sid)
                if not is_valid or clean_id is None:
                    logger.error(f"❌ Invalid ID: {sid}")
                    return False
                
                # Ensure ID is an integer
                if not isinstance(clean_id, int):
                    try:
                        clean_id = int(clean_id)
                    except (ValueError, TypeError) as convert_error:
                        logger.error(f"❌ ID conversion error: {convert_error}")
                        return False
                        
            except Exception as sid_error:
                logger.error(f"❌ ID validation error: {sid_error}")
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
            
            # Enhanced command formatting with error handling
            try:
                formatted_command = format_command(command)
                if not formatted_command or not isinstance(formatted_command, str):
                    logger.error(f"❌ Command formatting failed for: {command}")
                    return False
            except Exception as cmd_error:
                logger.error(f"❌ Command formatting error: {cmd_error}")
                return False
            
            # Use correct endpoint (NO "/graphql" suffix)
            endpoint = Config.GPORTAL_API_ENDPOINT
            if not endpoint:
                logger.error("❌ No GraphQL endpoint configured")
                return False
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "GUST-Bot/2.0-ServiceIDEnhanced"
            }
            
            # Enhanced GraphQL payload with comprehensive validation
            payload = {
                "operationName": "sendConsoleMessage",
                "variables": {
                    "sid": clean_id,
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
            logger.info(f"🔄 Sending command to ID {clean_id} ({region}): {formatted_command}")
            logger.info(f"🌐 Using endpoint: {endpoint}")
            
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
                            'target_id': str(clean_id),
                            'status': 'sent' if success else 'failed',
                            'source': 'graphql_api',
                            'type': 'command',
                            'message': f'Command: {formatted_command}',
                            'success': success,
                            'service_id_enhanced': True  # ✅ Mark as Service ID enhanced
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
        """Start background tasks (SERVICE ID AUTO-DISCOVERY ENHANCED)"""
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
        
        # Schedule server health monitoring
        schedule.every(2).minutes.do(self.update_server_health_metrics)
        
        # Schedule WebSocket sensor health monitoring
        schedule.every(1).minutes.do(self.monitor_websocket_sensors)
        
        # ✅ SERVICE ID AUTO-DISCOVERY: Schedule Service ID discovery health monitoring
        schedule.every(10).minutes.do(self.monitor_service_id_discovery)
        
        thread = threading.Thread(target=run_scheduled, daemon=True)
        thread.start()
        
        logger.info("📅 Background tasks started (including WebSocket sensor monitoring and Service ID discovery monitoring)")
    
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
        """Update server health metrics (background task with Service ID awareness)"""
        try:
            if self.server_health_storage:
                # Calculate current health metrics
                active_connections = len(self.live_connections) if self.live_connections else 0
                total_servers = len(self.managed_servers) if self.managed_servers else 0
                
                # ✅ SERVICE ID AUTO-DISCOVERY: Calculate Service ID coverage
                servers_with_service_id = 0
                if self.managed_servers:
                    servers_with_service_id = len([s for s in self.managed_servers if s.get('serviceId')])
                
                service_id_coverage = (servers_with_service_id / total_servers * 100) if total_servers > 0 else 0
                
                health_data = {
                    'timestamp': datetime.now().isoformat(),
                    'active_connections': active_connections,
                    'total_servers': total_servers,
                    'console_buffer_size': len(self.console_output),
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'websocket_import_success': WEBSOCKET_IMPORT_SUCCESS,
                    'database_connected': self.db is not None,
                    'service_id_discovery_available': self.service_id_discovery_available,  # ✅ NEW
                    'servers_with_service_id': servers_with_service_id,  # ✅ NEW
                    'service_id_coverage_percentage': service_id_coverage,  # ✅ NEW
                    'dual_id_system_operational': self.service_id_discovery_available and service_id_coverage > 0  # ✅ NEW
                }
                
                # Store health snapshot
                self.server_health_storage.store_system_health(health_data)
                
        except Exception as health_error:
            logger.error(f"❌ Error updating server health metrics: {health_error}")
    
    def monitor_websocket_sensors(self):
        """Monitor WebSocket sensor connections and data (background task with Service ID context)"""
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
                                        logger.debug(f"📊 Sensor data healthy for server {server_id} (WebSocket uses Server ID)")
                                    else:
                                        logger.warning(f"⚠️ No sensor data for connected server {server_id}")
                                except Exception as sensor_error:
                                    logger.warning(f"⚠️ Sensor data error for server {server_id}: {sensor_error}")
                    
                    logger.debug(f"📡 WebSocket sensor monitor: {active_sensor_connections} active connections (using Server IDs)")
                    
                except Exception as monitor_error:
                    logger.warning(f"⚠️ WebSocket sensor monitor error: {monitor_error}")
            else:
                logger.debug("📡 WebSocket sensor monitor: No WebSocket manager available")
                
        except Exception as sensor_monitor_error:
            logger.error(f"❌ Error in WebSocket sensor monitoring: {sensor_monitor_error}")
    
    def monitor_service_id_discovery(self):
        """✅ SERVICE ID AUTO-DISCOVERY: Monitor Service ID discovery system health (background task)"""
        try:
            if self.service_id_discovery_available and self.service_id_mapper:
                # Check Service ID discovery system health
                try:
                    # Get cache statistics
                    cache_stats = self.service_id_mapper.get_cache_stats()
                    active_cache_entries = cache_stats.get('active_entries', 0)
                    total_cache_entries = cache_stats.get('total_entries', 0)
                    
                    logger.debug(f"🔍 Service ID discovery monitor: {active_cache_entries}/{total_cache_entries} active cache entries")
                    
                    # Check if any servers need Service ID discovery
                    if self.managed_servers:
                        servers_needing_discovery = [
                            s for s in self.managed_servers 
                            if not s.get('serviceId') and s.get('discovery_status') not in ['success', 'manual_skip']
                        ]
                        
                        if servers_needing_discovery:
                            logger.debug(f"🔍 Service ID discovery: {len(servers_needing_discovery)} servers could benefit from discovery")
                        else:
                            logger.debug("🔍 Service ID discovery: All eligible servers have Service IDs")
                    
                except Exception as discovery_check_error:
                    logger.warning(f"⚠️ Service ID discovery monitor error: {discovery_check_error}")
            else:
                logger.debug("🔍 Service ID discovery monitor: System not available or not initialized")
                
        except Exception as discovery_monitor_error:
            logger.error(f"❌ Error in Service ID discovery monitoring: {discovery_monitor_error}")
    
    def run(self, host=None, port=None, debug=False):
        """Run the enhanced application (SERVICE ID AUTO-DISCOVERY INTEGRATION COMPLETE)"""
        host = host or Config.DEFAULT_HOST
        port = port or Config.DEFAULT_PORT
        
        logger.info(f"🚀 Starting GUST Bot Enhanced on {host}:{port}")
        logger.info(f"🔧 WebSocket Support: {'Available' if WEBSOCKETS_AVAILABLE else 'Not Available'}")
        logger.info(f"🔧 WebSocket Import: {'Success' if WEBSOCKET_IMPORT_SUCCESS else 'Failed'}")
        logger.info(f"🔍 Service ID Discovery: {'Available' if self.service_id_discovery_available else 'Not Available'}")
        logger.info(f"🗄️ Database: {'MongoDB' if self.db else 'In-Memory'}")
        logger.info(f"👥 User Storage: {type(self.user_storage).__name__}")
        logger.info(f"📡 Live Console: {'Enabled' if self.websocket_manager else 'Disabled'}")
        logger.info(f"🏥 Server Health: Complete integration with {type(self.server_health_storage).__name__}")
        logger.info(f"📊 Health Monitoring: 75/25 layout with real-time metrics and command feed")
        logger.info(f"✅ CRITICAL FIX: GraphQL endpoint correctly configured (no '/graphql' suffix)")
        logger.info(f"🤖 ENHANCED: Auto command API endpoint with Service ID support")
        logger.info(f"📡 ENHANCED: WebSocket sensor integration {'ENABLED' if self.websocket_manager else 'DISABLED'}")
        logger.info(f"🔄 ENHANCED: Real-time sensor monitoring {'ACTIVE' if self.websocket_manager else 'INACTIVE'}")
        logger.info(f"🔧 ENHANCED: WebSocket debug endpoint available at /api/websocket/debug/status")
        logger.info(f"🔍 NEW: Service ID Auto-Discovery {'ENABLED' if self.service_id_discovery_available else 'DISABLED'}")
        logger.info(f"⚙️ NEW: Dual ID system (Server ID for sensors, Service ID for commands) {'OPERATIONAL' if self.service_id_discovery_available else 'UNAVAILABLE'}")
        logger.info(f"🎯 NEW: Enhanced server management with automatic Service ID discovery")
        logger.info(f"📊 NEW: Service ID system status and debug endpoints available")
        
        if self.websocket_error:
            logger.warning(f"⚠️ WebSocket Error: {self.websocket_error}")
        
        if self.service_id_discovery_error:
            logger.warning(f"⚠️ Service ID Discovery Error: {self.service_id_discovery_error}")
        
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
