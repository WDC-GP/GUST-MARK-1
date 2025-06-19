"""
GUST Bot Enhanced - WebSocket Package
====================================
WebSocket client and manager for live console monitoring

This package provides real-time WebSocket connections to G-Portal servers
for live console monitoring. Components are conditionally imported based
on websockets package availability.
"""


from config import WEBSOCKETS_AVAILABLE

if WEBSOCKETS_AVAILABLE:
    try:
        from .client import GPortalWebSocketClient
        from .manager import WebSocketManager
        
        __all__ = ['GPortalWebSocketClient', 'WebSocketManager']
        
        # Package is fully functional
        PACKAGE_STATUS = "available"
        
    except ImportError as e:
        # Fallback if there are import issues even with websockets installed
        __all__ = []
        PACKAGE_STATUS = "import_error"
        
        def GPortalWebSocketClient(*args, **kwargs):
            raise RuntimeError("WebSocket client not available due to import error")
        
        def WebSocketManager(*args, **kwargs):
            raise RuntimeError("WebSocket manager not available due to import error")

else:
    # WebSocket package not available
    __all__ = []
    PACKAGE_STATUS = "not_available"
    
    def GPortalWebSocketClient(*args, **kwargs):
        raise RuntimeError(
            "WebSocket support not available. Install with: pip install websockets"
        )
    
    def WebSocketManager(*args, **kwargs):
        raise RuntimeError(
            "WebSocket support not available. Install with: pip install websockets"
        )

def get_websocket_status():
    """
    Get WebSocket package status information
    
    Returns:
        dict: Status information including availability and components
    """
    return {
        "websockets_available": WEBSOCKETS_AVAILABLE,
        "package_status": PACKAGE_STATUS,
        "components_loaded": len(__all__),
        "available_components": __all__,
        "install_command": "pip install websockets" if not WEBSOCKETS_AVAILABLE else None
    }

def check_websocket_support():
    """
    Check if WebSocket support is available and working
    
    Returns:
        bool: True if WebSocket support is fully available
    """
    return WEBSOCKETS_AVAILABLE and PACKAGE_STATUS == "available"

# Convenience function for checking availability
is_available = check_websocket_support

# Version info for the WebSocket package
__version__ = "1.0.0"
__author__ = "GUST Bot Enhanced"
__description__ = "WebSocket client and manager for G-Portal live console monitoring"
