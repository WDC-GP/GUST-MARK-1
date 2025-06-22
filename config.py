"""
GUST Bot Enhanced - Configuration Settings (OPTIMIZED + AUTO-AUTHENTICATION)
=============================================================================
✅ OPTIMIZED: Console refresh interval: 3s → 15s (80% reduction)
✅ OPTIMIZED: Server list polling: Configured for 30s intervals
✅ OPTIMIZED: Added request throttling and batching settings
✅ OPTIMIZED: WebSocket reconnection delays increased for stability
✅ FIXED: Added missing logs_polling_interval and other optimization keys
✅ NEW: Auto-authentication system with secure credential storage
✅ NEW: Background token renewal service (every 3 minutes)
✅ NEW: Encrypted credential management with Fernet encryption
✅ PRESERVED: All functionality while dramatically reducing API calls

Expected Impact: 70-80% reduction in concurrent API requests + seamless auth
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

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

# Application Configuration
class Config:
    """Main configuration class with optimized intervals and auto-authentication"""
    
    # Flask settings
    SECRET_KEY = secrets.token_hex(32)
    
    # File paths
    TOKEN_FILE = 'gp-session.json'
    DATA_DIR = 'data'
    TEMPLATES_DIR = 'templates'
    
    # ============================================================================
    # 🔐 AUTO-AUTHENTICATION SETTINGS (NEW)
    # ============================================================================
    
    # Auto-authentication configuration
    AUTO_AUTH_ENABLED = os.environ.get('AUTO_AUTH_ENABLED', 'true').lower() == 'true'
    AUTO_AUTH_ENCRYPTION_KEY = os.environ.get('AUTO_AUTH_KEY', None)
    AUTO_AUTH_RENEWAL_INTERVAL = int(os.environ.get('AUTO_AUTH_INTERVAL', '180'))  # 3 minutes
    AUTO_AUTH_MAX_RETRIES = int(os.environ.get('AUTO_AUTH_MAX_RETRIES', '3'))
    AUTO_AUTH_FAILURE_COOLDOWN = int(os.environ.get('AUTO_AUTH_COOLDOWN', '600'))  # 10 minutes
    
    # Credential storage paths
    CREDENTIALS_FILE = os.path.join('data', 'secure_credentials.enc')
    AUTH_KEY_FILE = os.path.join('data', '.auth_key')
    
    # Auto-auth monitoring and safety
    AUTO_AUTH_MAX_CONCURRENT_ATTEMPTS = 1    # Prevent multiple auth attempts
    AUTO_AUTH_RATE_LIMIT_WINDOW = 30         # 30 seconds between auth attempts
    AUTO_AUTH_SUCCESS_LOG_INTERVAL = 300     # Log success every 5 minutes
    
    @classmethod
    def get_encryption_key(cls):
        """Get or generate encryption key for credentials"""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError("Cryptography package required for auto-authentication. Run: pip install cryptography")
        
        if cls.AUTO_AUTH_ENCRYPTION_KEY:
            return cls.AUTO_AUTH_ENCRYPTION_KEY.encode()
        
        # Generate new key if not exists
        key_file = cls.AUTH_KEY_FILE
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs('data', exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            # Make file read-only (Windows compatible)
            try:
                os.chmod(key_file, 0o600)
            except OSError:
                pass  # Windows may not support chmod
            return key
    
    @classmethod
    def is_auto_auth_available(cls):
        """Check if auto-authentication is available"""
        return CRYPTOGRAPHY_AVAILABLE and cls.AUTO_AUTH_ENABLED
    
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
    
    # Logs API polling (NEW - FIXED: Added the missing setting)
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
    DEBOUNCE_LOGS = 2000                    # 2 seconds for logs refresh (NEW)
    DEBOUNCE_AUTO_AUTH = 30000              # 30 seconds for auto-auth attempts (NEW)
    
    # ============================================================================
    # OPTIMIZED CACHING SETTINGS (NEW)
    # ============================================================================
    
    # Request caching to reduce API calls
    DEFAULT_CACHE_TTL = 60000               # 1 minute default cache
    CONSOLE_STATUS_CACHE_TTL = 15000        # 15 seconds for console status
    SERVER_STATUS_CACHE_TTL = 30000         # 30 seconds for server status
    TOKEN_STATUS_CACHE_TTL = 300000         # 5 minutes for token status
    AUTH_STATUS_CACHE_TTL = 180000          # 3 minutes for auth status (NEW)
    
    # ============================================================================
    # ORIGINAL SETTINGS (PRESERVED)
    # ============================================================================
    
    # G-Portal API settings
    GPORTAL_AUTH_URL = 'https://auth.g-portal.com/auth/realms/master/protocol/openid-connect/token'
    GPORTAL_CLIENT_ID = 'website'
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
        missing_deps.append("pymongo (for persistent storage)")
    
    if not CRYPTOGRAPHY_AVAILABLE:
        missing_deps.append("cryptography (for auto-authentication)")
    
    return WEBSOCKETS_AVAILABLE, MONGODB_AVAILABLE, CRYPTOGRAPHY_AVAILABLE, missing_deps

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
    print("📋 Logs API Polling:")
    print(f"   Before: Variable/Frequent  →  After: {Config.LOGS_POLLING_INTERVAL}ms ({Config.LOGS_POLLING_INTERVAL/1000}s)")
    print(f"   Cache TTL: {Config.LOGS_CACHE_TTL/1000}s")
    print()
    print("🔐 AUTO-AUTHENTICATION:")
    if Config.is_auto_auth_available():
        print(f"   • Status: ✅ Enabled (renewal every {Config.AUTO_AUTH_RENEWAL_INTERVAL}s)")
        print(f"   • Max retries: {Config.AUTO_AUTH_MAX_RETRIES}")
        print(f"   • Failure cooldown: {Config.AUTO_AUTH_FAILURE_COOLDOWN}s")
        print(f"   • Rate limiting: {Config.AUTO_AUTH_RATE_LIMIT_WINDOW}s between attempts")
    else:
        print(f"   • Status: ❌ Disabled (config: {Config.AUTO_AUTH_ENABLED}, crypto: {CRYPTOGRAPHY_AVAILABLE})")
        if not CRYPTOGRAPHY_AVAILABLE:
            print(f"   • Missing: pip install cryptography")
    print()
    print("🎯 NEW OPTIMIZATIONS:")
    print(f"   • Request Throttling: Max {Config.MAX_CONCURRENT_API_CALLS} concurrent requests")
    print(f"   • Request Batching: {Config.REQUEST_BATCH_SIZE} requests per batch")
    print(f"   • Intelligent Caching: {Config.DEFAULT_CACHE_TTL/1000}s default TTL")
    print(f"   • Debouncing: Up to {Config.DEBOUNCE_SERVER_HEALTH/1000}s for health checks")
    print(f"   • Auto-auth Debouncing: {Config.DEBOUNCE_AUTO_AUTH/1000}s for auth attempts")
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
    print(f"   • Auto re-authentication: Seamless background renewal")
    print(f"   • Server performance: Significantly improved")
    print()
    print("🔧 MONITORING:")
    print(f"   • Stats collected every {Config.OPTIMIZATION_STATS_INTERVAL/1000}s")
    print(f"   • Warning threshold: {Config.OPTIMIZATION_WARNING_THRESHOLD/1000}s average interval")
    print(f"   • Target interval: {Config.TARGET_AVG_REQUEST_INTERVAL/1000}s between requests")
    print("=" * 80)

def print_startup_info():
    """Print detailed startup information with optimization and auto-auth details"""
    websockets_available, mongodb_available, crypto_available, missing_deps = check_dependencies()
    
    print("=" * 80)
    print("🚀 GUST Bot Enhanced - OPTIMIZED + AUTO-AUTHENTICATION")
    print("=" * 80)
    print("✅ FEATURES COMBINED:")
    print("   • Fixed KOTH system (vanilla Rust compatible)")
    print("   • Working GraphQL command sending")
    print("   • OPTIMIZED auto live console monitoring (reduced intervals)")
    print("   • AUTO-AUTHENTICATION (seamless re-login)")
    print("   • Enhanced web interface with 9 functional tabs")
    print("   • Message classification and filtering")
    print("   • Multi-server management with optimized polling")
    print("   • Economy & gambling systems")
    print("   • Clan management tools")
    print("   • User administration & bans")
    print("   • Server logs management with direct G-Portal integration")
    print()
    print("✅ KOTH EVENTS (FIXED):")
    print("   • Works with any vanilla Rust server")
    print("   • 5-minute preparation countdown")
    print("   • 28+ arena location options")
    print("   • Automatic combat supply distribution")
    print("   • Reward distribution to participants")
    print("   • No plugins required")
    print()
    print("🔐 AUTO-AUTHENTICATION:")
    if crypto_available and Config.AUTO_AUTH_ENABLED:
        print("   • Status: ✅ ENABLED")
        print("   • Secure credential storage with Fernet encryption")
        print(f"   • Background renewal every {Config.AUTO_AUTH_RENEWAL_INTERVAL} seconds")
        print(f"   • Maximum {Config.AUTO_AUTH_MAX_RETRIES} retries before cooldown")
        print("   • Seamless fallback to credential re-authentication")
        print("   • Zero user intervention required")
    elif not crypto_available:
        print("   • Status: ❌ DISABLED (missing cryptography)")
        print("   • Install with: pip install cryptography")
    elif not Config.AUTO_AUTH_ENABLED:
        print("   • Status: ❌ DISABLED (config setting)")
        print("   • Enable with: AUTO_AUTH_ENABLED=true in .env")
    print()
    print("⚡ OPTIMIZED AUTO LIVE CONSOLE:")
    if websockets_available:
        print("   • WebSocket support: ✅ Available")
        print("   • Real-time messaging: ✅ Enabled")
        print("   • Connection management: ✅ Optimized")
    else:
        print("   • WebSocket support: ❌ Requires 'pip install websockets'")
        print("   • Real-time messaging: ❌ Disabled")
        print("   • Connection management: ⚠️ Limited")
    
    print()
    print("📊 OPTIMIZATION STATUS:")
    print(f"   • Console refresh: {Config.CONSOLE_AUTO_REFRESH_INTERVAL/1000}s intervals")
    print(f"   • Server list updates: {Config.SERVER_LIST_REFRESH_INTERVAL/1000}s")
    print(f"   • Player count polling: {Config.PLAYER_COUNT_REFRESH_INTERVAL/1000}s")
    print(f"   • Logs API polling: {Config.LOGS_POLLING_INTERVAL/1000}s")
    print(f"   • Auto-auth renewal: {Config.AUTO_AUTH_RENEWAL_INTERVAL}s")
    print(f"   • Maximum concurrent requests: {Config.MAX_CONCURRENT_API_CALLS}")
    
    if mongodb_available:
        print("   • MongoDB: ✅ Persistent storage enabled")
    else:
        print("   • MongoDB: ⚠️ In-memory storage (install pymongo for persistence)")
    
    if missing_deps:
        print()
        print("⚠️ MISSING OPTIONAL DEPENDENCIES:")
        for dep in missing_deps:
            print(f"   • {dep}")
    
    print_optimization_summary()
    
    print()
    print("🚀 Starting OPTIMIZED enhanced GUST bot with AUTO-AUTHENTICATION...")
    print("Press Ctrl+C to stop the server")
    print("=" * 80)

def get_optimization_config():
    """
    ✅ ENHANCED: Return a complete dictionary of optimization settings including auto-auth
    """
    return {
        # Core polling intervals
        'console_refresh_interval': Config.CONSOLE_AUTO_REFRESH_INTERVAL,
        'server_list_interval': Config.SERVER_LIST_REFRESH_INTERVAL,
        'player_count_interval': Config.PLAYER_COUNT_REFRESH_INTERVAL,
        'logs_polling_interval': Config.LOGS_POLLING_INTERVAL,
        'server_health_interval': Config.SERVER_HEALTH_CHECK_INTERVAL,
        
        # WebSocket settings
        'websocket_reconnect_delay': Config.WEBSOCKET_RECONNECT_DELAY,
        'websocket_ping_interval': Config.WEBSOCKET_PING_INTERVAL,
        'websocket_ping_timeout': Config.WEBSOCKET_PING_TIMEOUT,
        'websocket_max_reconnects': Config.WEBSOCKET_MAX_RECONNECT_ATTEMPTS,
        
        # Request throttling and batching
        'max_concurrent_requests': Config.MAX_CONCURRENT_API_CALLS,
        'request_batch_size': Config.REQUEST_BATCH_SIZE,
        'request_batch_delay': Config.REQUEST_BATCH_DELAY,
        
        # Caching settings
        'default_cache_ttl': Config.DEFAULT_CACHE_TTL,
        'logs_cache_ttl': Config.LOGS_CACHE_TTL,
        'player_count_cache_ttl': Config.PLAYER_COUNT_CACHE_TTL,
        'console_status_cache_ttl': Config.CONSOLE_STATUS_CACHE_TTL,
        'server_status_cache_ttl': Config.SERVER_STATUS_CACHE_TTL,
        'token_status_cache_ttl': Config.TOKEN_STATUS_CACHE_TTL,
        'auth_status_cache_ttl': Config.AUTH_STATUS_CACHE_TTL,
        
        # Debouncing settings
        'debounce_console': Config.DEBOUNCE_CONSOLE_REFRESH,
        'debounce_player_count': Config.DEBOUNCE_PLAYER_COUNT,
        'debounce_server_refresh': Config.DEBOUNCE_SERVER_REFRESH,
        'debounce_logs': Config.DEBOUNCE_LOGS,
        'debounce_server_health': Config.DEBOUNCE_SERVER_HEALTH,
        'debounce_auto_auth': Config.DEBOUNCE_AUTO_AUTH,
        
        # Player count specific settings
        'player_count_batch_size': Config.PLAYER_COUNT_BATCH_SIZE,
        'player_count_batch_delay': Config.PLAYER_COUNT_BATCH_DELAY,
        
        # Auto-authentication settings
        'auto_auth_enabled': Config.AUTO_AUTH_ENABLED,
        'auto_auth_available': Config.is_auto_auth_available(),
        'auto_auth_renewal_interval': Config.AUTO_AUTH_RENEWAL_INTERVAL,
        'auto_auth_max_retries': Config.AUTO_AUTH_MAX_RETRIES,
        'auto_auth_failure_cooldown': Config.AUTO_AUTH_FAILURE_COOLDOWN,
        'auto_auth_rate_limit_window': Config.AUTO_AUTH_RATE_LIMIT_WINDOW,
        'auto_auth_max_concurrent': Config.AUTO_AUTH_MAX_CONCURRENT_ATTEMPTS,
        
        # Performance targets
        'target_reduction_percent': Config.TARGET_API_REDUCTION_PERCENT,
        'target_avg_request_interval': Config.TARGET_AVG_REQUEST_INTERVAL,
        'optimization_stats_interval': Config.OPTIMIZATION_STATS_INTERVAL,
        'optimization_warning_threshold': Config.OPTIMIZATION_WARNING_THRESHOLD,
        
        # Logs specific settings
        'logs_batch_processing': Config.LOGS_BATCH_PROCESSING,
        'logs_max_batch_size': Config.LOGS_MAX_BATCH_SIZE,
        'logs_directory': Config.LOGS_DIRECTORY,
        'max_log_files': Config.MAX_LOG_FILES,
        'log_retention_days': Config.LOG_RETENTION_DAYS
    }

def validate_optimization_settings():
    """Validate that optimization settings are reasonable"""
    issues = []
    warnings = []
    
    # Check for intervals that might be too long
    if Config.CONSOLE_AUTO_REFRESH_INTERVAL > 60000:  # 1 minute
        warnings.append("Console refresh interval might be too long for good UX")
    
    if Config.SERVER_LIST_REFRESH_INTERVAL > 120000:  # 2 minutes
        warnings.append("Server list refresh interval might be too long")
    
    if Config.LOGS_POLLING_INTERVAL > 60000:  # 1 minute
        warnings.append("Logs polling interval might be too long")
    
    # Check for intervals that might be too short (defeating optimization)
    if Config.CONSOLE_AUTO_REFRESH_INTERVAL < 5000:  # 5 seconds
        warnings.append("Console refresh interval might be too short for optimization")
    
    if Config.SERVER_LIST_REFRESH_INTERVAL < 10000:  # 10 seconds
        warnings.append("Server list refresh interval might be too short for optimization")
    
    if Config.LOGS_POLLING_INTERVAL < 15000:  # 15 seconds
        warnings.append("Logs polling interval might be too short for optimization")
    
    # Check concurrency limits
    if Config.MAX_CONCURRENT_API_CALLS > 5:
        warnings.append("Max concurrent API calls might be too high")
    
    if Config.MAX_CONCURRENT_API_CALLS < 1:
        issues.append("Max concurrent API calls must be at least 1")
    
    # Check cache TTL values
    if Config.DEFAULT_CACHE_TTL < 30000:  # 30 seconds
        warnings.append("Default cache TTL might be too short for effective caching")
    
    # Auto-authentication validation
    if Config.AUTO_AUTH_ENABLED and not CRYPTOGRAPHY_AVAILABLE:
        issues.append("Auto-authentication enabled but cryptography package not installed")
    
    if Config.AUTO_AUTH_RENEWAL_INTERVAL < 120:  # 2 minutes
        warnings.append("Auto-auth renewal interval might be too short (recommended: 3+ minutes)")
    
    if Config.AUTO_AUTH_RENEWAL_INTERVAL > 600:  # 10 minutes
        warnings.append("Auto-auth renewal interval might be too long (tokens may expire)")
    
    if Config.AUTO_AUTH_MAX_RETRIES > 5:
        warnings.append("Auto-auth max retries might be too high")
    
    if Config.AUTO_AUTH_MAX_RETRIES < 1:
        issues.append("Auto-auth max retries must be at least 1")
    
    # Print results
    if issues:
        print("❌ CONFIGURATION ISSUES (must fix):")
        for issue in issues:
            print(f"   • {issue}")
        print()
    
    if warnings:
        print("⚠️ CONFIGURATION WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
        print()
    
    if not issues and not warnings:
        print("✅ All optimization and auto-auth settings validated successfully")
    
    return len(issues) == 0

def get_auto_auth_status():
    """Get detailed auto-authentication status"""
    return {
        'enabled': Config.AUTO_AUTH_ENABLED,
        'available': Config.is_auto_auth_available(),
        'cryptography_installed': CRYPTOGRAPHY_AVAILABLE,
        'credentials_file': Config.CREDENTIALS_FILE,
        'renewal_interval': Config.AUTO_AUTH_RENEWAL_INTERVAL,
        'max_retries': Config.AUTO_AUTH_MAX_RETRIES,
        'failure_cooldown': Config.AUTO_AUTH_FAILURE_COOLDOWN,
        'rate_limit_window': Config.AUTO_AUTH_RATE_LIMIT_WINDOW
    }

# Run validation when module is imported
if __name__ != "__main__":
    validate_optimization_settings()
