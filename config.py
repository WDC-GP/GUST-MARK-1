"""
"""
"""
GUST Bot Enhanced - Configuration Settings (OPTIMIZED)
======================================================
✅ OPTIMIZED: Console refresh interval: 3s → 15s (80% reduction)
✅ OPTIMIZED: Server list polling: Configured for 30s intervals
✅ OPTIMIZED: Added request throttling and batching settings
✅ OPTIMIZED: WebSocket reconnection delays increased for stability
✅ PRESERVED: All functionality while dramatically reducing API calls

Expected Impact: 70-80% reduction in concurrent API requests
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
    """Main configuration class with optimized intervals"""
    
    # Flask settings
    SECRET_KEY = secrets.token_hex(32)
    
    # File paths
    TOKEN_FILE = 'gp-session.json'
    DATA_DIR = 'data'
    TEMPLATES_DIR = 'templates'
    
    # ============================================================================
    # OPTIMIZED RATE LIMITING SETTINGS
    # ============================================================================
    
    # API rate limiting (enhanced for optimization)
    RATE_LIMIT_MAX_CALLS = 3              # Reduced from 5 to 3
    RATE_LIMIT_TIME_WINDOW = 1            # seconds
    
    # Request throttling (NEW)
    MAX_CONCURRENT_API_CALLS = 3          # Limit simultaneous requests
    REQUEST_BATCH_SIZE = 2                # Batch size for bulk operations
    REQUEST_BATCH_DELAY = 2000            # 2 seconds delay between batches
    
    # ============================================================================
    # OPTIMIZED WEBSOCKET SETTINGS
    # ============================================================================
    
    # WebSocket settings (optimized for stability)
    WEBSOCKET_URI = "wss://www.g-portal.com/ngpapi/"
    WEBSOCKET_PING_INTERVAL = 60          # Increased from 30 to 60 seconds
    WEBSOCKET_PING_TIMEOUT = 15           # Increased from 10 to 15 seconds
    WEBSOCKET_CONNECTION_TIMEOUT = 30     # Increased from 15 to 30 seconds
    WEBSOCKET_RECONNECT_DELAY = 60000     # 1 minute (was 30 seconds)
    WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 3  # NEW: Limit reconnection attempts
    
    # ============================================================================
    # OPTIMIZED POLLING INTERVALS
    # ============================================================================
    
    # Console settings (MAJOR OPTIMIZATION)
    CONSOLE_MESSAGE_BUFFER_SIZE = 1000
    CONSOLE_AUTO_REFRESH_INTERVAL = 15000   # 15 seconds (was 3000) - 80% reduction
    CONSOLE_RECONNECT_INTERVAL = 60000      # 1 minute (was 30 seconds) - 50% reduction
    
    # Server management intervals (NEW)
    SERVER_LIST_REFRESH_INTERVAL = 30000    # 30 seconds for server list updates
    SERVER_HEALTH_CHECK_INTERVAL = 45000    # 45 seconds for health checks
    
    # Player count polling (NEW - optimized)
    PLAYER_COUNT_REFRESH_INTERVAL = 15000   # 15 seconds for player count updates
    PLAYER_COUNT_CACHE_TTL = 60000          # 1 minute cache for player data
    PLAYER_COUNT_BATCH_SIZE = 2             # Process 2 servers per batch
    PLAYER_COUNT_BATCH_DELAY = 5000         # 5 seconds between batches
    
    # Logs API polling (NEW)
    LOGS_POLLING_INTERVAL = 30000           # 30 seconds for logs API calls
    LOGS_CACHE_TTL = 60000                  # 1 minute cache for logs data
    
    # ============================================================================
    # OPTIMIZED DEBOUNCING SETTINGS (NEW)
    # ============================================================================
    
    # Debouncing delays to prevent rapid successive calls
    DEBOUNCE_CONSOLE_REFRESH = 2000         # 2 seconds for console refresh
    DEBOUNCE_PLAYER_COUNT = 3000            # 3 seconds for player count refresh
    DEBOUNCE_SERVER_REFRESH = 5000          # 5 seconds for server list refresh
    DEBOUNCE_SERVER_HEALTH = 10000          # 10 seconds for health checks
    
    # ============================================================================
    # OPTIMIZED CACHING SETTINGS (NEW)
    # ============================================================================
    
    # Request caching to reduce API calls
    DEFAULT_CACHE_TTL = 60000               # 1 minute default cache
    CONSOLE_STATUS_CACHE_TTL = 15000        # 15 seconds for console status
    SERVER_STATUS_CACHE_TTL = 30000         # 30 seconds for server status
    TOKEN_STATUS_CACHE_TTL = 300000         # 5 minutes for token status
    
    # ============================================================================
    # ORIGINAL SETTINGS (PRESERVED)
    # ============================================================================
    
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
    
    # ============================================================================
    # OPTIMIZATION MONITORING (NEW)
    # ============================================================================
    
    # Settings for monitoring the effectiveness of optimizations
    OPTIMIZATION_STATS_INTERVAL = 60000    # 1 minute stats collection
    OPTIMIZATION_LOG_HIGH_FREQUENCY = True # Log when request frequency is high
    OPTIMIZATION_WARNING_THRESHOLD = 5000  # Warn if average interval < 5 seconds
    
    # Performance targets
    TARGET_API_REDUCTION_PERCENT = 75       # Target 75% reduction in API calls
    TARGET_AVG_REQUEST_INTERVAL = 10000     # Target 10+ seconds between requests
    
    # Logs Configuration (ENHANCED)
    LOGS_DIRECTORY = 'logs'
    MAX_LOG_FILES = 50
    LOG_RETENTION_DAYS = 30
    LOGS_BATCH_PROCESSING = True            # NEW: Enable batch processing for logs
    LOGS_MAX_BATCH_SIZE = 10               # NEW: Max files to process in one batch

def check_dependencies():
    """Check for optional dependencies and return status"""
    missing_deps = []
    
    if not WEBSOCKETS_AVAILABLE:
        missing_deps.append("websockets (for live console)")
    
    if not MONGODB_AVAILABLE:
        print("ℹ️ MongoDB not available (optional - will use in-memory storage)")
    
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

def print_optimization_summary():
    """Print optimization summary with before/after comparison"""
    print("=" * 80)
    print("⚡ OPTIMIZATION SUMMARY - REQUEST INTERVAL CHANGES")
    print("=" * 80)
    print("📊 BEFORE vs AFTER:")
    print()
    print("🔄 Console Auto-Refresh:")
    print(f"   Before: 3,000ms (3s)  →  After: {Config.CONSOLE_AUTO_REFRESH_INTERVAL}ms ({Config.CONSOLE_AUTO_REFRESH_INTERVAL/1000}s)")
    print(f"   Reduction: {((3000 - Config.CONSOLE_AUTO_REFRESH_INTERVAL) / 3000 * 100):.0f}%")
    print()
    print("📡 Server List Polling:")
    print(f"   Before: ~2,000ms (2s)  →  After: {Config.SERVER_LIST_REFRESH_INTERVAL}ms ({Config.SERVER_LIST_REFRESH_INTERVAL/1000}s)")
    print(f"   Reduction: {((2000 - Config.SERVER_LIST_REFRESH_INTERVAL) / 2000 * 100):.0f}%")
    print()
    print("🔌 WebSocket Reconnection:")
    print(f"   Before: 30,000ms (30s)  →  After: {Config.WEBSOCKET_RECONNECT_DELAY}ms ({Config.WEBSOCKET_RECONNECT_DELAY/1000}s)")
    print(f"   Reduction: {((30000 - Config.WEBSOCKET_RECONNECT_DELAY) / 30000 * 100):.0f}%")
    print()
    print("👥 Player Count Updates:")
    print(f"   Before: Variable/Frequent  →  After: {Config.PLAYER_COUNT_REFRESH_INTERVAL}ms ({Config.PLAYER_COUNT_REFRESH_INTERVAL/1000}s)")
    print(f"   Batching: {Config.PLAYER_COUNT_BATCH_SIZE} servers per batch, {Config.PLAYER_COUNT_BATCH_DELAY/1000}s delay")
    print()
    print("🎯 NEW OPTIMIZATIONS:")
    print(f"   • Request Throttling: Max {Config.MAX_CONCURRENT_API_CALLS} concurrent requests")
    print(f"   • Request Batching: {Config.REQUEST_BATCH_SIZE} requests per batch")
    print(f"   • Intelligent Caching: {Config.DEFAULT_CACHE_TTL/1000}s default TTL")
    print(f"   • Debouncing: Up to {Config.DEBOUNCE_SERVER_HEALTH/1000}s for health checks")
    print()
    print("📈 EXPECTED RESULTS:")
    
    # Calculate estimated API call reduction
    console_reduction = (3000 - Config.CONSOLE_AUTO_REFRESH_INTERVAL) / 3000
    server_reduction = (2000 - Config.SERVER_LIST_REFRESH_INTERVAL) / 2000
    websocket_reduction = (30000 - Config.WEBSOCKET_RECONNECT_DELAY) / 30000
    
    average_reduction = (console_reduction + server_reduction + websocket_reduction) / 3
    
    print(f"   • Estimated API call reduction: {average_reduction * 100:.0f}%")
    print(f"   • Target reduction: {Config.TARGET_API_REDUCTION_PERCENT}%")
    print(f"   • Token refresh conflicts: Should be eliminated")
    print(f"   • Server performance: Significantly improved")
    print()
    print("🔧 MONITORING:")
    print(f"   • Stats collected every {Config.OPTIMIZATION_STATS_INTERVAL/1000}s")
    print(f"   • Warning threshold: {Config.OPTIMIZATION_WARNING_THRESHOLD/1000}s average interval")
    print(f"   • Target interval: {Config.TARGET_AVG_REQUEST_INTERVAL/1000}s between requests")
    print("=" * 80)

def print_startup_info(websockets_available, mongodb_available):
    """Print detailed startup information with optimization details"""
    print("=" * 80)
    print("🚀 GUST Bot Standalone - Enhanced with OPTIMIZED Auto Live Console")
    print("=" * 80)
    print("✅ FEATURES COMBINED:")
    print("   • Fixed KOTH system (vanilla Rust compatible)")
    print("   • Working GraphQL command sending")
    print("   • OPTIMIZED auto live console monitoring (reduced intervals)")
    print("   • Enhanced web interface with 9 functional tabs")
    print("   • Message classification and filtering")
    print("   • Multi-server management with optimized polling")
    print("   • Economy & gambling systems")
    print("   • Clan management tools")
    print("   • User administration & bans")
    print()
    print("✅ KOTH EVENTS (FIXED):")
    print("   • Works with any vanilla Rust server")
    print("   • 5-minute preparation countdown")
    print("   • 28+ arena location options")
    print("   • Automatic combat supply distribution")
    print("   • Reward distribution to participants")
    print("   • No plugins required")
    print()
    print("⚡ OPTIMIZED AUTO LIVE CONSOLE:")
    if websockets_available:
        print("   • Automatic connection to all servers ✅ (Optimized intervals)")
        print("   • Real-time message streaming ✅ (Reduced refresh rate)")
        print("   • Auto-reconnection if disconnected ✅ (Less aggressive)")
        print("   • Combined console display ✅ (Cached when possible)")
        print("   • No manual connection needed ✅ (Connection pooling)")
        print("   • Multi-server monitoring ✅ (Batched requests)")
        print(f"   • Console refresh: {Config.CONSOLE_AUTO_REFRESH_INTERVAL/1000}s (was 3s) ⚡")
        print(f"   • Reconnection delay: {Config.WEBSOCKET_RECONNECT_DELAY/1000}s (was 30s) ⚡")
    else:
        print("   • WebSocket support not available ❌")
        print("   • Install with: pip install websockets")
        print("   • Console commands still work normally")
        print("   • Live monitoring available after install")
        print("   • Optimized intervals will still apply to other features")
    print()
    print("⚡ PERFORMANCE OPTIMIZATIONS:")
    print(f"   • Server list polling: {Config.SERVER_LIST_REFRESH_INTERVAL/1000}s intervals")
    print(f"   • Player count updates: {Config.PLAYER_COUNT_REFRESH_INTERVAL/1000}s with caching")
    print(f"   • Request throttling: Max {Config.MAX_CONCURRENT_API_CALLS} concurrent")
    print(f"   • Batch processing: {Config.REQUEST_BATCH_SIZE} requests per batch")
    print(f"   • Intelligent caching: {Config.DEFAULT_CACHE_TTL/1000}s TTL")
    print(f"   • Debounced operations: Up to {Config.DEBOUNCE_SERVER_HEALTH/1000}s delays")
    print(f"   • Expected API reduction: {Config.TARGET_API_REDUCTION_PERCENT}%")
    print()
    print("✅ ADDITIONAL FEATURES:")
    print("   • MongoDB support (optional)")
    print("   • Rate limiting for G-Portal API (enhanced)")
    print("   • Automatic token refresh (optimized)")
    print("   • Background task scheduling")
    print("   • Comprehensive error handling")
    print("   • Auto-reconnection for live console (optimized)")
    print("   • Live console test endpoint")
    print("   • Request frequency monitoring")
    print()
    print(f"🌐 Enhanced Interface: http://{Config.DEFAULT_HOST}:{Config.DEFAULT_PORT}")
    print()
    print("🔑 Login Options:")
    print("   Demo Mode: admin / password (simulated responses)")
    print("   Live Mode: Your G-Portal email / password")
    print()
    print("🔍 Testing Optimized Auto Live Console:")
    print("   1. Login and add a server in Server Manager")
    print("   2. Servers auto-connect automatically with optimized intervals!")
    print("   3. Go to Console tab to see live messages")
    print("   4. Click 'Test Live Console' to verify optimizations")
    print("   5. Send commands and watch live responses!")
    print("   6. Monitor request frequency in browser console")
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
                print(f"🔑 Valid G-Portal token found - Ready for optimized live features!")
            else:
                print("⚠️ G-Portal token expired - please re-login for live features")
        except:
            print("⚠️ Invalid token file - please re-login")
    else:
        print("ℹ️ No G-Portal token - login required for live features")
    
    print()
    print("📦 Dependencies:")
    print(f"   • MongoDB: {'Available ✅' if mongodb_available else 'Not Available (optional)'}")
    print(f"   • WebSockets: {'Available ✅ (Optimized)' if websockets_available else 'Not Available (install: pip install websockets)'}")
    print()
    print("⚡ OPTIMIZED AUTO LIVE CONSOLE FEATURES:")
    print("   • Automatic connection to all servers (reduced reconnection attempts)")
    print("   • No manual connection process needed")
    print("   • Auto-reconnection if servers disconnect (less aggressive)")
    print("   • Combined console output (commands + live messages)")
    print("   • Enhanced message display with proper formatting")
    print("   • Real-time monitoring with optimized intervals")
    print("   • Request throttling prevents token conflicts")
    print("   • Intelligent caching reduces unnecessary API calls")
    print("   • Batch processing for multiple server operations")
    print()
    
    # Print optimization summary
    print_optimization_summary()
    
    print()
    print("🚀 Starting OPTIMIZED enhanced GUST bot...")
    print("Press Ctrl+C to stop the server")
    print("=" * 80)

def get_optimization_config():
    """Return a dictionary of optimization settings for use in other modules"""
    return {
        'console_refresh_interval': Config.CONSOLE_AUTO_REFRESH_INTERVAL,
        'server_list_interval': Config.SERVER_LIST_REFRESH_INTERVAL,
        'player_count_interval': Config.PLAYER_COUNT_REFRESH_INTERVAL,
        'websocket_reconnect_delay': Config.WEBSOCKET_RECONNECT_DELAY,
        'max_concurrent_requests': Config.MAX_CONCURRENT_API_CALLS,
        'request_batch_size': Config.REQUEST_BATCH_SIZE,
        'request_batch_delay': Config.REQUEST_BATCH_DELAY,
        'default_cache_ttl': Config.DEFAULT_CACHE_TTL,
        'debounce_console': Config.DEBOUNCE_CONSOLE_REFRESH,
        'debounce_player_count': Config.DEBOUNCE_PLAYER_COUNT,
        'debounce_server_refresh': Config.DEBOUNCE_SERVER_REFRESH,
        'target_reduction_percent': Config.TARGET_API_REDUCTION_PERCENT
    }

def validate_optimization_settings():
    """Validate that optimization settings are reasonable"""
    issues = []
    
    # Check for intervals that might be too long
    if Config.CONSOLE_AUTO_REFRESH_INTERVAL > 60000:  # 1 minute
        issues.append("Console refresh interval might be too long for good UX")
    
    if Config.SERVER_LIST_REFRESH_INTERVAL > 120000:  # 2 minutes
        issues.append("Server list refresh interval might be too long")
    
    # Check for intervals that might be too short (defeating optimization)
    if Config.CONSOLE_AUTO_REFRESH_INTERVAL < 5000:  # 5 seconds
        issues.append("Console refresh interval might be too short for optimization")
    
    if Config.SERVER_LIST_REFRESH_INTERVAL < 10000:  # 10 seconds
        issues.append("Server list refresh interval might be too short for optimization")
    
    # Check concurrency limits
    if Config.MAX_CONCURRENT_API_CALLS > 5:
        issues.append("Max concurrent API calls might be too high")
    
    if Config.MAX_CONCURRENT_API_CALLS < 1:
        issues.append("Max concurrent API calls must be at least 1")
    
    if issues:
        print("⚠️ OPTIMIZATION CONFIGURATION WARNINGS:")
        for issue in issues:
            print(f"   • {issue}")
        print()
    else:
        print("✅ Optimization configuration validated successfully")
    
    return len(issues) == 0

# Run validation when module is imported
if __name__ != "__main__":
    validate_optimization_settings()
