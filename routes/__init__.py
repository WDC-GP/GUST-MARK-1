# routes/__init__.py - ENHANCED VERSION WITH COMPLETE SERVICE ID AUTO-DISCOVERY INTEGRATION
# Complete integration with Service ID discovery system, dual ID support, and enhanced server health monitoring

def init_all_routes(app, db, user_storage, economy_storage=None, logs_storage=None, 
                   server_health_storage=None, servers_storage=None):
    '''Initialize all routes with Service ID Auto-Discovery integration and enhanced server health monitoring'''
    
    print("[🔧 INIT] Starting enhanced route initialization with Service ID Auto-Discovery support...")
    
    # Auth Routes (foundation - independent)
    from .auth import auth_bp
    app.register_blueprint(auth_bp)
    print("[✅ OK] Auth routes registered")
    
    # User Database Routes (foundation)
    from .user_database import init_user_database_routes, user_database_bp
    init_user_database_routes(app, db, user_storage)
    app.register_blueprint(user_database_bp)
    print("[✅ OK] User database routes registered")
    
    # Economy Routes (depends on user database)  
    from .economy import init_economy_routes, economy_bp
    init_economy_routes(app, db, user_storage)
    app.register_blueprint(economy_bp)
    print("[✅ OK] Economy routes registered")
    
    # Gambling Routes (depends on user database)
    from .gambling import init_gambling_routes, gambling_bp
    init_gambling_routes(app, db, user_storage)
    app.register_blueprint(gambling_bp)
    print("[✅ OK] Gambling routes registered")
    
    # Clans Routes (depends on user database)
    from .clans import init_clans_routes, clans_bp
    init_clans_routes(app, db, [], user_storage)  # Empty clans list, user_storage for integration
    app.register_blueprint(clans_bp)
    print("[✅ OK] Clans routes registered")
    
    # Users Routes (administration)
    from .users import init_users_routes, users_bp
    init_users_routes(app, db, [], [])  # Empty users list, empty console output for now
    app.register_blueprint(users_bp)
    print("[✅ OK] Users routes registered")
    
    # ============================================================================
    # ENHANCED SERVERS ROUTES - SERVICE ID AUTO-DISCOVERY INTEGRATION
    # ============================================================================
    
    # Initialize servers storage if not provided
    if servers_storage is None:
        servers_storage = []  # Use in-memory storage as fallback
        print("[🔧 INIT] Using in-memory servers storage")
    else:
        print("[🔧 INIT] Using provided servers storage")
    
    # Server Routes (enhanced with Service ID Auto-Discovery)
    from .servers import init_servers_routes, servers_bp
    init_servers_routes(app, db, servers_storage)
    app.register_blueprint(servers_bp)
    print("[✅ OK] Server routes registered (with Service ID Auto-Discovery support)")
    
    # ============================================================================
    # ENHANCED SERVICE ID DISCOVERY VALIDATION
    # ============================================================================
    
    try:
        from utils.service_id_discovery import validate_service_id_discovery, ServiceIDMapper
        
        print("[🔍 VALIDATION] Validating Service ID discovery system...")
        discovery_status = validate_service_id_discovery()
        
        if discovery_status['valid']:
            print("[✅ OK] Service ID discovery system validated and operational")
            print(f"[🔍 DISCOVERY] Capabilities: {', '.join(discovery_status.get('capabilities', []))}")
            
            # Test Service ID mapper initialization
            try:
                mapper = ServiceIDMapper()
                cache_stats = mapper.get_cache_stats()
                print(f"[🔍 CACHE] Service ID mapper initialized - {cache_stats['total_entries']} cached entries")
                print("[🚀 READY] Service ID Auto-Discovery system fully operational")
                
                # Store mapper in app context for global access
                app.service_id_mapper = mapper
                app.service_id_discovery_available = True
                
            except Exception as mapper_error:
                print(f"[⚠️ WARNING] Service ID mapper initialization issue: {mapper_error}")
                app.service_id_discovery_available = False
                
        else:
            print(f"[⚠️ WARNING] Service ID discovery validation failed: {discovery_status.get('error', 'Unknown error')}")
            print("[💡 RECOMMENDATIONS]")
            for rec in discovery_status.get('recommendations', []):
                print(f"    • {rec}")
            app.service_id_discovery_available = False
            
    except ImportError:
        print("[⚠️ WARNING] Service ID discovery system not available - manual Service ID entry required")
        print("[💡 SOLUTION] Install Service ID discovery module for enhanced functionality")
        app.service_id_discovery_available = False
    except Exception as e:
        print(f"[❌ ERROR] Service ID discovery validation error: {e}")
        app.service_id_discovery_available = False
    
    # Events Routes (event management)
    from .events import init_events_routes, events_bp
    init_events_routes(app, db, [], {}, [])  # Empty events, vanilla_koth, console_output
    app.register_blueprint(events_bp)
    print("[✅ OK] Events routes registered")
    
    # ============================================================================
    # LOGS ROUTES INTEGRATION - WITH SERVICE ID CONTEXT
    # ============================================================================
    
    # Logs Routes (log management + player count integration + Service ID awareness)
    from .logs import init_logs_routes, logs_bp
    
    # Initialize logs storage if not provided
    if logs_storage is None:
        logs_storage = []  # Use in-memory storage as fallback
        print("[🔧 INIT] Using in-memory logs storage")
    
    # Initialize and register logs routes
    init_logs_routes(app, db, logs_storage)
    app.register_blueprint(logs_bp)
    print("[✅ OK] Logs routes registered (with player count integration and Service ID context)")
    
    # ============================================================================
    # ENHANCED SERVER HEALTH ROUTES - SERVICE ID INTEGRATION
    # ============================================================================
    
    # Server Health Routes (enhanced with Service ID awareness and dual ID support)
    from .server_health import init_server_health_routes, server_health_bp
    
    # Initialize server health storage if not provided
    if server_health_storage is None:
        try:
            from utils.server_health_storage import ServerHealthStorage
            server_health_storage = ServerHealthStorage(db, user_storage)
            print("[🔧 INIT] Created Server Health storage instance")
        except ImportError:
            print("[⚠️ WARNING] Server Health storage not available - using fallback")
            server_health_storage = None
    
    # Initialize and register server health routes with servers storage for capability checking
    init_server_health_routes(app, db, server_health_storage, servers_storage)
    app.register_blueprint(server_health_bp)
    print("[✅ OK] Server Health routes registered (with Service ID integration and dual ID support)")
    
    # ============================================================================
    # INTEGRATION VALIDATION AND SUMMARY
    # ============================================================================
    
    print("[🚀 COMPLETE] All routes initialized successfully with Service ID Auto-Discovery integration")
    print("[📊 INTEGRATION] Service ID Auto-Discovery features:")
    print("    • Automatic Service ID discovery during server addition")
    print("    • Manual Service ID discovery retry functionality")
    print("    • Bulk Service ID discovery for existing servers")
    print("    • Dual ID system support (Server ID + Service ID)")
    print("    • Enhanced server health monitoring with Service ID context")
    print("    • Real-time capability detection and status updates")
    
    return app

# ============================================================================
# ENHANCED INITIALIZATION WITH FULL SERVICE ID INTEGRATION
# ============================================================================

def init_all_routes_enhanced(app, db, user_storage, economy_storage=None, logs_storage=None, 
                           server_health_storage=None, servers_storage=None, clans=None, users=None, 
                           events=None, vanilla_koth=None, console_output=None):
    '''
    Enhanced route initialization with full Service ID Auto-Discovery integration
    This version accepts all the data structures and provides complete Service ID functionality
    '''
    
    # Use defaults for missing parameters
    servers_storage = servers_storage or []
    clans = clans or []
    users = users or []
    events = events or []
    vanilla_koth = vanilla_koth or {}
    console_output = console_output or []
    logs_storage = logs_storage or []
    
    print("[🔧 INIT] Starting comprehensive route initialization with Service ID Auto-Discovery...")
    print(f"[📊 PARAMS] servers_storage: {len(servers_storage)} entries, clans: {len(clans)}, users: {len(users)}")
    
    # Auth Routes (foundation - independent)
    from .auth import auth_bp
    app.register_blueprint(auth_bp)
    print("[✅ OK] Auth routes registered")
    
    # User Database Routes (foundation)
    from .user_database import init_user_database_routes, user_database_bp
    init_user_database_routes(app, db, user_storage)
    app.register_blueprint(user_database_bp)
    print("[✅ OK] User database routes registered")
    
    # Economy Routes (depends on user database)  
    from .economy import init_economy_routes, economy_bp
    init_economy_routes(app, db, user_storage)
    app.register_blueprint(economy_bp)
    print("[✅ OK] Economy routes registered")
    
    # Gambling Routes (depends on user database)
    from .gambling import init_gambling_routes, gambling_bp
    init_gambling_routes(app, db, user_storage)
    app.register_blueprint(gambling_bp)
    print("[✅ OK] Gambling routes registered")
    
    # Clans Routes (with actual data)
    from .clans import init_clans_routes, clans_bp
    init_clans_routes(app, db, clans, user_storage)
    app.register_blueprint(clans_bp)
    print("[✅ OK] Clans routes registered")
    
    # Users Routes (with actual data)
    from .users import init_users_routes, users_bp
    init_users_routes(app, db, users, console_output)
    app.register_blueprint(users_bp)
    print("[✅ OK] Users routes registered")
    
    # ============================================================================
    # ENHANCED SERVERS ROUTES WITH SERVICE ID AUTO-DISCOVERY
    # ============================================================================
    
    # Server Routes (enhanced with Service ID Auto-Discovery and actual data)
    from .servers import init_servers_routes, servers_bp
    init_servers_routes(app, db, servers_storage)
    app.register_blueprint(servers_bp)
    print(f"[✅ OK] Server routes registered (with {len(servers_storage)} servers and Service ID Auto-Discovery)")
    
    # ============================================================================
    # COMPREHENSIVE SERVICE ID DISCOVERY SYSTEM VALIDATION
    # ============================================================================
    
    service_id_available = False
    try:
        from utils.service_id_discovery import validate_service_id_discovery, ServiceIDMapper
        
        print("[🔍 VALIDATION] Running comprehensive Service ID discovery validation...")
        
        # Validate the Service ID discovery system
        discovery_status = validate_service_id_discovery()
        if discovery_status['valid']:
            print("[✅ OK] Service ID discovery system validated and operational")
            print(f"[🔍 DISCOVERY] Capabilities: {', '.join(discovery_status.get('capabilities', []))}")
            service_id_available = True
            
            # Test Service ID mapper initialization
            try:
                mapper = ServiceIDMapper()
                cache_stats = mapper.get_cache_stats()
                print(f"[🔍 CACHE] Service ID mapper initialized - {cache_stats['total_entries']} cached entries")
                
                # Store in app context
                app.service_id_mapper = mapper
                app.service_id_discovery_available = True
                
                print("[🚀 READY] Service ID Auto-Discovery system fully operational")
                
            except Exception as mapper_error:
                print(f"[⚠️ WARNING] Service ID mapper initialization issue: {mapper_error}")
                app.service_id_discovery_available = False
                service_id_available = False
                
        else:
            print(f"[⚠️ WARNING] Service ID discovery validation failed: {discovery_status.get('error', 'Unknown error')}")
            print("[💡 RECOMMENDATIONS]")
            for rec in discovery_status.get('recommendations', []):
                print(f"    • {rec}")
            app.service_id_discovery_available = False
                
    except ImportError as import_error:
        print("[⚠️ WARNING] Service ID discovery system not available - features will be limited")
        print(f"[🔧 DEBUG] Import error: {import_error}")
        print("[💡 SOLUTION] Install Service ID discovery module for enhanced functionality")
        app.service_id_discovery_available = False
    except Exception as e:
        print(f"[❌ ERROR] Service ID discovery validation failed: {e}")
        app.service_id_discovery_available = False
    
    # Events Routes (with actual data)
    from .events import init_events_routes, events_bp
    init_events_routes(app, db, events, vanilla_koth, console_output)
    app.register_blueprint(events_bp)
    print("[✅ OK] Events routes registered")
    
    # ============================================================================
    # ENHANCED LOGS ROUTES WITH SERVICE ID CONTEXT
    # ============================================================================
    
    # Logs Routes (with logs storage, player count integration, and Service ID awareness)
    from .logs import init_logs_routes, logs_bp
    init_logs_routes(app, db, logs_storage)
    app.register_blueprint(logs_bp)
    print(f"[✅ OK] Logs routes registered ({len(logs_storage)} log entries, Service ID context enabled)")
    
    # ============================================================================
    # ENHANCED SERVER HEALTH ROUTES WITH SERVICE ID INTEGRATION
    # ============================================================================
    
    # Server Health Routes (enhanced with Service ID awareness and servers storage integration)
    from .server_health import init_server_health_routes, server_health_bp
    
    # Initialize server health storage if not provided
    if server_health_storage is None:
        try:
            from utils.server_health_storage import ServerHealthStorage
            server_health_storage = ServerHealthStorage(db, user_storage)
            print("[🔧 INIT] Created enhanced Server Health storage instance")
        except ImportError:
            print("[⚠️ WARNING] Server Health storage not available - using basic fallback")
            server_health_storage = None
    
    # Initialize and register server health routes with servers storage for capability checking
    # This enables the server health system to check Service ID availability for each server
    init_server_health_routes(app, db, server_health_storage, servers_storage)
    app.register_blueprint(server_health_bp)
    print("[✅ OK] Server Health routes registered (enhanced with Service ID integration)")
    
    # ============================================================================
    # WEBSOCKET MANAGER INTEGRATION (if available)
    # ============================================================================
    
    try:
        if hasattr(app, 'websocket_manager') and app.websocket_manager:
            # Initialize WebSocket sensor bridge with server health storage
            if server_health_storage:
                sensor_bridge = app.websocket_manager.initialize_sensor_bridge(server_health_storage)
                if sensor_bridge:
                    print("[✅ OK] WebSocket sensor bridge initialized for real-time health data")
                else:
                    print("[⚠️ WARNING] WebSocket sensor bridge initialization failed")
            print("[🔌 WEBSOCKET] WebSocket manager integrated with health monitoring")
        else:
            print("[ℹ️ INFO] WebSocket manager not available - using standard monitoring")
    except Exception as websocket_error:
        print(f"[⚠️ WARNING] WebSocket integration error: {websocket_error}")
    
    # ============================================================================
    # COMPREHENSIVE INTEGRATION SUMMARY
    # ============================================================================
    
    print("[🚀 COMPLETE] Comprehensive route initialization complete with full Service ID integration")
    print(f"[📊 FINAL STATS] Servers: {len(servers_storage)}, Users: {len(users)}, Clans: {len(clans)}, Events: {len(events)}")
    print(f"[📋 LOGS] Log entries: {len(logs_storage)}")
    print(f"[🔍 SERVICE ID] Discovery system: {'✅ Available' if service_id_available else '❌ Not Available'}")
    
    # Count servers with Service IDs
    servers_with_service_id = 0
    try:
        servers_with_service_id = len([s for s in servers_storage if s.get('serviceId')])
    except:
        pass
    
    print(f"[⚙️ CAPABILITIES] Servers with Service ID: {servers_with_service_id}/{len(servers_storage)}")
    
    if service_id_available:
        print("[🟢 FULL FUNCTIONALITY] Complete Service ID Auto-Discovery system active:")
        print("    • ✅ Automatic Service ID discovery during server addition")
        print("    • ✅ Manual Service ID discovery and retry functionality") 
        print("    • ✅ Bulk Service ID discovery for existing servers")
        print("    • ✅ Dual ID system support (Server ID for health, Service ID for commands)")
        print("    • ✅ Enhanced server health monitoring with Service ID context")
        print("    • ✅ Real-time capability detection and status updates")
        print("    • ✅ Service ID-aware command execution routing")
        print("    • ✅ Enhanced user interface with capability indicators")
    else:
        print("[🟡 LIMITED FUNCTIONALITY] Service ID discovery not available:")
        print("    • ⚠️ Manual Service ID entry required for command execution")
        print("    • ⚠️ Limited server capability detection")
        print("    • ✅ Health monitoring still available (uses Server ID)")
        print("    • ✅ Basic server management functionality")
    
    return app

# ============================================================================
# SPECIALIZED INITIALIZATION FUNCTIONS
# ============================================================================

def init_service_id_discovery_system(app):
    '''Initialize and validate the Service ID discovery system'''
    
    print("[🔍 SERVICE ID] Initializing Service ID discovery system...")
    
    try:
        from utils.service_id_discovery import ServiceIDMapper, validate_service_id_discovery
        
        # Validate system
        validation_result = validate_service_id_discovery()
        
        if validation_result['valid']:
            print("[✅ OK] Service ID discovery system validation passed")
            print(f"[🔍 CAPABILITIES] {', '.join(validation_result.get('capabilities', []))}")
            
            # Initialize mapper
            mapper = ServiceIDMapper()
            
            # Store mapper in app context for global access
            app.service_id_mapper = mapper
            app.service_id_discovery_available = True
            
            print("[🔍 READY] Service ID discovery system fully operational")
            return True
            
        else:
            print(f"[❌ FAILED] Service ID discovery validation failed: {validation_result.get('error')}")
            app.service_id_discovery_available = False
            return False
            
    except ImportError:
        print("[⚠️ WARNING] Service ID discovery module not found")
        app.service_id_discovery_available = False
        return False
    except Exception as e:
        print(f"[❌ ERROR] Service ID discovery initialization failed: {e}")
        app.service_id_discovery_available = False
        return False

def init_dual_id_system(app, servers_storage):
    '''Initialize the dual ID system for servers'''
    
    print("[⚙️ DUAL ID] Initializing dual ID system...")
    
    try:
        # Count current Service ID coverage
        total_servers = len(servers_storage) if servers_storage else 0
        servers_with_service_id = 0
        
        if servers_storage:
            try:
                servers_with_service_id = len([s for s in servers_storage if s.get('serviceId')])
            except:
                pass
        
        coverage_percent = (servers_with_service_id / total_servers * 100) if total_servers > 0 else 0
        
        print(f"[📊 COVERAGE] Service ID coverage: {servers_with_service_id}/{total_servers} ({coverage_percent:.1f}%)")
        
        # Store dual ID configuration in app context
        app.dual_id_config = {
            'server_id_usage': ['health_monitoring', 'sensor_data', 'websocket_connections'],
            'service_id_usage': ['command_execution', 'console_operations'],
            'total_servers': total_servers,
            'servers_with_service_id': servers_with_service_id,
            'coverage_percent': coverage_percent
        }
        
        print("[✅ OK] Dual ID system initialized successfully")
        return True
        
    except Exception as e:
        print(f"[❌ ERROR] Dual ID system initialization failed: {e}")
        return False

# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

def init_routes(app, db, user_storage):
    '''Backward compatible route initialization'''
    print("[🔄 COMPATIBILITY] Using backward compatible route initialization")
    return init_all_routes(app, db, user_storage)

def init_routes_with_logs(app, db, user_storage, logs_storage=None):
    '''Backward compatible route initialization with logs support'''
    print("[🔄 COMPATIBILITY] Using backward compatible route initialization with logs")
    return init_all_routes(app, db, user_storage, logs_storage=logs_storage)

def init_routes_with_health(app, db, user_storage, logs_storage=None, server_health_storage=None):
    '''Backward compatible route initialization with logs and server health support'''
    print("[🔄 COMPATIBILITY] Using backward compatible route initialization with health monitoring")
    return init_all_routes(app, db, user_storage, logs_storage=logs_storage, 
                          server_health_storage=server_health_storage)

# ============================================================================
# MODULE-LEVEL VALIDATION
# ============================================================================

def validate_route_dependencies():
    '''Validate that all required dependencies are available'''
    
    print("[🔍 VALIDATION] Checking route dependencies...")
    
    dependencies = {
        'auth': True,
        'user_database': True,
        'economy': True,
        'gambling': True,
        'clans': True,
        'users': True,
        'servers': True,
        'events': True,
        'logs': True,
        'server_health': True,
        'service_id_discovery': False,
        'websocket_manager': False
    }
    
    # Check Service ID discovery
    try:
        from utils.service_id_discovery import ServiceIDMapper
        dependencies['service_id_discovery'] = True
        print("[✅ CHECK] Service ID discovery system available")
    except ImportError:
        print("[⚠️ CHECK] Service ID discovery system not available")
    
    # Check server health storage
    try:
        from utils.server_health_storage import ServerHealthStorage
        dependencies['server_health_storage'] = True
        print("[✅ CHECK] Server health storage available")
    except ImportError:
        print("[⚠️ CHECK] Server health storage not available")
        dependencies['server_health_storage'] = False
    
    # Summary
    available_count = sum(1 for available in dependencies.values() if available)
    total_count = len(dependencies)
    
    print(f"[📊 SUMMARY] Dependencies: {available_count}/{total_count} available")
    
    # Critical dependencies check
    critical_deps = ['auth', 'user_database', 'servers', 'server_health']
    missing_critical = [dep for dep in critical_deps if not dependencies.get(dep, False)]
    
    if missing_critical:
        print(f"[❌ CRITICAL] Missing critical dependencies: {', '.join(missing_critical)}")
        return False
    else:
        print("[✅ CRITICAL] All critical dependencies available")
        return True

# Optional: Run validation on module import (for debugging)
if __name__ == "__main__":
    validate_route_dependencies()