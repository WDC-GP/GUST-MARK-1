"""
"""
"""
GUST Bot Enhanced - Configuration Settings
==========================================
All configuration settings and dependency checks
"""

# Standard library imports
import json
import os

# Other imports
import secrets



# Try to import optional dependencies
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# Application Configuration
class Config:
    """Main configuration class"""
    
    # Flask settings
    SECRET_KEY = secrets.token_hex(32)
    
    # File paths
    TOKEN_FILE = 'gp-session.json'
    DATA_DIR = 'data'
    TEMPLATES_DIR = 'templates'
    
    # Rate limiting settings
    RATE_LIMIT_MAX_CALLS = 5
    RATE_LIMIT_TIME_WINDOW = 1  # seconds
    
    # WebSocket settings
    WEBSOCKET_URI = "wss://www.g-portal.com/ngpapi/"
    WEBSOCKET_PING_INTERVAL = 30
    WEBSOCKET_PING_TIMEOUT = 10
    WEBSOCKET_CONNECTION_TIMEOUT = 15
    
    # G-Portal API settings
    GPORTAL_AUTH_URL = 'https://auth.g-portal.com/auth/realms/master/protocol/openid-connect/token'
    GPORTAL_API_ENDPOINT = "https://www.g-portal.com/ngpapi/"
    
    # Server settings
    DEFAULT_HOST = '127.0.0.1'
    DEFAULT_PORT = 5000
    
    # MongoDB settings (optional)
    MONGODB_URI = 'mongodb://localhost:27017/'
    MONGODB_DATABASE = 'gust'
    MONGODB_TIMEOUT = 2000
    
    # Console settings
    CONSOLE_MESSAGE_BUFFER_SIZE = 1000
    CONSOLE_AUTO_REFRESH_INTERVAL = 3000  # milliseconds
    CONSOLE_RECONNECT_INTERVAL = 30000  # milliseconds
    
    # KOTH Event settings
    KOTH_DEFAULT_DURATION = 30  # minutes
    KOTH_PREPARATION_TIME = 300  # 5 minutes in seconds
    
    # Arena locations for KOTH events
    ARENA_LOCATIONS = [
        "Launch Site", "Military Base", "Airfield", "Power Plant",
        "Water Treatment Plant", "Train Yard", "Satellite Dish", "Dome",
        "Nuclear Missile Silo", "Supermarket", "Gas Station", "Lighthouse",
        "Mining Outpost", "Compound", "Junkyard", "Quarry", "Desert Base",
        "Arctic Base", "Forest Base", "Island Base", "Mountain Peak",
        "Valley Floor", "Beach Landing", "Crater Site", "Abandoned Town",
        "Research Facility", "Oil Rig", "Wind Farm"
    ]

def check_dependencies():
    """Check for optional dependencies and return status"""
    missing_deps = []
    
    if not WEBSOCKETS_AVAILABLE:
        missing_deps.append("websockets (for live console)")
    
    if not MONGODB_AVAILABLE:
        print("â„¹ï¸ MongoDB not available (optional - will use in-memory storage)")
    
    return WEBSOCKETS_AVAILABLE, MONGODB_AVAILABLE, missing_deps

def ensure_directories():
    """Create necessary directories"""
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(Config.TEMPLATES_DIR, exist_ok=True)

def ensure_data_files():
    """Create essential data files if they don't exist"""
    essential_files = [
        'eventPoints.json', 'numberofkoth.json', 'tempBans.json',
        'banned_users.json', 'customBots.json'
    ]
    
    for file in essential_files:
        filepath = os.path.join(Config.DATA_DIR, file)
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([], f)

def print_startup_info(websockets_available, mongodb_available):
    """Print detailed startup information"""
    print("=" * 80)
    print("ðŸš€ GUST Bot Standalone - Enhanced with Auto Live Console")
    print("=" * 80)
    print("âœ… FEATURES COMBINED:")
    print("   â€¢ Fixed KOTH system (vanilla Rust compatible)")
    print("   â€¢ Working GraphQL command sending")
    print("   â€¢ Auto live console monitoring (all servers)")
    print("   â€¢ Enhanced web interface with 9 functional tabs")
    print("   â€¢ Message classification and filtering")
    print("   â€¢ Multi-server management")
    print("   â€¢ Economy & gambling systems")
    print("   â€¢ Clan management tools")
    print("   â€¢ User administration & bans")
    print()
    print("âœ… KOTH EVENTS (FIXED):")
    print("   â€¢ Works with any vanilla Rust server")
    print("   â€¢ 5-minute preparation countdown")
    print("   â€¢ 28+ arena location options")
    print("   â€¢ Automatic combat supply distribution")
    print("   â€¢ Reward distribution to participants")
    print("   â€¢ No plugins required")
    print()
    print("âœ… AUTO LIVE CONSOLE:")
    if websockets_available:
        print("   â€¢ Automatic connection to all servers âœ…")
        print("   â€¢ Real-time message streaming âœ…")
        print("   â€¢ Auto-reconnection if disconnected âœ…")
        print("   â€¢ Combined console display âœ…")
        print("   â€¢ No manual connection needed âœ…")
        print("   â€¢ Multi-server monitoring âœ…")
    else:
        print("   â€¢ WebSocket support not available âŒ")
        print("   â€¢ Install with: pip install websockets")
        print("   â€¢ Console commands still work normally")
        print("   â€¢ Live monitoring available after install")
    print()
    print("âœ… ADDITIONAL FEATURES:")
    print("   â€¢ MongoDB support (optional)")
    print("   â€¢ Rate limiting for G-Portal API")
    print("   â€¢ Automatic token refresh")
    print("   â€¢ Background task scheduling")
    print("   â€¢ Comprehensive error handling")
    print("   â€¢ Auto-reconnection for live console")
    print("   â€¢ Live console test endpoint")
    print()
    print(f"ðŸŒ Enhanced Interface: http://{Config.DEFAULT_HOST}:{Config.DEFAULT_PORT}")
    print()
    print("ðŸ”‘ Login Options:")
    print("   Demo Mode: admin / password (simulated responses)")
    print("   Live Mode: Your G-Portal email / password")
    print()
    print("ðŸ” Testing Auto Live Console:")
    print("   1. Login and add a server in Server Manager")
    print("   2. Servers auto-connect automatically!")
    print("   3. Go to Console tab to see live messages")
    print("   4. Click 'Test Live Console' to verify")
    print("   5. Send commands and watch live responses!")
    print()
    
    # Check for existing token
    if os.path.exists(Config.TOKEN_FILE):
        try:
            with open(Config.TOKEN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            import time
            current_time = time.time()
            token_exp = data.get('access_token_exp', 0)
            if token_exp > current_time:
                print(f"ðŸ” Valid G-Portal token found - Ready for live features!")
            else:
                print("âš ï¸ G-Portal token expired - please re-login for live features")
        except:
            print("âš ï¸ Invalid token file - please re-login")
    else:
        print("â„¹ï¸ No G-Portal token - login required for live features")
    
    print()
    print("ðŸ“¦ Dependencies:")
    print(f"   â€¢ MongoDB: {'Available âœ…' if mongodb_available else 'Not Available (optional)'}")
    print(f"   â€¢ WebSockets: {'Available âœ…' if websockets_available else 'Not Available (install: pip install websockets)'}")
    print()
    print("ðŸ”§ AUTO LIVE CONSOLE FEATURES:")
    print("   â€¢ Automatic connection to all servers")
    print("   â€¢ No manual connection process needed")
    print("   â€¢ Auto-reconnection if servers disconnect")
    print("   â€¢ Combined console output (commands + live messages)")
    print("   â€¢ Enhanced message display with proper formatting")
    print("   â€¢ Real-time monitoring of all managed servers")
    print()
    print("ðŸš€ Starting enhanced GUST bot...")
    print("Press Ctrl+C to stop the server")
    print("=" * 80)

    # Logs Configuration
    LOGS_DIRECTORY = 'logs'
    MAX_LOG_FILES = 50
    LOG_RETENTION_DAYS = 30
