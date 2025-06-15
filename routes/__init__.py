"""
GUST Bot Enhanced - Routes Package
=================================
Flask route blueprints for different features

This package contains all Flask route blueprints organized by functionality:
- Authentication and session management
- Server management operations
- Event management (KOTH events, etc.)
- Economy system operations
- Gambling games
- Clan management
- User administration and moderation

Each route module is designed to be modular and can be used independently.
"""

from .auth import auth_bp
from .servers import init_servers_routes
from .events import init_events_routes
from .economy import init_economy_routes
from .gambling import init_gambling_routes
from .clans import init_clans_routes
from .users import init_users_routes

__all__ = [
    'auth_bp',
    'init_servers_routes',
    'init_events_routes', 
    'init_economy_routes',
    'init_gambling_routes',
    'init_clans_routes',
    'init_users_routes',
    'get_routes_info',
    'register_all_routes'
]

# Package metadata
__version__ = "1.0.0"
__author__ = "GUST Bot Enhanced"
__description__ = "Flask route blueprints for GUST Bot features"

def get_routes_info():
    """
    Get information about all available route modules
    
    Returns:
        dict: Information about route modules and their features
    """
    return {
        'package': 'routes',
        'version': __version__,
        'description': __description__,
        'available_routes': [
            {
                'name': 'auth',
                'blueprint': 'auth_bp',
                'description': 'Authentication and session management',
                'endpoints': ['login', 'logout', 'token_status', 'token_refresh'],
                'features': ['g_portal_auth', 'demo_mode', 'session_management']
            },
            {
                'name': 'servers',
                'blueprint': 'servers_bp',
                'description': 'Server management operations',
                'endpoints': ['add', 'update', 'delete', 'ping', 'bulk_action'],
                'features': ['crud_operations', 'status_monitoring', 'bulk_actions']
            },
            {
                'name': 'events',
                'blueprint': 'events_bp',
                'description': 'Event management (KOTH, etc.)',
                'endpoints': ['koth_start', 'koth_stop', 'event_status'],
                'features': ['koth_events', 'vanilla_compatible', 'multiple_arenas']
            },
            {
                'name': 'economy',
                'blueprint': 'economy_bp',
                'description': 'Economy system operations',
                'endpoints': ['balance', 'transfer', 'add_coins', 'transactions'],
                'features': ['coin_management', 'transactions', 'leaderboards']
            },
            {
                'name': 'gambling',
                'blueprint': 'gambling_bp',
                'description': 'Gambling games (slots, coinflip, dice)',
                'endpoints': ['slots', 'coinflip', 'dice', 'history'],
                'features': ['multiple_games', 'history_tracking', 'statistics']
            },
            {
                'name': 'clans',
                'blueprint': 'clans_bp',
                'description': 'Clan management operations',
                'endpoints': ['create', 'join', 'leave', 'kick', 'update'],
                'features': ['clan_creation', 'member_management', 'leadership']
            },
            {
                'name': 'users',
                'blueprint': 'users_bp',
                'description': 'User administration and moderation',
                'endpoints': ['temp_ban', 'permanent_ban', 'unban', 'give_items'],
                'features': ['ban_management', 'item_giving', 'user_history']
            }
        ],
        'total_modules': 7,
        'initialization_required': ['servers', 'events', 'economy', 'gambling', 'clans', 'users'],
        'direct_blueprints': ['auth']
    }

def register_all_routes(app, **kwargs):
    """
    Register all route blueprints with the Flask application
    
    Args:
        app: Flask application instance
        **kwargs: Dependencies for route initialization (db, storage objects, etc.)
    
    Returns:
        dict: Registration results for each route module
    """
    import logging
    logger = logging.getLogger(__name__)
    
    registration_results = {}
    
    try:
        # Register auth blueprint (no initialization needed)
        app.register_blueprint(auth_bp)
        registration_results['auth'] = {'success': True, 'type': 'direct_blueprint'}
        logger.info("✅ Auth routes registered")
        
        # Initialize and register other route modules
        route_initializers = {
            'servers': init_servers_routes,
            'events': init_events_routes,
            'economy': init_economy_routes,
            'gambling': init_gambling_routes,
            'clans': init_clans_routes,
            'users': init_users_routes
        }
        
        for route_name, initializer in route_initializers.items():
            try:
                # Call initializer with app and dependencies
                blueprint = initializer(app, **kwargs)
                app.register_blueprint(blueprint)
                registration_results[route_name] = {'success': True, 'type': 'initialized_blueprint'}
                logger.info(f"✅ {route_name.title()} routes registered")
                
            except Exception as e:
                registration_results[route_name] = {
                    'success': False, 
                    'error': str(e),
                    'type': 'initialization_error'
                }
                logger.error(f"❌ Failed to register {route_name} routes: {e}")
        
        # Summary
        successful = sum(1 for result in registration_results.values() if result['success'])
        total = len(registration_results)
        
        logger.info(f"📊 Route registration complete: {successful}/{total} successful")
        
        return {
            'summary': {
                'total_modules': total,
                'successful': successful,
                'failed': total - successful
            },
            'details': registration_results
        }
        
    except Exception as e:
        logger.error(f"❌ Critical error during route registration: {e}")
        return {
            'summary': {
                'total_modules': 0,
                'successful': 0,
                'failed': 1,
                'critical_error': str(e)
            },
            'details': {}
        }

# Validation functions
def validate_route_dependencies(**kwargs):
    """
    Validate that required dependencies are provided for route initialization
    
    Args:
        **kwargs: Dependencies to validate
        
    Returns:
        tuple: (is_valid, missing_dependencies)
    """
    required_deps = ['db', 'servers_storage', 'events_storage', 'economy_storage', 'clans_storage']
    optional_deps = ['console_output', 'vanilla_koth', 'gust_bot']
    
    missing = []
    for dep in required_deps:
        if dep not in kwargs:
            missing.append(dep)
    
    return len(missing) == 0, missing

def get_route_health():
    """
    Get health status of the routes package
    
    Returns:
        dict: Health status information
    """
    return {
        'package_loaded': True,
        'blueprints_available': len(__all__),
        'modules_importable': True,
        'ready_for_registration': True,
        'version': __version__
    }