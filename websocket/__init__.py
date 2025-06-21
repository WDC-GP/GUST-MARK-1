"""
GUST Bot Enhanced - WebSocket Package (FIXED IMPORTS)
===============================================================
✅ FIXED: Import order and error handling
✅ FIXED: Proper class name exports
✅ FIXED: Sensor bridge integration
"""

from config import WEBSOCKETS_AVAILABLE

if WEBSOCKETS_AVAILABLE:
    try:
        from .client import GPortalWebSocketClient
        from .manager import EnhancedWebSocketManager
        from .sensor_bridge import WebSocketSensorBridge
        
        # ✅ FIXED: Export correct classes with proper names
        __all__ = [
            'GPortalWebSocketClient', 
            'EnhancedWebSocketManager',
            'WebSocketSensorBridge'
        ]
        
        # ✅ FIXED: Backward compatibility alias
        WebSocketManager = EnhancedWebSocketManager
        
        # Package is fully functional
        PACKAGE_STATUS = "available"
        SENSOR_SUPPORT = True
        
        # Create logging for successful import
        import logging
        logger = logging.getLogger(__name__)
        logger.info("✅ WebSocket package imported successfully with sensor support")
        
    except ImportError as e:
        # Fallback if there are import issues even with websockets installed
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ WebSocket component import error: {e}")
        
        __all__ = []
        PACKAGE_STATUS = "import_error"
        SENSOR_SUPPORT = False
        
        def GPortalWebSocketClient(*args, **kwargs):
            raise RuntimeError(f"WebSocket client not available due to import error: {e}")
        
        def EnhancedWebSocketManager(*args, **kwargs):
            raise RuntimeError(f"Enhanced WebSocket manager not available due to import error: {e}")
            
        def WebSocketSensorBridge(*args, **kwargs):
            raise RuntimeError(f"WebSocket sensor bridge not available due to import error: {e}")
        
        # Backward compatibility
        WebSocketManager = EnhancedWebSocketManager

else:
    # WebSocket package not available
    __all__ = []
    PACKAGE_STATUS = "not_available"
    SENSOR_SUPPORT = False
    
    def GPortalWebSocketClient(*args, **kwargs):
        raise RuntimeError(
            "WebSocket support not available. Install with: pip install websockets==11.0.3"
        )
    
    def EnhancedWebSocketManager(*args, **kwargs):
        raise RuntimeError(
            "Enhanced WebSocket support not available. Install with: pip install websockets==11.0.3"
        )
        
    def WebSocketSensorBridge(*args, **kwargs):
        raise RuntimeError(
            "WebSocket sensor bridge not available. Install with: pip install websockets==11.0.3"
        )
    
    # Backward compatibility
    WebSocketManager = EnhancedWebSocketManager

def get_websocket_status():
    """
    Get WebSocket package status information including sensor support
    
    Returns:
        dict: Status information including availability and components
    """
    return {
        "websockets_available": WEBSOCKETS_AVAILABLE,
        "package_status": PACKAGE_STATUS,
        "sensor_support": SENSOR_SUPPORT,
        "components_loaded": len(__all__),
        "available_components": __all__,
        "install_command": "pip install websockets==11.0.3" if not WEBSOCKETS_AVAILABLE else None,
        "features": {
            "console_monitoring": WEBSOCKETS_AVAILABLE and PACKAGE_STATUS == "available",
            "sensor_data": SENSOR_SUPPORT,
            "health_bridge": SENSOR_SUPPORT,
            "real_time_metrics": SENSOR_SUPPORT
        }
    }

def check_websocket_support():
    """
    Check if WebSocket support is available and working
    
    Returns:
        bool: True if WebSocket support is fully available
    """
    return WEBSOCKETS_AVAILABLE and PACKAGE_STATUS == "available"

def check_sensor_support():
    """
    Check if sensor data support is available
    
    Returns:
        bool: True if sensor data support is available
    """
    return SENSOR_SUPPORT and PACKAGE_STATUS == "available"

def create_websocket_manager(gust_bot, enable_sensors=True):
    """
    Create and configure WebSocket manager with optional sensor support
    
    Args:
        gust_bot: Reference to main GUST bot instance
        enable_sensors (bool): Whether to enable sensor bridge
        
    Returns:
        EnhancedWebSocketManager or None: Configured manager or None if not available
    """
    if not check_websocket_support():
        return None
        
    try:
        manager = EnhancedWebSocketManager(gust_bot)
        
        if enable_sensors and check_sensor_support():
            # Sensor bridge will be initialized when needed
            pass
            
        return manager
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Error creating WebSocket manager: {e}")
        return None

def create_sensor_bridge(websocket_manager, server_health_storage=None):
    """
    Create sensor bridge for WebSocket manager
    
    Args:
        websocket_manager: WebSocket manager instance
        server_health_storage: Optional server health storage system
        
    Returns:
        WebSocketSensorBridge or None: Sensor bridge or None if not available
    """
    if not check_sensor_support():
        return None
        
    try:
        return WebSocketSensorBridge(websocket_manager, server_health_storage)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Error creating sensor bridge: {e}")
        return None

# Convenience functions for checking availability
is_available = check_websocket_support
has_sensor_support = check_sensor_support

# Version info for the WebSocket package
__version__ = "2.1.0"  # Updated version for fixes
__author__ = "GUST Bot Enhanced"
__description__ = "WebSocket client and manager for G-Portal live console monitoring and real-time sensor data"
__features__ = [
    "Live console monitoring",
    "Real-time sensor data (CPU, memory, uptime)",
    "Server configuration monitoring", 
    "Health metrics calculation",
    "Automatic reconnection",
    "Connection health monitoring",
    "Message classification",
    "Sensor data bridge integration"
]

# Export sensor-related constants
SENSOR_DATA_FIELDS = [
    'cpu_usage',
    'cpu_total', 
    'memory_percent',
    'memory_used_mb',
    'memory_total_mb',
    'uptime_seconds',
    'timestamp',
    'server_id'
]

CONFIG_DATA_FIELDS = [
    'server_state',
    'fsm_state', 
    'is_transitioning',
    'ip_address',
    'timestamp',
    'server_id'
]

HEALTH_STATUS_LEVELS = [
    'healthy',    # 80%+
    'warning',    # 60-79%
    'critical'    # <60%
]