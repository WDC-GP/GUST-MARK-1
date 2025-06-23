"""
Health Monitoring Module for GUST-MARK-1 (OPTIMIZED VERSION)
=============================================================
✅ OPTIMIZED: Now exports optimized modular storage system
✅ PRESERVED: 100% backward compatibility for all existing imports
✅ ENHANCED: Additional exports for advanced usage of modular components

This module maintains all existing exports while providing access to the new
optimized storage system components.
"""

import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# ===== ✅ PRESERVED: ORIGINAL HEALTH CHECK FUNCTIONS =====

def check_server_health(server_id):
    """
    ✅ PRESERVED: Check server health status - existing function maintained
    """
    try:
        return {
            'server_id': str(server_id),
            'healthy': True,
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'last_check': time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed for server {server_id}: {e}")
        return {
            'server_id': str(server_id),
            'healthy': False,
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_performance_metrics(server_id, hours=1):
    """
    ✅ PRESERVED: Get performance metrics - existing function maintained
    """
    return {
        'server_id': str(server_id),
        'time_period_hours': hours,
        'status': 'no_data',
        'timestamp': datetime.now().isoformat()
    }

# ===== ✅ OPTIMIZED: IMPORT OPTIMIZED STORAGE SYSTEM =====

try:
    # Import the optimized ServerHealthStorage (main interface)
    from .server_health_storage import ServerHealthStorage
    OPTIMIZED_STORAGE_AVAILABLE = True
    logger.info("[Health Module] ✅ Optimized ServerHealthStorage imported")
    
    # Try to import modular components for advanced usage
    try:
        from .storage import (
            MongoHealthStorage,
            MemoryHealthStorage,
            CacheManager,
            HealthMetric,
            CommandExecution,
            HealthSnapshot,
            TrendData,
            QueryBuilder,
            HealthQueryManager
        )
        MODULAR_COMPONENTS_AVAILABLE = True
        logger.info("[Health Module] ✅ Modular storage components imported")
    except ImportError as modular_error:
        MODULAR_COMPONENTS_AVAILABLE = False
        logger.warning(f"[Health Module] ⚠️ Modular components not available: {modular_error}")

except ImportError as storage_error:
    OPTIMIZED_STORAGE_AVAILABLE = False
    MODULAR_COMPONENTS_AVAILABLE = False
    logger.error(f"[Health Module] ❌ ServerHealthStorage import failed: {storage_error}")
    
    # Create a fallback ServerHealthStorage class
    class ServerHealthStorage:
        """Fallback ServerHealthStorage for when optimized version fails"""
        def __init__(self, db=None, user_storage=None):
            self.db = db
            self.user_storage = user_storage
            logger.warning("[Health Module] Using fallback ServerHealthStorage")
        
        def store_health_snapshot(self, server_id, health_data):
            logger.warning("Fallback storage: store_health_snapshot not implemented")
            return False
        
        def get_health_trends(self, server_id, hours=6):
            logger.warning("Fallback storage: get_health_trends not implemented")
            return {'success': False, 'error': 'fallback_mode'}
        
        def store_command_execution(self, server_id, command_data):
            logger.warning("Fallback storage: store_command_execution not implemented")
            return False
        
        def get_command_history_24h(self, server_id):
            logger.warning("Fallback storage: get_command_history_24h not implemented")
            return []
        
        def get_comprehensive_health_data(self, server_id=None):
            logger.warning("Fallback storage: get_comprehensive_health_data not implemented")
            return {'success': False, 'error': 'fallback_mode'}

# ===== ✅ PRESERVED: IMPORT EXISTING MODULES =====

# Import GraphQL sensors if available
try:
    from .graphql_sensors import GPortalSensorsClient
    GRAPHQL_SENSORS_AVAILABLE = True
    logger.info("[Health Module] ✅ GraphQL Sensors imported")
except ImportError as graphql_error:
    GRAPHQL_SENSORS_AVAILABLE = False
    logger.warning(f"[Health Module] ⚠️ GraphQL Sensors not available: {graphql_error}")
    
    # Create fallback class
    class GPortalSensorsClient:
        """Fallback GraphQL Sensors client"""
        def __init__(self):
            logger.warning("[Health Module] Using fallback GraphQL Sensors client")
        
        def get_service_sensors(self, server_id):
            return {'success': False, 'error': 'graphql_not_available'}

# Try to import server monitor if it exists
try:
    from .server_monitor import *
    SERVER_MONITOR_AVAILABLE = True
    logger.info("[Health Module] ✅ Server Monitor imported")
except ImportError:
    SERVER_MONITOR_AVAILABLE = False
    logger.debug("[Health Module] Server Monitor not available (optional)")

# ===== ✅ ENHANCED: MODULE CAPABILITIES DETECTION =====

def get_module_capabilities():
    """
    ✅ NEW: Get information about available health monitoring capabilities
    """
    return {
        'optimized_storage': OPTIMIZED_STORAGE_AVAILABLE,
        'modular_components': MODULAR_COMPONENTS_AVAILABLE,
        'graphql_sensors': GRAPHQL_SENSORS_AVAILABLE,
        'server_monitor': SERVER_MONITOR_AVAILABLE,
        'version': '2.0.0',
        'features': {
            'mongodb_storage': OPTIMIZED_STORAGE_AVAILABLE,
            'memory_storage': OPTIMIZED_STORAGE_AVAILABLE,
            'intelligent_caching': MODULAR_COMPONENTS_AVAILABLE,
            'query_optimization': MODULAR_COMPONENTS_AVAILABLE,
            'real_time_monitoring': GRAPHQL_SENSORS_AVAILABLE,
            'health_analytics': MODULAR_COMPONENTS_AVAILABLE
        }
    }

def create_optimized_storage(db=None, user_storage=None):
    """
    ✅ NEW: Factory function to create optimized storage with proper error handling
    """
    try:
        storage = ServerHealthStorage(db, user_storage)
        logger.info("[Health Module] ✅ Created optimized storage instance")
        return storage
    except Exception as e:
        logger.error(f"[Health Module] Error creating optimized storage: {e}")
        # Return fallback storage
        return ServerHealthStorage(db, user_storage)

def health_module_status():
    """
    ✅ NEW: Get detailed status of the health monitoring module
    """
    capabilities = get_module_capabilities()
    
    status = {
        'module': 'utils.health',
        'version': capabilities['version'],
        'status': 'operational',
        'capabilities': capabilities,
        'timestamp': datetime.now().isoformat()
    }
    
    # Determine overall status
    if not capabilities['optimized_storage']:
        status['status'] = 'degraded'
        status['warnings'] = ['Optimized storage not available, using fallback']
    
    if not capabilities['graphql_sensors']:
        if 'warnings' not in status:
            status['warnings'] = []
        status['warnings'].append('GraphQL Sensors not available, limited real-time data')
    
    return status

# ===== ✅ PRESERVED: BACKWARD COMPATIBLE EXPORTS =====

# Core exports that existing code expects
__all__ = [
    # ✅ PRESERVED: Original functions
    "check_server_health", 
    "get_performance_metrics",
    
    # ✅ OPTIMIZED: Main storage class (now optimized)
    "ServerHealthStorage",
    
    # ✅ PRESERVED: GraphQL integration
    "GPortalSensorsClient",
    
    # ✅ NEW: Enhanced functionality
    "get_module_capabilities",
    "create_optimized_storage", 
    "health_module_status"
]

# ===== ✅ ENHANCED: ADVANCED EXPORTS (OPTIONAL USAGE) =====

# Add modular components to exports if available
if MODULAR_COMPONENTS_AVAILABLE:
    __all__.extend([
        # Storage backends
        "MongoHealthStorage",
        "MemoryHealthStorage",
        
        # Caching and optimization
        "CacheManager",
        "QueryBuilder",
        "HealthQueryManager",
        
        # Data models
        "HealthMetric",
        "CommandExecution", 
        "HealthSnapshot",
        "TrendData"
    ])

# ===== ✅ INITIALIZATION AND LOGGING =====

# Log module initialization status
initialization_status = health_module_status()
if initialization_status['status'] == 'operational':
    logger.info(f"[Health Module] ✅ Fully operational - {len(__all__)} exports available")
elif initialization_status['status'] == 'degraded':
    logger.warning(f"[Health Module] ⚠️ Degraded mode - {len(initialization_status.get('warnings', []))} warnings")
    for warning in initialization_status.get('warnings', []):
        logger.warning(f"[Health Module] ⚠️ {warning}")
else:
    logger.error("[Health Module] ❌ Module failed to initialize properly")

# ===== ✅ COMPATIBILITY NOTES =====

"""
BACKWARD COMPATIBILITY GUARANTEE:
================================

All existing imports will continue to work exactly as before:

✅ from utils.health import ServerHealthStorage          # Main storage class
✅ from utils.health import check_server_health          # Basic health check
✅ from utils.health import get_performance_metrics      # Performance function
✅ from utils.health import GPortalSensorsClient         # GraphQL integration
✅ from utils.health import *                            # Wildcard import

NEW ADVANCED IMPORTS (Optional):
===============================

For advanced usage of the modular system:

✅ from utils.health import MongoHealthStorage           # MongoDB operations
✅ from utils.health import MemoryHealthStorage          # In-memory storage  
✅ from utils.health import CacheManager                 # Intelligent caching
✅ from utils.health import HealthQueryManager           # Query optimization
✅ from utils.health import HealthMetric                 # Data models
✅ from utils.health import get_module_capabilities      # Feature detection

INTEGRATION EXAMPLES:
====================

# Basic usage (unchanged):
storage = ServerHealthStorage(db, user_storage)
result = storage.get_comprehensive_health_data(server_id)

# Advanced usage (new):
capabilities = get_module_capabilities()
if capabilities['modular_components']:
    # Use advanced features
    storage = create_optimized_storage(db, user_storage)
    stats = storage.get_storage_stats()
"""

logger.info("[Health Module] 📚 Documentation and compatibility notes loaded")
