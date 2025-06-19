# routes/__init__.py - FIXED VERSION WITH LOGS ROUTES INTEGRATION
# Remove circular imports by lazy loading + Add logs routes

def init_all_routes(app, db, user_storage, economy_storage=None, logs_storage=None):
    '''Initialize all routes with lazy loading to prevent circular imports + logs integration'''
    
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
    
    # Server Routes (server management)
    from .servers import init_servers_routes, servers_bp
    init_servers_routes(app, db, [])  # Empty servers list for now
    app.register_blueprint(servers_bp)
    print("[✅ OK] Server routes registered")
    
    # Events Routes (event management)
    from .events import init_events_routes, events_bp
    init_events_routes(app, db, [], {}, [])  # Empty events, vanilla_koth, console_output
    app.register_blueprint(events_bp)
    print("[✅ OK] Events routes registered")
    
    # ============================================================================
    # LOGS ROUTES INTEGRATION - NEW ADDITION
    # ============================================================================
    
    # Logs Routes (log management + player count integration)
    from .logs import init_logs_routes, logs_bp
    
    # Initialize logs storage if not provided
    if logs_storage is None:
        logs_storage = []  # Use in-memory storage as fallback
    
    # Initialize and register logs routes
    init_logs_routes(app, db, logs_storage)
    app.register_blueprint(logs_bp)
    print("[✅ OK] Logs routes registered (with player count integration)")
    
    print("[🚀 COMPLETE] All routes initialized successfully with logs integration")
    
    return app

# ============================================================================
# ENHANCED INITIALIZATION WITH LOGS SUPPORT
# ============================================================================

def init_all_routes_enhanced(app, db, user_storage, economy_storage=None, logs_storage=None, 
                           servers=None, clans=None, users=None, events=None, 
                           vanilla_koth=None, console_output=None):
    '''
    Enhanced route initialization with full parameter support
    This version accepts all the data structures that might be passed from main app
    '''
    
    # Use defaults for missing parameters
    servers = servers or []
    clans = clans or []
    users = users or []
    events = events or []
    vanilla_koth = vanilla_koth or {}
    console_output = console_output or []
    logs_storage = logs_storage or []
    
    print("[🔧 INIT] Starting enhanced route initialization...")
    
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
    
    # Server Routes (with actual data)
    from .servers import init_servers_routes, servers_bp
    init_servers_routes(app, db, servers)
    app.register_blueprint(servers_bp)
    print("[✅ OK] Server routes registered")
    
    # Events Routes (with actual data)
    from .events import init_events_routes, events_bp
    init_events_routes(app, db, events, vanilla_koth, console_output)
    app.register_blueprint(events_bp)
    print("[✅ OK] Events routes registered")
    
    # Logs Routes (with logs storage and player count integration)
    from .logs import init_logs_routes, logs_bp
    init_logs_routes(app, db, logs_storage)
    app.register_blueprint(logs_bp)
    print("[✅ OK] Logs routes registered (with player count integration)")
    
    print("[🚀 COMPLETE] Enhanced route initialization complete")
    print(f"[📊 STATS] Initialized with {len(servers)} servers, {len(users)} users, {len(clans)} clans")
    print(f"[📋 LOGS] Logs storage initialized with {len(logs_storage)} entries")
    
    return app

# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

# Keep the original function name for backward compatibility
def init_routes(app, db, user_storage):
    '''Backward compatible route initialization'''
    return init_all_routes(app, db, user_storage)

# Remove any global imports at module level that cause circular dependencies
# All imports are now done locally within functions