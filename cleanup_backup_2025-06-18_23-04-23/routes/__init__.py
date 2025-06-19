# routes/__init__.py - FIXED VERSION
# Remove circular imports by lazy loading

def init_all_routes(app, db, user_storage, economy_storage=None):
    '''Initialize all routes with lazy loading to prevent circular imports'''
    
    # User Database Routes (foundation)
    from .user_database import init_user_database_routes, user_database_bp
    init_user_database_routes(app, db, user_storage)
    app.register_blueprint(user_database_bp)
    
    # Economy Routes (depends on user database)  
    from .economy import init_economy_routes, economy_bp
    init_economy_routes(app, db, user_storage)
    app.register_blueprint(economy_bp)
    
    # Auth Routes (independent)
    from .auth import init_auth_routes, auth_bp
    init_auth_routes(app, db, user_storage)
    app.register_blueprint(auth_bp)
    
    return app

# Remove any global imports at module level that cause circular dependencies
